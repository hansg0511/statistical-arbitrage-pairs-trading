"""Consolidated shared-account combined backtest (mechanisms A and B).

Replays the two pct=0.25 leg backtests' *trade events* (trade log + per-trade
daily marks) from the fixed sweep into a single capital account. Each leg keeps its own native
walk-forward grid, universe, and per-fold capital; the combination happens at
the trade-event level.

Pairs are modeled as cash-neutral (buy ~notional of one leg, short ~notional of
the other; net cash ~ 0), matching the engine, which never rejects on cash in
these runs. The fold's cash therefore only moves by realized PnL, and "deployed"
= gross notional outstanding.

Momentum weights are causal: trailing lookback Sharpe is evaluated strictly
before each month and the configured step and bounds set the capital split.

  Mechanism A (monthly re-weight of fold capital):
    each month, every active fold of leg L is re-funded to
    fold_capital = w_L(m) * C / n_active_L; new entries sized pct * fold_capital.
    Approximates the CSV momentum book (weight re-applied monthly).

  Mechanism B (entry-flow, let-drift):
    fold_capital is locked at fold start = C(fold_start) / n_active_L(start)
    (an equal slice of that leg's book, no weight); each new entry is sized
    pct * w_L(entry month) * fold_capital and rides to its logged exit.
    No monthly re-tilt; the leg split drifts with realized returns.

No forced rebalancing in either mechanism: open trades ride to their logged
exits (signal / stop / guard / max_holding / session_end).

Usage:
  python research/run_combined_backtest.py [--window recent|historical]
      [--mechanism A|B|both] [--config research/selected_book_config.json]
"""
import os
import math
import json
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

DEFAULT_CONFIG = Path(__file__).with_name('selected_book_config.json')


def load_selected_book_config(path=DEFAULT_CONFIG):
    """Load and validate the locked book configuration."""
    with open(path, encoding='utf-8') as handle:
        config = json.load(handle)
    if config.get('status') != 'locked':
        raise ValueError(f'selected book config is not locked: {path}')
    for key in ('pair', 'momentum', 'book', 'event_replay'):
        if key not in config:
            raise ValueError(f'selected book config is missing {key!r}: {path}')
    return config


def leg_specs(config, window):
    """Resolve configured relative fixed-sweep run directories."""
    root = config['event_replay']['input_root']
    windows = config['event_replay']['windows']
    if window not in windows:
        raise ValueError(f'unknown event-replay window: {window}')
    return {
        leg: (os.path.join(root, relative_path), leg)
        for leg, relative_path in windows[window].items()
    }


# --------------------------------------------------------------------------
# Loading helpers (take a fixed-sweep run directory or a legacy-style config name)
# --------------------------------------------------------------------------
def _run_dir(cfg_or_dir):
    """Accept a configured relative run directory or an absolute path."""
    return os.fspath(cfg_or_dir)


def load_ret(cfg_or_dir):
    df = pd.read_csv(os.path.join(_run_dir(cfg_or_dir), 'daily_returns.csv'), parse_dates=['date'])
    return df.set_index('date')['daily_return']


def load_trades(cfg_or_dir):
    p = os.path.join(_run_dir(cfg_or_dir), 'trade_logs', 'test_trade_log.csv')
    return pd.read_csv(p, parse_dates=['entry_date', 'exit_date'])


def load_marks(cfg_or_dir):
    p = os.path.join(_run_dir(cfg_or_dir), 'trade_marks.csv')
    return pd.read_csv(p, parse_dates=['date'])


def load_folds(cfg_or_dir):
    p = os.path.join(_run_dir(cfg_or_dir), 'oos_fold_summary.csv')
    return pd.read_csv(p, parse_dates=['start', 'end'])


# --------------------------------------------------------------------------
# Weight path (causal: trailing configured Sharpe strictly before each month)
# --------------------------------------------------------------------------
def _sharpe(x):
    x = x.dropna()
    if len(x) == 0:
        return float('nan')
    return x.mean() / x.std() * math.sqrt(252)


def weight_path_momentum_causal(a, b, lookback=63, step=0.10, wmin=0.25, wmax=0.75):
    union = a.index.union(b.index).sort_values()
    a = a.reindex(union).fillna(0.0)
    b = b.reindex(union).fillna(0.0)
    w = 0.5
    out = []
    for m in union.to_period('M').unique():
        cutoff = m.to_timestamp()
        sa = _sharpe(a[a.index < cutoff].tail(lookback))
        sb = _sharpe(b[b.index < cutoff].tail(lookback))
        if not math.isnan(sa) and not math.isnan(sb):
            if sa > sb:
                w = min(w + step, wmax)
            elif sb > sa:
                w = max(w - step, wmin)
        out.append((pd.Timestamp(cutoff), w))
    return pd.Series(dict(out))


# --------------------------------------------------------------------------
# Trade event construction (trade log + daily marks -> per-day returns)
# --------------------------------------------------------------------------
def build_trades(cfg_or_dir):
    """Return (trades, folds). Each trade has a 'daily' date->ret map."""
    logs = load_trades(cfg_or_dir)
    marks = load_marks(cfg_or_dir)
    folds = load_folds(cfg_or_dir)

    fc = folds.columns.tolist()
    i_fold, i_fs, i_fe = fc.index('fold'), fc.index('start'), fc.index('end')
    fold_start = {int(f[i_fold]): f[i_fs] for f in folds.itertuples(index=False, name=None)}
    fold_end = {int(f[i_fold]): f[i_fe] for f in folds.itertuples(index=False, name=None)}

    mc = marks.columns.tolist()
    i_mfid, i_mpair, i_mdate, i_mmp, i_mnt = (mc.index('fold_id'), mc.index('pair'),
                                              mc.index('date'), mc.index('mark_pnl'),
                                              mc.index('target_notional'))
    # group marks by (fold_id, pair) once as plain tuples (no per-trade pandas)
    mark_groups = {}
    for m in marks.itertuples(index=False, name=None):
        mark_groups.setdefault((int(m[i_mfid]), m[i_mpair]), []).append(
            (m[i_mdate], m[i_mmp], m[i_mnt]))

    tc = logs.columns.tolist()
    i_pair, i_ent, i_exit, i_reason, i_ret, i_fid = (tc.index('pair'), tc.index('entry_date'),
                                                     tc.index('exit_date'), tc.index('exit_reason'),
                                                     tc.index('return'), tc.index('fold_id'))
    trades = []
    for t in logs.itertuples(index=False, name=None):
        fid = int(t[i_fid])
        pair, entry, exit_, reason, ret = t[i_pair], t[i_ent], t[i_exit], t[i_reason], t[i_ret]
        rows = mark_groups.get((fid, pair), [])
        sub = sorted((r for r in rows if entry <= r[0] < exit_), key=lambda r: r[0])
        daily = {}
        if not sub:
            span = pd.date_range(entry, exit_, freq='B')
            if entry == exit_ or len(span) == 0:
                daily[entry] = ret
            else:
                share = ret / len(span)
                for d in span:
                    daily[d] = share
        else:
            notional = float(sub[0][2])
            prev = 0.0
            for dt, mp, _ in sub:
                v = mp / notional
                daily[dt] = v - prev
                prev = v
            daily[pd.Timestamp(exit_)] = ret - prev

        trades.append({
            'pair': pair,
            'fold_id': fid,
            'entry': entry,
            'exit': exit_,
            'reason': reason,
            'ret': float(ret),
            'daily': daily,
            'fold_start': fold_start.get(fid),
            'fold_end': fold_end.get(fid),
        })
    return trades, folds


def build_leg_data(cfg_or_dir):
    """Return {'trades', 'folds', 'ret'} for one run directory/config."""
    trades, folds = build_trades(cfg_or_dir)
    return {'trades': trades, 'folds': folds, 'ret': load_ret(cfg_or_dir)}


# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------
def simulate(leg_data, weight_path, mech, capital=1e6, pct=0.25, max_pairs=20):
    """leg_data: {'A': {'trades','folds'}, 'B': {'trades','folds'}}.
    Returns (rows, ledger, rejected, trade_rows)."""
    leg_names = ['A', 'B']
    all_trades = {L: leg_data[L]['trades'] for L in leg_names}
    folds_by_leg = {L: leg_data[L]['folds'] for L in leg_names}

    # One shared cash pool (pairs are cash-neutral; cash moves only on realized
    # PnL). Sub-accounts carry only a sizing 'basis' + their open trades.
    book_cash = capital
    subs = {}
    for L in leg_names:
        for _, f in folds_by_leg[L].iterrows():
            subs[(L, int(f['fold']))] = {'basis': None, 'open': {}}

    # date universe
    dates = set()
    for L in leg_names:
        for t in all_trades[L]:
            dates.update(t['daily'].keys())
    dates = sorted(dates)

    # precompute per-day active folds, weights, and rebalance days
    import bisect
    active_by_day = {d: set() for d in dates}
    fold_first_day = {}
    for L in leg_names:
        for _, f in folds_by_leg[L].iterrows():
            key = (L, int(f['fold']))
            lo = bisect.bisect_left(dates, f['start'])
            hi = bisect.bisect_right(dates, f['end'])
            for i in range(lo, min(hi, len(dates))):
                active_by_day[dates[i]].add(key)
            fold_first_day[key] = dates[lo] if lo < len(dates) and dates[lo] <= f['end'] else None

    w_index = weight_path.dropna().index
    wA_by_day = {}
    w_cur = 0.5
    it = iter(w_index)
    w_next = next(it, None)
    for d in dates:
        while w_next is not None and w_next <= d:
            w_cur = float(weight_path[w_next])
            w_next = next(it, None)
        wA_by_day[d] = w_cur

    rebalance_dates = set()
    prev = None
    for d in dates:
        if prev is None or (d.year, d.month) != (prev.year, prev.month):
            rebalance_dates.add(d)
        prev = d

    def wA(d):
        return wA_by_day.get(d, 0.5)

    def wL(leg, d):
        return wA(d) if leg == 'A' else (1 - wA(d))

    live = set()

    def total_value():
        return book_cash + sum(
            sum(info['notional'] * info['cumret'] for info in subs[key]['open'].values())
            for key in live
        )

    # --- mechanism A: monthly re-base of the entry-sizing basis ---
    def rebalance_a(d):
        C = total_value()
        for L in leg_names:
            active = sorted(k for k in active_by_day[d] if k[0] == L)
            if not active:
                continue
            target = wL(L, d) * C / len(active)
            for key in active:
                subs[key]['basis'] = target
        for key, sub in subs.items():
            if key not in active_by_day[d]:
                sub['basis'] = None

    # --- mechanism B: lock fold basis at fold start (equal slice of that leg) ---
    def activate_fold_b(leg, fid, d):
        sub = subs[(leg, fid)]
        if sub['basis'] is not None:
            return
        C = total_value()
        n_active_leg = sum(1 for key in active_by_day[d] if key[0] == leg)
        fc = C / n_active_leg if n_active_leg else 0.0
        sub['basis'] = fc

    entries_by_date = {}
    for L in leg_names:
        for t in all_trades[L]:
            entries_by_date.setdefault(t['entry'], []).append((L, t))

    rows = []
    ledger = []
    rejected = []
    trade_rows = []

    C_prev = None
    for d in dates:
        if mech == 'A':
            if d in rebalance_dates:
                rebalance_a(d)
        else:
            for key in active_by_day[d]:
                if fold_first_day.get(key) == d:
                    activate_fold_b(*key, d)

        # daily marks on live sub-accounts only
        for key in live:
            sub = subs[key]
            for info in sub['open'].values():
                info['cumret'] += info['daily'].get(d, 0.0)

        # exits (cash moves by realized PnL)
        for key in list(live):
            sub = subs[key]
            if not sub['open']:
                live.discard(key)
                continue
            for pair in list(sub['open'].keys()):
                info = sub['open'][pair]
                if info['exit'] <= d:
                    book_cash += info['notional'] * info['cumret']
                    del sub['open'][pair]
            if not sub['open']:
                live.discard(key)

        # entries
        for L, t in entries_by_date.get(d, []):
            sub = subs[(L, t['fold_id'])]
            basis = sub['basis']
            if mech == 'A':
                notional = pct * basis if basis else 0.0
            else:
                notional = pct * wL(L, d) * basis if basis else 0.0
            if notional <= 0:
                rejected.append({'date': d.date().isoformat(), 'leg': L, 'fold_id': t['fold_id'],
                                 'pair': t['pair'], 'reason': 'no_basis'})
                continue
            sub['open'][t['pair']] = {
                'notional': notional,
                'cumret': t['daily'].get(d, 0.0),
                'exit': t['exit'],
                'daily': t['daily'],
                'reason': t['reason'],
            }
            live.add((L, t['fold_id']))

        # end-of-day accounting
        C = total_value()
        pnl_d = 0.0 if C_prev is None else (C - C_prev)
        ret = 0.0 if C_prev is None or C_prev == 0 else (C - C_prev) / C_prev
        C_prev = C

        leg_val = {L: 0.0 for L in leg_names}
        leg_dep = {L: 0.0 for L in leg_names}
        for key in live:
            L, fid = key
            sub = subs[key]
            leg_val[L] += sum(info['notional'] * info['cumret'] for info in sub['open'].values())
            leg_dep[L] += sum(info['notional'] for info in sub['open'].values())

        rows.append({'date': d, 'pnl': pnl_d, 'total_capital': C, 'daily_return': ret})
        ledger.append({
            'date': d, 'weight_A': wA(d),
            'legA_open_pnl': leg_val['A'], 'legB_open_pnl': leg_val['B'],
            'legA_deployed': leg_dep['A'], 'legB_deployed': leg_dep['B'],
            'total_deployed': leg_dep['A'] + leg_dep['B'],
            'book_cash': book_cash,
        })

    for L in leg_names:
        for t in all_trades[L]:
            trade_rows.append({
                'leg': L, 'fold_id': t['fold_id'], 'pair': t['pair'],
                'entry': t['entry'].date().isoformat(),
                'exit': t['exit'].date().isoformat(),
                'reason': t['reason'],
                'return': round(t['ret'], 6),
            })

    return rows, ledger, rejected, trade_rows


# --------------------------------------------------------------------------
# Metrics & outputs
# --------------------------------------------------------------------------
def metrics(returns):
    r = returns.dropna()
    n = len(r)
    if n == 0:
        return {'ann_ret': float('nan'), 'ann_vol': float('nan'), 'sharpe': float('nan'), 'mdd': float('nan')}
    ann_ret = (1 + r).prod() ** (252 / n) - 1
    ann_vol = r.std() * math.sqrt(252)
    sh = _sharpe(r)
    mdd = ((1 + r).cumprod() / (1 + r).cumprod().cummax() - 1).min()
    return {'ann_ret': ann_ret, 'ann_vol': ann_vol, 'sharpe': sh, 'mdd': mdd}


def write_outputs(out_dir, rows, ledger, rejected, trade_rows, weight_path, m):
    os.makedirs(out_dir, exist_ok=True)
    pd.DataFrame(rows).to_csv(os.path.join(out_dir, 'daily_returns.csv'), index=False)
    pd.DataFrame(ledger).to_csv(os.path.join(out_dir, 'ledger.csv'), index=False)
    if rejected:
        pd.DataFrame(rejected).to_csv(os.path.join(out_dir, 'rejected_entries.csv'), index=False)
    if trade_rows:
        pd.DataFrame(trade_rows).to_csv(os.path.join(out_dir, 'trade_log.csv'), index=False)
    weight_path.to_frame('weight_A').reset_index().rename(columns={'index': 'date'}).to_csv(
        os.path.join(out_dir, 'weight_path.csv'), index=False)
    with open(os.path.join(out_dir, 'metrics.json'), 'w') as f:
        json.dump(m, f, indent=2, default=str)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default=str(DEFAULT_CONFIG))
    ap.add_argument('--window', default='recent', choices=['recent', 'historical'])
    ap.add_argument('--mechanism', default='both', choices=['A', 'B', 'both'])
    ap.add_argument('--capital', type=float)
    ap.add_argument('--pct-per-pair', type=float)
    ap.add_argument('--lookback', type=int)
    ap.add_argument('--step', type=float)
    ap.add_argument('--clamp', type=float, nargs=2)
    ap.add_argument('--out')
    args = ap.parse_args()

    config = load_selected_book_config(args.config)
    momentum = config['momentum']
    bounds = momentum['weight_bounds']
    capital = args.capital if args.capital is not None else config['book']['initial_capital']
    pct = args.pct_per_pair if args.pct_per_pair is not None else config['book']['pct_per_pair']
    lookback = args.lookback if args.lookback is not None else momentum['lookback_days']
    step = args.step if args.step is not None else momentum['step']
    clamp = args.clamp if args.clamp is not None else [bounds['min'], bounds['max']]
    output_root = args.out or config['event_replay']['output_root']

    leg_specs = leg_specs(config, args.window)
    leg_data = {}
    leg_rets = {}
    for L, (cfg, label) in leg_specs.items():
        leg_data[L] = {'trades': None, 'folds': None}
        leg_data[L]['trades'], leg_data[L]['folds'] = build_trades(cfg)
        leg_rets[L] = load_ret(cfg)

    wp = weight_path_momentum_causal(
        leg_rets['A'], leg_rets['B'],
        lookback=lookback, step=step,
        wmin=clamp[0], wmax=clamp[1],
    )

    mechanisms = ['A', 'B'] if args.mechanism == 'both' else [args.mechanism]
    for mech in mechanisms:
        rows, ledger, rejected, trade_rows = simulate(
            leg_data, wp, mech,
            capital=capital, pct=pct,
        )
        m = metrics(pd.Series([r['daily_return'] for r in rows]))
        m.update({'window': args.window, 'mechanism': mech, 'capital': capital,
                  'pct_per_pair': pct, 'lookback_days': lookback, 'step': step,
                  'weight_min': clamp[0], 'weight_max': clamp[1],
                  'config': os.path.abspath(args.config), 'n_days': len(rows),
                  'rejected_entries': len(rejected)})
        out_dir = os.path.join(output_root, args.window, mech)
        write_outputs(out_dir, rows, ledger, rejected, trade_rows, wp, m)
        print(f"[{args.window} {mech}] sharpe={m['sharpe']:.4f} ann_ret={m['ann_ret']*100:.2f}% "
              f"vol={m['ann_vol']*100:.2f}% mdd={m['mdd']*100:.1f}% rejected={len(rejected)} -> {out_dir}")


if __name__ == '__main__':
    main()
