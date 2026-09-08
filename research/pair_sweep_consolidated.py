"""Systematic pair sweep with the consolidated shared-account book (mechs A & B).

Mirrors research/pair_sweep.py's leg universe (4 strategies x 8 configs, 496
pairs) but combines via the trade-event replay simulator instead of return
arithmetic. Requires trade_marks.csv for every leg (re-run at pct=0.25 into
fixed_diagnosis/_sweep_pct25/<section>/<start>_<cfg>/).

  recent : mean Sharpe over the 5 aligned start-pairs
  hist   : Sharpe on the single aligned historical window
  score  : min(recent, hist)

Usage: python research/pair_sweep_consolidated.py [--mechanism A|B|both]
       [--pct 0.25] [--top 20] [--report]
"""
import os
import math
import json
import argparse
import itertools
import warnings
import pandas as pd

warnings.filterwarnings('ignore', category=RuntimeWarning)

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research.run_combined_backtest import (  # noqa: E402
    build_leg_data, weight_path_momentum_causal, simulate, metrics,
)

BASE = 'fixed_diagnosis'
SWEEP_ROOT = '_sweep_pct25'
OUT = os.path.join(BASE, '_combined', 'consolidated_sweep')
SEPARATE = os.path.join(BASE, 'separate')

CFGS = ['same_sector_slide3m_noscreen', 'same_sector_slide3m_bd7',
        'same_sector_slide1m_noscreen', 'same_sector_slide1m_bd7',
        'cross_sector_slide3m_noscreen', 'cross_sector_slide3m_bd7',
        'cross_sector_slide1m_noscreen', 'cross_sector_slide1m_bd7']

STARTS_2M = ['2023-11-01', '2023-12-01', '2024-01-01', '2024-02-01', '2024-03-01']
STARTS_12M = ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01']

STRATEGIES = {
    'core-2m':   ('06', '08a', STARTS_2M),
    'sp500-2m':  ('07', '09a', STARTS_2M),
    'core-12m':  ('10a', '08b', STARTS_12M),
    'sp500-12m': ('10b', '09b', STARTS_12M),
}

_leg_cache = {}


def leg_dir(strat, cfg, window, start_idx=0):
    rsec, hsec, starts = STRATEGIES[strat]
    if window == 'recent':
        return f"{SWEEP_ROOT}/{rsec}/{starts[start_idx]}_{cfg}"
    hist_start = '2014-11-01' if starts is STARTS_2M else '2014-01-01'
    return f"{SWEEP_ROOT}/{hsec}/{hist_start}_{cfg}"


def get_leg(strat, cfg, window, start_idx=0):
    key = (strat, cfg, window, start_idx)
    if key not in _leg_cache:
        _leg_cache[key] = build_leg_data(leg_dir(strat, cfg, window, start_idx))
    return _leg_cache[key]


def one_window(strat_a, cfg_a, strat_b, cfg_b, window, mech, pct, start_idx=0):
    a = get_leg(strat_a, cfg_a, window, start_idx)
    b = get_leg(strat_b, cfg_b, window, start_idx)
    wp = weight_path_momentum_causal(a['ret'], b['ret'])
    rows, _, _, _ = simulate({'A': a, 'B': b}, wp, mech, capital=1e6, pct=pct)
    r = pd.Series([row['daily_return'] for row in rows])
    m = metrics(r)
    return m['sharpe'], m['ann_ret']


def pair_results(sa, ca, sb, cb, mech, pct):
    res = [one_window(sa, ca, sb, cb, 'recent', mech, pct, i) for i in range(5)]
    recent_shs = [x[0] for x in res]
    recent_rets = [x[1] for x in res]
    hist_sh, hist_ret = one_window(sa, ca, sb, cb, 'historical', mech, pct)
    return (sum(recent_shs) / len(recent_shs), (min(recent_shs), max(recent_shs)),
            hist_sh, sum(recent_rets) / len(recent_rets), hist_ret)


def winner_series(sa, ca, sb, cb, window, mech, pct):
    a = get_leg(sa, ca, window, 0)
    b = get_leg(sb, cb, window, 0)
    wp = weight_path_momentum_causal(a['ret'], b['ret'])
    rows, _, _, _ = simulate({'A': a, 'B': b}, wp, mech, capital=1e6, pct=pct)
    return pd.DataFrame(rows)


def write_winner_csv(sa, ca, sb, cb, window, mech, pct, label):
    d = os.path.join(OUT, mech, label, window)
    os.makedirs(d, exist_ok=True)
    df = winner_series(sa, ca, sb, cb, window, mech, pct)
    df.to_csv(os.path.join(d, 'daily_returns.csv'), index=False)
    meta = os.path.join(OUT, mech, label, 'pair.json')
    with open(meta, 'w', encoding='utf-8') as f:
        json.dump({'leg_a': '%s/%s' % (sa, ca), 'leg_b': '%s/%s' % (sb, cb),
                   'mechanism': mech, 'pct': pct}, f, indent=2)


def dense_ranks(values, reverse=True):
    order = sorted(range(len(values)), key=values.__getitem__, reverse=reverse)
    ranks = [0] * len(values)
    rank = 0
    prev = None
    for i, idx in enumerate(order):
        v = values[idx]
        if prev is None or abs(prev - v) > 1e-12:
            rank = i + 1
            prev = v
        ranks[idx] = rank
    return ranks


def add_rank_avg(results):
    """Rank each pair by recent Sharpe and by hist Sharpe, then average the two ranks."""
    recent = [r['recent'] for r in results]
    hist = [r['hist'] for r in results]
    r_rank = dense_ranks(recent)
    h_rank = dense_ranks(hist)
    for i, r in enumerate(results):
        r['r_rank'] = r_rank[i]
        r['h_rank'] = h_rank[i]
        r['rank_avg'] = (r_rank[i] + h_rank[i]) / 2.0
    results.sort(key=lambda x: x['rank_avg'])
    return results


def leg_rec_sh_map():
    """Per-leg mean recent Sharpe over the 5 aligned start-pairs (from metrics.json)."""
    import statistics
    root = os.path.join(BASE, SWEEP_ROOT)
    out = {}
    for strat, (rsec, _hsec, starts) in STRATEGIES.items():
        for cfg in CFGS:
            shs = []
            for st in starts:
                with open(os.path.join(root, rsec, f'{st}_{cfg}', 'metrics.json'),
                          encoding='utf-8') as f:
                    shs.append(json.load(f)['annualized_sharpe'])
            out['%s/%s' % (strat, cfg)] = statistics.mean(shs)
    return out


def reorder_legs(rows, rec_sh_map):
    """Swap A/B in each row so leg A is always the recent-strong leg."""
    for r in rows:
        if rec_sh_map[r['B']] > rec_sh_map[r['A']]:
            r['A'], r['B'] = r['B'], r['A']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mechanism', default='both', choices=['A', 'B', 'both'])
    ap.add_argument('--pct', type=float, default=0.25)
    ap.add_argument('--top', type=int, default=20)
    ap.add_argument('--report', action='store_true')
    args = ap.parse_args()

    legs = [(s, c) for s in STRATEGIES for c in CFGS]
    mechanisms = ['A', 'B'] if args.mechanism == 'both' else [args.mechanism]

    report = []
    report.append('# Combined two-leg book: consolidated sweep (trade-event replay)\n')
    report.append('Mechanisms A (monthly re-base) and B (entry-flow), pct=%.3f. '
                  'Recent = mean Sharpe over the 5 aligned start-pairs; hist = single aligned '
                  'window; score = min(recent, hist).\n' % args.pct)

    rec_sh_map = leg_rec_sh_map()

    for mech in mechanisms:
        results = []
        for (sa, ca), (sb, cb) in itertools.combinations(legs, 2):
            rm, rng, hs, rret, hret = pair_results(sa, ca, sb, cb, mech, args.pct)
            if math.isnan(hs):
                continue
            results.append({
                'A': '%s/%s' % (sa, ca), 'B': '%s/%s' % (sb, cb),
                'recent': rm, 'r_lo': rng[0], 'r_hi': rng[1],
                'hist': hs, 'r_ret': rret, 'h_ret': hret, 'score': min(rm, hs),
            })
        results.sort(key=lambda x: x['score'], reverse=True)
        print(f"=== Mechanism {mech} | {len(results)} pairs | top {args.top} ===")
        print('%-62s | %6s | %9s | %6s | %6s | %7s | %7s' % ('PAIR', 'recent', 'range', 'hist', 'score', 'R%', 'H%'))
        print('-' * 122)
        for r in results[:args.top]:
            print('%-62s | %6.2f | %5.2f-%5.2f | %6.2f | %6.2f | %6.1f%% | %6.1f%%'
                  % (r['A'] + '  +  ' + r['B'], r['recent'], r['r_lo'], r['r_hi'],
                     r['hist'], r['score'], r['r_ret'] * 100, r['h_ret'] * 100))
        print()

        report.append(f'## Mechanism {mech} — top 20 pairs\n')
        report.append('| Pair | Recent | Range | Hist | Score | R% | H% |')
        report.append('|---|---:|---:|---:|---:|---:|---:|')
        for r in results[:20]:
            report.append('| %s + %s | %.2f | %.2f–%.2f | %.2f | %.2f | %+.1f%% | %+.1f%% |'
                          % (r['A'], r['B'], r['recent'], r['r_lo'], r['r_hi'], r['hist'],
                             r['score'], r['r_ret'] * 100, r['h_ret'] * 100))
        report.append('')

        rank_rows = add_rank_avg([dict(r) for r in results])
        reorder_legs(rank_rows, rec_sh_map)
        print(f"=== Mechanism {mech} | top {args.top} by rank-average (rec-rank + hist-rank) ===")
        for r in rank_rows[:args.top]:
            print('%-62s | rec#%3d | hist#%3d | avg %.1f | rec %.2f | hist %.2f'
                  % (r['A'] + '  +  ' + r['B'], r['r_rank'], r['h_rank'], r['rank_avg'],
                     r['recent'], r['hist']))
        print()

        report.append(f'## Mechanism {mech} — top 20 pairs by rank-average\n')
        report.append('Ranked by the mean of each pair\\\'s recent-rank and hist-rank (lower = '
                      'better). For each pair, rank against all 496 pairs by recent Sharpe and by '
                      'hist Sharpe, then average the two ranks. **Leg A = recent-strong.**\n')
        report.append('| Pair | Rec Rank | Hist Rank | RankAvg | Recent | Hist | Score |')
        report.append('|---|---:|---:|---:|---:|---:|---:|')
        for r in rank_rows[:20]:
            report.append('| %s + %s | %d | %d | %.1f | %.2f | %.2f | %.2f |'
                          % (r['A'], r['B'], r['r_rank'], r['h_rank'], r['rank_avg'],
                             r['recent'], r['hist'], r['score']))
        report.append('')

        if args.report:
            winners = results[:5]
            report.append(f'## Mechanism {mech} — winners (daily_returns.csv written)\n')
            for i, r in enumerate(winners):
                label = f'pair_{i + 1:02d}'
                a_strat, a_cfg = r['A'].split('/', 1)
                b_strat, b_cfg = r['B'].split('/', 1)
                write_winner_csv(a_strat, a_cfg, b_strat, b_cfg, 'recent', mech, args.pct, label)
                write_winner_csv(a_strat, a_cfg, b_strat, b_cfg, 'historical', mech, args.pct, label)
                report.append('- **%d.** `%s` + `%s` → recent %.2f (%+.1f%%/yr), hist %.2f (%+.1f%%/yr) '
                              '(label `%s`)'
                              % (i + 1, r['A'], r['B'], r['recent'], r['r_ret'] * 100,
                                 r['hist'], r['h_ret'] * 100, label))
            report.append('')

    out_path = os.path.join(SEPARATE, '_COMBINED_BOOK_CONSOLIDATED.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report) + '\n')
    print('wrote', out_path)


if __name__ == '__main__':
    main()
