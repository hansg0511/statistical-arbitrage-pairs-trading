import argparse
import os
import pandas as pd
import numpy as np
import backtrader as bt
from datetime import datetime
import warnings

# Internal imports from GITHUBREPO/src
from src.constants import TICKERS, SECTOR_MAP, UNIVERSE
from src.data_loader import DataLoader
from src.pair_selection import PairSelector
from src.walk_forward import FoldBuilder
from src.backtest import PairTradingStrategy, ZScoreData, prepare_backtest_data
from src.config import STRATEGY_PARAMS, BACKTEST_SETTINGS, FOLD_SETTINGS, OUTPUT_DIR
from src.earnings_screen import EarningsScreen
from src.pair_cache import PairSelectionCache

warnings.filterwarnings('ignore')

def parse_args():
    parser = argparse.ArgumentParser(description='Run Walk-Forward Backtest for Pairs Trading Strategy')
    
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
    parser.add_argument('--no_warmup', action='store_true', help='Disable data warmup period (historical buffer)')
    
    # Walk-Forward Settings
    parser.add_argument('--sel_months', type=int, default=FOLD_SETTINGS['sel_months'], help='Selection window months')
    parser.add_argument('--test_months', type=int, default=FOLD_SETTINGS['test_months'], help='Test window months')
    parser.add_argument('--slide_months', type=int, default=FOLD_SETTINGS['slide_months'], help='Slide window months')
    
    # Pair Selection
    parser.add_argument('--cross_sector', action='store_true', default=False, help='Allow pairs across different sectors (default: within-sector only)')
    parser.add_argument('--fixed_params', action='store_true', default=False, help='Use formation-period fixed parameters for Z-score (no rolling estimates)')
    parser.add_argument('--return_divergence', type=float, default=None, help='Max cumulative return divergence between pair stocks over selection window (e.g. 0.10)')

    # Earnings Screen
    parser.add_argument('--earnings_screen', action='store_true', help='Enable earnings date screen (skip entry within 15d of earnings)')
    parser.add_argument('--earnings_cache', type=str, default=None, help='Path to shared earnings cache pickle')
    parser.add_argument('--earnings_block_days', type=int, default=0, help='Block entry for N days after an earnings event')

    # Cache
    parser.add_argument('--cache_dir', type=str, default='research/cache', help='Directory for pair selection cache')

    # Output
    parser.add_argument('--output', type=str, default=OUTPUT_DIR, help='Output directory for results')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    return parser.parse_args()

def run_backtest():
    args = parse_args()
    
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

    # 2. Build Folds
    fb = FoldBuilder(args.start, args.end, args.sel_months, 0, args.test_months, args.slide_months)
    if not fb.folds:
        print(f"Error: No folds generated. Your date range ({args.start} to {args.end}) is likely too short for the current settings.")
        print(f"Selection Window: {args.sel_months} months, Test Window: {args.test_months} months (Total {args.sel_months + args.test_months} months required).")
        return
        
    print(f"Generated {len(fb.folds)} walk-forward folds.")

    selector = PairSelector(pvalue_threshold=args.pvalue)
    pair_cache = PairSelectionCache(args.cache_dir)
    fold_summaries = []
    all_trade_logs = []
    all_daily_returns = []
    all_daily_active_counts = []
    all_rejected_orders = []
    
    for i, fold in enumerate(fb.folds):
        sel_start, sel_end, _, _, test_start, test_end = fold
        print(f"\n--- Processing Fold {i} [Test: {test_start} to {test_end}] ---")
        
        # 3. Pair Selection (with two-tier cache)
        divergence = args.return_divergence or 0.0
        filtered_key = (UNIVERSE, str(sel_start), str(sel_end), not args.cross_sector, round(divergence, 4))
        viable_pairs = pair_cache.get_filtered(filtered_key)
        if viable_pairs is not None:
            print(f"  [filtered cache HIT for sel {sel_start} to {sel_end}]")
        else:
            cache_key = (UNIVERSE, str(sel_start), str(sel_end), not args.cross_sector)
            viable_pairs = pair_cache.get(cache_key)
            if viable_pairs is None:
                viable_pairs = selector.select_pairs(master_df, SECTOR_MAP, str(sel_start), str(sel_end), same_sector_only=not args.cross_sector, return_divergence_threshold=args.return_divergence)
                pair_cache.set(cache_key, viable_pairs)
            else:
                print(f"  [cache HIT for sel {sel_start} to {sel_end}]")

            # Apply return divergence filter (for unfiltered cache data or fresh computation)
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

        top_pairs = viable_pairs.head(args.max_pairs)
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
            
            # Use appropriate metrics based on space
            hl_col = 'half_life_log' if args.log_space else 'half_life'
            hr_col = 'hedge_ratio_log' if args.log_space else 'hedge_ratio'
            intercept_col = 'intercept_log' if args.log_space else 'intercept'
            
            hl = row[hl_col]
            hr = row[hr_col]
            is_stats[pair_name] = {'hr': hr}
            
            # Calculate Z-score lookback (used only in non-fixed mode)
            z_lb = max(int(hl * args.z_m), 10)
            
            # Extract closing prices for data preparation
            if isinstance(master_df.columns, pd.MultiIndex):
                s1_close = master_df['Close'][t1]
                s2_close = master_df['Close'][t2]
            else:
                s1_close = master_df[t1]
                s2_close = master_df[t2]
            
            # Fixed-parameter mode: compute formation-period spread stats
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
                
            # Create Backtrader Feeds
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

        # 5. Add Strategy
        cerebro.addstrategy(
            PairTradingStrategy,
            entry_z=args.entry_z,
            exit_z=args.exit_z,
            stop_z=args.stop_z,
            max_holding_days=args.max_holding_days,
            hr_threshold=args.hr_thresh,
            is_stats=is_stats,
            log_space=args.log_space,
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
            all_daily_active_counts.append({'date': rec['date'], 'count': rec['count'], 'fold_id': i})

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

            # Reconstruct each fold's daily dollar PnL from percentage returns
            fold_dollar_pnl = []
            fold_capital = []

            for fold_id in returns_df['fold_id'].unique():
                fold_rets = returns_df[returns_df['fold_id'] == fold_id].sort_values('date')
                value = cash
                for _, row in fold_rets.iterrows():
                    pnl = value * row['pnl_pct']
                    fold_dollar_pnl.append({'date': row['date'], 'pnl_dollars': pnl, 'fold_id': fold_id})
                    fold_capital.append({'date': row['date'], 'capital_begin': value, 'fold_id': fold_id})
                    value += pnl

            pnl_df = pd.DataFrame(fold_dollar_pnl).groupby('date')['pnl_dollars'].sum()
            cap_df = pd.DataFrame(fold_capital).groupby('date')['capital_begin'].sum()
            daily_ret_series = (pnl_df / cap_df).dropna()

            daily_df = pd.DataFrame({
                'pnl': pnl_df,
                'total_capital': cap_df,
                'daily_return': daily_ret_series
            }).reset_index()
            daily_df.columns = ['date', 'pnl', 'total_capital', 'daily_return']
            daily_df.to_csv(os.path.join(args.output, "daily_returns.csv"), index=False)

            total_days = len(daily_ret_series)
            if total_days > 0:
                cum_ret = (1 + daily_ret_series).prod() - 1
                ann_ret = (1 + cum_ret)**(252 / total_days) - 1
                std = daily_ret_series.std()
                global_sharpe = (daily_ret_series.mean() / std * np.sqrt(252)) if std > 0 else 0.0
                
                # Merge daily active counts across overlapping folds
                if all_daily_active_counts:
                    at_df = pd.DataFrame(all_daily_active_counts)
                    daily_merged = at_df.groupby('date')['count'].sum()
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
            else:
                print("\nBacktest finished with no daily returns recorded.")
    else:
        print("\nBacktest finished with no results.")

    pair_cache.save()

if __name__ == "__main__":
    run_backtest()
