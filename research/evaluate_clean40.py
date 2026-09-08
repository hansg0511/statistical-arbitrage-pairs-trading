"""Evaluate the selected clean40 momentum configuration across all 496 pairs.

The leg corpus is fixed at ``fixed_diagnosis/_sweep_pct25``. This is a
post-selection evaluation of the explicitly chosen clean40 parameters, not a
new search over momentum parameters.

Usage: python research/evaluate_clean40.py
"""
import itertools
import math
import os
import statistics
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research.pair_sweep_consolidated import (  # noqa: E402
    CFGS,
    STRATEGIES,
    get_leg,
    simulate,
    metrics,
    weight_path_momentum_causal,
)


BASE = 'fixed_diagnosis'
OUT = os.path.join(BASE, 'clean40')
PCT = 0.25
PARAMS = dict(lookback=84, step=0.40, wmin=0.10, wmax=0.90)


def _pair_label(a, b):
    return '%s/%s + %s/%s' % (a[0], a[1], b[0], b[1])


def _series(a, b, mech, window, start_idx):
    leg_a = get_leg(a[0], a[1], window, start_idx)
    leg_b = get_leg(b[0], b[1], window, start_idx)
    weights = weight_path_momentum_causal(leg_a['ret'], leg_b['ret'], **PARAMS)
    rows, _, rejected, _ = simulate(
        {'A': leg_a, 'B': leg_b}, weights, mech, capital=1e6, pct=PCT)
    series = pd.Series([r['daily_return'] for r in rows],
                       index=[r['date'] for r in rows])
    return series, len(rejected)


def _average(rows, key):
    values = [r[key] for r in rows]
    return statistics.mean(values) if values else float('nan')


def pair_metrics(a, b, mech):
    recent = [_series(a, b, mech, 'recent', i) for i in range(5)]
    historical = _series(a, b, mech, 'historical', 0)
    recent_metrics = [metrics(series) for series, _ in recent]
    hist_metrics = metrics(historical[0])
    joined_metrics = [metrics(pd.concat([historical[0], series]))
                      for series, _ in recent]

    row = {
        'A': '%s/%s' % a,
        'B': '%s/%s' % b,
        'mech': mech,
        'recent_sh': _average(recent_metrics, 'sharpe'),
        'recent_ret': _average(recent_metrics, 'ann_ret'),
        'recent_vol': _average(recent_metrics, 'ann_vol'),
        'recent_mdd': _average(recent_metrics, 'mdd'),
        'hist_sh': hist_metrics['sharpe'],
        'hist_ret': hist_metrics['ann_ret'],
        'hist_vol': hist_metrics['ann_vol'],
        'hist_mdd': hist_metrics['mdd'],
        'joined_sh': _average(joined_metrics, 'sharpe'),
        'joined_ret': _average(joined_metrics, 'ann_ret'),
        'rejected_entries': sum(x[1] for x in recent) + historical[1],
    }
    row['score'] = min(row['recent_sh'], row['hist_sh'])
    return row


def dense_rank(values, reverse=True):
    order = sorted(range(len(values)), key=values.__getitem__, reverse=reverse)
    ranks = [0] * len(values)
    previous = None
    rank = 0
    for i, index in enumerate(order):
        value = values[index]
        if previous is None or abs(previous - value) > 1e-12:
            rank = i + 1
            previous = value
        ranks[index] = rank
    return ranks


def add_ranks(rows):
    recent = [r['recent_sh'] for r in rows]
    historical = [r['hist_sh'] for r in rows]
    joined = [r['joined_sh'] for r in rows]
    score = [r['score'] for r in rows]
    recent_rank = dense_rank(recent)
    historical_rank = dense_rank(historical)
    rank_average = [(a + b) / 2 for a, b in zip(recent_rank, historical_rank)]
    for i, row in enumerate(rows):
        row.update({
            'recent_rank': recent_rank[i],
            'hist_rank': historical_rank[i],
            'rank_avg': rank_average[i],
            'score_rank': dense_rank(score)[i],
            'rank_avg_rank': dense_rank(rank_average, reverse=False)[i],
            'joined_rank': dense_rank(joined)[i],
        })


def _pair_sets(df, column):
    return {tuple(sorted((r['A'], r['B'])))
            for _, r in df.nsmallest(20, column).iterrows()}


def write_report(frames):
    lines = [
        '# clean40 all-496 pair evaluation\n',
        'Fixed leg inputs: `fixed_diagnosis/_sweep_pct25`; pct=0.25; capital=$1M. '
        'Momentum parameters: lookback=84, step=0.40, bounds=[0.10, 0.90]. '
        'Recent values are means over five aligned starts; historical is the single aligned '
        '2015-2019 start; joined concatenates historical and each recent series.\n',
    ]
    consensus = []
    for mech, frame in frames.items():
        lines.append('## Mechanism %s\n' % mech)
        for title, column, reverse in [
                ('Top 20 by separate score', 'score', True),
                ('Top 20 by rank-average', 'rank_avg', False),
                ('Top 20 by joined Sharpe', 'joined_sh', True)]:
            lines.append('### %s\n' % title)
            lines.append('| # | Pair | Recent Sh | Recent Ret% | Hist Sh | Hist Ret% | Joined Sh | Score |')
            lines.append('|---|---|---:|---:|---:|---:|---:|---:|')
            ordered = frame.sort_values(column, ascending=not reverse).head(20)
            for i, (_, row) in enumerate(ordered.iterrows(), 1):
                lines.append('| %d | `%s` + `%s` | %.2f | %+.2f%% | %.2f | %+.2f%% | %.2f | %.2f |'
                             % (i, row['A'], row['B'], row['recent_sh'], row['recent_ret'] * 100,
                                row['hist_sh'], row['hist_ret'] * 100, row['joined_sh'], row['score']))
            lines.append('')

        sets = [_pair_sets(frame, c) for c in ['score_rank', 'rank_avg_rank', 'joined_rank']]
        consensus.append(set.intersection(*sets))
        lines.append('Top-20 intersection across all three methods: **%d** pairs.\n' % len(consensus[-1]))

    both = consensus[0] & consensus[1]
    lines.append('## Cross-mechanism consensus\n')
    lines.append('Pairs in the top 20 of all three methods for both mechanisms: **%d**.\n' % len(both))
    for pair in sorted(both):
        lines.append('- `%s` + `%s`\n' % pair)
    lines.append('')

    path = os.path.join(OUT, '_CLEAN40_PAIR_RANKS.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return both, path


def main():
    os.makedirs(OUT, exist_ok=True)
    legs = [(strategy, cfg) for strategy in STRATEGIES for cfg in CFGS]
    frames = {}
    for mech in ['A', 'B']:
        rows = []
        for a, b in itertools.combinations(legs, 2):
            row = pair_metrics(a, b, mech)
            if not any(math.isnan(row[key]) for key in ['recent_sh', 'hist_sh', 'joined_sh']):
                rows.append(row)
        add_ranks(rows)
        frame = pd.DataFrame(rows)
        frames[mech] = frame
        frame.to_csv(os.path.join(OUT, '_CLEAN40_PAIR_RANKS_%s.csv' % mech), index=False)
        print('mechanism %s: %d pairs' % (mech, len(frame)))

    both, report = write_report(frames)
    print('cross-mechanism consensus: %d pairs' % len(both))
    print('wrote', report)


if __name__ == '__main__':
    main()
