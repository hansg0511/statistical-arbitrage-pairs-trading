"""Write fixed_diagnosis/separate/_PAIRS_WITH_RECENT1.md: every config pair that
includes the recent-window #1 single leg
(sp500-12m/cross_sector_slide1m_noscreen), mechanism A.

Because that leg is the strongest in the recent window, it is always the
'recent-strong' leg (leg A) in every pair. Pairs are replayed with the
trade-event simulator (research.run_combined_backtest.simulate, mech A, pct=0.25).

Usage: python research/write_pairs_with_recent1.py
"""
import os
import statistics

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research.pair_sweep_consolidated import (  # noqa: E402
    STRATEGIES, CFGS, pair_results,
)
from research.write_top7_period import leg_metrics, dense_ranks  # noqa: E402

BASE = 'fixed_diagnosis'
SEPARATE = os.path.join(BASE, 'separate')
TARGET = ('sp500-12m', 'cross_sector_slide1m_noscreen')
OUT = os.path.join(SEPARATE, '_PAIRS_WITH_RECENT1.md')

PCT = 0.25


def all_legs():
    return [(s, c) for s in STRATEGIES for c in CFGS]


def main():
    ts, tc = TARGET
    legs = leg_metrics()
    rec_rank = dense_ranks(legs, 'rec_sh')
    hist_rank = dense_ranks(legs, 'hist_sh')
    by_name = {l['name']: l for l in legs}

    partners = []
    for (s, c) in all_legs():
        if (s, c) == TARGET:
            continue
        rm, rng, hs, rret, hret = pair_results(ts, tc, s, c, 'A', PCT)
        if rm != rm or hs != hs:  # NaN guard
            continue
        partners.append({
            'partner': '%s/%s' % (s, c),
            'rec': rm, 'r_lo': rng[0], 'r_hi': rng[1], 'hist': hs,
            'score': min(rm, hs), 'r_ret': rret, 'h_ret': hret,
        })

    partners.sort(key=lambda x: x['score'], reverse=True)

    t_leg = by_name['%s/%s' % TARGET]
    lines = []
    lines.append('# Pairs with the recent-window #1 leg\n')
    lines.append('Target leg: `%s/%s` (recent Sh %.2f, recent Ret %+.2f%%/yr; '
                 'hist Sh %.2f, hist Ret %+.2f%%/yr; ranks: recent #%d, hist #%d).\n'
                 % (TARGET[0], TARGET[1], t_leg['rec_sh'], t_leg['rec_ret'] * 100,
                    t_leg['hist_sh'], t_leg['hist_ret'] * 100,
                    rec_rank[t_leg['name']], hist_rank[t_leg['name']]))
    lines.append('All pairs use the trade-event replay (mechanism A, pct=0.25, shared-account '
                 'momentum allocation). Because the target is the strongest recent leg in the '
                 'universe, it is **leg A (recent-strong)** in every row; the partner is '
                 '**leg B (historical-strong)**. Recent = mean over the 5 aligned start-pairs; '
                 'hist = single aligned window. Score = min(recent, hist).\n')
    lines.append('Partner leg ranks are across the full 32-leg set.\n')

    lines.append('| # | Partner (leg B) | Partner Rec# | Partner Hist# | Pair rec | Range | '
                 'Pair hist | Score | R% | H% |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    for i, p in enumerate(partners, 1):
        p_leg = by_name[p['partner']]
        lines.append('| %d | `%s` | %d | %d | %.2f | %.2f–%.2f | %.2f | %.2f | %+.1f%% | %+.1f%% |'
                     % (i, p['partner'], rec_rank[p_leg['name']], hist_rank[p_leg['name']],
                        p['rec'], p['r_lo'], p['r_hi'], p['hist'], p['score'],
                        p['r_ret'] * 100, p['h_ret'] * 100))
    lines.append('')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', OUT)


if __name__ == '__main__':
    main()