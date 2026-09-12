import backtrader as bt
import pandas as pd
import numpy as np
import math
from typing import Dict, List, Optional
from src.signal import compute_residuals, compute_zscore
from src.hedge_ratio_guard import check_hr_stability, calculate_locked_zscore


PAIR_SIZING_MODES = ('reference_leg', 'gross_exposure')


def calculate_pair_sizes(
    sizing_capital,
    equity_fraction,
    price1,
    price2,
    hr_entry,
    log_space=True,
    dollar_neutral=False,
    pair_sizing_mode='reference_leg',
):
    """Calculate entry share quantities for one pair.

    ``reference_leg`` deliberately contains the canonical sizing branches. Its
    ``reference_notional`` is also retained as the PnL normalization unit for
    replay compatibility. ``gross_exposure`` uses that same sizing capital to
    request a total two-leg gross budget, then applies the existing hedge-ratio
    share conversion before integer rounding. In reference-leg mode,
    ``pair_gross_budget`` is populated with the reference notional only as a
    comparison baseline; ``pair_gross_budget_enforced`` distinguishes it from
    the V2 cap.

    Gross sizing is incompatible with ``dollar_neutral`` because that option is
    itself a different two-leg allocation rule. Invalid gross inputs return a
    rejected result; they never fall back to reference-leg sizing.
    """
    if pair_sizing_mode not in PAIR_SIZING_MODES:
        raise ValueError(
            f'unsupported pair_sizing_mode {pair_sizing_mode!r}; '
            f'expected one of {PAIR_SIZING_MODES}'
        )

    try:
        sizing_capital = float(sizing_capital)
        equity_fraction = float(equity_fraction)
        p1 = float(price1)
        p2 = float(price2)
        reference_notional = sizing_capital * equity_fraction
    except (TypeError, ValueError):
        p1 = p2 = reference_notional = float('nan')

    budget_enforced = pair_sizing_mode == 'gross_exposure'

    def rejected(reason, reference_leg_target_notional=None):
        return {
            'valid': False,
            'reason': reason,
            'pair_sizing_mode': pair_sizing_mode,
            'reference_notional': reference_notional,
            'target_notional': reference_notional,
            'pair_gross_budget': reference_notional,
            'pair_gross_budget_enforced': budget_enforced,
            'reference_leg_target_notional': reference_leg_target_notional,
            'size1': 0,
            'size2': 0,
            'actual_gross_exposure': 0.0,
        }

    if (
        not math.isfinite(p1)
        or not math.isfinite(p2)
        or p1 <= 0
        or p2 <= 0
        or not math.isfinite(reference_notional)
        or reference_notional <= 0
    ):
        return rejected('invalid_sizing_input')

    if pair_sizing_mode == 'reference_leg':
        # Keep these branches identical to the pre-V2 implementation.
        if not dollar_neutral:
            try:
                hr_entry = float(hr_entry)
            except (TypeError, ValueError):
                return rejected('invalid_hedge_ratio')
            if not math.isfinite(hr_entry):
                return rejected('invalid_hedge_ratio')

        if dollar_neutral:
            size1 = int(reference_notional / p1)
            size2 = int(reference_notional / p2)
        elif log_space:
            size2 = int(reference_notional / p2)
            size1 = int(abs(size2 * hr_entry * (p2 / p1)))
        else:
            size2 = int(reference_notional / p2)
            size1 = int(abs(size2 * hr_entry))

        valid = size1 > 0 and size2 > 0

        return {
            'valid': valid,
            'reason': None if valid else 'zero_size',
            'pair_sizing_mode': pair_sizing_mode,
            'reference_notional': reference_notional,
            'target_notional': reference_notional,
            'pair_gross_budget': reference_notional,
            'pair_gross_budget_enforced': False,
            'reference_leg_target_notional': reference_notional,
            'size1': size1,
            'size2': size2,
            'actual_gross_exposure': size1 * p1 + size2 * p2,
        }

    if dollar_neutral:
        raise ValueError(
            'gross_exposure pair sizing requires dollar_neutral=False'
        )

    pair_gross_budget = reference_notional
    try:
        hr = float(hr_entry)
    except (TypeError, ValueError):
        hr = float('nan')

    if not math.isfinite(hr) or hr == 0:
        return rejected('invalid_hedge_ratio')

    hr_abs = abs(hr)
    if log_space:
        reference_leg_target_notional = pair_gross_budget / (1.0 + hr_abs)
        size2 = int(reference_leg_target_notional / p2)
        # Preserve the canonical log-space hedge conversion exactly; only its
        # reference-leg input notional changes under gross sizing.
        size1 = int(abs(size2 * hr * (p2 / p1)))
    else:
        # Raw-space V1 expresses the hedge relationship in share quantities, so
        # solve the gross-budget equation in shares instead of under-allocating
        # when the two leg prices differ.
        per_reference_share = p2 + hr_abs * p1
        reference_leg_target_notional = (
            pair_gross_budget * p2 / per_reference_share
        )
        size2 = int(pair_gross_budget / per_reference_share)
        size1 = int(abs(size2 * hr))

    actual_gross_exposure = size1 * p1 + size2 * p2
    if actual_gross_exposure > pair_gross_budget and size2 > 0:
        # Integer rounding in raw space can exceed the budget because the
        # canonical raw-space relationship is in shares rather than dollars.
        per_reference_share = p2 + (hr_abs * p2 if log_space else hr_abs * p1)
        reduction = max(
            1,
            int(math.ceil(
                (actual_gross_exposure - pair_gross_budget)
                / per_reference_share
            )),
        )
        size2 = max(0, size2 - reduction)
        if log_space:
            size1 = int(abs(size2 * hr * (p2 / p1)))
        else:
            size1 = int(abs(size2 * hr))
        actual_gross_exposure = size1 * p1 + size2 * p2
        while actual_gross_exposure > pair_gross_budget and size2 > 0:
            size2 -= 1
            if log_space:
                size1 = int(abs(size2 * hr * (p2 / p1)))
            else:
                size1 = int(abs(size2 * hr))
            actual_gross_exposure = size1 * p1 + size2 * p2

    valid = size1 > 0 and size2 > 0
    return {
        'valid': valid,
        'reason': None if valid else 'zero_size',
        'pair_sizing_mode': pair_sizing_mode,
        'reference_notional': reference_notional,
        'target_notional': reference_notional,
        'pair_gross_budget': pair_gross_budget,
        'pair_gross_budget_enforced': True,
        'reference_leg_target_notional': reference_leg_target_notional,
        'size1': size1,
        'size2': size2,
        'actual_gross_exposure': actual_gross_exposure,
    }

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
        ('pair_sizing_mode', 'reference_leg'),
        ('dollar_neutral', False),
        ('initial_cash', 1000000.0),
        ('verbose', False),
        ('earnings_screen', None),
        ('earnings_block_days', 0),
        ('margin_behavior', 'off'),  # off | report | reject (off = no margin, unchanged behavior)
        ('margin_long', 0.50),
        ('margin_short', 0.50),
        ('maintenance_long', 0.25),
        ('maintenance_short', 0.30),
        ('margin_rates', {}),  # per-ticker overrides {TICKER: {'long': x, 'short': y}}
    )

    def log(self, txt, dt=None):
        if self.p.verbose:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')

    def margin_rate(self, ticker, side):
        """Initial margin rate for a ticker/side: per-ticker override else global."""
        override = self.p.margin_rates.get(ticker)
        if isinstance(override, dict) and side in override:
            return float(override[side])
        if isinstance(override, (int, float)):
            return float(override)
        return float(getattr(self.p, f'margin_{side}'))

    def _position_book(self):
        """Long/short market values per ticker from live broker positions at close[0]."""
        long_book, short_book = {}, {}
        for data in self.datas:
            pos = self.getposition(data).size
            if pos == 0:
                continue
            value = abs(pos) * data.close[0]
            book = long_book if pos > 0 else short_book
            book[data._name] = book.get(data._name, 0.0) + value
        return long_book, short_book

    def _required_margin(self, long_book, short_book):
        return (sum(self.margin_rate(t, 'long') * v for t, v in long_book.items())
                + sum(self.margin_rate(t, 'short') * v for t, v in short_book.items()))

    def _maintenance_margin(self, long_book, short_book):
        return (self.p.maintenance_long * sum(long_book.values())
                + self.p.maintenance_short * sum(short_book.values()))

    def __init__(self):
        if self.p.pair_sizing_mode not in PAIR_SIZING_MODES:
            raise ValueError(
                f'unsupported pair_sizing_mode {self.p.pair_sizing_mode!r}; '
                f'expected one of {PAIR_SIZING_MODES}'
            )
        if self.p.pair_sizing_mode == 'gross_exposure' and self.p.dollar_neutral:
            raise ValueError(
                'gross_exposure pair sizing requires dollar_neutral=False'
            )
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
        self.trade_marks = []
        self.daily_margin = []
        self.daily_exposure = []
        self.signal_log = []
        self.entry_order_refs = set()

    def _update_entry_exposure(self, info):
        """Refresh signed entry quantities, dollar exposures, and margin estimates."""
        signed_size1 = float(info.get('signed_size1', 0.0))
        signed_size2 = float(info.get('signed_size2', 0.0))
        entry_price1 = float(info.get('entry_price1', 0.0))
        entry_price2 = float(info.get('entry_price2', 0.0))
        leg1_exposure = abs(signed_size1) * entry_price1
        leg2_exposure = abs(signed_size2) * entry_price2
        long_exposure = 0.0
        short_exposure = 0.0
        if signed_size1 > 0:
            long_exposure += leg1_exposure
        elif signed_size1 < 0:
            short_exposure += leg1_exposure
        if signed_size2 > 0:
            long_exposure += leg2_exposure
        elif signed_size2 < 0:
            short_exposure += leg2_exposure

        info.update({
            'leg1_entry_exposure': leg1_exposure,
            'leg2_entry_exposure': leg2_exposure,
            'gross_entry_exposure': leg1_exposure + leg2_exposure,
            'long_entry_exposure': long_exposure,
            'short_entry_exposure': short_exposure,
            'estimated_initial_margin_requirement': (
                self.margin_rate(info['ticker1'], info['side1']) * leg1_exposure
                + self.margin_rate(info['ticker2'], info['side2']) * leg2_exposure
            ),
            'estimated_maintenance_margin_requirement': (
                self.p.maintenance_long * long_exposure
                + self.p.maintenance_short * short_exposure
            ),
        })

    def _record_daily_exposure(self):
        """Record account-level gross and margin utilization from live positions."""
        long_book, short_book = self._position_book()
        equity = float(self.broker.getvalue())
        gross_long = float(sum(long_book.values()))
        gross_short = float(sum(short_book.values()))
        gross_exposure = gross_long + gross_short
        required = float(self._required_margin(long_book, short_book))
        maintenance = float(self._maintenance_margin(long_book, short_book))
        open_pairs = sum(
            1 for p in self.pairs
            if self.getposition(p['s1']).size != 0
            and self.getposition(p['s2']).size != 0
        )
        self.daily_exposure.append({
            'date': self.datas[0].datetime.date(0),
            'equity': equity,
            'cash': float(self.broker.getcash()),
            'gross_long': gross_long,
            'gross_short': gross_short,
            'gross_exposure': gross_exposure,
            'gross_utilization': gross_exposure / equity if equity > 0 else 0.0,
            'open_pairs': open_pairs,
            'estimated_initial_margin_requirement': required,
            'initial_margin_utilization': required / equity if equity > 0 else 0.0,
            'estimated_maintenance_margin_requirement': maintenance,
            'maintenance_margin_utilization': maintenance / equity if equity > 0 else 0.0,
        })

    def notify_order(self, order):
        """Track and reset order objects to prevent redundant entry attempts."""
        if order.status in [order.Submitted, order.Accepted]:
            return

        # Identify the pair for this order by the *identity* of the data feed.
        # A ticker can appear in many pairs (e.g. UNH in MO-UNH, PYPL-UNH, ...), so
        # matching by name/equality and breaking on the first hit attributes the
        # order to the wrong pair. Identity matching is unambiguous.
        p = next((pp for pp in self.pairs
                  if order.data is pp['s1'] or order.data is pp['s2']), None)
        if p is None:
            return

        pair_name = f"{p['s1']._name}-{p['s2']._name}"
        info = self.active_trades.get(pair_name)
        is_entry = info is not None and 'filled_legs' in info

        if order.status in [order.Rejected, order.Margin]:
            # Only treat a rejection as a real "failed entry" if this order is one of
            # the entry orders we submitted. A close order (self.close()) of a successful
            # trade can also surface a Margin status; those are NOT failed entries and
            # must not be logged to rejected_orders.csv.
            if order.ref not in self.entry_order_refs:
                p['order'] = None
                return
            reason = 'order_rejected' if order.status == order.Rejected else 'margin'
            leg = 's1' if order.data is p['s1'] else 's2'
            # side: the direction this leg is being opened (long for a BUY, short for a SELL)
            side = 'long' if order.isbuy() else 'short'
            self.rejected_orders.append({
                'date': self.datas[0].datetime.date(0),
                'pair': pair_name,
                'reason': reason,
                'cash': self.broker.getcash(),
                'value': self.broker.getvalue(),
                'leg': leg,
                'ticker': order.data._name,
                'side': side,
                'req_size': order.size,
                'hr_entry': info.get('hr_entry') if info is not None else None,
                'entry_date': info.get('entry_date') if info is not None else None,
            })
            self.entry_order_refs.discard(order.ref)
            # An entry leg failed to fill. Unwind any leg that already filled
            # (avoid a naked position) and drop the entry so it never surfaces
            # as a phantom trade.
            if is_entry:
                if 's1' in info['filled_legs']:
                    self.close(p['s1'])
                if 's2' in info['filled_legs']:
                    self.close(p['s2'])
                self.active_trades.pop(pair_name, None)
        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED ({order.data._name}), {order.executed.price:.2f}')
            else:
                self.log(f'SELL EXECUTED ({order.data._name}), {order.executed.price:.2f}')
            self.entry_order_refs.discard(order.ref)
            if is_entry:
                # Only count a leg as filled if the broker actually executed a
                # non-zero size (a zero-size fill means it couldn't afford it).
                if order.executed.size != 0:
                    leg = 's1' if order.data is p['s1'] else 's2'
                    info[f'signed_size{1 if leg == "s1" else 2}'] = float(order.executed.size)
                    info[f'size{1 if leg == "s1" else 2}'] = int(abs(order.executed.size))
                    info[f'entry_price{1 if leg == "s1" else 2}'] = float(order.executed.price)
                    self._update_entry_exposure(info)
                    info['filled_legs'].add(leg)
                else:
                    leg = 's1' if order.data is p['s1'] else 's2'
                    self.rejected_orders.append({
                        'date': self.datas[0].datetime.date(0),
                        'pair': pair_name,
                        'reason': 'zero_fill',
                        'cash': self.broker.getcash(),
                        'value': self.broker.getvalue(),
                        'leg': leg,
                        'ticker': order.data._name,
                        'side': 'long' if order.isbuy() else 'short',
                        'req_size': order.size,
                        'hr_entry': info.get('hr_entry'),
                        'entry_date': info.get('entry_date'),
                    })
                    # Close/undo any already-filled leg and drop the entry.
                    if 's1' in info['filled_legs']:
                        self.close(p['s1'])
                    if 's2' in info['filled_legs']:
                        self.close(p['s2'])
                    self.active_trades.pop(pair_name, None)

        p['order'] = None  # Clear state for next trade

    def next(self):
        deployed = sum(info['target_notional'] for info in self.active_trades.values())
        self.daily_active_counts.append({
            'date': self.datas[0].datetime.date(0),
            'count': len(self.active_trades),
            'deployed_capital': deployed
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

            # --- SIGNAL LOG (diagnostic: capture the entry decision inputs) ---
            self.signal_log.append({
                    'date': self.datas[0].datetime.date(0),
                    'pair': pair_name,
                    'z': z,
                    'entry_z': self.p.entry_z,
                    'exit_z': self.p.exit_z,
                    'stop_z': self.p.stop_z,
                    'pos2': pos2,
                    'order_state': ('guard_blocked' if p['order'] == 'guard_blocked'
                                    else ('OPEN' if p['order'] else None)),
                    'in_active': pair_name in self.active_trades,
                    'in_pending': pair_name in getattr(self, 'pending_trades', {}),
                    'hr': current_hr,
                    'anchor_hr': anchor_hr,
                })

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
                if isinstance(p['order'], str) and p['order'] == 'guard_blocked':
                    if abs(z) < self.p.exit_z: p['order'] = None
                    else: continue
                
                if not p['order']:
                    if abs(z) >= self.p.entry_z and abs(z) < self.p.stop_z:
                        try:
                            current_hr_value = float(current_hr)
                        except (TypeError, ValueError):
                            current_hr_value = float('nan')
                        invalid_hr = not math.isfinite(current_hr_value)
                        zero_hr = current_hr_value == 0 and not self.p.dollar_neutral
                        if invalid_hr or zero_hr:
                            self.rejected_orders.append({
                                'date': self.datas[0].datetime.date(0),
                                'pair': pair_name,
                                'reason': (
                                    'invalid_hedge_ratio'
                                    if invalid_hr or self.p.pair_sizing_mode == 'gross_exposure'
                                    else 'zero_size'
                                ),
                                'cash': self.broker.getcash(),
                                'value': self.broker.getvalue(),
                                'pair_sizing_mode': self.p.pair_sizing_mode,
                                'hr_entry': current_hr,
                                'pair_gross_budget': (
                                    self.p.initial_cash * self.p.equity_fraction
                                ),
                            })
                            continue
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

                        sizing = calculate_pair_sizes(
                            self.p.initial_cash,
                            self.p.equity_fraction,
                            p['s1'].close[0],
                            p['s2'].close[0],
                            current_hr,
                            log_space=self.p.log_space,
                            dollar_neutral=self.p.dollar_neutral,
                            pair_sizing_mode=self.p.pair_sizing_mode,
                        )
                        size1 = sizing['size1']
                        size2 = sizing['size2']
                        notional = sizing['target_notional']

                        if not sizing['valid']:
                            self.rejected_orders.append({
                                'date': self.datas[0].datetime.date(0),
                                'pair': pair_name,
                                'reason': sizing['reason'],
                                'cash': self.broker.getcash(),
                                'value': self.broker.getvalue(),
                                'pair_sizing_mode': self.p.pair_sizing_mode,
                                'hr_entry': current_hr,
                                'pair_gross_budget': sizing['pair_gross_budget'],
                            })
                            continue

                        if z <= -self.p.entry_z:
                            s2_side = 'long'
                            s1_side = 'short' if current_hr >= 0 else 'long'
                        else:
                            s2_side = 'short'
                            s1_side = 'long' if current_hr >= 0 else 'short'

                        if self.p.margin_behavior != 'off':
                            equity = self.broker.getvalue()
                            long_book, short_book = self._position_book()
                            required = self._required_margin(long_book, short_book)
                            s1_val = size1 * p['s1'].close[0]
                            s2_val = size2 * p['s2'].close[0]
                            incremental = (self.margin_rate(p['s2']._name, s2_side) * s2_val
                                           + self.margin_rate(p['s1']._name, s1_side) * s1_val)
                            free_after = equity - (required + incremental)
                            if free_after < 0:
                                self.rejected_orders.append({
                                    'date': self.datas[0].datetime.date(0),
                                    'pair': pair_name,
                                    'reason': 'margin' if self.p.margin_behavior == 'reject' else 'margin_report',
                                    'cash': self.broker.getcash(),
                                    'value': equity,
                                    'required_margin': required,
                                    'incremental_margin': incremental,
                                    'free_margin_after': free_after,
                                })
                                if self.p.margin_behavior == 'reject':
                                    continue

                        if z <= -self.p.entry_z:
                            o2 = self.buy(p['s2'], size=size2)
                            o1 = self.sell(p['s1'], size=size1) if current_hr >= 0 else self.buy(p['s1'], size=size1)
                        else:
                            o2 = self.sell(p['s2'], size=size2)
                            o1 = self.buy(p['s1'], size=size1) if current_hr >= 0 else self.sell(p['s1'], size=size1)
                        p['order'] = o2
                        # Mark both leg orders as entry orders so notify_order only
                        # logs/act on rejections that belong to an entry attempt
                        # (not close-orders of a successful trade).
                        self.entry_order_refs.add(o2.ref)
                        self.entry_order_refs.add(o1.ref)

                        self.trade_count += 1
                        self.active_trades[pair_name] = {
                            'entry_date': self.datas[0].datetime.date(0),
                            'p1_entry': p['s1'].close[0], 'p2_entry': p['s2'].close[0],
                            'hr_entry': current_hr, 'intercept_entry': p['intercept'][0],
                            'mu_entry': p['rolling_mean'][0], 'sigma_entry': p['rolling_std'][0],
                            # target_notional is retained as the legacy
                            # reference-sizing unit used by replay PnL.
                            'pair_sizing_mode': self.p.pair_sizing_mode,
                            'reference_notional': sizing['reference_notional'],
                            'target_notional': notional,
                            'pair_gross_budget': sizing['pair_gross_budget'],
                            'pair_gross_budget_enforced': sizing[
                                'pair_gross_budget_enforced'
                            ],
                            'reference_leg_target_notional': sizing['reference_leg_target_notional'],
                            'planned_size1': size1,
                            'planned_size2': size2,
                            'size1': size1,
                            'size2': size2,
                            'entry_price1': float(p['s1'].close[0]),
                            'entry_price2': float(p['s2'].close[0]),
                            'signed_size1': float(size1 if s1_side == 'long' else -size1),
                            'signed_size2': float(size2 if s2_side == 'long' else -size2),
                            'side1': s1_side,
                            'side2': s2_side,
                            'ticker1': p['s1']._name,
                            'ticker2': p['s2']._name,
                            'filled_legs': set()
                        }
                        self._update_entry_exposure(self.active_trades[pair_name])

        # --- DAILY MARKS (mark-to-market per open trade, end of day) ---
        if self.active_trades:
            pair_by_name = {f"{p['s1']._name}-{p['s2']._name}": p for p in self.pairs}
            for pair_name in list(self.active_trades.keys()):
                p = pair_by_name.get(pair_name)
                if p is None:
                    continue
                info = self.active_trades[pair_name]
                self.trade_marks.append({
                    'date': self.datas[0].datetime.date(0),
                    'pair': pair_name,
                    'mark_pnl': self._current_pnl(p, info),
                    'target_notional': info['target_notional'],
                    'pair_sizing_mode': info['pair_sizing_mode'],
                    'reference_notional': info['reference_notional'],
                    'pair_gross_budget': info['pair_gross_budget'],
                    'pair_gross_budget_enforced': info[
                        'pair_gross_budget_enforced'
                    ],
                    'gross_entry_exposure': info['gross_entry_exposure'],
                    'pnl_per_reference_sizing_unit': (
                        self._current_pnl(p, info) / info['target_notional']
                    ),
                })

        # --- DAILY MARGIN (end-of-day, same convention/lag as trade_marks) ---
        if self.p.margin_behavior != 'off':
            long_book, short_book = self._position_book()
            equity = self.broker.getvalue()
            required = self._required_margin(long_book, short_book)
            maintenance = self._maintenance_margin(long_book, short_book)
            self.daily_margin.append({
                'date': self.datas[0].datetime.date(0),
                'equity': equity,
                'cash': self.broker.getcash(),
                'gross_long': sum(long_book.values()),
                'gross_short': sum(short_book.values()),
                'required_margin': required,
                'maintenance_margin': maintenance,
                'free_margin': equity - required,
                'utilization': required / equity if equity > 0 else 0.0,
                'margin_call_distance': equity - maintenance,
                'margin_call': bool(equity < maintenance),
            })

        self._record_daily_exposure()

    def _current_pnl(self, p, info):
        p1_curr, p2_curr = p['s1'].close[0], p['s2'].close[0]
        pnl2 = self.getposition(p['s2']).size * (p2_curr - info['p2_entry'])
        pnl1 = self.getposition(p['s1']).size * (p1_curr - info['p1_entry'])
        return pnl1 + pnl2

    def record_exit(self, p, reason):
        pair_name = f"{p['s1']._name}-{p['s2']._name}"
        if pair_name in self.active_trades:
            info = self.active_trades.pop(pair_name)

            # Simple PnL logging
            trade_pnl = self._current_pnl(p, info)
            pnl_per_reference_unit = trade_pnl / info['target_notional']

            self.trade_logs.append({
                'pair': pair_name,
                'entry_date': info['entry_date'],
                'exit_date': self.datas[0].datetime.date(0),
                'exit_reason': reason,
                'pnl': trade_pnl,
                # Retain the legacy field for replay compatibility. It is PnL
                # per reference sizing unit, not a return on capital employed.
                'return': pnl_per_reference_unit,
                'pnl_per_reference_sizing_unit': pnl_per_reference_unit,
                'pair_sizing_mode': info['pair_sizing_mode'],
                'hr_entry': info['hr_entry'],
                'reference_notional': info['reference_notional'],
                'target_notional': info['target_notional'],
                'pair_gross_budget': info['pair_gross_budget'],
                'pair_gross_budget_enforced': info[
                    'pair_gross_budget_enforced'
                ],
                'size1': info['size1'],
                'size2': info['size2'],
                'entry_price1': info['entry_price1'],
                'entry_price2': info['entry_price2'],
                'leg1_entry_exposure': info['leg1_entry_exposure'],
                'leg2_entry_exposure': info['leg2_entry_exposure'],
                'gross_entry_exposure': info['gross_entry_exposure'],
                'long_entry_exposure': info['long_entry_exposure'],
                'short_entry_exposure': info['short_entry_exposure'],
                'estimated_initial_margin_requirement': (
                    info['estimated_initial_margin_requirement']
                ),
                'estimated_maintenance_margin_requirement': (
                    info['estimated_maintenance_margin_requirement']
                ),
            })

    def stop(self):
        """Force close any open trades at the end of the session."""
        for pair_name in list(self.active_trades.keys()):
            p = next((x for x in self.pairs if f"{x['s1']._name}-{x['s2']._name}" == pair_name), None)
            if p:
                info = self.active_trades[pair_name]
                # Do not record a session_end trade for a pair that holds no position
                # or whose entry never fully filled (e.g. entered on the last bar).
                if (self.getposition(p['s1']).size == 0 and self.getposition(p['s2']).size == 0
                        or len(info.get('filled_legs', ())) < 2):
                    self.active_trades.pop(pair_name, None)
                    continue
                self.record_exit(p, 'session_end')

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

    Only the rows needed to compute signals inside the test window are used:
    the input series are sliced to ``[test_start - warmup : test_end]`` before
    the rolling regression, where ``warmup`` covers the residual lookback plus
    the z-score lookback (with a calendar-day buffer). This keeps the rolling
    OLS from scanning the full history on every fold (a large speedup) without
    changing the resulting test-window signals.
    """
    if test_start is not None:
        ts = pd.to_datetime(test_start)
        te = pd.to_datetime(test_end) if test_end is not None else None
        # Trading days needed before test_start: resid_lb + z_lb. Convert to
        # calendar days with a ~1.5x buffer (weekends/holidays) plus margin.
        need_rows = resid_lb + z_lb
        cal_buffer = int(need_rows * 1.5) + 30
        warm_start = ts - pd.Timedelta(days=cal_buffer)
        if te is not None:
            s1 = s1.loc[warm_start:te]
            s2 = s2.loc[warm_start:te]
        else:
            s1 = s1.loc[warm_start:]
            s2 = s2.loc[warm_start:]

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
