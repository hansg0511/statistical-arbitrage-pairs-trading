import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from src.signal import compute_residuals, compute_zscore
from src.hedge_ratio_guard import check_hr_stability, calculate_locked_zscore

class ZScoreData(bt.feeds.PandasData):
    """
    Custom Backtrader data feed that includes pre-calculated signals 
    and regression parameters.
    """
    lines = ('zscore', 'hedge_ratio', 'intercept', 'rolling_std', 'rolling_mean', 'phi', 'sigma_eq',)
    params = tuple((l, -1) for l in lines)

class PairTradingStrategy(bt.Strategy):
    """
    A statistical arbitrage strategy with a Hedge Ratio Stability Guard.
    
    Key Features:
    - Adaptive signal generation using rolling Z-scores.
    - Hedge Ratio Guard: Exits if the relationship structurally decouples.
    - Locked Reference: Z-scores can be calculated against parameters 
      fixed at trade entry to prevent signal drift.
    """
    params = (
        ('entry_z', 2.0),
        ('exit_z', 0.5),
        ('stop_z', 3.0),
        ('hr_threshold', 0.5),
        ('is_stats', {}), # Initial/Anchor stats for guards
        ('log_space', True),
        ('lock_hr_for_zscore', True),
        ('lock_std_for_zscore', True),
        ('max_holding_days', 15),
        ('equity_fraction', 0.18),
        ('verbose', False),
        ('earnings_screen', None),
        ('earnings_block_days', 0),
    )

    def log(self, txt, dt=None):
        if self.p.verbose:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        self.pairs = []
        # Input data is expected to be provided in pairs (S1, S2)
        for i in range(0, len(self.datas), 2):
            s1, s2 = self.datas[i], self.datas[i+1]
            self.pairs.append({
                's1': s1, 's2': s2,
                'zscore': s1.zscore,
                'hedge_ratio': s1.hedge_ratio,
                'intercept': s1.intercept,
                'rolling_std': s1.rolling_std,
                'rolling_mean': s1.rolling_mean,
                'phi': s1.phi,
                'sigma_eq': s1.sigma_eq,
                'order': None
            })
        self.active_trades = {}
        self.trade_logs = []
        self.trade_count = 0
        self.daily_active_counts = []
        self.rejected_orders = []

    def notify_order(self, order):
        """Track and reset order objects to prevent redundant entry attempts."""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        for p in self.pairs:
            if order.data in [p['s1'], p['s2']]:
                pair_name = f"{p['s1']._name}-{p['s2']._name}"
                if order.status == order.Rejected:
                    self.rejected_orders.append({
                        'date': self.datas[0].datetime.date(0),
                        'pair': pair_name,
                        'reason': 'order_rejected',
                        'cash': self.broker.getcash(),
                        'value': self.broker.getvalue()
                    })
                elif order.status in [order.Completed]:
                    if order.isbuy():
                        self.log(f'BUY EXECUTED ({order.data._name}), {order.executed.price:.2f}')
                    else:
                        self.log(f'SELL EXECUTED ({order.data._name}), {order.executed.price:.2f}')
                
                p['order'] = None # Clear state for next trade
                break

    def next(self):
        self.daily_active_counts.append({
            'date': self.datas[0].datetime.date(0),
            'count': len(self.active_trades)
        })
        for p in self.pairs:
            pair_name = f"{p['s1']._name}-{p['s2']._name}"
            pos2 = self.getposition(p['s2']).size
            
            # --- SIGNAL CALCULATION ---
            # If we are in a trade and "locking" is enabled, recalculate Z using entry parameters
            if (self.p.lock_hr_for_zscore or self.p.lock_std_for_zscore) and pos2 != 0 and pair_name in self.active_trades:
                info = self.active_trades[pair_name]
                z = calculate_locked_zscore(
                    p['s1'].close[0], p['s2'].close[0],
                    info['intercept_entry'] if self.p.lock_hr_for_zscore else p['intercept'][0],
                    info['hr_entry'] if self.p.lock_hr_for_zscore else p['hedge_ratio'][0],
                    info['mu_entry'] if self.p.lock_std_for_zscore else p['rolling_mean'][0],
                    info['sigma_entry'] if self.p.lock_std_for_zscore else p['rolling_std'][0],
                    log_space=self.p.log_space
                )
            else:
                z = p['zscore'][0]

            anchor_hr = self.p.is_stats.get(pair_name, {}).get('hr', 0)
            current_hr = p['hedge_ratio'][0]

            # --- EXIT LOGIC ---
            if pos2 != 0:
                reason = None
                
                # 1. Hedge Ratio Stability Guard
                if not check_hr_stability(current_hr, anchor_hr, self.p.hr_threshold):
                    reason = 'guard_trip'
                
                # 2. Stop Loss (Z-score based)
                if not reason and abs(z) >= self.p.stop_z:
                    reason = 'stop_loss'
                
                # 3. Mean Reversion Signal
                if not reason:
                    if (pos2 > 0 and z >= -self.p.exit_z) or (pos2 < 0 and z <= self.p.exit_z):
                        reason = 'signal'
                
                # 4. Holding Period (Loss-only)
                if not reason and pair_name in self.active_trades:
                    info = self.active_trades[pair_name]
                    holding_days = (self.datas[0].datetime.date(0) - info['entry_date']).days
                    
                    # Calculate current PnL
                    p1_curr, p2_curr = p['s1'].close[0], p['s2'].close[0]
                    pnl2 = pos2 * (p2_curr - info['p2_entry'])
                    pnl1 = self.getposition(p['s1']).size * (p1_curr - info['p1_entry'])
                    
                    if holding_days >= self.p.max_holding_days and (pnl1 + pnl2) < 0:
                        reason = 'max_holding_loss'

                if reason:
                    self.record_exit(p, reason)
                    self.close(p['s1'])
                    self.close(p['s2'])
                    p['order'] = 'guard_blocked' if reason == 'guard_trip' else None
                    continue

            # --- ENTRY LOGIC ---
            if pos2 == 0:
                if p['order'] == 'guard_blocked':
                    if abs(z) < self.p.exit_z: p['order'] = None
                    else: continue
                
                if not p['order']:
                    if abs(z) >= self.p.entry_z and abs(z) < self.p.stop_z:
                        if not check_hr_stability(current_hr, anchor_hr, self.p.hr_threshold):
                            continue

                        if self.p.earnings_screen is not None:
                            s1_name = p['s1']._name
                            s2_name = p['s2']._name
                            entry_date = self.datas[0].datetime.date(0)
                            if (self.p.earnings_screen.has_earnings_in_window(s1_name, entry_date, self.p.max_holding_days, self.p.earnings_block_days)
                                or self.p.earnings_screen.has_earnings_in_window(s2_name, entry_date, self.p.max_holding_days, self.p.earnings_block_days)):
                                if self.p.verbose:
                                    self.log(f'Earnings screen blocked {pair_name}')
                                continue

                        notional = self.broker.getvalue() * self.p.equity_fraction
                        size2 = int(notional / p['s2'].close[0])
                        if self.p.log_space:
                            size1 = int(abs(size2 * current_hr * (p['s2'].close[0] / p['s1'].close[0])))
                        else:
                            size1 = int(abs(size2 * current_hr))
                        
                        if size1 <= 0 or size2 <= 0:
                            self.rejected_orders.append({
                                'date': self.datas[0].datetime.date(0),
                                'pair': pair_name,
                                'reason': 'zero_size',
                                'cash': self.broker.getcash(),
                                'value': self.broker.getvalue()
                            })
                            continue

                        if z <= -self.p.entry_z:
                            p['order'] = self.buy(p['s2'], size=size2)
                            if current_hr >= 0: self.sell(p['s1'], size=size1)
                            else: self.buy(p['s1'], size=size1)
                        else:
                            p['order'] = self.sell(p['s2'], size=size2)
                            if current_hr >= 0: self.buy(p['s1'], size=size1)
                            else: self.sell(p['s1'], size=size1)

                            self.trade_count += 1
                            self.active_trades[pair_name] = {
                                'entry_date': self.datas[0].datetime.date(0),
                                'p1_entry': p['s1'].close[0], 'p2_entry': p['s2'].close[0],
                                'hr_entry': current_hr, 'intercept_entry': p['intercept'][0],
                                'mu_entry': p['rolling_mean'][0], 'sigma_entry': p['rolling_std'][0],
                                'target_notional': notional
                            }

    def record_exit(self, p, reason):
        pair_name = f"{p['s1']._name}-{p['s2']._name}"
        if pair_name in self.active_trades:
            info = self.active_trades.pop(pair_name)
            p1_exit, p2_exit = p['s1'].close[0], p['s2'].close[0]
            
            # Simple PnL logging
            pnl2 = self.getposition(p['s2']).size * (p2_exit - info['p2_entry'])
            pnl1 = self.getposition(p['s1']).size * (p1_exit - info['p1_entry'])
            trade_pnl = pnl1 + pnl2
            
            self.trade_logs.append({
                'pair': pair_name,
                'entry_date': info['entry_date'],
                'exit_date': self.datas[0].datetime.date(0),
                'exit_reason': reason,
                'pnl': trade_pnl,
                'return': trade_pnl / info['target_notional']
            })

    def stop(self):
        """Force close any open trades at the end of the session."""
        for pair_name in list(self.active_trades.keys()):
            p = next((x for x in self.pairs if f"{x['s1']._name}-{x['s2']._name}" == pair_name), None)
            if p: self.record_exit(p, 'session_end')

def prepare_backtest_data(s1: pd.Series, s2: pd.Series, 
                          resid_lb: int, z_lb: int, 
                          test_start: Optional[str] = None,
                          test_end: Optional[str] = None,
                          log_space: bool = True,
                          fixed_params: Optional[Dict[str, float]] = None) -> Dict[str, pd.Series]:
    """
    Utility to pre-calculate all signals and alignment needed for 
    Backtrader feeds.
    
    When fixed_params is provided (dict with 'hedge_ratio', 'intercept', 
    'mu', 'sigma'), uses formation-period fixed parameters for Z-score 
    calculation instead of rolling estimates.
    """
    if fixed_params is not None:
        hr = fixed_params['hedge_ratio']
        intercept = fixed_params['intercept']
        mu = fixed_params['mu']
        sigma = fixed_params['sigma']
        
        if log_space:
            spread = np.log(s2) - (intercept + hr * np.log(s1))
        else:
            spread = s2 - (intercept + hr * s1)
        
        zscore = (spread - mu) / (sigma + 1e-10)
        
        data = {
            'dateIndex': zscore.index,
            'zscore': zscore,
            'hedge_ratio': pd.Series(hr, index=zscore.index),
            'intercept': pd.Series(intercept, index=zscore.index),
            'phi': pd.Series(np.nan, index=zscore.index),
            'sigma_eq': pd.Series(np.nan, index=zscore.index),
            'rolling_std': pd.Series(sigma, index=zscore.index),
            'rolling_mean': pd.Series(mu, index=zscore.index)
        }
    else:
        res_df = compute_residuals(s1, s2, lookback=resid_lb, log_space=log_space)
        zscore = compute_zscore(res_df['residual'], lookback=z_lb)
        
        data = {
            'dateIndex': zscore.index,
            'zscore': zscore,
            'hedge_ratio': res_df['hedge_ratio'],
            'intercept': res_df['intercept'],
            'phi': res_df['phi'],
            'sigma_eq': res_df['sigma_eq'],
            'rolling_std': res_df['residual'].rolling(z_lb).std(),
            'rolling_mean': res_df['residual'].rolling(z_lb).mean()
        }
    
    if test_start and test_end:
        idx = data['dateIndex']
        mask = (idx >= pd.to_datetime(test_start)) & (idx <= pd.to_datetime(test_end))
        for k in data:
            if k == 'dateIndex':
                data[k] = idx[mask]
            else:
                data[k] = data[k][mask]
                
    return data
