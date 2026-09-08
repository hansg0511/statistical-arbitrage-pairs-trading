"""Write fixed_diagnosis/separate/_PAIRS_WITH_HIST1.md: every config pair that
includes a historical-window #1 single leg (tie: sp500-2m/cross_sector_slide3m_noscreen
and sp500-2m/cross_sector_slide3m_bd7, both hist Sh 0.57), mechanism A.

The target is the historical-strong leg, so it is **leg B** in every row (the
partner, with the higher recent Sharpe, is leg A). Pairs are replayed with the
trade-event simulator (research.run_combined_backtest.simulate, mech A, pct=0.25).

Usage: python research/write_pairs_with_hist1.py
"""
import os

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research.pair_sweep_consolidated import (  # noqa: E402
    STRATEGIES, CFGS, pair_results,
)
from research.write_top7_period import leg_metrics, dense_ranks  # noqa: E402

BASE = 'fixed_diagnosis'
SEPARATE = os.path.join(BASE, 'separate')
OUT = os.path.join(SEPARATE, '_PAIRS_WITH_HIST1.md')
PCT = 0.25


def all_legs():
    return [(s, c) for s in STRATEGIES for c in CFGS]


def write_section(lines, target, legs, rec_rank, hist_rank):
    ts, tc = target
    by_name = {l['name']: l for l in legs}
    t_leg = by_name['%s/%s' % (ts, tc)]

    partners = []
    for (s, c) in all_legs():
        if (s, c) == target:
            continue
        rm, rng, hs, rret, hret = pair_results(ts, tc, s, c, 'A', PCT)
        if rm != rm or hs != hs:
            continue
        partners.append({
            'partner': '%s/%s' % (s, c),
            'rec': rm, 'r_lo': rng[0], 'r_hi': rng[1], 'hist': hs,
            'score': min(rm, hs), 'r_ret': rret, 'h_ret': hret,
        })

    partners.sort(key=lambda x: x['score'], reverse=True)

    lines.append('## Target leg: `%s/%s` (leg B, historical-strong)\n' % (ts, tc))
    lines.append('Single leg: hist Sh %.2f, hist Ret %+.2f%%/yr (hist rank #%d); recent Sh %.2f, '
                 'recent Ret %+.2f%%/yr (recent rank #%d).\n'
                 % (t_leg['hist_sh'], t_leg['hist_ret'] * 100, hist_rank[t_leg['name']],
                    t_leg['rec_sh'], t_leg['rec_ret'] * 100, rec_rank[t_leg['name']]))
    lines.append('Rows sorted by score = min(recent, hist). The partner (leg A) is the '
                 'recent-strong leg; the target is the historical-strong leg.\n')

    lines.append('| # | Partner (leg A) | Partner Rec# | Partner Hist# | Pair rec | Range | '
                 'Pair hist | Score | R% | H% |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    for i, p in enumerate(partners, 1):
        p_leg = by_name[p['partner']]
        lines.append('| %d | `%s` | %d | %d | %.2f | %.2f–%.2f | %.2f | %.2f | %+.1f%% | %+.1f%% |'
                     % (i, p['partner'], rec_rank[p_leg['name']], hist_rank[p_leg['name']],
                        p['rec'], p['r_lo'], p['r_hi'], p['hist'], p['score'],
                        p['r_ret'] * 100, p['h_ret'] * 100))
    lines.append('')


def main():
    legs = leg_metrics()
    rec_rank = dense_ranks(legs, 'rec_sh')
    hist_rank = dense_ranks(legs, 'hist_sh')

    targets = [(s, c) for (s, c) in all_legs()
               if hist_rank['%s/%s' % (s, c)] == 1]

    lines = []
    lines.append('# Pairs with the historical-window #1 legs\n')
    lines.append('All pairs use the trade-event replay (mechanism A, pct=0.25, shared-account '
                 'momentum allocation). Recent = mean over the 5 aligned start-pairs; hist = '
                 'single aligned window. Score = min(recent, hist). Partner leg ranks are across '
                 'the full 32-leg set. R% = pair book recent annualized return; H% = pair book '
                 'historical annualized return.\n')

    for target in targets:
        write_section(lines, target, legs, rec_rank, hist_rank)

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', OUT)


if __name__ == '__main__':
    main()