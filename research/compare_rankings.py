"""Compare the three config-pair ranking methods across all 496 pairs.

Methods (all rank the same objects: the pct=0.25 trade-event two-leg books):
  separate  : score = min(mean recent Sharpe, hist Sharpe)          [pair_sweep_consolidated]
  rank-avg  : mean of each pair's rec-rank and hist-rank (dense)    [add_rank_avg]
  joined    : Sharpe of the hist ++ recent concatenated series       [write_joint_eval]

Spearman is computed as the Pearson correlation of the rank vectors (mathematically
identical, avoids a scipy dependency). Mechanism A joined is read from the existing
joined_pairs.csv; B is computed on the fly (same join logic, mech B).

Outputs (fixed_diagnosis/compare/):
  _RANK_COMPARISON.md   per-mechanism spearman matrix, top-20 per method, overlaps
  rank_comparison_<M>.csv   all pairs: recent, hist, joined, all three ranks

Usage: python research/compare_rankings.py
"""
import os
import sys
import itertools
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from research.pair_sweep_consolidated import (  # noqa: E402
    STRATEGIES, CFGS, pair_results, dense_ranks, get_leg, weight_path_momentum_causal,
    simulate, metrics,
)
from research.write_joint_eval import joined_metrics  # noqa: E402

BASE = 'fixed_diagnosis'
OUT = os.path.join(BASE, 'compare')
PCT = 0.25
JOINT_CSV = os.path.join(BASE, 'joint', 'joined_pairs.csv')


def _key(a, b):
    return tuple(sorted([a, b]))


def load_joined_a():
    df = pd.read_csv(JOINT_CSV)
    return {_key(str(r['A']), str(r['B'])): float(r['joined_sh']) for _, r in df.iterrows()}


def pair_series_mech(sa, ca, sb, cb, window, mech, start_idx=0):
    a = get_leg(sa, ca, window, start_idx)
    b = get_leg(sb, cb, window, start_idx)
    wp = weight_path_momentum_causal(a['ret'], b['ret'])
    rows, _, _, _ = simulate({'A': a, 'B': b}, wp, mech, capital=1e6, pct=PCT)
    return pd.Series([r['daily_return'] for r in rows], index=[r['date'] for r in rows])


def joined_sh_for_pair(sa, ca, sb, cb, mech):
    hist_s = pair_series_mech(sa, ca, sb, cb, 'historical', mech)
    rec_s = [pair_series_mech(sa, ca, sb, cb, 'recent', mech, i) for i in range(5)]
    return joined_metrics([(hist_s, r) for r in rec_s])[0]


def compute_rows(mech, joined_a):
    legs = [(s, c) for s in STRATEGIES for c in CFGS]
    rows = []
    for (sa, ca), (sb, cb) in itertools.combinations(legs, 2):
        rm, rng, hs, rret, hret = pair_results(sa, ca, sb, cb, mech, PCT)
        if rm != rm or hs != hs:
            continue
        na, nb = '%s/%s' % (sa, ca), '%s/%s' % (sb, cb)
        if mech == 'A':
            jsh = joined_a.get(_key(na, nb), float('nan'))
        else:
            jsh = joined_sh_for_pair(sa, ca, sb, cb, mech)
        if jsh != jsh:
            continue
        rows.append({'A': na, 'B': nb, 'recent': rm, 'hist': hs,
                     'joined_sh': jsh, 'score': min(rm, hs), 'r_ret': rret, 'h_ret': hret})
    return rows


def add_ranks(rows):
    r_rank = dense_ranks([r['recent'] for r in rows])
    h_rank = dense_ranks([r['hist'] for r in rows])
    score = [r['score'] for r in rows]
    joined = [r['joined_sh'] for r in rows]
    for i, r in enumerate(rows):
        r['r_rank'] = r_rank[i]
        r['h_rank'] = h_rank[i]
        r['rank_avg'] = (r_rank[i] + h_rank[i]) / 2.0
    rank_avg = [r['rank_avg'] for r in rows]
    for i, r in enumerate(rows):
        r['score_rank'] = dense_ranks(score)[i]
        r['rank_avg_rank'] = dense_ranks(rank_avg, reverse=False)[i]
        r['joined_rank'] = dense_ranks(joined)[i]


def spearman(md_lines, rows, mech):
    df = pd.DataFrame({'score_rank': [r['score_rank'] for r in rows],
                       'rank_avg_rank': [r['rank_avg_rank'] for r in rows],
                       'joined_rank': [r['joined_rank'] for r in rows]})
    corr = df.corr(method='pearson')
    md_lines.append('### Mechanism %s — Spearman correlation of pair ranks (%d pairs)\n'
                    % (mech, len(rows)))
    md_lines.append('| | separate (min) | rank-avg | joined |')
    md_lines.append('|---|---:|---:|---:|')
    for a in ['score_rank', 'rank_avg_rank', 'joined_rank']:
        md_lines.append('| %s | %.3f | %.3f | %.3f |'
                        % (a, corr['score_rank'][a], corr['rank_avg_rank'][a],
                           corr['joined_rank'][a]))
    md_lines.append('')
    return corr


def fmt_pair(r):
    return '`%s` + `%s`' % (r['A'], r['B'])


def top20_sections(md_lines, rows, mech):
    md_lines.append('### Mechanism %s — top 20 by each method\n' % mech)
    md_lines.append('| # | separate (min) | min | rank-avg | avg | joined | J Sh |')
    md_lines.append('|---|---:|---:|---:|---:|---:|---:|')
    by_score = sorted(rows, key=lambda r: r['score'], reverse=True)[:20]
    by_avg = sorted(rows, key=lambda r: r['rank_avg'])[:20]
    by_j = sorted(rows, key=lambda r: r['joined_sh'], reverse=True)[:20]
    for i in range(20):
        md_lines.append('| %d | %s | %.2f | %s | %.1f | %s | %.2f |'
                        % (i + 1, fmt_pair(by_score[i]), by_score[i]['score'],
                           fmt_pair(by_avg[i]), by_avg[i]['rank_avg'],
                           fmt_pair(by_j[i]), by_j[i]['joined_sh']))
    md_lines.append('')

    for title, key, rev in [('Separate (min score)', 'score', True),
                            ('Rank-average', 'rank_avg', False),
                            ('Joined Sharpe', 'joined_sh', True)]:
        md_lines.append('#### %s\n' % title)
        md_lines.append('| # | Pair | Recent | Hist | Joined Sh |')
        md_lines.append('|---|---:|---:|---:|---:|')
        for i, r in enumerate(sorted(rows, key=lambda x: x[key], reverse=rev)[:20], 1):
            md_lines.append('| %d | %s | %.2f | %.2f | %.2f |'
                            % (i, fmt_pair(r), r['recent'], r['hist'], r['joined_sh']))
        md_lines.append('')


def overlap_section(md_lines, rows, mech):
    sk = {_key(r['A'], r['B']) for r in sorted(rows, key=lambda x: x['score'], reverse=True)[:20]}
    ak = {_key(r['A'], r['B']) for r in sorted(rows, key=lambda x: x['rank_avg'])[:20]}
    jk = {_key(r['A'], r['B']) for r in sorted(rows, key=lambda x: x['joined_sh'], reverse=True)[:20]}
    inter = sk & ak & jk
    md_lines.append('### Mechanism %s — top-20 overlap\n' % mech)
    md_lines.append('| Pair sets | Count |')
    md_lines.append('|---|---:|')
    md_lines.append('| separate ∩ rank-avg | %d |' % len(sk & ak))
    md_lines.append('| separate ∩ joined | %d |' % len(sk & jk))
    md_lines.append('| rank-avg ∩ joined | %d |' % len(ak & jk))
    md_lines.append('| all three | %d |' % len(inter))
    md_lines.append('')
    if inter:
        md_lines.append('Pairs in all three top-20s:')
        for k in sorted(inter):
            md_lines.append('  - %s + %s' % k)
        md_lines.append('')
    else:
        md_lines.append('(no pair appears in all three top-20s)\n')
    md_lines.append('')


def main():
    os.makedirs(OUT, exist_ok=True)
    joined_a = load_joined_a()
    lines = ['# Config-pair ranking comparison (all pairs)\n']
    lines.append('Methods: separate (score = min(mean recent Sharpe, hist Sharpe)), '
                 'rank-average (mean dense rank across the two windows, lower = better), '
                 'joined (single Sharpe of hist ++ recent concatenated series). pct=0.25. '
                 'Mechanism A joined read from joined_pairs.csv; B joined computed here.\n')

    for mech in ['A', 'B']:
        print('=== Mechanism %s ===' % mech)
        rows = compute_rows(mech, joined_a)
        add_ranks(rows)
        corr = spearman(lines, rows, mech)
        top20_sections(lines, rows, mech)
        overlap_section(lines, rows, mech)
        pd.DataFrame(rows).to_csv(os.path.join(OUT, 'rank_comparison_%s.csv' % mech), index=False)
        print('  spearman score-vs-rankavg: %.3f  score-vs-joined: %.3f  rankavg-vs-joined: %.3f'
              % (corr['score_rank']['rank_avg_rank'], corr['score_rank']['joined_rank'],
                 corr['rank_avg_rank']['joined_rank']))
        print('  wrote rank_comparison_%s.csv' % mech)

    out_path = os.path.join(OUT, '_RANK_COMPARISON.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', out_path)


if __name__ == '__main__':
    main()