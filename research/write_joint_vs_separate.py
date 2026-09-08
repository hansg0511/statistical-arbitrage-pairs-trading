"""Compare the joint-period evaluation vs the separate-window evaluation.

Separate (existing): each window scored alone; pair score = min(recent, hist);
legs ranked by recent or historical Sharpe.
Joint (new): historical ++ recent concatenated into one series, single Sharpe
and return (mean over the 5 recent start-pairs).

This script recomputes the separate scores for ALL 496 pairs (via
research.pair_sweep_consolidated.pair_results), merges with the cached joint
results in fixed_diagnosis/joint/joined_pairs.csv / joined_legs.csv, and writes:
  fixed_diagnosis/joint/_JOINT_VS_SEPARATE.md  comparison report
  fixed_diagnosis/joint/compare_pairs.csv       all 496 pairs, both metrics

Usage: python research/write_joint_vs_separate.py
"""
import os
import itertools
import statistics

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from research.pair_sweep_consolidated import (  # noqa: E402
    STRATEGIES, CFGS, pair_results,
)
from research.write_top7_period import leg_metrics, dense_ranks  # noqa: E402

BASE = 'fixed_diagnosis'
JOINT = os.path.join(BASE, 'joint')
SEPARATE = os.path.join(BASE, 'separate')
PCT = 0.25


def pair_key(a, b):
    return tuple(sorted([a, b]))


def spearman(xs, ys):
    def ranks(vals):
        idx = sorted(range(len(vals)), key=lambda i: vals[i])
        out = [0.0] * len(vals)
        i = 0
        while i < len(idx):
            j = i
            while j + 1 < len(idx) and vals[idx[j + 1]] == vals[idx[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                out[idx[k]] = avg
            i = j + 1
        return out

    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    den = (sum((rx[i] - mx) ** 2 for i in range(n)) *
           sum((ry[i] - my) ** 2 for i in range(n))) ** 0.5
    return num / den if den else float('nan')


def separate_pair_scores():
    all_legs = [(s, c) for s in STRATEGIES for c in CFGS]
    scores = {}
    for (sa, ca), (sb, cb) in itertools.combinations(all_legs, 2):
        rm, _rng, hs, _rret, _hret = pair_results(sa, ca, sb, cb, 'A', PCT)
        if rm != rm or hs != hs:
            continue
        a, b = '%s/%s' % (sa, ca), '%s/%s' % (sb, cb)
        scores[pair_key(a, b)] = {'rec': rm, 'hist': hs, 'score': min(rm, hs)}
    return scores


def main():
    legs_df = pd.read_csv(os.path.join(JOINT, 'joined_legs.csv'))
    pairs_df = pd.read_csv(os.path.join(JOINT, 'joined_pairs.csv'))

    print('computing separate pair scores (496 pairs)...')
    sep_scores = separate_pair_scores()

    # --- merge pair data ---
    for _, r in pairs_df.iterrows():
        k = pair_key(r['A'], r['B'])
        if k in sep_scores:
            r['rec'], r['hist'], r['score'] = (sep_scores[k]['rec'],
                                               sep_scores[k]['hist'],
                                               sep_scores[k]['score'])
        else:
            r['rec'], r['hist'], r['score'] = float('nan'), float('nan'), float('nan')
    pairs_df['rec'] = pairs_df.apply(lambda r: sep_scores.get(pair_key(r['A'], r['B']),
                                                              {}).get('rec'), axis=1)
    pairs_df['hist'] = pairs_df.apply(lambda r: sep_scores.get(pair_key(r['A'], r['B']),
                                                               {}).get('hist'), axis=1)
    pairs_df['score'] = pairs_df.apply(lambda r: sep_scores.get(pair_key(r['A'], r['B']),
                                                                {}).get('score'), axis=1)
    pairs_df['joined_rank'] = range(1, len(pairs_df) + 1)
    pairs_df['score_rank'] = pairs_df['score'].rank(ascending=False, method='min').astype(int)

    # --- leg data ---
    legs_df['score'] = legs_df[['rec_sh', 'hist_sh']].min(axis=1)
    legs_df['joined_rank'] = legs_df['joined_sh'].rank(ascending=False, method='min').astype(int)
    legs_df['score_rank'] = legs_df['score'].rank(ascending=False, method='min').astype(int)

    pairs_df.to_csv(os.path.join(JOINT, 'compare_pairs.csv'), index=False)

    # --- correlation ---
    pr = pairs_df.dropna(subset=['score'])
    rho_score_joined = spearman(list(pr['score']), list(pr['joined_sh']))
    rho_rec_joined = spearman(list(pr['rec']), list(pr['joined_sh']))
    rho_hist_joined = spearman(list(pr['hist']), list(pr['joined_sh']))

    lines = []
    lines.append('# Joint vs separate evaluation\n')
    lines.append('Separate: per-window metrics, pair score = min(recent, hist); legs ranked by '
                 'per-window Sharpe. Joint: historical (2015–2019) ++ recent (2024–2025) daily '
                 'returns as one series, one Sharpe/return (mean over the 5 recent start-pairs).\n')
    lines.append('Spearman correlation across all %d pairs:\n' % len(pr))
    lines.append('| vs joined Sharpe | rho |')
    lines.append('|---|---:|')
    lines.append('| separate score = min(rec, hist) | %.3f |' % rho_score_joined)
    lines.append('| recent Sharpe | %.3f |' % rho_rec_joined)
    lines.append('| historical Sharpe | %.3f |' % rho_hist_joined)
    lines.append('')

    # --- leg tables ---
    lj = legs_df.sort_values('joined_sh', ascending=False).head(15)
    ls = legs_df.sort_values('score', ascending=False).head(15)
    lines.append('## Legs — top 15 by joined Sharpe\n')
    lines.append('| # | Config | Joined Sh | Joined Ret% | J# | Rec Sh | Hist Sh | Score | S# |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|')
    for i, (_, l) in enumerate(lj.iterrows(), 1):
        lines.append('| %d | `%s` | %.2f | %+.2f%% | %d | %.2f | %.2f | %.2f | %d |'
                     % (i, l['name'], l['joined_sh'], l['joined_ret'] * 100, l['joined_rank'],
                        l['rec_sh'], l['hist_sh'], l['score'], l['score_rank']))
    lines.append('')
    lines.append('## Legs — top 15 by separate score min(rec, hist)\n')
    lines.append('| # | Config | Score | Rec Sh | Hist Sh | J# | Joined Sh | Joined Ret% |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|---:|')
    for i, (_, l) in enumerate(ls.iterrows(), 1):
        lines.append('| %d | `%s` | %.2f | %.2f | %.2f | %d | %.2f | %+.2f%% |'
                     % (i, l['name'], l['score'], l['rec_sh'], l['hist_sh'], l['joined_rank'],
                        l['joined_sh'], l['joined_ret'] * 100))
    lines.append('')

    # --- pair tables ---
    pj = pairs_df.sort_values('joined_sh', ascending=False).head(20)
    ps = pairs_df.sort_values('score', ascending=False).head(20)
    lines.append('## Pairs — top 20 by joined Sharpe\n')
    lines.append('| # | Leg A | Leg B | Joined Sh | Joined Ret% | J# | S# | Score | Rec Sh | Hist Sh |')
    lines.append('|---|---|---|---:|---:|---:|---:|---:|---:|---:|')
    for i, (_, r) in enumerate(pj.iterrows(), 1):
        lines.append('| %d | `%s` | `%s` | %.2f | %+.2f%% | %d | %d | %.2f | %.2f | %.2f |'
                     % (i, r['A'], r['B'], r['joined_sh'], r['joined_ret'] * 100,
                        r['joined_rank'], r['score_rank'], r['score'], r['rec'], r['hist']))
    lines.append('')
    lines.append('## Pairs — top 20 by separate score\n')
    lines.append('| # | Leg A | Leg B | Score | Rec Sh | Hist Sh | J# | Joined Sh | Joined Ret% |')
    lines.append('|---|---|---|---:|---:|---:|---:|---:|---:|')
    for i, (_, r) in enumerate(ps.iterrows(), 1):
        lines.append('| %d | `%s` | `%s` | %.2f | %.2f | %.2f | %d | %.2f | %+.2f%% |'
                     % (i, r['A'], r['B'], r['score'], r['rec'], r['hist'], r['joined_rank'],
                        r['joined_sh'], r['joined_ret'] * 100))
    lines.append('')

    out = os.path.join(JOINT, '_JOINT_VS_SEPARATE.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', out)
    print('wrote', os.path.join(JOINT, 'compare_pairs.csv'))


if __name__ == '__main__':
    main()