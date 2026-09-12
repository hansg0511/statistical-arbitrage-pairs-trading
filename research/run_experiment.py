import argparse
import json
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import backtrader as bt
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings

if __package__ in {None, ""}:  # Support both `python research/...` and `python -m ...`.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.cli import parse_args
from src.constants import TICKERS_CORE, TICKERS_SP500, SECTOR_MAP_CORE, SECTOR_MAP_SP500
from src.data_loader import DataLoader, load_or_fetch_prices
from src.walk_forward import FoldBuilder
from src.pair_selection import PairSelector
from src.backtest import PairTradingStrategy, ZScoreData, prepare_backtest_data
from src.pair_cache import PoolCache, filter_pairs_by_half_life, filter_pairs_by_return_divergence
from src.earnings_screen import EarningsScreen

warnings.filterwarnings('ignore')

_global = {}


def _write_run_status(output_dir, status, expected_folds=None,
                      completed_folds=None, failed_folds=None, reason=None):
    """Persist machine-readable run state so partial output cannot look valid."""
    payload = {'status': status}
    if expected_folds is not None:
        payload['expected_folds'] = int(expected_folds)
    if completed_folds is not None:
        payload['completed_folds'] = int(completed_folds)
    if failed_folds:
        payload['failed_folds'] = sorted(int(i) for i in failed_folds)
    if reason:
        payload['reason'] = str(reason)

    path = os.path.join(output_dir, 'run_status.json')
    temp_path = path + '.tmp'
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
    os.replace(temp_path, path)


def summarize_exposure(rows, dates=None):
    """Summarize daily gross, open-pair, and estimated-margin utilization."""
    if not rows:
        return {
            'average_gross_utilization': 0.0,
            'median_gross_utilization': 0.0,
            'gross_utilization_p95': 0.0,
            'gross_utilization_p99': 0.0,
            'peak_gross_utilization': 0.0,
            'average_open_pairs': 0.0,
            'peak_open_pairs': 0,
            'average_margin_utilization': 0.0,
            'margin_utilization_p95': 0.0,
            'margin_utilization_p99': 0.0,
            'peak_margin_utilization': 0.0,
            'average_maintenance_margin_utilization': 0.0,
            'maintenance_margin_utilization_p95': 0.0,
            'maintenance_margin_utilization_p99': 0.0,
            'peak_maintenance_margin_utilization': 0.0,
        }

    frame = pd.DataFrame(rows)
    if dates is not None:
        frame['date'] = pd.to_datetime(frame['date'])
        frame = frame[frame['date'].isin(pd.to_datetime(dates))]
        if frame.empty:
            return summarize_exposure([])

    # Fold outputs represent separate virtual accounts. Aggregate their dollar
    # numerators and equity by date before calculating account-level ratios.
    exposure_columns = {
        'equity', 'gross_exposure', 'open_pairs',
        'estimated_initial_margin_requirement',
        'estimated_maintenance_margin_requirement',
    }
    if exposure_columns.issubset(frame.columns):
        sum_columns = sorted(exposure_columns - {'open_pairs'}) + ['open_pairs']
        for column in sum_columns:
            frame[column] = pd.to_numeric(frame[column], errors='coerce').fillna(0.0)
        frame = frame.groupby('date', as_index=False)[sum_columns].sum()
        equity = frame['equity']
        gross = pd.Series(
            np.where(equity > 0, frame['gross_exposure'] / equity, 0.0),
            index=frame.index,
        )
        margin = pd.Series(
            np.where(
                equity > 0,
                frame['estimated_initial_margin_requirement'] / equity,
                0.0,
            ),
            index=frame.index,
        )
        maintenance = pd.Series(
            np.where(
                equity > 0,
                frame['estimated_maintenance_margin_requirement'] / equity,
                0.0,
            ),
            index=frame.index,
        )
        open_pairs = frame['open_pairs']
    else:
        # Retain compatibility with older or minimal diagnostic rows.
        gross = pd.to_numeric(frame['gross_utilization'], errors='coerce').fillna(0.0)
        margin = pd.to_numeric(
            frame['initial_margin_utilization'], errors='coerce'
        ).fillna(0.0)
        maintenance = pd.to_numeric(
            frame['maintenance_margin_utilization'], errors='coerce'
        ).fillna(0.0)
        open_pairs = pd.to_numeric(frame['open_pairs'], errors='coerce').fillna(0.0)

    def percentiles(values):
        return (
            float(values.mean()),
            float(values.median()),
            float(np.percentile(values, 95)),
            float(np.percentile(values, 99)),
            float(values.max()),
        )

    gross_stats = percentiles(gross)
    margin_stats = percentiles(margin)
    maintenance_stats = percentiles(maintenance)
    return {
        'average_gross_utilization': round(gross_stats[0], 8),
        'median_gross_utilization': round(gross_stats[1], 8),
        'gross_utilization_p95': round(gross_stats[2], 8),
        'gross_utilization_p99': round(gross_stats[3], 8),
        'peak_gross_utilization': round(gross_stats[4], 8),
        'average_open_pairs': round(float(open_pairs.mean()), 4),
        'peak_open_pairs': int(open_pairs.max()),
        'average_margin_utilization': round(margin_stats[0], 8),
        'margin_utilization_p95': round(margin_stats[2], 8),
        'margin_utilization_p99': round(margin_stats[3], 8),
        'peak_margin_utilization': round(margin_stats[4], 8),
        'average_maintenance_margin_utilization': round(maintenance_stats[0], 8),
        'maintenance_margin_utilization_p95': round(maintenance_stats[2], 8),
        'maintenance_margin_utilization_p99': round(maintenance_stats[3], 8),
        'peak_maintenance_margin_utilization': round(maintenance_stats[4], 8),
    }


def _clear_run_outputs(output_dir, trade_logs_dir):
    """Remove artifacts from an older attempt before writing a new run."""
    filenames = [
        'metrics.json', 'oos_fold_summary.csv', 'daily_returns.csv',
        'daily_returns_active_only.csv', 'trade_marks.csv',
        'rejected_orders.csv', 'signal_log.csv', 'daily_margin.csv',
        'daily_exposure.csv', 'sizing_audit.csv', 'selected_pairs.csv',
        'run.log', 'run_status.json', 'run_status.json.tmp',
    ]
    for filename in filenames:
        path = os.path.join(output_dir, filename)
        if os.path.exists(path):
            os.remove(path)

    trade_log = os.path.join(trade_logs_dir, 'test_trade_log.csv')
    if os.path.exists(trade_log):
        os.remove(trade_log)


def _worker_init(master_df, args_dict, TICKERS, SECTOR_MAP, universe_name, pool_path, earnings_screen):
    _global['master_df'] = master_df
    _global['args'] = argparse.Namespace(**args_dict)
    _global['TICKERS'] = TICKERS
    _global['SECTOR_MAP'] = SECTOR_MAP
    _global['universe_name'] = universe_name
    _global['pair_selector'] = PairSelector(pvalue_threshold=args_dict['pvalue'])
    _global['pool_cache'] = PoolCache(pool_path) if pool_path else None
    _global['earnings_screen'] = earnings_screen
    _global['universe_name'] = universe_name

def _process_fold(i, fold):
    return _process_fold_coint(i, fold, _global)

def _collect_results(cerebro, i, test_start, test_end, output_lines,
                     n_pairs=0, selected_pairs=None):
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', timeframe=bt.TimeFrame.Days, riskfreerate=0.0)
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='returns')

    results = cerebro.run()
    res = results[0]

    daily_rets = res.analyzers.returns.get_analysis()
    daily_returns = []
    for dt, ret in daily_rets.items():
        daily_returns.append({'date': dt, 'pnl_pct': ret, 'fold_id': i})

    logs = res.trade_logs
    s = res.analyzers.sharpe.get_analysis().get('sharperatio', 0)
    fold_summary = {
        'fold': i,
        'start': test_start,
        'end': test_end,
        'sharpe': s if s and not np.isnan(s) else 0.0,
        'trades': len(logs),
        'pairs': n_pairs,
    }

    daily_active_counts = []
    for rec in getattr(res, 'daily_active_counts', []):
        daily_active_counts.append({
            'date': rec['date'], 'count': rec['count'],
            'deployed_capital': rec.get('deployed_capital', 0.0), 'fold_id': i
        })

    rejected_orders = []
    for rec in getattr(res, 'rejected_orders', []):
        rec['fold_id'] = i
        rejected_orders.append(rec)

    trade_marks = []
    for rec in getattr(res, 'trade_marks', []):
        rec['fold_id'] = i
        trade_marks.append(rec)

    signal_log = []
    for rec in getattr(res, 'signal_log', []):
        rec['fold_id'] = i
        signal_log.append(rec)

    daily_margin = []
    for rec in getattr(res, 'daily_margin', []):
        rec['fold_id'] = i
        daily_margin.append(rec)

    daily_exposure = []
    for rec in getattr(res, 'daily_exposure', []):
        rec['fold_id'] = i
        daily_exposure.append(rec)

    sizing_audit = []
    for rec in getattr(res, 'sizing_audit', []):
        rec['fold_id'] = i
        sizing_audit.append(rec)

    selected_pair_rows = []
    for record in selected_pairs or []:
        record['fold_id'] = i
        selected_pair_rows.append(record)

    for log in logs:
        log['fold_id'] = i

    rejected_count = sum(1 for _ in getattr(res, 'rejected_orders', []))
    sh = s if s is not None and not np.isnan(s) else 0.0
    output_lines.append(f"Fold {i} Complete: Sharpe={sh:.2f}, Trades={len(logs)}, Rejected={rejected_count}")

    return (fold_summary, logs, daily_returns, daily_active_counts,
            rejected_orders, trade_marks, signal_log, daily_margin,
            daily_exposure, sizing_audit, selected_pair_rows, output_lines)


def _collect_zero_pair_fold(
    master_df, i, test_start, test_end, output_lines, initial_cash=1_000_000.0
):
    """Represent a valid formation window with no eligible pairs."""
    close_prices = master_df['Close'] if isinstance(master_df.columns, pd.MultiIndex) else master_df
    dates = [
        pd.Timestamp(dt).date()
        for dt in close_prices.loc[str(test_start):str(test_end)].index
    ]
    daily_returns = [
        {'date': dt, 'pnl_pct': 0.0, 'fold_id': i}
        for dt in dates
    ]
    daily_active_counts = [
        {'date': dt, 'count': 0, 'deployed_capital': 0.0, 'fold_id': i}
        for dt in dates
    ]
    daily_exposure = [
        {
            'date': dt,
            'equity': float(initial_cash),
            'cash': float(initial_cash),
            'gross_long': 0.0,
            'gross_short': 0.0,
            'gross_exposure': 0.0,
            'gross_utilization': 0.0,
            'open_pairs': 0,
            'estimated_initial_margin_requirement': 0.0,
            'initial_margin_utilization': 0.0,
            'estimated_maintenance_margin_requirement': 0.0,
            'maintenance_margin_utilization': 0.0,
            'fold_id': i,
        }
        for dt in dates
    ]
    output_lines.append(f"Fold {i} Complete: Sharpe=0.00, Trades=0, Rejected=0")
    fold_summary = {
        'fold': i,
        'start': test_start,
        'end': test_end,
        'sharpe': 0.0,
        'trades': 0,
        'pairs': 0,
    }
    return (
        fold_summary, [], daily_returns, daily_active_counts,
        [], [], [], [], daily_exposure, [], [], output_lines,
    )

def _process_fold_coint(i, fold, g):
    master_df = g['master_df']
    args = g['args']
    TICKERS = g['TICKERS']
    SECTOR_MAP = g['SECTOR_MAP']
    universe_name = g['universe_name']
    selector = g['pair_selector']
    pool_cache = g['pool_cache']
    earnings_screen = g['earnings_screen']

    sel_start, sel_end, _, _, test_start, test_end = fold
    output_lines = []
    output_lines.append(f"\n--- Processing Fold {i} [Test: {test_start} to {test_end}] ---")

    viable_pairs = None

    # A cached window is authoritative, including an empty filtered result.
    # Live selection is used only when the requested window is not cached.
    pool_hit = pool_cache is not None and pool_cache.has(sel_start)
    if pool_hit:
        viable_pairs = pool_cache.select(
            sel_start, universe_name, SECTOR_MAP,
            cross_sector=args.cross_sector,
            pvalue=args.pvalue,
            log_space=args.log_space,
        )
        if not pool_cache.divergence_matches(args.return_divergence):
            close_prices = master_df['Close'] if isinstance(master_df.columns, pd.MultiIndex) else master_df
            viable_pairs = filter_pairs_by_return_divergence(
                viable_pairs, close_prices, str(sel_start), str(sel_end), args.return_divergence
            )
        output_lines.append(
            f"  [pool {os.path.basename(pool_cache.path)} HIT for sel {sel_start} to {sel_end}: {len(viable_pairs)} pairs]"
        )
    else:
        viable_pairs = selector.select_pairs(
            master_df, SECTOR_MAP, str(sel_start), str(sel_end),
            same_sector_only=not args.cross_sector,
            return_divergence_threshold=args.return_divergence,
            log_space=args.log_space
        )
        output_lines.append(f"  [live select_pairs for sel {sel_start} to {sel_end}: {len(viable_pairs)} pairs]")

    # Cache routes can contain rows produced in a different price space or
    # before the half-life validity filter was applied. Validate once more
    # before the max_pairs * 3 candidate window is taken below.
    active_log_space = args.log_space
    before_half_life_filter = len(viable_pairs)
    viable_pairs = filter_pairs_by_half_life(viable_pairs, log_space=active_log_space)
    removed_half_life = before_half_life_filter - len(viable_pairs)
    if removed_half_life:
        output_lines.append(
            f"  Half-life filter ({'log' if active_log_space else 'raw'} space): "
            f"removed {removed_half_life} invalid pairs"
        )

    if viable_pairs.empty:
        output_lines.append(f"No viable pairs found for fold {i}")
        return _collect_zero_pair_fold(
            master_df, i, test_start, test_end, output_lines,
            initial_cash=args.initial_cash,
        )

    # Pre-filter pairs: ensure both tickers have sufficient test-window data
    test_data_start = str(test_start)
    test_data_end = str(test_end)
    if isinstance(master_df.columns, pd.MultiIndex):
        close_cols = master_df['Close'].columns
        def _has_data(t):
            return t in close_cols and master_df['Close'][t].loc[test_data_start:test_data_end].notna().sum() > 10
    else:
        def _has_data(t):
            return t in master_df.columns and master_df[t].loc[test_data_start:test_data_end].notna().sum() > 10

    filtered_rows = []
    for _, row in viable_pairs.head(args.max_pairs * 3).iterrows():
        t1, t2 = row['pair'].split('-')
        if _has_data(t1) and _has_data(t2):
            filtered_rows.append(row)
        if len(filtered_rows) >= args.max_pairs:
            break

    top_pairs = pd.DataFrame(filtered_rows).head(args.max_pairs)
    if top_pairs.empty:
        output_lines.append(f"No pairs with sufficient test-window data for fold {i}")
        return (None, [], [], [], [], [], [], [], [], [], [], output_lines)
    output_lines.append(f"Selected {len(top_pairs)} pairs: {', '.join(top_pairs['pair'].tolist())}")

    # Setup Backtest
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(args.initial_cash)
    if args.broker_leverage != 1.0:
        cerebro.broker.setcommission(leverage=args.broker_leverage)
    cerebro.broker.set_coc(True)

    is_stats = {}
    data_count = 0

    for _, row in top_pairs.iterrows():
        pair_name = row['pair']
        t1, t2 = pair_name.split('-')

        hl_col = 'half_life_log' if args.log_space else 'half_life'
        hr_col = 'hedge_ratio_log' if args.log_space else 'hedge_ratio'
        intercept_col = 'intercept_log' if args.log_space else 'intercept'

        hl = row[hl_col]
        hr = row[hr_col]
        is_stats[pair_name] = {'hr': hr}
        z_lb = max(int(hl * args.z_m), 10)

        if isinstance(master_df.columns, pd.MultiIndex):
            s1_close = master_df['Close'][t1]
            s2_close = master_df['Close'][t2]
        else:
            s1_close = master_df[t1]
            s2_close = master_df[t2]

        fixed_params = None
        if args.fixed_params:
            intercept = row[intercept_col]
            sel_s1 = s1_close.loc[str(sel_start):str(sel_end)]
            sel_s2 = s2_close.loc[str(sel_start):str(sel_end)]
            if args.log_space:
                sel_spread = np.log(sel_s2) - (intercept + hr * np.log(sel_s1))
            else:
                sel_spread = sel_s2 - (intercept + hr * sel_s1)
            mu = sel_spread.mean()
            sigma = sel_spread.std()
            fixed_params = {'hedge_ratio': hr, 'intercept': intercept, 'mu': mu, 'sigma': sigma}

        bt_data = prepare_backtest_data(
            s1_close, s2_close,
            args.resid_val, z_lb,
            test_start=str(test_start), test_end=str(test_end),
            log_space=args.log_space,
            fixed_params=fixed_params
        )

        if bt_data['dateIndex'].empty:
            continue

        df1 = pd.DataFrame(index=bt_data['dateIndex'])
        df1['close'] = s1_close.loc[bt_data['dateIndex']]
        for field in ['zscore', 'hedge_ratio', 'phi', 'sigma_eq', 'intercept', 'rolling_std', 'rolling_mean']:
            df1[field] = bt_data[field]

        df2 = s2_close.loc[df1.index].to_frame(name='close')

        data0 = ZScoreData(dataname=df1, name=t1)
        data1 = bt.feeds.PandasData(dataname=df2, name=t2)
        cerebro.adddata(data0)
        cerebro.adddata(data1)
        data_count += 1

    if data_count == 0:
        output_lines.append(f"No data available for selected pairs in fold {i} test window.")
        return (None, [], [], [], [], [], [], [], [], [], [], output_lines)

    cerebro.addstrategy(
        PairTradingStrategy,
        entry_z=args.entry_z,
        exit_z=args.exit_z,
        stop_z=args.stop_z,
        max_holding_days=args.max_holding_days,
        hr_threshold=args.hr_thresh,
        is_stats=is_stats,
        log_space=args.log_space,
        dollar_neutral=args.dollar_neutral,
        pair_sizing_mode=getattr(args, 'pair_sizing_mode', 'reference_leg'),
        initial_cash=args.initial_cash,
        equity_fraction=args.pct_per_pair,
        verbose=args.verbose,
        earnings_screen=earnings_screen,
        earnings_block_days=args.earnings_block_days,
        margin_behavior=args.margin_behavior,
        margin_long=args.margin_long,
        margin_short=args.margin_short,
        maintenance_long=args.maintenance_long,
        maintenance_short=args.maintenance_short,
        margin_rates=getattr(args, 'margin_rates_dict', {}),
    )

    selected_pairs = []
    for rank, (_, row) in enumerate(top_pairs.iterrows(), 1):
        selected_pairs.append({
            'pair': row['pair'],
            'rank': rank,
            'selection_start': str(sel_start),
            'selection_end': str(sel_end),
            'test_start': str(test_start),
            'test_end': str(test_end),
            'cointegration_pvalue_log': row.get('cointegration_pvalue_log'),
            'half_life_log': row.get('half_life_log'),
            'cointegration_pvalue': row.get('cointegration_pvalue'),
            'half_life': row.get('half_life'),
        })
    return _collect_results(
        cerebro, i, test_start, test_end, output_lines, len(top_pairs), selected_pairs
    )


def execute_folds(master_df, args, tickers, sector_map, universe_name,
                  pool_path, earnings_screen, folds, workers):
    """Run the same fold function serially or in worker processes.

    Keeping the fold callable and result contract identical is what makes the
    ``--workers 1`` and ``--workers N`` paths directly comparable.
    """
    args_dict = vars(args).copy()
    output = {}
    failed = []

    def record(index, fold, result=None, error=None):
        if error is not None:
            failed.append(index)
            output[index] = [
                f"\n--- Processing Fold {index} ---",
                f"  ERROR: {error}",
                traceback.format_exc(),
            ]
        else:
            output[index] = result

    n_workers = max(1, min(int(workers), os.cpu_count() or 1))
    if n_workers == 1:
        _worker_init(
            master_df, args_dict, tickers, sector_map, universe_name,
            pool_path, earnings_screen,
        )
        for index, fold in enumerate(folds):
            try:
                record(index, fold, result=_process_fold(index, fold))
            except Exception as exc:
                record(index, fold, error=exc)
        return output, failed

    with ProcessPoolExecutor(
        max_workers=n_workers,
        initializer=_worker_init,
        initargs=(master_df, args_dict, tickers, sector_map, universe_name,
                  pool_path, earnings_screen),
    ) as executor:
        futures = {
            executor.submit(_process_fold, index, fold): index
            for index, fold in enumerate(folds)
        }
        for future in as_completed(futures):
            index = futures[future]
            try:
                record(index, None, result=future.result())
            except Exception as exc:
                failed.append(index)
                output[index] = [
                    f"\n--- Processing Fold {index} ---",
                    f"  ERROR: {exc}",
                    traceback.format_exc(),
                ]
    return output, failed


def run_experiment(argv=None):
    args = parse_args(argv)

    import json as _json
    args.margin_rates_dict = {}
    if args.margin_rates:
        with open(args.margin_rates) as f:
            args.margin_rates_dict = _json.load(f)

    universe_name = args.universe
    if universe_name == 'core':
        TICKERS = TICKERS_CORE
        SECTOR_MAP = SECTOR_MAP_CORE
    else:
        TICKERS = TICKERS_SP500
        SECTOR_MAP = SECTOR_MAP_SP500
    os.makedirs(args.output, exist_ok=True)
    trade_logs_dir = os.path.join(args.output, "trade_logs")
    os.makedirs(trade_logs_dir, exist_ok=True)
    _clear_run_outputs(args.output, trade_logs_dir)
    _write_run_status(args.output, 'running')

    # Resolve the window-keyed pool for this run. Missing pools intentionally
    # fall back to deterministic live selection; an existing corrupt pool fails.
    from src.config import pool_path_for
    pool_path = args.pool_path or pool_path_for(args.sel_months, universe_name)
    if not os.path.isfile(pool_path):
        pool_path = None

    print(f"Starting Walk-Forward Experiment from {args.start} to {args.end}")
    print(f"Strategy: EntryZ={args.entry_z}, ExitZ={args.exit_z}, StopZ={args.stop_z}")

    loader = DataLoader(TICKERS, start=args.start, end=args.end, use_warmup=not args.no_warmup)
    try:
        master_df, price_snapshot = load_or_fetch_prices(
            loader, args.price_snapshot, args.write_price_snapshot
        )
    except (OSError, ValueError) as exc:
        print(f'Error: {exc}')
        _write_run_status(args.output, 'failed', reason=str(exc))
        return 1
    if price_snapshot:
        print(f"Price snapshot {price_snapshot['mode']}: {price_snapshot['path']} "
              f"({price_snapshot['sha256'][:12]})")
    if master_df.empty:
        print("Error: No data fetched.")
        _write_run_status(args.output, 'failed', reason='No data fetched')
        return 1

    # Pre-load earnings screen
    cache_path = args.earnings_cache or os.path.join(args.output, "earnings_cache.pkl")
    if args.earnings_screen:
        earnings_screen = EarningsScreen(TICKERS, args.start, args.end, cache_path=cache_path)
        print(earnings_screen.summary())
    else:
        earnings_screen = None

    fb = FoldBuilder(args.start, args.end, args.sel_months, 0, args.test_months, args.slide_months)
    if not fb.folds:
        print(f"Error: No folds generated.")
        _write_run_status(args.output, 'failed', reason='No folds generated')
        return 1

    total_folds = len(fb.folds)
    print(f"Generated {total_folds} walk-forward folds (workers={args.workers}).")
    _write_run_status(args.output, 'running', expected_folds=total_folds)

    all_fold_summaries = []
    all_trade_logs = []
    all_trade_marks = []
    all_daily_returns = []
    all_daily_active_counts = []
    all_rejected_orders = []
    all_signal_log = []
    all_daily_margin = []
    all_daily_exposure = []
    all_sizing_audit = []
    all_selected_pairs = []
    all_output = {}
    failed_folds = []

    all_output, failed_folds = execute_folds(
        master_df, args, TICKERS, SECTOR_MAP, universe_name, pool_path,
        earnings_screen, fb.folds, args.workers,
    )

    for i, result in all_output.items():
        if i in failed_folds:
            continue
        (fold_summary, logs, daily_returns, active_counts, rejected, marks,
         signal_log, daily_margin, daily_exposure, sizing_audit, selected_pairs,
         output_lines) = result
        if fold_summary is not None:
            all_fold_summaries.append(fold_summary)
        all_trade_logs.extend(logs)
        all_trade_marks.extend(marks)
        all_daily_returns.extend(daily_returns)
        all_daily_active_counts.extend(active_counts)
        all_rejected_orders.extend(rejected)
        all_signal_log.extend(signal_log)
        all_daily_margin.extend(daily_margin)
        all_daily_exposure.extend(daily_exposure)
        all_sizing_audit.extend(sizing_audit)
        all_selected_pairs.extend(selected_pairs)

    for i in sorted(all_output):
        for line in all_output[i]:
            print(line)

    if failed_folds:
        failed_folds.sort()
        reason = f"Worker failures in folds: {', '.join(str(i) for i in failed_folds)}"
        _write_run_status(
            args.output, 'failed', expected_folds=total_folds,
            completed_folds=len(all_fold_summaries),
            failed_folds=failed_folds, reason=reason,
        )
        print(f"\nBacktest failed: {reason}")
        return 1

    # Aggregate results (identical logic to run_backtest.py)
    if not all_fold_summaries:
        print("\nBacktest finished with no results.")
        _write_run_status(
            args.output, 'failed', expected_folds=total_folds,
            completed_folds=0, reason='No fold results produced',
        )
        return 1

    summary_df = pd.DataFrame(all_fold_summaries)
    summary_df.to_csv(os.path.join(args.output, "oos_fold_summary.csv"), index=False)
    if all_trade_logs:
        pd.DataFrame(all_trade_logs).to_csv(os.path.join(trade_logs_dir, "test_trade_log.csv"), index=False)
    if all_trade_marks:
        pd.DataFrame(all_trade_marks).to_csv(os.path.join(args.output, "trade_marks.csv"), index=False)
    if all_rejected_orders:
        pd.DataFrame(all_rejected_orders).to_csv(os.path.join(args.output, "rejected_orders.csv"), index=False)

    if all_signal_log:
        pd.DataFrame(all_signal_log).to_csv(os.path.join(args.output, "signal_log.csv"), index=False)

    if all_daily_margin:
        pd.DataFrame(all_daily_margin).to_csv(os.path.join(args.output, "daily_margin.csv"), index=False)

    if all_daily_exposure:
        pd.DataFrame(all_daily_exposure).to_csv(
            os.path.join(args.output, "daily_exposure.csv"), index=False
        )

    if all_sizing_audit:
        pd.DataFrame(all_sizing_audit).to_csv(
            os.path.join(args.output, "sizing_audit.csv"), index=False
        )

    if all_selected_pairs:
        pd.DataFrame(all_selected_pairs).to_csv(
            os.path.join(args.output, "selected_pairs.csv"), index=False
        )

    if not all_daily_returns:
        print("\nBacktest finished with no daily returns recorded.")
        _write_run_status(
            args.output, 'failed', expected_folds=total_folds,
            completed_folds=len(all_fold_summaries),
            reason='No daily returns recorded',
        )
        return 1

    if all_daily_returns:
        returns_df = pd.DataFrame(all_daily_returns)
        returns_df['date'] = pd.to_datetime(returns_df['date'])
        cash = args.initial_cash
        cost_rate = args.spy_cost_bps / 10000

        deployed_lookup = {}
        if args.market_invest and all_daily_active_counts:
            at_df = pd.DataFrame(all_daily_active_counts)
            at_df['date'] = pd.to_datetime(at_df['date'])
            for fold_id, grp in at_df.groupby('fold_id'):
                grp = grp.sort_values('date')
                deployed_lookup[fold_id] = dict(zip(grp['date'], grp['deployed_capital']))

        fold_dollar_pnl = []
        fold_capital = []
        fold_market_pnl = []

        for fold_id in returns_df['fold_id'].unique():
            fold_rets = returns_df[returns_df['fold_id'] == fold_id].sort_values('date')
            value = cash
            prev_idle = 0.0
            deployed_map = deployed_lookup.get(fold_id, {})
            for _, row in fold_rets.iterrows():
                dt = row['date']
                pnl = value * row['pnl_pct']
                fold_dollar_pnl.append({'date': dt, 'pnl_dollars': pnl, 'fold_id': fold_id})
                fold_capital.append({'date': dt, 'capital_begin': value, 'fold_id': fold_id})
                if args.market_invest:
                    deployed = deployed_map.get(dt, 0.0)
                    idle = max(0.0, value - deployed)
                    change = abs(idle - prev_idle)
                    fold_market_pnl.append({
                        'date': dt, 'fold_id': fold_id,
                        'idle_cash': idle,
                        'txn_cost': change * cost_rate,
                        'prev_idle': prev_idle
                    })
                    prev_idle = idle
                value += pnl

        pnl_df = pd.DataFrame(fold_dollar_pnl).groupby('date')['pnl_dollars'].sum()
        cap_df = pd.DataFrame(fold_capital).groupby('date')['capital_begin'].sum()

        spy_df = None
        if args.market_invest:
            import yfinance as yf
            spy_raw = yf.download('SPY', start=args.start, end=args.end, progress=False)
            if isinstance(spy_raw.columns, pd.MultiIndex):
                spy_close = spy_raw['Close'].squeeze()
            else:
                spy_close = spy_raw['Close'] if 'Close' in spy_raw.columns else spy_raw.iloc[:, 0]
            spy_df = spy_close.pct_change().dropna().to_frame('spy_return')

        if args.market_invest and spy_df is not None:
            mkt_df = pd.DataFrame(fold_market_pnl).groupby('date').agg({
                'idle_cash': 'sum', 'txn_cost': 'sum'
            }).join(spy_df, how='left')
            mkt_df['market_pnl_dollars'] = mkt_df['idle_cash'] * mkt_df['spy_return'].fillna(0)
            mkt_df['combined_pnl'] = pnl_df + mkt_df['market_pnl_dollars'] - mkt_df['txn_cost']
            daily_ret_series = (mkt_df['combined_pnl'] / cap_df).dropna()
            daily_df = pd.DataFrame({
                'pair_pnl': pnl_df.reindex(daily_ret_series.index),
                'market_pnl': mkt_df['market_pnl_dollars'],
                'txn_cost': mkt_df['txn_cost'],
                'combined_pnl': mkt_df['combined_pnl'],
                'total_capital': cap_df.reindex(daily_ret_series.index),
                'pair_return': pnl_df.reindex(daily_ret_series.index) / cap_df.reindex(daily_ret_series.index),
                'market_return': mkt_df['market_pnl_dollars'] / cap_df.reindex(daily_ret_series.index),
                'daily_return': daily_ret_series
            }).reset_index()
        else:
            daily_ret_series = (pnl_df / cap_df).dropna()
            daily_df = pd.DataFrame({
                'pnl': pnl_df, 'total_capital': cap_df, 'daily_return': daily_ret_series
            }).reset_index()
            daily_df.columns = ['date', 'pnl', 'total_capital', 'daily_return']

        daily_df.columns = [c.lower() for c in daily_df.columns]
        daily_df.to_csv(os.path.join(args.output, "daily_returns.csv"), index=False)

        untrimmed_daily_ret_series = daily_ret_series.copy()
        total_days = len(daily_ret_series)
        trim_months = args.test_months - args.slide_months
        if trim_months > 0 and total_days > 0:
            daily_dates = daily_ret_series.index.sort_values()
            cut_start = daily_dates[0] + pd.DateOffset(months=trim_months)
            cut_end = daily_dates[-1] - pd.DateOffset(months=trim_months)
            daily_ret_series = daily_ret_series[(daily_ret_series.index >= cut_start) & (daily_ret_series.index <= cut_end)]
            total_days = len(daily_ret_series)
            if total_days > 0:
                print(f"  Trimmed {trim_months}m from each end: {daily_dates[0].date()}..{daily_dates[-1].date()} -> "
                      f"{daily_ret_series.index[0].date()}..{daily_ret_series.index[-1].date()} ({total_days} days)")

        # A run containing only zero-pair folds has no overlapping portfolio
        # edges to trim. Keep its zero-return dates so it remains a valid run.
        if (
            total_days == 0
            and len(untrimmed_daily_ret_series) > 0
            and np.allclose(untrimmed_daily_ret_series.to_numpy(dtype=float), 0.0)
        ):
            daily_ret_series = untrimmed_daily_ret_series
            total_days = len(daily_ret_series)
            print(f"  Retained zero-return dates after empty overlap trim ({total_days} days)")

        if all_daily_active_counts:
            at_df = pd.DataFrame(all_daily_active_counts)
            at_df['date'] = pd.to_datetime(at_df['date'])
            active_counts = at_df.groupby('date')['count'].sum()
            active_dates = active_counts[active_counts > 0].index
            active_df = daily_df[daily_df['date'].isin(active_dates)].copy()
            if len(active_df) > 0:
                active_df.to_csv(os.path.join(args.output, "daily_returns_active_only.csv"), index=False)

        if total_days > 0:
            cum_ret = (1 + daily_ret_series).prod() - 1
            ann_ret = (1 + cum_ret)**(252 / total_days) - 1
            std = daily_ret_series.std()
            global_sharpe = (daily_ret_series.mean() / std * np.sqrt(252)) if std > 0 else 0.0

            if all_daily_active_counts:
                at_df = pd.DataFrame(all_daily_active_counts)
                at_df['date'] = pd.to_datetime(at_df['date'])
                daily_merged = at_df.groupby('date')['count'].sum()
                daily_merged = daily_merged[daily_merged.index.isin(daily_ret_series.index)]
                mean_at = daily_merged.mean()
                total_at_days = len(daily_merged)
                total_lt10 = (daily_merged < 10).sum()
            else:
                mean_at = total_at_days = total_lt10 = 0

            print(f"\n--- BACKTEST COMPLETE ---")
            print(f"Global Annualized Return: {ann_ret:.2%}")
            print(f"Global Annualized Sharpe: {global_sharpe:.2f}")
            print(f"Total Trades: {len(all_trade_logs)}")
            print(f"Mean Active Trades (merged across folds): {mean_at:.1f}")
            print(f"Days with Active Trades < 10 (merged): {total_lt10} / {total_at_days}")
            print(f"Results saved to {args.output}")

            metrics = {
                'experiment': str(args.name),
                'mode': 'coint',
                'universe': str(universe_name),
                'cross_sector': bool(args.cross_sector),
                'start': str(args.start),
                'end': str(args.end),
                'sel_months': int(args.sel_months),
                'test_months': int(args.test_months),
                'slide_months': int(args.slide_months),
                'entry_z': float(args.entry_z),
                'exit_z': float(args.exit_z),
                'stop_z': float(args.stop_z),
                'resid_val': int(args.resid_val),
                'z_m': float(args.z_m),
                'hr_thresh': float(args.hr_thresh),
                'max_holding_days': int(args.max_holding_days),
                'pvalue': float(args.pvalue),
                'pct_per_pair': float(args.pct_per_pair),
                'pair_sizing_mode': str(getattr(args, 'pair_sizing_mode', 'reference_leg')),
                'max_pairs': int(args.max_pairs),
                'broker_leverage': float(args.broker_leverage),
                'log_space': bool(args.log_space),
                'dollar_neutral': bool(args.dollar_neutral),
                'expected_folds': int(total_folds),
                'completed_folds': int(len(all_fold_summaries)),
                'total_folds': int(len(all_fold_summaries)),
                'total_trades': int(len(all_trade_logs)),
                'annualized_return': float(round(ann_ret, 6)),
                'annualized_sharpe': float(round(global_sharpe, 6)),
                'mean_active_trades': float(round(mean_at, 2)),
                'total_days': int(total_days),
                'days_active_lt10': int(total_lt10),
            }
            metrics.update(summarize_exposure(
                all_daily_exposure, dates=daily_ret_series.index
            ))
            metrics['margin_behavior'] = str(args.margin_behavior)
            metrics['margin_long'] = float(args.margin_long)
            metrics['margin_short'] = float(args.margin_short)
            metrics['maintenance_long'] = float(args.maintenance_long)
            metrics['maintenance_short'] = float(args.maintenance_short)
            if price_snapshot:
                metrics['price_snapshot'] = price_snapshot['path']
                metrics['price_snapshot_sha256'] = price_snapshot['sha256']
                metrics['price_snapshot_mode'] = price_snapshot['mode']
            margin_rejections = sum(1 for r in all_rejected_orders if r.get('reason') == 'margin')
            metrics['margin_rejections'] = int(margin_rejections)
            if all_daily_margin:
                dm = pd.DataFrame(all_daily_margin)
                metrics['margin_call_days'] = int(dm['margin_call'].sum())
                metrics['max_utilization'] = float(round(dm['utilization'].max(), 4))
                metrics['min_free_margin'] = float(round(dm['free_margin'].min(), 2))
            with open(os.path.join(args.output, 'metrics.json'), 'w') as f:
                json.dump(metrics, f, indent=2)
            _write_run_status(
                args.output, 'success', expected_folds=total_folds,
                completed_folds=len(all_fold_summaries),
            )
        else:
            print("\nBacktest finished with no daily returns recorded after processing.")
            _write_run_status(
                args.output, 'failed', expected_folds=total_folds,
                completed_folds=len(all_fold_summaries),
                reason='No daily returns recorded after processing',
            )
            return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(run_experiment())
