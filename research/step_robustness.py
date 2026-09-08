"""Robustness of our pair's Sharpe and rank (all 496) to momentum params.

For each (lookback, step) combo, recompute for every pair the three ranking
inputs exactly as compare_rankings.py does (recent = mean of 5 aligned starts,
hist = one window, joined = Sharpe of hist ++ recent concat, mech A and B), then
report our pair's rank under all three ranking methods plus its Sharpe values.

Mode:
  step  : vary step size at fixed lookback 63   [default]
  lookback : vary lookback at fixed step 0.10

Usage: python research/step_robustness.py [step|lookback]
"""
import os
import sys
import itertools
import statistics
import multiprocessing as mp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from research.pair_sweep_consolidated import (  # noqa: E402
    STRATEGIES, CFGS, get_leg, dense_ranks,
)
from research.run_combined_backtest import (  # noqa: E402
    weight_path_momentum_causal, simulate, metrics,
)

BASE = 'fixed_diagnosis'
PCT = 0.25
LEGS = [(s, c) for s in STRATEGIES for c in CFGS]
PAIRS = list(itertools.combinations(LEGS, 2))

TARGET_A = 'sp500-2m/cross_sector_slide3m_bd7'
TARGET_B = 'sp500-12m/cross_sector_slide1m_noscreen'

DEFAULT_STEP = 0.10
DEFAULT_LOOKBACK = 63


def _series(a, b, mech, step, lookback, wmin, wmax):
    wp = weight_path_momentum_causal(a['ret'], b['ret'], lookback=lookback, step=step,
                                     wmin=wmin, wmax=wmax)
    rows, _, _, _ = simulate({'A': a, 'B': b}, wp, mech, capital=1e6, pct=PCT)
    return pd.Series([r['daily_return'] for r in rows], index=[r['date'] for r in rows])


def _pair_stats(sa, ca, sb, cb, mech, step, lookback, wmin, wmax):
    """Return (recent_mean, hist, joined) Sharpe for one pair/mech."""
    rec_s = []
    for i in range(5):
        a = get_leg(sa, ca, 'recent', i)
        b = get_leg(sb, cb, 'recent', i)
        rec_s.append(_series(a, b, mech, step, lookback, wmin, wmax))
    ha = get_leg(sa, ca, 'historical', 0)
    hb = get_leg(sb, cb, 'historical', 0)
    hist_s = _series(ha, hb, mech, step, lookback, wmin, wmax)
    rm = statistics.mean(metrics(s)['sharpe'] for s in rec_s)
    hs = metrics(hist_s)['sharpe']
    joined = statistics.mean(metrics(pd.concat([hist_s, s]))['sharpe'] for s in rec_s)
    return rm, hs, joined


def _work(args):
    (sa, ca), (sb, cb), mech, step, lookback, wmin, wmax = args
    try:
        rm, hs, jsh = _pair_stats(sa, ca, sb, cb, mech, step, lookback, wmin, wmax)
    except Exception:
        return None
    return {'A': '%s/%s' % (sa, ca), 'B': '%s/%s' % (sb, cb),
            'mech': mech, 'recent': rm, 'hist': hs, 'joined_sh': jsh}


def _compute(step, lookback, wmin, wmax):
    tasks = [((sa, ca), (sb, cb), mech, step, lookback, wmin, wmax)
             for (sa, ca), (sb, cb) in PAIRS for mech in ['A', 'B']]
    with mp.Pool(16) as pool:
        rows = [r for r in pool.map(_work, tasks) if r is not None]
    out = {}
    for mech in ['A', 'B']:
        sub = [r for r in rows if r['mech'] == mech]
        rec = [r['recent'] for r in sub]
        hist = [r['hist'] for r in sub]
        joined = [r['joined_sh'] for r in sub]
        r_rank = dense_ranks(rec)
        h_rank = dense_ranks(hist)
        score = [min(r['recent'], r['hist']) for r in sub]
        rank_avg = [(r_rank[i] + h_rank[i]) / 2.0 for i in range(len(sub))]
        for i, r in enumerate(sub):
            r['score_rank'] = dense_ranks(score)[i]
            r['rank_avg_rank'] = dense_ranks(rank_avg, reverse=False)[i]
            r['joined_rank'] = dense_ranks(joined)[i]
        out[mech] = sub
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'step'
    force = '--force' in sys.argv[2:]
    if mode == 'step':
        grid = [('step', s, DEFAULT_LOOKBACK, 0.25, 0.75) for s in [0.05, 0.10, 0.15]]
        out_csv = '_STEP_ROBUSTNESS.csv'
    elif mode == 'lookback':
        grid = [('lookback', DEFAULT_STEP, lb, 0.25, 0.75) for lb in [42, 63, 84]]
        out_csv = '_LOOKBACK_ROBUSTNESS.csv'
    elif mode == 'joint':
        grid = [('lb%d_s%.2f' % (lb, s), s, lb, 0.25, 0.75)
                for lb in [63, 84, 126] for s in [0.10, 0.15, 0.20]]
        out_csv = '_JOINT_ROBUSTNESS.csv'
    elif mode == 'bounds':
        grid = [('b%.2f_%.2f' % (wmin, wmax), 0.20, 84, wmin, wmax)
                for wmin, wmax in [(0.25, 0.75), (0.20, 0.80), (0.30, 0.70), (0.35, 0.65)]]
        out_csv = '_BOUNDS_ROBUSTNESS.csv'
    elif mode == 'frontier':
        grid = [
            ('b%.2f_%.2f' % (wmin, wmax), 0.20, 84, wmin, wmax)
            for wmin, wmax in [(0.20, 0.80), (0.15, 0.85), (0.10, 0.90)]
        ] + [
            ('step%.2f_b%.2f_%.2f' % (s, wmin, wmax), s, 84, wmin, wmax)
            for s, wmin, wmax in [(0.25, 0.20, 0.80)]
        ]
        out_csv = '_FRONTIER_ROBUSTNESS.csv'
    elif mode == 'final':
        grid = [('final_lb84_s0.30_b0.15_0.85', 0.30, 84, 0.15, 0.85)]
        out_csv = '_FINAL_ROBUSTNESS.csv'
    elif mode == 'clean':
        grid = [
            ('clean_s%.2f_b%.2f_%.2f' % (s, wmin, wmax), s, 84, wmin, wmax)
            for s, wmin, wmax in [
                (0.50, 0.00, 1.00), (0.40, 0.10, 0.90), (0.30, 0.20, 0.80),
                (0.25, 0.25, 0.75),
            ]
        ]
        out_csv = '_CLEAN_ROBUSTNESS.csv'
    elif mode == 'top':
        out = _compute(0.30, 84, 0.15, 0.85)
        for mech in ['A', 'B']:
            sub = out[mech]
            print('=== Mech %s top-10 by each method (final lb84/s0.30/b15-85) ===' % mech)
            for col, label in [('score_rank', 'min-score'), ('rank_avg_rank', 'rank-avg'),
                               ('joined_rank', 'joined')]:
                top = sorted(sub, key=lambda r: r[col])[:10]
                print('  -- %s --' % label)
                for r in top:
                    is_ours = r['A'] == TARGET_A and r['B'] == TARGET_B
                    print('     %2d  %s + %s%s' % (r[col], r['A'], r['B'],
                                                   '  <== OURS' if is_ours else ''))
            print()
        return
    else:
        raise SystemExit('usage: python research/step_robustness.py [step|lookback|joint|bounds|frontier|final|clean|top]')

    out_path = os.path.join(BASE, 'compare', out_csv)
    if force and os.path.exists(out_path):
        os.remove(out_path)
    done = set()
    if os.path.exists(out_path) and not force:
        prev = pd.read_csv(out_path)
        done = set(prev['param'])
        print('resuming: %d configs already in %s' % (len(done), out_csv))

    result_rows = []
    for name, step, lookback, wmin, wmax in grid:
        if name in done:
            continue
        out = _compute(step, lookback, wmin, wmax)
        for mech in ['A', 'B']:
            for r in out[mech]:
                if r['A'] == TARGET_A and r['B'] == TARGET_B:
                    result_rows.append({'param': name, 'mech': mech,
                                        'recent': round(r['recent'], 3),
                                        'hist': round(r['hist'], 3),
                                        'joined': round(r['joined_sh'], 3),
                                        'score_rank': r['score_rank'],
                                        'rank_avg_rank': r['rank_avg_rank'],
                                        'joined_rank': r['joined_rank']})
        if result_rows:
            out_df = pd.DataFrame(result_rows)
            if os.path.exists(out_path):
                out_df = pd.concat([pd.read_csv(out_path), out_df], ignore_index=True)
            out_df.to_csv(out_path, index=False)
            result_rows = []
        print('done %s (lb=%d step=%.2f bounds=%.2f-%.2f)' % (
            name, lookback, step, wmin, wmax), flush=True)

    df = pd.read_csv(out_path)
    print(df.to_string(index=False))
    print('\nwrote', out_path)


if __name__ == '__main__':
    main()
