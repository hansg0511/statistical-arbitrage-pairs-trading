"""Write consolidated Markdown analyses for the default and clean40 books.

The pair CSVs are the source of truth for pair ranks and pair-window metrics.
Leg metrics are read from the corrected pct=0.25 sweep.  The historical default
ranking CSVs predate the addition of joined returns, so the default mechanism-B
joined returns are computed with the same event-replay code used by the ranking
generator.  Only rows that appear in a displayed top-20 table are recomputed.

Outputs:
  fixed_diagnosis/compare/_HUMAN_ANALYSIS_DEFAULT.md
  fixed_diagnosis/clean40/_HUMAN_ANALYSIS.md

Usage: python research/write_human_analysis.py
"""
import itertools
import json
import math
import os
import statistics
import sys
import warnings

import pandas as pd


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from research.run_combined_backtest import (  # noqa: E402
    build_leg_data,
    metrics,
    simulate,
    weight_path_momentum_causal,
)


BASE = os.path.join(ROOT, 'fixed_diagnosis')
SWEEP = os.path.join(BASE, '_sweep_pct25')
PAIR_TOP = 20
PCT = 0.25
CAPITAL = 1_000_000.0

DEFAULT_PARAMS = {
    'lookback': 63,
    'step': 0.10,
    'wmin': 0.25,
    'wmax': 0.75,
}
CLEAN40_PARAMS = {
    'lookback': 84,
    'step': 0.40,
    'wmin': 0.10,
    'wmax': 0.90,
}

CFGS = [
    'same_sector_slide3m_noscreen',
    'same_sector_slide3m_bd7',
    'same_sector_slide1m_noscreen',
    'same_sector_slide1m_bd7',
    'cross_sector_slide3m_noscreen',
    'cross_sector_slide3m_bd7',
    'cross_sector_slide1m_noscreen',
    'cross_sector_slide1m_bd7',
]

STARTS_2M = [
    '2023-11-01', '2023-12-01', '2024-01-01',
    '2024-02-01', '2024-03-01',
]
STARTS_12M = [
    '2023-01-01', '2023-02-01', '2023-03-01',
    '2023-04-01', '2023-05-01',
]

STRATEGIES = {
    'core-2m': ('06', '08a', '2014-11-01', STARTS_2M),
    'sp500-2m': ('07', '09a', '2014-11-01', STARTS_2M),
    'core-12m': ('10a', '08b', '2014-01-01', STARTS_12M),
    'sp500-12m': ('10b', '09b', '2014-01-01', STARTS_12M),
}

METHODS = [
    ('separate score', 'score_rank'),
    ('rank-average', 'rank_avg_rank'),
    ('joined Sharpe', 'joined_rank'),
]

_leg_data_cache = {}
_default_joined_cache = {}


def _pair_key(a, b):
    return tuple(sorted((str(a), str(b))))


def _fmt_sh(value):
    return '-' if pd.isna(value) else '%.2f' % float(value)


def _fmt_pct(value):
    return '-' if pd.isna(value) else '%+.2f%%' % (float(value) * 100.0)


def _fmt_rank(value):
    return '-' if pd.isna(value) else str(int(value))


def _pair_md(a, b):
    return '`%s` + `%s`' % (a, b)


def _dense_ranks(values, descending=True):
    """Return deterministic dense ranks, with rank 1 as the best value."""
    order = sorted(
        range(len(values)),
        key=lambda i: (-float(values[i]) if descending else float(values[i]), i),
    )
    ranks = [0] * len(values)
    previous = None
    rank = 0
    for position, index in enumerate(order):
        value = float(values[index])
        if previous is None or not math.isclose(previous, value, rel_tol=0.0, abs_tol=1e-12):
            rank += 1
            previous = value
        ranks[index] = rank
    return ranks


def _metric_json(section, start, cfg):
    path = os.path.join(SWEEP, section, '%s_%s' % (start, cfg), 'metrics.json')
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)


def load_leg_frame():
    """Load recent, historical, and joined metrics for all 32 legs."""
    rows = []
    for strategy, (recent_section, historical_section, historical_start, starts) in STRATEGIES.items():
        for cfg in CFGS:
            recent = [_metric_json(recent_section, start, cfg) for start in starts]
            historical = _metric_json(historical_section, historical_start, cfg)
            rows.append({
                'name': '%s/%s' % (strategy, cfg),
                'recent_sh': statistics.mean(m['annualized_sharpe'] for m in recent),
                'recent_ret': statistics.mean(m['annualized_return'] for m in recent),
                'hist_sh': historical['annualized_sharpe'],
                'hist_ret': historical['annualized_return'],
            })

    frame = pd.DataFrame(rows)
    joined_path = os.path.join(BASE, 'joint', 'joined_legs.csv')
    joined = pd.read_csv(joined_path)[['name', 'joined_sh', 'joined_ret']]
    frame = frame.merge(joined, on='name', how='left', validate='one_to_one')
    if frame[['joined_sh', 'joined_ret']].isna().any().any():
        raise RuntimeError('joined leg metrics are incomplete')

    for value_column in ['recent_sh', 'hist_sh', 'joined_sh',
                         'recent_ret', 'hist_ret', 'joined_ret']:
        frame['%s_rank' % value_column] = _dense_ranks(frame[value_column].tolist())
    return frame


def load_pair_frames(kind):
    frames = {}
    for mech in ['A', 'B']:
        if kind == 'default':
            path = os.path.join(BASE, 'compare', 'rank_comparison_%s.csv' % mech)
            frame = pd.read_csv(path)
            frame = frame.rename(columns={
                'r_rank': 'recent_rank',
                'h_rank': 'hist_rank',
                'r_ret': 'recent_ret',
                'h_ret': 'hist_ret',
            })
        else:
            path = os.path.join(BASE, 'clean40', '_CLEAN40_PAIR_RANKS_%s.csv' % mech)
            frame = pd.read_csv(path)
            frame = frame[frame['mech'] == mech].copy()
            frame = frame.rename(columns={
                'recent_sh': 'recent',
                'hist_sh': 'hist',
            })
        if len(frame) != 496:
            raise RuntimeError('%s %s has %d rows, expected 496' % (kind, mech, len(frame)))
        frame['mech'] = mech
        frame['pair_key'] = [
            _pair_key(row['A'], row['B']) for _, row in frame.iterrows()
        ]
        frames[mech] = frame.reset_index(drop=True)
    return frames


def _top(frame, rank_column):
    # Stable sorting preserves the source generator's deterministic tie order.
    return frame.sort_values(rank_column, ascending=True, kind='mergesort').head(PAIR_TOP)


def _top_keys(frame, rank_column):
    return set(_top(frame, rank_column)['pair_key'])


def consensus_sets(frames):
    per_method = {
        mech: {name: _top_keys(frames[mech], column) for name, column in METHODS}
        for mech in ['A', 'B']
    }
    per_mech = {
        mech: set.intersection(*sets.values())
        for mech, sets in per_method.items()
    }
    cross = per_mech['A'] & per_mech['B']
    return per_method, per_mech, cross


def _leg_path(name, window, start_index):
    strategy, cfg = str(name).split('/', 1)
    recent_section, historical_section, historical_start, starts = STRATEGIES[strategy]
    if window == 'recent':
        section = recent_section
        start = starts[start_index]
    else:
        section = historical_section
        start = historical_start
    return os.path.join(SWEEP, section, '%s_%s' % (start, cfg))


def _pair_series(name_a, name_b, window, start_index, mech, params):
    key = (name_a, name_b, window, start_index, mech, tuple(sorted(params.items())))
    if key in _default_joined_cache:
        return _default_joined_cache[key]

    def get_cached(name):
        path = _leg_path(name, window, start_index)
        if path not in _leg_data_cache:
            _leg_data_cache[path] = build_leg_data(path)
        return _leg_data_cache[path]

    leg_a = get_cached(name_a)
    leg_b = get_cached(name_b)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        weights = weight_path_momentum_causal(
            leg_a['ret'], leg_b['ret'],
            lookback=params['lookback'],
            step=params['step'],
            wmin=params['wmin'],
            wmax=params['wmax'],
        )
    rows, _, _, _ = simulate(
        {'A': leg_a, 'B': leg_b}, weights, mech,
        capital=CAPITAL, pct=PCT,
    )
    series = pd.Series(
        [row['daily_return'] for row in rows],
        index=[row['date'] for row in rows],
    )
    _default_joined_cache[key] = series
    return series


def _joined_pair_metrics(name_a, name_b, mech, params):
    historical = _pair_series(name_a, name_b, 'historical', 0, mech, params)
    recent = [
        _pair_series(name_a, name_b, 'recent', index, mech, params)
        for index in range(5)
    ]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        joined = [metrics(pd.concat([historical, series])) for series in recent]
    return (
        statistics.mean(m['sharpe'] for m in joined),
        statistics.mean(m['ann_ret'] for m in joined),
    )


def add_default_joined_returns(frames):
    """Fill joined returns for the displayed default rows only."""
    joined_path = os.path.join(BASE, 'joint', 'joined_pairs.csv')
    joined = pd.read_csv(joined_path)
    joined_a = {
        _pair_key(row['A'], row['B']): float(row['joined_ret'])
        for _, row in joined.iterrows()
    }

    needed = {}
    for mech, frame in frames.items():
        keys = set()
        for _, rank_column in METHODS:
            keys.update(_top_keys(frame, rank_column))
        for key in keys:
            row = frame[frame['pair_key'] == key].iloc[0]
            needed[(mech, key)] = (str(row['A']), str(row['B']))

    computed = 0
    for (mech, key), (name_a, name_b) in sorted(needed.items()):
        if mech == 'A' and key in joined_a:
            joined_ret = joined_a[key]
        else:
            joined_sh, joined_ret = _joined_pair_metrics(name_a, name_b, mech, DEFAULT_PARAMS)
            expected_sh = float(_row_for_key(frames[mech], key)['joined_sh'])
            if not math.isclose(joined_sh, expected_sh, rel_tol=0.0, abs_tol=1e-9):
                raise RuntimeError(
                    'default joined Sharpe mismatch for %s/%s: %.12f != %.12f' %
                    (mech, ' + '.join(key), joined_sh, expected_sh)
                )
            computed += 1
        frame = frames[mech]
        frame.loc[frame['pair_key'] == key, 'joined_ret'] = joined_ret

    print('default joined returns: reused %d mechanism-A rows, computed %d rows' %
          (len(needed) - computed, computed))


def _rank_correlations(frame):
    columns = ['score_rank', 'rank_avg_rank', 'joined_rank']
    return frame[columns].corr(method='pearson')


def _row_for_key(frame, key):
    rows = frame[frame['pair_key'] == key]
    if rows.empty:
        raise RuntimeError('pair not found: %s' % (key,))
    return rows.iloc[0]


def _pair_table(lines, frame, title, rank_column):
    lines.append('### %s\n' % title)
    lines.append(
        '| # | Pair | Rec # | Rec Sh | Rec Ret% | Hist # | Hist Sh | Hist Ret% | '
        'Joined # | Joined Sh | Joined Ret% | Score | Rank Avg |'
    )
    lines.append('|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    for _, row in _top(frame, rank_column).iterrows():
        lines.append(
            '| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %.1f |' %
            (
                _fmt_rank(row[rank_column]),
                _pair_md(row['A'], row['B']),
                _fmt_rank(row['recent_rank']),
                _fmt_sh(row['recent']),
                _fmt_pct(row['recent_ret']),
                _fmt_rank(row['hist_rank']),
                _fmt_sh(row['hist']),
                _fmt_pct(row['hist_ret']),
                _fmt_rank(row['joined_rank']),
                _fmt_sh(row['joined_sh']),
                _fmt_pct(row['joined_ret']),
                _fmt_sh(row['score']),
                float(row['rank_avg']),
            )
        )
    lines.append('')


def _leg_table(lines, legs, title='All 32 legs'):
    lines.append('## Leg rankings - %s\n' % title)
    lines.append(
        'Ranks are dense ranks across all 32 legs; rank 1 is the highest value. '
        'Return ranks are separate from Sharpe ranks.\n'
    )
    lines.append(
        '| Leg | Rec Sh | Sh# | Rec Ret% | Ret# | Hist Sh | Sh# | Hist Ret% | Ret# | '
        'Joined Sh | Sh# | Joined Ret% | Ret# |'
    )
    lines.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    ordered = legs.sort_values(['joined_sh_rank', 'name'], kind='mergesort')
    for _, row in ordered.iterrows():
        lines.append(
            '| `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' %
            (
                row['name'],
                _fmt_sh(row['recent_sh']), _fmt_rank(row['recent_sh_rank']),
                _fmt_pct(row['recent_ret']), _fmt_rank(row['recent_ret_rank']),
                _fmt_sh(row['hist_sh']), _fmt_rank(row['hist_sh_rank']),
                _fmt_pct(row['hist_ret']), _fmt_rank(row['hist_ret_rank']),
                _fmt_sh(row['joined_sh']), _fmt_rank(row['joined_sh_rank']),
                _fmt_pct(row['joined_ret']), _fmt_rank(row['joined_ret_rank']),
            )
        )
    lines.append('')


def _selected_leg_table(lines, legs, selected_pairs):
    names = sorted(set(itertools.chain.from_iterable(selected_pairs)))
    if not names:
        return
    selected = legs[legs['name'].isin(names)].copy()
    lines.append('## Legs used by the strict consensus shortlist\n')
    lines.append(
        'This compact view connects the pair shortlist to the individual-leg rankings. '
        'The full 32-leg table is above.\n'
    )
    lines.append(
        '| Leg | Rec Sh (#) | Rec Ret% (#) | Hist Sh (#) | Hist Ret% (#) | '
        'Joined Sh (#) | Joined Ret% (#) |'
    )
    lines.append('|---|---:|---:|---:|---:|---:|---:|')
    selected = selected.sort_values(['joined_sh_rank', 'name'], kind='mergesort')
    for _, row in selected.iterrows():
        lines.append(
            '| `%s` | %s (%s) | %s (%s) | %s (%s) | %s (%s) | %s (%s) | %s (%s) |' %
            (
                row['name'],
                _fmt_sh(row['recent_sh']), _fmt_rank(row['recent_sh_rank']),
                _fmt_pct(row['recent_ret']), _fmt_rank(row['recent_ret_rank']),
                _fmt_sh(row['hist_sh']), _fmt_rank(row['hist_sh_rank']),
                _fmt_pct(row['hist_ret']), _fmt_rank(row['hist_ret_rank']),
                _fmt_sh(row['joined_sh']), _fmt_rank(row['joined_sh_rank']),
                _fmt_pct(row['joined_ret']), _fmt_rank(row['joined_ret_rank']),
            )
        )
    lines.append('')


def _consensus_summary(lines, frames, per_method, per_mech, cross):
    lines.append('## Consensus and rank agreement\n')
    lines.append(
        '| Mechanism | Separate / rank-average | Separate / joined | Rank-average / joined | All three |'
    )
    lines.append('|---|---:|---:|---:|---:|')
    for mech in ['A', 'B']:
        sets = per_method[mech]
        lines.append(
            '| %s | %d | %d | %d | %d |' %
            (
                mech,
                len(sets['separate score'] & sets['rank-average']),
                len(sets['separate score'] & sets['joined Sharpe']),
                len(sets['rank-average'] & sets['joined Sharpe']),
                len(per_mech[mech]),
            )
        )
    lines.append('')

    lines.append(
        '| Mechanism | Separate vs rank-average | Separate vs joined | Rank-average vs joined |'
    )
    lines.append('|---|---:|---:|---:|')
    for mech in ['A', 'B']:
        corr = _rank_correlations(frames[mech])
        lines.append(
            '| %s | %.3f | %.3f | %.3f |' %
            (
                mech,
                corr.loc['score_rank', 'rank_avg_rank'],
                corr.loc['score_rank', 'joined_rank'],
                corr.loc['rank_avg_rank', 'joined_rank'],
            )
        )
    lines.append('')

    lines.append(
        'The strict cross-mechanism shortlist contains **%d** pair(s): top 20 in '
        'all three methods for both mechanisms.\n' % len(cross)
    )
    if cross:
        for key in sorted(cross):
            lines.append('- %s' % _pair_md(key[0], key[1]))
        lines.append('')


def _consensus_detail(lines, frames, cross):
    if not cross:
        return
    lines.append('## Strict consensus pair detail\n')
    lines.append(
        '| Pair | Mech | Separate # | Rank-average # | Joined # | Recent Sh / Ret% | '
        'Hist Sh / Ret% | Joined Sh / Ret% | Score |'
    )
    lines.append('|---|---|---:|---:|---:|---:|---:|---:|---:|')

    def rank_sum(key):
        return sum(
            float(_row_for_key(frames[mech], key)[column])
            for mech in ['A', 'B']
            for _, column in METHODS
        )

    for key in sorted(cross, key=lambda item: (rank_sum(item), item)):
        for mech in ['A', 'B']:
            row = _row_for_key(frames[mech], key)
            lines.append(
                '| %s | %s | %s | %s | %s | %s / %s | %s / %s | %s / %s | %s |' %
                (
                    _pair_md(key[0], key[1]), mech,
                    _fmt_rank(row['score_rank']),
                    _fmt_rank(row['rank_avg_rank']),
                    _fmt_rank(row['joined_rank']),
                    _fmt_sh(row['recent']), _fmt_pct(row['recent_ret']),
                    _fmt_sh(row['hist']), _fmt_pct(row['hist_ret']),
                    _fmt_sh(row['joined_sh']), _fmt_pct(row['joined_ret']),
                    _fmt_sh(row['score']),
                )
            )
    lines.append('')


def _analysis_lines(lines, kind, frames, per_mech, cross, other_frames=None):
    lines.append('## Human analysis\n')
    lines.append(
        'The three methods answer different questions. The separate score protects the '
        'weaker window, rank-average rewards a consistently high position in both windows, '
        'and joined Sharpe treats the historical and recent series as one sample. A method '
        'disagreement is therefore evidence of regime dependence, not a reason to select the '
        'largest recent Sharpe automatically.\n'
    )
    for mech in ['A', 'B']:
        frame = frames[mech]
        leaders = []
        for name, rank_column in METHODS:
            row = _top(frame, rank_column).iloc[0]
            leaders.append(
                '%s: %s (joined Sh %s, joined return %s)' %
                (name, _pair_md(row['A'], row['B']),
                 _fmt_sh(row['joined_sh']), _fmt_pct(row['joined_ret']))
            )
        lines.append('- Mechanism %s leaders: %s.' % (mech, '; '.join(leaders)))
        lines.append(
            '  The top-20 all-method intersection for mechanism %s is %d pair(s).' %
            (mech, len(per_mech[mech]))
        )

    if cross:
        def consensus_order(key):
            return sum(
                float(_row_for_key(frames[mech], key)[column])
                for mech in ['A', 'B']
                for _, column in METHODS
            )

        best = min(cross, key=consensus_order)
        lines.append(
            '- The strongest strict-consensus pair by the sum of its six method ranks is '
            '%s (rank-sum %.1f). This is a mechanical shortlist, not an automatic trading '
            'decision.' % (_pair_md(best[0], best[1]), consensus_order(best))
        )
    else:
        lines.append(
            '- No pair survives the strict cross-mechanism intersection, so any final choice '
            'needs an explicitly stated tie-break or human-selection rule.'
        )

    lines.append(
        '- Pair ranks and leg ranks are different objects. Dynamic capital rotation and the '
        'shared-account event replay can make a pair attractive even when neither leg is the '
        'top standalone leg in every window.'
    )
    lines.append(
        '- Return ranks should be read alongside Sharpe ranks: a high annualized return can '
        'come with materially higher volatility or drawdown, while a high Sharpe can reflect '
        'a smaller but steadier return.'
    )
    if kind == 'clean40':
        lines.append(
            '- `clean40` is evaluated here as an explicitly selected parameter set across all '
            '496 pairs. This report is not a new momentum-parameter optimization.'
        )
    else:
        lines.append(
            '- This report is the original default allocation baseline. The clean40 report '
            'should be read as the later parameterized comparison, not mixed into these values.'
        )
    lines.append(
        '- These diagnostics do not establish out-of-sample alpha. The existing factor '
        'diagnostics remain the appropriate place to assess exposure and statistical alpha.'
    )
    lines.append('')

    if other_frames is not None:
        lines.append('## Default versus clean40 leaders\n')
        lines.append(
            '| Mechanism | Method | Default leader | Default Joined Sh | Default Joined Ret% | '
            'clean40 leader | clean40 Joined Sh | clean40 Joined Ret% |'
        )
        lines.append('|---|---|---|---:|---:|---|---:|---:|')
        for mech in ['A', 'B']:
            for name, rank_column in METHODS:
                first = _top(frames[mech], rank_column).iloc[0]
                other = _top(other_frames[mech], rank_column).iloc[0]
                if kind == 'clean40':
                    default_row, clean_row = other, first
                else:
                    default_row, clean_row = first, other
                lines.append(
                    '| %s | %s | %s | %s | %s | %s | %s | %s |' %
                    (
                        mech, name,
                        _pair_md(default_row['A'], default_row['B']),
                        _fmt_sh(default_row['joined_sh']), _fmt_pct(default_row['joined_ret']),
                        _pair_md(clean_row['A'], clean_row['B']),
                        _fmt_sh(clean_row['joined_sh']), _fmt_pct(clean_row['joined_ret']),
                    )
                )
        lines.append('')


def write_report(kind, frames, legs, per_method, per_mech, cross, other_frames=None):
    if kind == 'default':
        params = DEFAULT_PARAMS
        output = os.path.join(BASE, 'compare', '_HUMAN_ANALYSIS_DEFAULT.md')
        title = '# Original default allocation - consolidated human analysis\n'
        source = (
            'Pair ranks and recent/historical pair metrics: `fixed_diagnosis/compare/'
            'rank_comparison_A.csv` and `rank_comparison_B.csv`. Mechanism-A joined returns '
            'come from `fixed_diagnosis/joint/joined_pairs.csv`; displayed mechanism-B joined '
            'returns are recomputed from the corrected sweep with the default event replay. '
        )
    else:
        params = CLEAN40_PARAMS
        output = os.path.join(BASE, 'clean40', '_HUMAN_ANALYSIS.md')
        title = '# clean40 human analysis - consolidated pair and leg rankings\n'
        source = (
            'Pair metrics and ranks: `fixed_diagnosis/clean40/_CLEAN40_PAIR_RANKS_A.csv` '
            'and `_CLEAN40_PAIR_RANKS_B.csv`. '
        )

    lines = [title]
    lines.append(
        '%s pct=%.2f and capital=$%s. Momentum parameters: lookback=%d days, '
        'step=%.2f, weight bounds=[%.2f, %.2f], initial weight_A=0.50.\n' %
        (
            source, PCT, format(int(CAPITAL), ','), params['lookback'], params['step'],
            params['wmin'], params['wmax'],
        )
    )
    lines.append(
        'Universe: 32 corrected legs and 496 two-leg combinations. Recent metrics are '
        'means over five aligned starts; historical metrics use the single aligned 2015-2019 '
        'window. Joined metrics concatenate historical and each recent series, then average '
        'the five joined results. All Sharpe ratios and returns are annualized.\n'
    )
    lines.append(
        'Mechanism A and mechanism B are the two shared-account event-replay implementations. '
        'The displayed pair order is the source CSV order and does not change the stored '
        'mechanism result.\n'
    )

    _analysis_lines(lines, kind, frames, per_mech, cross, other_frames)
    _consensus_summary(lines, frames, per_method, per_mech, cross)
    _consensus_detail(lines, frames, cross)

    lines.append('## Pair rankings\n')
    lines.append(
        'Each table contains the top 20 rows for one method. `Rec #`, `Hist #`, and `Joined #` '
        'are the pair ranks for the corresponding Sharpe metric; `Score` is the minimum of '
        'recent and historical Sharpe.\n'
    )
    for mech in ['A', 'B']:
        lines.append('## Mechanism %s\n' % mech)
        for name, rank_column in METHODS:
            _pair_table(lines, frames[mech], 'Top 20 by %s' % name, rank_column)

    _leg_table(lines, legs)
    _selected_leg_table(lines, legs, cross)

    lines.append('## Source files\n')
    lines.append('- Corrected leg metrics: `fixed_diagnosis/_sweep_pct25/`')
    lines.append('- Leg joined metrics: `fixed_diagnosis/joint/joined_legs.csv`')
    lines.append('- Ranking method definitions: `research/compare_rankings.py`')
    lines.append('- Default event replay: `research/run_combined_backtest.py`')
    lines.append('- Corrected pipeline context: `RESEARCH_PIPELINE_FIXED.md`')
    lines.append('')

    with open(output, 'w', encoding='utf-8') as handle:
        handle.write('\n'.join(lines) + '\n')
    print('wrote', output)
    return output


def main():
    legs = load_leg_frame()
    default_frames = load_pair_frames('default')
    clean40_frames = load_pair_frames('clean40')
    add_default_joined_returns(default_frames)

    default_method, default_mech, default_cross = consensus_sets(default_frames)
    clean_method, clean_mech, clean_cross = consensus_sets(clean40_frames)

    default_output = write_report(
        'default', default_frames, legs, default_method, default_mech,
        default_cross, other_frames=clean40_frames,
    )
    clean_output = write_report(
        'clean40', clean40_frames, legs, clean_method, clean_mech,
        clean_cross, other_frames=default_frames,
    )
    print('default consensus:', len(default_cross))
    print('clean40 consensus:', len(clean_cross))
    print('outputs:', default_output, clean_output)


if __name__ == '__main__':
    main()
