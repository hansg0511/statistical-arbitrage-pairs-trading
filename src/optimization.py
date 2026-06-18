import backtrader as bt
import pandas as pd
import numpy as np
from skopt import gp_minimize
from skopt.space import Real, Integer, Categorical
from skopt.utils import use_named_args
from src.backtest import PairTradingStrategy, ZScoreData, prepare_backtest_data

class BayesianOptimizer:
    """
    Optimizes strategy parameters using Gaussian Processes to find the 
    highest risk-adjusted return (Sharpe Ratio) for a set of pairs.
    """
    def __init__(self, master_df: pd.DataFrame, pairs: pd.DataFrame, start: str, end: str, verbose: bool = True):
        self.master_df = master_df
        self.pairs = pairs
        self.start = start
        self.end = end
        self.verbose = verbose

    def optimize(self, n_calls: int = 50):
        # Define the search space based on empirical sensitivity analysis
        space = [
            Categorical([30, 45, 60, 90], name='resid_val'),
            Real(0.5, 1.5, name='z_m'),
            Real(1.5, 3.0, name='entry_z'),
            Real(0.0, 1.0, name='exit_z')
        ]

        @use_named_args(space)
        def objective(**params):
            total_sharpe = 0
            valid_pairs = 0
            
            for _, row in self.pairs.iterrows():
                t1, t2 = row['pair'].split('-')
                # Calculate Z-score lookback as a fraction of half-life
                z_lb = max(int(row['half_life_log'] * params['z_m']), 10)
                
                # Prepare data
                s1_close = self.master_df['Close'][t1]
                s2_close = self.master_df['Close'][t2]
                
                signals = prepare_backtest_data(s1_close, s2_close, params['resid_val'], z_lb)
                
                # Align and slice to the optimization window
                df1 = s1_close.loc[signals['dateIndex']].to_frame(name='close')
                for k, v in signals.items():
                    if k != 'dateIndex': df1[k] = v
                
                mask = (df1.index >= pd.to_datetime(self.start)) & (df1.index <= pd.to_datetime(self.end))
                df1 = df1.loc[mask].dropna()
                
                if len(df1) < 20: continue
                
                df2 = s2_close.loc[df1.index].to_frame(name='close')
                
                # Backtest execution
                cerebro = bt.Cerebro()
                data0 = ZScoreData(dataname=df1, close=0, zscore=1, hedge_ratio=2)
                data1 = bt.feeds.PandasData(dataname=df2, close=0)
                
                cerebro.adddata(data0, name=t1)
                cerebro.adddata(data1, name=t2)
                cerebro.addstrategy(PairTradingStrategy, 
                                    entry_z=params['entry_z'], 
                                    exit_z=params['exit_z'], 
                                    verbose=False)
                
                cerebro.broker.setcash(1000000.0)
                cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', timeframe=bt.TimeFrame.Days, riskfreerate=0.0)
                
                try:
                    res = cerebro.run()[0]
                    sharpe = res.analyzers.sharpe.get_analysis().get('sharperatio', 0)
                    total_sharpe += sharpe if (sharpe and not np.isnan(sharpe)) else 0
                    valid_pairs += 1
                except:
                    continue
            
            avg_sharpe = total_sharpe / max(valid_pairs, 1)
            if self.verbose:
                print(f"Params: {params} | Avg Sharpe: {avg_sharpe:.4f}")
            return -avg_sharpe

        res_gp = gp_minimize(objective, space, n_calls=n_calls, random_state=42)
        return res_gp
