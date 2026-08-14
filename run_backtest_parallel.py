import argparse
import os
import pickle
import sys
import pandas as pd
import numpy as np
import backtrader as bt
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings

from run_backtest import parse_args, _merge_profile, HUCK_CACHE_PATH
from src.constants import TICKERS_CORE, TICKERS_SP500, SECTOR_MAP_CORE, SECTOR_MAP_SP500
from src.data_loader import DataLoader
from src.walk_forward import FoldBuilder
from src.pair_selection import PairSelector
from src.backtest import PairTradingStrategy, ZScoreData, prepare_backtest_data
from src.gatev_selection import GatevSelector
from src.gatev_strategy import GatevStrategy, GatevData, prepare_gatev_data
from src.pair_cache import PairSelectionCache, PoolCache
from src.earnings_screen import EarningsScreen

warnings.filterwarnings('ignore')

_global = {}

def _worker_init(master_df, args_dict, TICKERS, SECTOR_MAP, universe_name, cache_dir, pool_path, earnings_screen):
    _global['master_df'] = master_df
    _global['args'] = argparse.Namespace(**args_dict)
    _global['TICKERS'] = TICKERS
    _global['SECTOR_MAP'] = SECTOR_MAP
    _global['universe_name'] = universe_name
    _global['pair_selector'] = PairSelector(pvalue_threshold=args_dict['pvalue'])
    _global['pair_cache'] = PairSelectionCache(cache_dir) if cache_dir else None
    _global['pool_cache'] = PoolCache(pool_path, prefiltered=(pool_path is not None and pool_path.endswith('core_2m.pkl'))) if pool_path else None
    _global['earnings_screen'] = earnings_screen
    # huck2015 profile (12m) reads the pool directly, keyed by bare sel_start.
    _global['huck_cache'] = _global['pool_cache']._data if (args_dict.get('sel_months') == 12 and _global['pool_cache']) else None

def _process_fold(i, fold):
    g = _global
    if g['args'].mode == 'gatev':
        return _process_fold_gatev(i, fold, g)
    return _process_fold_coint(i, fold, g)

def _collect_results(cerebro, i, test_start, test_end, output_lines, n_pairs=0):
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

    for log in logs:
        log['fold_id'] = i

    rejected_count = sum(1 for _ in getattr(res, 'rejected_orders', []))
    sh = s if s is not None and not np.isnan(s) else 0.0
    output_lines.append(f"Fold {i} Complete: Sharpe={sh:.2f}, Trades={len(logs)}, Rejected={rejected_count}")

    return fold_summary, logs, daily_returns, daily_active_counts, rejected_orders, trade_marks, output_lines

def _process_fold_gatev(i, fold, g):
    master_df = g['master_df']
    args = g['args']
    TICKERS = g['TICKERS']

    sel_start, sel_end, _, _, test_start, test_end = fold
    output_lines = []
    output_lines.append(f"\n--- Processing Fold {i} [Test: {test_start} to {test_end}] ---")

    close_prices = master_df['Close'] if isinstance(master_df.columns, pd.MultiIndex) else master_df
    sel_window_data = close_prices.loc[str(sel_start):str(sel_end)]
    valid_tickers = sorted([t for t in close_prices.columns if t in TICKERS and sel_window_data[t].notna().sum() > 20])

    gsel = GatevSelector(top_k=args.max_pairs)
    top_pairs = gsel.select_pairs(close_prices[valid_tickers], str(sel_start), str(sel_end))

    if top_pairs.empty:
        output_lines.append(f"No Gatev pairs found for fold {i}")
        return (None, [], [], [], [], [], output_lines)

    output_lines.append(f"Selected {len(top_pairs)} pairs: {', '.join(top_pairs['pair'].tolist())}")

    cerebro = bt.Cerebro()
    cerebro.broker.setcash(args.initial_cash)
    cerebro.broker.set_coc(True)
    data_count = 0

    for _, row in top_pairs.iterrows():
        t1, t2 = row['pair'].split('-')
        if isinstance(master_df.columns, pd.MultiIndex):
            s1_close = master_df['Close'][t1]
            s2_close = master_df['Close'][t2]
        else:
            s1_close = master_df[t1]
            s2_close = master_df[t2]

        bt_data = prepare_gatev_data(
            s1_close, s2_close,
            str(sel_start), str(sel_end),
            str(test_start), str(test_end),
        )

        if bt_data['dateIndex'].empty:
            continue

        df1 = pd.DataFrame(index=bt_data['dateIndex'])
        df1['close'] = s1_close.loc[bt_data['dateIndex']]
        df1['zscore'] = bt_data['zscore']

        df2 = s2_close.loc[df1.index].to_frame(name='close')

        data0 = GatevData(dataname=df1, name=t1)
        data1 = bt.feeds.PandasData(dataname=df2, name=t2)
        cerebro.adddata(data0)
        cerebro.adddata(data1)
        data_count += 1

    if data_count == 0:
        output_lines.append(f"No valid Gatev data for fold {i}")
        return (None, [], [], [], [], [], output_lines)

    cerebro.addstrategy(
        GatevStrategy,
        entry_z=args.entry_z,
        exit_z=args.exit_z,
        equity_fraction=args.pct_per_pair,
        initial_cash=args.initial_cash,
    )

    return _collect_results(cerebro, i, test_start, test_end, output_lines, len(top_pairs))


def _process_fold_coint(i, fold, g):
    master_df = g['master_df']
    args = g['args']
    TICKERS = g['TICKERS']
    SECTOR_MAP = g['SECTOR_MAP']
    universe_name = g['universe_name']
    selector = g['pair_selector']
    huck_cache = g['huck_cache']
    pair_cache = g['pair_cache']
    pool_cache = g['pool_cache']
    earnings_screen = g['earnings_screen']

    sel_start, sel_end, _, _, test_start, test_end = fold
    output_lines = []
    output_lines.append(f"\n--- Processing Fold {i} [Test: {test_start} to {test_end}] ---")

    viable_pairs = None

    # ==== COINTEGRATION PIPELINE ====
    if args.profile == 'huck2015':
        sel_key = str(sel_start)
        raw = huck_cache.get(sel_key, pd.DataFrame()) if huck_cache else pd.DataFrame()
        ticker_set = set(TICKERS)
        universe_mask = raw['pair'].apply(lambda p: all(t in ticker_set for t in p.split('-')))
        raw = raw[universe_mask]
        mask = (raw['cointegration_pvalue'] < args.pvalue) & (raw['half_life'] > 0)
        viable_pairs = raw[mask].sort_values('cointegration_pvalue')
        output_lines.append(f"  [H&A cache: {len(raw)} in-universe, {len(viable_pairs)} pass coint filter]")
    else:
        # huck2015 (H&A) cache is handled exclusively in the profile=='huck2015'
        # branch above; it must NOT be consulted for other profiles (baseline/golden),
        # which use 2-month windows. Prior code looked it up here keyed by bare
        # str(sel_start), silently substituting 12-month sp500 cross-sector pairs
        # for 2-month core pairs (cache-shadow bug). That bug is permanently removed.
        # Go straight to the properly-keyed pool / pair cache.
        if viable_pairs is None or viable_pairs.empty:
            # Primary: universe-free window-keyed pool (masked at load time).
            filtered_key = (universe_name, str(sel_start), str(sel_end), not args.cross_sector,
                            round(args.return_divergence or 0.0, 4))
            from_pool = False
            if pool_cache is not None and pool_cache.has(sel_start):
                viable_pairs = pool_cache.select(
                    sel_start, universe_name, SECTOR_MAP,
                    cross_sector=args.cross_sector,
                    pvalue=args.pvalue,
                    return_divergence=args.return_divergence,
                    log_space=args.log_space,
                )
                from_pool = not viable_pairs.empty
                output_lines.append(
                    f"  [pool {os.path.basename(pool_cache.path)} HIT for sel {sel_start} to {sel_end}: {len(viable_pairs)} pairs]"
                )
                if args.return_divergence is not None and not viable_pairs.empty:
                    close_prices = master_df['Close'] if isinstance(master_df.columns, pd.MultiIndex) else master_df
                    sel_data = close_prices.loc[str(sel_start):str(sel_end)]
                    mask = []
                    for _, row in viable_pairs.iterrows():
                        t1, t2 = row['pair'].split('-')
                        if t1 in sel_data.columns and t2 in sel_data.columns:
                            r1 = sel_data[t1].iloc[-1] / sel_data[t1].iloc[0] - 1
                            r2 = sel_data[t2].iloc[-1] / sel_data[t2].iloc[0] - 1
                            mask.append(abs(r1 - r2) <= args.return_divergence)
                        else:
                            mask.append(False)
                    viable_pairs = viable_pairs[mask]
                    output_lines.append(f"  Pool return divergence filter: {viable_pairs.shape[0]} pairs remaining")

            if viable_pairs is None or viable_pairs.empty:
                divergence = args.return_divergence or 0.0
                filtered_key = (universe_name, str(sel_start), str(sel_end), not args.cross_sector, round(divergence, 4))
                if pair_cache is not None:
                    viable_pairs = pair_cache.get_filtered(filtered_key)
                if viable_pairs is not None and pair_cache is not None:
                    output_lines.append(f"  [filtered cache HIT for sel {sel_start} to {sel_end}]")

            if viable_pairs is None or viable_pairs.empty:
                cache_key = (universe_name, str(sel_start), str(sel_end), not args.cross_sector)
                if pair_cache is not None:
                    viable_pairs = pair_cache.get(cache_key)
                if viable_pairs is not None and not viable_pairs.empty:
                    viable_pairs = viable_pairs[
                        (viable_pairs['cointegration_pvalue_log'] < args.pvalue) &
                        (viable_pairs['half_life_log'] > 0)
                    ].sort_values('cointegration_pvalue_log')
                    output_lines.append(f"  [cache HIT for sel {sel_start} to {sel_end}: {len(viable_pairs)} pairs after filter]")

            if viable_pairs is None or viable_pairs.empty:
                viable_pairs = selector.select_pairs(
                    master_df, SECTOR_MAP, str(sel_start), str(sel_end),
                    same_sector_only=not args.cross_sector,
                    return_divergence_threshold=args.return_divergence,
                    log_space=args.log_space
                )
                output_lines.append(f"  [live select_pairs for sel {sel_start} to {sel_end}: {len(viable_pairs)} pairs]")
            elif not from_pool:
                if pair_cache is not None:
                    cache_key = (universe_name, str(sel_start), str(sel_end), not args.cross_sector)
                    viable_pairs = pair_cache.get(cache_key)

                # Fallback: if same_sector mode misses, try cross_sector cache
                if viable_pairs is None and pair_cache is not None and not args.cross_sector:
                    fallback_key = (universe_name, str(sel_start), str(sel_end), False)
                    all_pairs = pair_cache.get(fallback_key)
                    if all_pairs is not None:
                        ticker_to_sector = {}
                        for sector, tickers in SECTOR_MAP.items():
                            for t in tickers:
                                ticker_to_sector[t] = sector
                        same_mask = all_pairs['pair'].apply(
                            lambda p: ticker_to_sector.get(p.split('-')[0]) == ticker_to_sector.get(p.split('-')[1])
                        )
                        viable_pairs = all_pairs[same_mask].copy()
                        viable_pairs['sector'] = viable_pairs['pair'].apply(
                            lambda p: ticker_to_sector.get(p.split('-')[0], 'Unknown')
                        )
                        pair_cache.set(cache_key, viable_pairs)
                        output_lines.append(f"  [fallback cache HIT (cross to same) for sel {sel_start} to {sel_end}: {len(viable_pairs)} raw pairs]")

                if viable_pairs is None or pair_cache is None:
                    viable_pairs = selector.select_pairs(
                        master_df, SECTOR_MAP, str(sel_start), str(sel_end),
                        same_sector_only=not args.cross_sector,
                        return_divergence_threshold=args.return_divergence,
                        log_space=args.log_space
                    )
                    if pair_cache is not None:
                        cache_key = (universe_name, str(sel_start), str(sel_end), not args.cross_sector)
                        pair_cache.set(cache_key, viable_pairs)
                else:
                    # Cache may store all pairs (if seeded); apply filter at load time
                    viable_pairs = viable_pairs[
                        (viable_pairs['cointegration_pvalue_log'] < args.pvalue) &
                        (viable_pairs['half_life_log'] > 0)
                    ].sort_values('cointegration_pvalue_log')
                    output_lines.append(f"  [cache HIT for sel {sel_start} to {sel_end}: {len(viable_pairs)} pairs after filter]")

                if args.return_divergence is not None and not viable_pairs.empty:
                    close_prices = master_df['Close'] if isinstance(master_df.columns, pd.MultiIndex) else master_df
                    sel_data = close_prices.loc[str(sel_start):str(sel_end)]
                    mask = []
                    for _, row in viable_pairs.iterrows():
                        t1, t2 = row['pair'].split('-')
                        if t1 in sel_data.columns and t2 in sel_data.columns:
                            r1 = sel_data[t1].iloc[-1] / sel_data[t1].iloc[0] - 1
                            r2 = sel_data[t2].iloc[-1] / sel_data[t2].iloc[0] - 1
                            mask.append(abs(r1 - r2) <= args.return_divergence)
                        else:
                            mask.append(False)
                    viable_pairs = viable_pairs[mask]
                    output_lines.append(f"  Return divergence filter: {viable_pairs.shape[0]} pairs remaining")

                if pair_cache is not None:
                    pair_cache.set_filtered(filtered_key, viable_pairs)

    if viable_pairs.empty:
        output_lines.append(f"No viable pairs found for fold {i}")
        return (None, [], [], [], [], [], output_lines)

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
        return (None, [], [], [], [], [], output_lines)
    output_lines.append(f"Selected {len(top_pairs)} pairs: {', '.join(top_pairs['pair'].tolist())}")

    # Setup Backtest
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(args.initial_cash)
    cerebro.broker.set_coc(True)

    is_stats = {}
    data_count = 0

    for _, row in top_pairs.iterrows():
        pair_name = row['pair']
        t1, t2 = pair_name.split('-')

        if args.profile == 'huck2015':
            hl_col, hr_col, intercept_col = 'half_life', 'hedge_ratio', 'intercept'
        else:
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
        return (None, [], [], [], [], [], output_lines)

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
        initial_cash=args.initial_cash,
        equity_fraction=args.pct_per_pair,
        verbose=args.verbose,
        earnings_screen=earnings_screen,
        earnings_block_days=args.earnings_block_days
    )

    return _collect_results(cerebro, i, test_start, test_end, output_lines, len(top_pairs))


def run_backtest_parallel():
    args = parse_args()
    if args.mode == 'coint':
        _merge_profile(args)

    universe_name = 'core'
    if args.profile in __import__('src.config', fromlist=['PROFILES']).PROFILES:
        universe_name = __import__('src.config', fromlist=['PROFILES']).PROFILES[args.profile].get('universe', 'sp500')
    if universe_name == 'core':
        TICKERS = TICKERS_CORE
        SECTOR_MAP = SECTOR_MAP_CORE
    else:
        TICKERS = TICKERS_SP500
        SECTOR_MAP = SECTOR_MAP_SP500
    if args.universe:
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

    # Resolve the universe-free window-keyed pool for this run.
    from src.config import pool_path_for
    pool_path = pool_path_for(args.sel_months, universe_name, args.cross_sector, args.profile) if args.mode == 'coint' else None

    print(f"Starting Walk-Forward Backtest (Parallel) from {args.start} to {args.end}")
    if args.mode == 'gatev':
        print(f"Strategy: EntryZ={args.entry_z}, ExitZ={args.exit_z}")
    else:
        print(f"Strategy: EntryZ={args.entry_z}, ExitZ={args.exit_z}, StopZ={args.stop_z}")

    loader = DataLoader(TICKERS, start=args.start, end=args.end, use_warmup=not args.no_warmup)
    master_df = loader.fetch_prices()
    if master_df.empty:
        print("Error: No data fetched.")
        return

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
        return

    total_folds = len(fb.folds)
    print(f"Generated {total_folds} walk-forward folds (workers={args.workers}).")

    args_dict = vars(args)

    all_fold_summaries = []
    all_trade_logs = []
    all_trade_marks = []
    all_daily_returns = []
    all_daily_active_counts = []
    all_rejected_orders = []
    all_output = {}

    n_workers = max(1, min(args.workers, os.cpu_count() or 1))

    with ProcessPoolExecutor(
        max_workers=n_workers,
        initializer=_worker_init,
        initargs=(master_df, args_dict, TICKERS, SECTOR_MAP, universe_name, args.cache_dir, pool_path, earnings_screen)
    ) as ex:
        futures = {ex.submit(_process_fold, i, fold): i for i, fold in enumerate(fb.folds)}

        for future in as_completed(futures):
            i = futures[future]
            try:
                fold_summary, logs, daily_returns, active_counts, rejected, marks, output_lines = future.result()
                all_output[i] = output_lines
                if fold_summary is not None:
                    all_fold_summaries.append(fold_summary)
                all_trade_logs.extend(logs)
                all_trade_marks.extend(marks)
                all_daily_returns.extend(daily_returns)
                all_daily_active_counts.extend(active_counts)
                all_rejected_orders.extend(rejected)
            except Exception as e:
                all_output[i] = [f"\n--- Processing Fold {i} ---", f"  ERROR: {e}"]
                import traceback
                all_output[i].append(traceback.format_exc())

    for i in sorted(all_output):
        for line in all_output[i]:
            print(line)

    # Aggregate results (identical logic to run_backtest.py)
    if not all_fold_summaries:
        print("\nBacktest finished with no results.")
        return

    summary_df = pd.DataFrame(all_fold_summaries)
    summary_df.to_csv(os.path.join(args.output, "oos_fold_summary.csv"), index=False)
    if all_trade_logs:
        pd.DataFrame(all_trade_logs).to_csv(os.path.join(trade_logs_dir, "test_trade_log.csv"), index=False)
    if all_trade_marks:
        pd.DataFrame(all_trade_marks).to_csv(os.path.join(args.output, "trade_marks.csv"), index=False)
    if all_rejected_orders:
        pd.DataFrame(all_rejected_orders).to_csv(os.path.join(args.output, "rejected_orders.csv"), index=False)

    if all_daily_returns:
        returns_df = pd.DataFrame(all_daily_returns)
        cash = args.initial_cash
        cost_rate = args.spy_cost_bps / 10000

        deployed_lookup = {}
        if args.market_invest and all_daily_active_counts:
            at_df = pd.DataFrame(all_daily_active_counts)
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

        if all_daily_active_counts:
            at_df = pd.DataFrame(all_daily_active_counts)
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

            import json
            metrics = {
                'profile': str(args.profile),
                'mode': str(args.mode),
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
                'max_pairs': int(args.max_pairs),
                'log_space': bool(args.log_space),
                'dollar_neutral': bool(args.dollar_neutral),
                'total_folds': int(len(all_fold_summaries)),
                'total_trades': int(len(all_trade_logs)),
                'annualized_return': float(round(ann_ret, 6)),
                'annualized_sharpe': float(round(global_sharpe, 6)),
                'mean_active_trades': float(round(mean_at, 2)),
                'total_days': int(total_days),
                'days_active_lt10': int(total_lt10),
            }
            with open(os.path.join(args.output, 'metrics.json'), 'w') as f:
                json.dump(metrics, f, indent=2)
        else:
            print("\nBacktest finished with no daily returns recorded.")

if __name__ == "__main__":
    run_backtest_parallel()
