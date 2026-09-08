"""Rank-average-only survivor selection + momentum/FF analysis.

Variant of momentum_ff_pairs.py with fewer constraints: the separate (min-score)
and joined-Scarpe rankings are dropped. Survivors are the pairs in the TOP-20 by
rank-average (mean of the recent-window dense rank and the historical-window
dense rank; lower = better) for mechanisms A AND B — i.e. the intersection of
the two top-20s.

Ranking inputs are read from the existing rank_comparison_<M>.csv files written
by research/compare_rankings.py (same post-fix, deterministic run data). The
momentum-param sensitivity (Task 1) and Fama-French regression (Task 2)
machinery is reused from research/momentum_ff_pairs.py.

Outputs (fixed_diagnosis/rankavg/):
  _RANKAVG_SELECTION.md    top-20 per mechanism + intersection (survivors)
  _MOMENTUM_FF_RANKAVG.md  momentum sensitivity + Fama-French tables
  momentum_sensitivity.csv
  ff_regressions.csv

Usage: python research/momentum_ff_rankavg.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from research.momentum_ff_pairs import (  # noqa: E402
    build_sensitivity_csv, build_ff_rows, write_md,
)

BASE = 'fixed_diagnosis'
COMPARE = os.path.join(BASE, 'compare')
OUT = os.path.join(BASE, 'rankavg')
TOP = 20


def _key(a, b):
    return tuple(sorted([a, b]))


def _parse_leg(label):
    strat, cfg = label.split('/', 1)
    return strat, cfg


def _load_top20(mech):
    df = pd.read_csv(os.path.join(COMPARE, 'rank_comparison_%s.csv' % mech))
    top = df.nsmallest(TOP, 'rank_avg')
    ranked = {_key(r['A'], r['B']): (r['A'], r['B']) for _, r in top.iterrows()}
    return df, top, ranked


def pairs_from_labels(labels):
    return [(sa, ca, sb, cb) for sa, ca, sb, cb in
            (_parse_leg(a) + _parse_leg(b) for a, b in labels)]


def selection_md(rows_a, rows_b, inter, only_a, only_b, total_pairs):
    lines = ['# Rank-average-only survivor selection\n']
    lines.append('Method: drop the separate (min-score) and joined-Sharpe rankings. Rank all '
                 '%d pairs by rank-average (mean of recent and historical dense ranks, lower = '
                 'better). Survivors = top-%d in mechanism A AND top-%d in mechanism B.\n'
                 % (total_pairs, TOP, TOP))

    for mech, rows in [('A', rows_a), ('B', rows_b)]:
        lines.append('## Mechanism %s — top %d by rank-average\n' % (mech, TOP))
        lines.append('| # | Pair | rank_avg | recent | hist | min | joined Sh |')
        lines.append('|---|---:|---:|---:|---:|---:|---:|')
        for i, (_, r) in enumerate(rows.iterrows(), 1):
            lines.append('| %d | `%s` + `%s` | %.1f | %.2f | %.2f | %.2f | %.2f |'
                         % (i, r['A'], r['B'], r['rank_avg'], r['recent'], r['hist'],
                            r['score'], r['joined_sh']))
        lines.append('')

    lines.append('## Intersection (survivors, %d)\n' % len(inter))
    for k in sorted(inter):
        lines.append('  - `%s` + `%s`' % k)
    lines.append('')

    lines.append('## Mechanism A only (%d)\n' % len(only_a))
    for k in sorted(only_a):
        lines.append('  - `%s` + `%s`' % k)
    lines.append('')

    lines.append('## Mechanism B only (%d)\n' % len(only_b))
    for k in sorted(only_b):
        lines.append('  - `%s` + `%s`' % k)
    lines.append('')
    return lines


def main():
    os.makedirs(OUT, exist_ok=True)

    df_a, top_a, set_a = _load_top20('A')
    df_b, top_b, set_b = _load_top20('B')

    inter = set_a.keys() & set_b.keys()
    only_a = set_a.keys() - set_b.keys()
    only_b = set_b.keys() - set_a.keys()

    labels = [(set_a[k][0], set_a[k][1]) for k in inter]
    pairs = pairs_from_labels(labels)
    print('%d pairs in top-%d rank-average for both mechanisms:' % (len(pairs), TOP))
    for sa, ca, sb, cb in pairs:
        print('  %s/%s + %s/%s' % (sa, ca, sb, cb))

    lines = selection_md(top_a, top_b, inter, only_a, only_b, len(df_a))
    sel_path = os.path.join(OUT, '_RANKAVG_SELECTION.md')
    with open(sel_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', sel_path)

    print('Task 1: momentum-param sensitivity sweep...')
    sens = build_sensitivity_csv(pairs)
    print('Task 2: Fama-French regressions...')
    ff = build_ff_rows(pairs)

    desc = ('Pairs are the top-%d by rank-average (mean dense rank across the recent and '
            'historical windows) in BOTH mechanisms A and B. pct=0.25, capital $1M.' % TOP)
    md = write_md(sens, ff, desc=desc)
    md_path = os.path.join(OUT, '_MOMENTUM_FF_RANKAVG.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md) + '\n')
    sens.to_csv(os.path.join(OUT, 'momentum_sensitivity.csv'), index=False)
    ff.to_csv(os.path.join(OUT, 'ff_regressions.csv'), index=False)
    print('wrote', md_path)
    print('wrote', os.path.join(OUT, 'momentum_sensitivity.csv'))
    print('wrote', os.path.join(OUT, 'ff_regressions.csv'))


if __name__ == '__main__':
    main()
