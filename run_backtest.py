import argparse
import os
import pickle
import sys
import pandas as pd
import numpy as np
import backtrader as bt
from datetime import datetime
import warnings

# Internal imports from GITHUBREPO/src
from src.constants import TICKERS_CORE, TICKERS_SP500, SECTOR_MAP_CORE, SECTOR_MAP_SP500
from src.data_loader import DataLoader
from src.pair_selection import PairSelector
from src.walk_forward import FoldBuilder
from src.backtest import PairTradingStrategy, ZScoreData, prepare_backtest_data
from src.config import STRATEGY_PARAMS, BACKTEST_SETTINGS, FOLD_SETTINGS, OUTPUT_DIR, PROFILES
from src.earnings_screen import EarningsScreen
from src.pair_cache import PairSelectionCache
from src.gatev_selection import GatevSelector
from src.gatev_strategy import GatevStrategy, GatevData, prepare_gatev_data

warnings.filterwarnings('ignore')

def parse_args():
    parser = argparse.ArgumentParser(description='Run Walk-Forward Backtest for Pairs Trading Strategy')
    
    # Mode / Profile
    parser.add_argument('--mode', type=str, default='coint', choices=['coint', 'gatev'], help='Backtest mode: coint (cointegration-based) or gatev (distance-based)')
    parser.add_argument('--profile', type=str, default='golden', choices=list(PROFILES.keys()), help='Configuration profile (coint mode only)')
    
    # Date Range
    parser.add_argument('--start', type=str, default='2020-01-01', help='Backtest start date (YYYY-MM-DD). Requires a 2 month selection window before this date for pair selection.')
    parser.add_argument('--end', type=str, default='2020-05-31', help='Backtest end date (YYYY-MM-DD)')
    
    # Strategy Parameters
    parser.add_argument('--entry_z', type=float, default=STRATEGY_PARAMS['entry_z'], help='Entry Z-score threshold')
    parser.add_argument('--exit_z', type=float, default=STRATEGY_PARAMS['exit_z'], help='Exit Z-score threshold')
    parser.add_argument('--stop_z', type=float, default=STRATEGY_PARAMS['stop_z'], help='Stop loss Z-score threshold')
    parser.add_argument('--resid_val', type=int, default=STRATEGY_PARAMS['resid_val'], help='Residual lookback period')
    parser.add_argument('--z_m', type=float, default=STRATEGY_PARAMS['z_m'], help='Z-score lookback multiplier (of half-life)')
    parser.add_argument('--hr_thresh', type=float, default=STRATEGY_PARAMS['hr_thresh'], help='Hedge ratio stability threshold')
    parser.add_argument('--max_holding_days', type=int, default=STRATEGY_PARAMS['max_holding_days'], help='Max holding days for loss')
    parser.add_argument('--pvalue', type=float, default=STRATEGY_PARAMS['pvalue_threshold'], help='Cointegration p-value threshold')
    
    # Environment Settings
    parser.add_argument('--initial_cash', type=float, default=BACKTEST_SETTINGS['initial_cash'], help='Starting capital')
    parser.add_argument('--pct_per_pair', type=float, default=BACKTEST_SETTINGS['pct_per_pair'], help='Equity fraction per pair')
    parser.add_argument('--max_pairs', type=int, default=BACKTEST_SETTINGS['max_pairs_per_fold'], help='Max pairs per fold')
    parser.add_argument('--log_space', action='store_true', default=BACKTEST_SETTINGS['log_space'], help='Use log prices')
    parser.add_argument('--dollar_neutral', action='store_true', default=BACKTEST_SETTINGS['dollar_neutral'], help='Dollar-neutral position sizing (equal notional each leg)')
    parser.add_argument('--no_warmup', action='store_true', help='Disable data warmup period (historical buffer)')
    
    # Walk-Forward Settings
    parser.add_argument('--sel_months', type=int, default=FOLD_SETTINGS['sel_months'], help='Selection window months')
    parser.add_argument('--test_months', type=int, default=FOLD_SETTINGS['test_months'], help='Test window months')
    parser.add_argument('--slide_months', type=int, default=FOLD_SETTINGS['slide_months'], help='Slide window months')
    
    # Pair Selection
    parser.add_argument('--cross_sector', action='store_true', default=False, help='Allow pairs across different sectors')
    parser.add_argument('--no-cross_sector', action='store_false', dest='cross_sector', help='Restrict pairs to same sector only')
    parser.add_argument('--fixed_params', action='store_true', default=False, help='Use formation-period fixed parameters for Z-score (no rolling estimates)')
    parser.add_argument('--return_divergence', type=float, default=None, help='Max cumulative return divergence between pair stocks over selection window (e.g. 0.10)')
    parser.add_argument('--universe', type=str, default=None, choices=['core', 'sp500'],
                        help='Override profile universe (core or sp500)')

    # Earnings Screen
    parser.add_argument('--earnings_screen', action='store_true', default=False, help='Enable earnings date screen (skip entry within 15d of earnings)')
    parser.add_argument('--no-earnings_screen', action='store_false', dest='earnings_screen', help='Disable earnings date screen')
    parser.add_argument('--earnings_cache', type=str, default=None, help='Path to shared earnings cache pickle')
    parser.add_argument('--earnings_block_days', type=int, default=0, help='Block entry for N days after an earnings event')

    # Cache
    parser.add_argument('--cache_dir', type=str, default='research/cache', help='Directory for pair selection cache')

    # Market investment (Method 2: idle cash → SPY)
    parser.add_argument('--market_invest', action='store_true', default=False, help='Invest idle cash in SPY')
    parser.add_argument('--spy_cost_bps', type=float, default=1.0, help='SPY transaction cost in bps')

    # Output
    parser.add_argument('--output', type=str, default=OUTPUT_DIR, help='Output directory for results')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    # Parallel fold workers (default 4; keep total workers low when running grids)
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel fold workers')
    
    args = parser.parse_args()
    args._provided = {
        action.dest
        for action in parser._actions
        if action.option_strings
        and any(opt in sys.argv for opt in action.option_strings)
    }
    return args

HUCK_CACHE_PATH = 'research/cache/huck2015_pvalues.pkl'

def _merge_profile(args):
    provided = getattr(args, '_provided', set())
    p = PROFILES[args.profile]
    for k, v in p['STRATEGY_PARAMS'].items():
        attr = 'pvalue' if k == 'pvalue_threshold' else k
        if hasattr(args, attr) and attr not in provided:
            setattr(args, attr, v)
    for k, v in p['BACKTEST_SETTINGS'].items():
        attr = 'max_pairs' if k == 'max_pairs_per_fold' else k
        if hasattr(args, attr) and attr not in provided:
            setattr(args, attr, v)
    for k, v in p['FOLD_SETTINGS'].items():
        if hasattr(args, k) and k not in provided:
            setattr(args, k, v)
    for flag in ('cross_sector', 'fixed_params', 'return_divergence', 'universe', 'earnings_screen', 'earnings_block_days', 'cache_dir'):
        if hasattr(args, flag) and flag not in provided:
            setattr(args, flag, p[flag])

def run_backtest():
    args = parse_args()
    if args.mode == 'coint':
        _merge_profile(args)

    # Select universe from profile
    universe_name = PROFILES[args.profile].get('universe', 'sp500')
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
    
    print(f"Starting Walk-Forward Backtest from {args.start} to {args.end}")
    print(f"Strategy: EntryZ={args.entry_z}, ExitZ={args.exit_z}, StopZ={args.stop_z}")
    
    # 1. Fetch Data
    loader = DataLoader(TICKERS, start=args.start, end=args.end, use_warmup=not args.no_warmup)
    master_df = loader.fetch_prices()
    if master_df.empty:
        print("Error: No data fetched. Check your internet connection and ticker list.")
        return

    # Earnings Screen
    if args.earnings_screen:
        cache_path = args.earnings_cache or os.path.join(args.output, "earnings_cache.pkl")
        earnings_screen = EarningsScreen(TICKERS, args.start, args.end, cache_path=cache_path)
        print(earnings_screen.summary())
    else:
        earnings_screen = None

    # 1b. Fetch SPY for market invest (Method 2)
    spy_df = None
    if args.market_invest:
        print("Fetching SPY for market investment...")
        import yfinance as yf
        spy_raw = yf.download('SPY', start=args.start, end=args.end, progress=False)
        if isinstance(spy_raw.columns, pd.MultiIndex):
            spy_close = spy_raw['Close'].squeeze()
        else:
            spy_close = spy_raw['Close'] if 'Close' in spy_raw.columns else spy_raw.iloc[:, 0]
        spy_df = spy_close.pct_change().dropna().to_frame('spy_return')
        print(f"  SPY data: {len(spy_df)} days ({spy_df.index[0].date()} to {spy_df.index[-1].date()})")

    # 2. Build Folds
    fb = FoldBuilder(args.start, args.end, args.sel_months, 0, args.test_months, args.slide_months)
    if not fb.folds:
        print(f"Error: No folds generated. Your date range ({args.start} to {args.end}) is likely too short for the current settings.")
        print(f"Selection Window: {args.sel_months} months, Test Window: {args.test_months} months (Total {args.sel_months + args.test_months} months required).")
        return
        
    print(f"Generated {len(fb.folds)} walk-forward folds.")

    selector = PairSelector(pvalue_threshold=args.pvalue)
    pair_cache = PairSelectionCache(args.cache_dir)
    from src.config import pool_path_for
    from src.pair_cache import PoolCache
    pool_path = pool_path_for(args.sel_months, universe_name, args.cross_sector) if args.mode == 'coint' else None
    pool_cache = PoolCache(pool_path, prefiltered=(pool_path is not None and pool_path.endswith('core_2m.pkl'))) if pool_path else None
    fold_summaries = []
    all_trade_logs = []
    all_daily_returns = []
    all_daily_active_counts = []
    all_rejected_orders = []
    
    # Pre-load H&A cache if using coint mode
    huck_cache = None
    if args.mode == 'coint' and args.profile == 'huck2015' and pool_cache is not None:
        huck_cache = pool_cache._data

    for i, fold in enumerate(fb.folds):
        sel_start, sel_end, _, _, test_start, test_end = fold
        print(f"\n--- Processing Fold {i} [Test: {test_start} to {test_end}] ---")

        if args.mode == 'gatev':
            # ==== GATEV PIPELINE ====

            close_prices = master_df['Close'] if isinstance(master_df.columns, pd.MultiIndex) else master_df
            sel_window_data = close_prices.loc[str(sel_start):str(sel_end)]
            valid_tickers = sorted([t for t in close_prices.columns if t in TICKERS and sel_window_data[t].notna().sum() > 20])

            gsel = GatevSelector(top_k=args.max_pairs)
            top_pairs = gsel.select_pairs(close_prices[valid_tickers], str(sel_start), str(sel_end))

            if top_pairs.empty:
                print(f"No Gatev pairs found for fold {i}")
                continue

            print(f"Selected {len(top_pairs)} pairs: {', '.join(top_pairs['pair'].tolist())}")

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
                print(f"No valid Gatev data for fold {i}")
                continue

            cerebro.addstrategy(
                GatevStrategy,
                entry_z=args.entry_z,
                exit_z=args.exit_z,
                max_holding_days=args.max_holding_days,
                equity_fraction=args.pct_per_pair,
                initial_cash=args.initial_cash,
            )

        else:
            # ==== COINTEGRATION PIPELINE (golden / H&A) ====

            # 3. Pair Selection
            viable_pairs = None
            if args.profile == 'huck2015':
                sel_key = str(sel_start)
                raw = huck_cache.get(sel_key, pd.DataFrame())
                ticker_set = set(TICKERS)
                universe_mask = raw['pair'].apply(lambda p: all(t in ticker_set for t in p.split('-')))
                raw = raw[universe_mask]
                mask = (raw['cointegration_pvalue'] < args.pvalue) & (raw['half_life'] > 0)
                viable_pairs = raw[mask].sort_values('cointegration_pvalue')
                print(f"  [H&A cache: {len(raw)} in-universe, {len(viable_pairs)} pass coint filter]")
            else:
                # The H&A pool is ONLY valid for the huck2015 (12-month) profile.
                # Prior code consulted it keyed by bare str(sel_start) for ALL
                # profiles, silently substituting 12-month sp500 cross-sector pairs
                # for 2-month core runs (cache-shadow bug). Now we gate it and go
                # straight to the properly-keyed pool / pair cache.
                if viable_pairs is None or viable_pairs.empty:
                    if pool_cache is not None and pool_cache.has(sel_start):
                        viable_pairs = pool_cache.select(
                            sel_start, universe_name, SECTOR_MAP,
                            cross_sector=args.cross_sector,
                            pvalue=args.pvalue,
                            return_divergence=args.return_divergence,
                            log_space=args.log_space,
                        )
                        print(f"  [pool HIT for sel {sel_start} to {sel_end}: {len(viable_pairs)} pairs]")
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
                            print(f"  Pool return divergence filter: {viable_pairs.shape[0]} pairs remaining")

                if viable_pairs is None or viable_pairs.empty:
                    divergence = args.return_divergence or 0.0
                    filtered_key = (universe_name, str(sel_start), str(sel_end), not args.cross_sector, round(divergence, 4))
                    viable_pairs = pair_cache.get_filtered(filtered_key)
                    if viable_pairs is not None:
                        print(f"  [filtered cache HIT for sel {sel_start} to {sel_end}]")
                    else:
                        cache_key = (universe_name, str(sel_start), str(sel_end), not args.cross_sector)
                        viable_pairs = pair_cache.get(cache_key)

                        # Fallback: if same_sector mode misses, try cross_sector cache
                        if viable_pairs is None and not args.cross_sector:
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
                                print(f"  [fallback cache HIT (cross to same) for sel {sel_start} to {sel_end}: {len(viable_pairs)} raw pairs]")

                        if viable_pairs is None:
                            viable_pairs = selector.select_pairs(master_df, SECTOR_MAP, str(sel_start), str(sel_end), same_sector_only=not args.cross_sector, return_divergence_threshold=args.return_divergence, log_space=args.log_space)
                            pair_cache.set(cache_key, viable_pairs)
                        else:
                            # Cache may store all pairs (if seeded); apply filter at load time
                            viable_pairs = viable_pairs[
                                (viable_pairs['cointegration_pvalue_log'] < args.pvalue) &
                                (viable_pairs['half_life_log'] > 0)
                            ].sort_values('cointegration_pvalue_log')
                            print(f"  [cache HIT for sel {sel_start} to {sel_end}: {len(viable_pairs)} pairs after filter]")

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
                            print(f"  Return divergence filter: {viable_pairs.shape[0]} pairs remaining")

                        pair_cache.set_filtered(filtered_key, viable_pairs)

            if viable_pairs.empty:
                print(f"No viable pairs found for fold {i}")
                continue

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
                print(f"No pairs with sufficient test-window data for fold {i}")
                continue
            print(f"Selected {len(top_pairs)} pairs: {', '.join(top_pairs['pair'].tolist())}")
            
            # 4. Setup Backtest
            cerebro = bt.Cerebro()
            cerebro.broker.setcash(args.initial_cash)
            cerebro.broker.set_coc(True)
            
            is_stats = {}
            data_count = 0
            
            for _, row in top_pairs.iterrows():
                pair_name = row['pair']
                t1, t2 = pair_name.split('-')
                
                if args.profile == 'huck2015':
                    hl_col = 'half_life'
                    hr_col = 'hedge_ratio'
                    intercept_col = 'intercept'
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
                print(f"No data available for selected pairs in fold {i} test window.")
                continue

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
        
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', timeframe=bt.TimeFrame.Days, riskfreerate=0.0)
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='returns')
        
        # 6. Run
        results = cerebro.run()
        res = results[0]
        
        # 7. Collect Results
        daily_rets = res.analyzers.returns.get_analysis()
        for dt, ret in daily_rets.items():
            all_daily_returns.append({'date': dt, 'pnl_pct': ret, 'fold_id': i})
            
        logs = res.trade_logs
        s = res.analyzers.sharpe.get_analysis().get('sharperatio', 0)
        fold_summaries.append({
            'fold': i,
            'start': test_start,
            'end': test_end,
            'sharpe': s if s and not np.isnan(s) else 0.0,
            'trades': len(logs),
        })
        
        for rec in getattr(res, 'daily_active_counts', []):
            all_daily_active_counts.append({'date': rec['date'], 'count': rec['count'], 'deployed_capital': rec.get('deployed_capital', 0.0), 'fold_id': i})

        for rec in getattr(res, 'rejected_orders', []):
            rec['fold_id'] = i
            all_rejected_orders.append(rec)
        
        for log in logs:
            log['fold_id'] = i
            all_trade_logs.append(log)
            
        rejected_count = sum(1 for rec in getattr(res, 'rejected_orders', []) if rec)
        sh = s if s is not None and not np.isnan(s) else 0.0
        print(f"Fold {i} Complete: Sharpe={sh:.2f}, Trades={len(logs)}, Rejected={rejected_count}")

    # 8. Save Aggregates
    if fold_summaries:
        summary_df = pd.DataFrame(fold_summaries)
        summary_df.to_csv(os.path.join(args.output, "oos_fold_summary.csv"), index=False)
        
        if all_trade_logs:
            pd.DataFrame(all_trade_logs).to_csv(os.path.join(trade_logs_dir, "test_trade_log.csv"), index=False)

        if all_rejected_orders:
            pd.DataFrame(all_rejected_orders).to_csv(os.path.join(args.output, "rejected_orders.csv"), index=False)
            
        if all_daily_returns:
            returns_df = pd.DataFrame(all_daily_returns)
            cash = args.initial_cash
            cost_rate = args.spy_cost_bps / 10000

            # Build deployed-capital lookup: per fold per day
            deployed_lookup = {}
            if args.market_invest and all_daily_active_counts:
                at_df = pd.DataFrame(all_daily_active_counts)
                for fold_id, grp in at_df.groupby('fold_id'):
                    grp = grp.sort_values('date')
                    deployed_lookup[fold_id] = dict(zip(grp['date'], grp['deployed_capital']))

            # Reconstruct each fold's daily dollar PnL from percentage returns
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
                    'pnl': pnl_df,
                    'total_capital': cap_df,
                    'daily_return': daily_ret_series
                }).reset_index()
                daily_df.columns = ['date', 'pnl', 'total_capital', 'daily_return']

            daily_df.columns = [c.lower() for c in daily_df.columns]
            daily_df.to_csv(os.path.join(args.output, "daily_returns.csv"), index=False)

            total_days = len(daily_ret_series)

            # Trim edges where not all overlapping portfolios are active
            trim_months = args.test_months - args.slide_months
            if trim_months > 0 and total_days > 0:
                daily_dates = daily_ret_series.index.sort_values()
                cut_start = daily_dates[0] + pd.DateOffset(months=trim_months)
                cut_end = daily_dates[-1] - pd.DateOffset(months=trim_months)
                daily_ret_series = daily_ret_series[(daily_ret_series.index >= cut_start) & (daily_ret_series.index <= cut_end)]
                total_days = len(daily_ret_series)
                if total_days > 0:
                    print(f"  Trimmed {trim_months}m from each end: {daily_dates[0].date()}..{daily_dates[-1].date()} → "
                          f"{daily_ret_series.index[0].date()}..{daily_ret_series.index[-1].date()} ({total_days} days)")

            # Method 3: active-only daily returns (for Fama-French regression)
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
                
                # Merge daily active counts across overlapping folds, trimmed to same window
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
                    'total_folds': int(len(fold_summaries)),
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
    else:
        print("\nBacktest finished with no results.")

    pair_cache.save()

if __name__ == "__main__":
    run_backtest()
