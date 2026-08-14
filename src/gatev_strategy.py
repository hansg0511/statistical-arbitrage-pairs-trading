import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, Optional


class GatevData(bt.feeds.PandasData):
    lines = ('zscore',)
    params = tuple((l, -1) for l in lines)


class GatevStrategy(bt.Strategy):
    """
    Gatev (2006) pairs trading strategy using normalized prices.
    - Entry: |z-score| > entry_z
    - Exit: |z-score| < exit_z
    - Dollar-neutral: equal notional in each leg (no hedge ratio)
    """
    params = (
        ('entry_z', 2.0),
        ('exit_z', 0.0),
        ('equity_fraction', 0.05),
        ('initial_cash', 1000000.0),
        ('verbose', False),
    )

    def __init__(self):
        self.pairs = []
        for i in range(0, len(self.datas), 2):
            s1, s2 = self.datas[i], self.datas[i + 1]
            self.pairs.append({
                's1': s1,
                's2': s2,
                'zscore': s1.zscore,
                'order': None,
            })
        self.active_trades = {}
        self.trade_logs = []
        self.trade_count = 0
        self.daily_active_counts = []
        self.rejected_orders = []

    def log(self, txt, dt=None):
        if self.p.verbose:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        for p in self.pairs:
            if order.data in [p['s1'], p['s2']]:
                p['order'] = None
                break

    def next(self):
        deployed = sum(info['target_notional'] for info in self.active_trades.values())
        self.daily_active_counts.append({
            'date': self.datas[0].datetime.date(0),
            'count': len(self.active_trades),
            'deployed_capital': deployed,
        })

        for p in self.pairs:
            pair_name = f"{p['s1']._name}-{p['s2']._name}"
            z = p['zscore'][0]
            pos2 = self.getposition(p['s2']).size

            # --- EXIT ---
            if pos2 != 0:
                reason = None

                if abs(z) <= self.p.exit_z:
                    reason = 'signal'

                if reason:
                    self._exit(p, pair_name, reason)
                    continue

            # --- ENTRY ---
            if pos2 == 0 and not p['order']:
                if abs(z) >= self.p.entry_z:
                    notional = self.p.initial_cash * self.p.equity_fraction
                    size1 = int(notional / p['s1'].close[0])
                    size2 = int(notional / p['s2'].close[0])

                    if size1 <= 0 or size2 <= 0:
                        self.rejected_orders.append({
                            'date': self.datas[0].datetime.date(0),
                            'pair': pair_name,
                            'reason': 'zero_size',
                        })
                        continue

                    # z < -entry_z: norm1 is cheap → long norm1 (buy s1), short norm2 (sell s2)
                    if z < -self.p.entry_z:
                        p['order'] = self.buy(p['s1'], size=size1)
                        self.sell(p['s2'], size=size2)
                    # z > entry_z: norm1 is expensive → short norm1 (sell s1), long norm2 (buy s2)
                    else:
                        p['order'] = self.sell(p['s1'], size=size1)
                        self.buy(p['s2'], size=size2)

                    self.active_trades[pair_name] = {
                        'entry_date': self.datas[0].datetime.date(0),
                        'p1_entry': p['s1'].close[0],
                        'p2_entry': p['s2'].close[0],
                        'target_notional': notional,
                    }
                    self.trade_count += 1

    def _exit(self, p, pair_name, reason):
        if pair_name in self.active_trades:
            info = self.active_trades.pop(pair_name)
            p1_exit, p2_exit = p['s1'].close[0], p['s2'].close[0]
            pnl2 = self.getposition(p['s2']).size * (p2_exit - info['p2_entry'])
            pnl1 = self.getposition(p['s1']).size * (p1_exit - info['p1_entry'])
            self.trade_logs.append({
                'pair': pair_name,
                'entry_date': info['entry_date'],
                'exit_date': self.datas[0].datetime.date(0),
                'exit_reason': reason,
                'pnl': pnl1 + pnl2,
                'return': (pnl1 + pnl2) / info['target_notional'],
            })
        self.close(p['s1'])
        self.close(p['s2'])
        p['order'] = None

    def stop(self):
        for pair_name in list(self.active_trades.keys()):
            p = next((x for x in self.pairs if f"{x['s1']._name}-{x['s2']._name}" == pair_name), None)
            if p:
                self._exit(p, pair_name, 'session_end')


def prepare_gatev_data(s1: pd.Series, s2: pd.Series,
                       sel_start: str, sel_end: str,
                       test_start: str, test_end: str) -> Dict:
    """
    Prepare Gatev-style normalized price spread data.

    1. Normalize each series by its first value in the selection window
    2. Spread = norm1 - norm2
    3. Z-score = (spread - mu) / sigma  (mu/sigma from formation period)
    """
    sel_s1 = s1.loc[sel_start:sel_end].dropna()
    sel_s2 = s2.loc[sel_start:sel_end].dropna()

    if len(sel_s1) < 10 or len(sel_s2) < 10:
        return {'dateIndex': pd.DatetimeIndex([]), 'zscore': pd.Series(dtype=float)}

    first_s1 = sel_s1.iloc[0]
    first_s2 = sel_s2.iloc[0]

    norm1 = s1 / first_s1
    norm2 = s2 / first_s2

    sel_spread = norm1.loc[sel_start:sel_end] - norm2.loc[sel_start:sel_end]
    mu = sel_spread.mean()
    sigma = sel_spread.std()

    if sigma < 1e-10:
        return {'dateIndex': pd.DatetimeIndex([]), 'zscore': pd.Series(dtype=float)}

    full_spread = norm1 - norm2
    zscore = (full_spread - mu) / sigma

    idx = zscore.index
    mask = (idx >= pd.to_datetime(test_start)) & (idx <= pd.to_datetime(test_end))

    return {
        'dateIndex': zscore.index[mask],
        'zscore': zscore[mask],
    }
