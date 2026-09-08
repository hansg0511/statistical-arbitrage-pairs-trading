"""Joined-period evaluation: ONE Sharpe and ONE return per leg/pair.

Instead of evaluating the historical and recent windows separately and ranking
by score = min(recent, hist), concatenate the two windows into a single daily
return series and compute a single annualized Sharpe and annualized return.

Windows (non-overlapping):
  historical : single aligned start, 2015-01..2019-12
  recent     : 5 aligned start-pairs, 2024-01..2025-12
Joined series = historical series ++ recent series(start i), for each of the 5
recent starts; the reported joined Sharpe/return is the mean over the 5 joins.

Legs: single-leg daily returns from _sweep_pct25/<sec>/<start>_<cfg>/.
Pairs: trade-event replay (mech A, pct=0.25) per window, then the same join.

Outputs (fixed_diagnosis/joint/):
  _JOINED_PER_PERIOD.md   top-15 legs by joined Sharpe
  _JOINED_CONFIG_PAIRS.md top-20 pairs by joined Sharpe
  joined_legs.csv         all 32 legs
  joined_pairs.csv        all 496 pairs

Usage: python research/write_joint_eval.py
"""
import os
import statistics

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from research.pair_sweep_consolidated import (  # noqa: E402
    STRATEGIES, CFGS, STARTS_2M, get_leg, weight_path_momentum_causal, simulate, metrics,
)
from research.write_top7_period import leg_metrics, dense_ranks  # noqa: E402

BASE = 'fixed_diagnosis'
JOINT = os.path.join(BASE, 'joint')
PCT = 0.25


def _avg(metrics_list, key):
    vals = [m[key] for m in metrics_list]
    return sum(vals) / len(vals)


def joined_metrics(series_list):
    """series_list: list of (hist_series, recent_series) pairs -> (sharpe, ret)."""
    out = []
    for hist_s, rec_s in series_list:
        joined = pd.concat([hist_s, rec_s])
        out.append(metrics(joined))
    return _avg(out, 'sharpe'), _avg(out, 'ann_ret')


def leg_joined():
    from research.write_top7_period import load_metrics

    legs = []
    for strat, (rsec, hsec, starts) in STRATEGIES.items():
        hstart = '2014-11-01' if starts is STARTS_2M else '2014-01-01'
        for cfg in CFGS:
            hist_ret = get_leg_dir_ret(hsec, hstart, cfg)
            rec_rets = [get_leg_dir_ret(rsec, st, cfg) for st in starts]
            sh, ret = joined_metrics([(hist_ret, r) for r in rec_rets])
            rec_sh = statistics.mean(load_metrics(rsec, st, cfg)[0] for st in starts)
            hist_sh = load_metrics(hsec, hstart, cfg)[0]
            legs.append({'name': '%s/%s' % (strat, cfg),
                         'joined_sh': sh, 'joined_ret': ret,
                         'rec_sh': rec_sh, 'hist_sh': hist_sh})
    return legs


def _leg_series(sec, start, cfg):
    return get_leg_dir_ret(sec, start, cfg)


def get_leg_dir_ret(sec, start, cfg):
    import pandas as pd
    p = os.path.join(BASE, '_sweep_pct25', sec, '%s_%s' % (start, cfg), 'daily_returns.csv')
    df = pd.read_csv(p, parse_dates=['date'])
    return df.set_index('date')['daily_return']


def pair_series(sa, ca, sb, cb, window, start_idx=0):
    a = get_leg(sa, ca, window, start_idx)
    b = get_leg(sb, cb, window, start_idx)
    wp = weight_path_momentum_causal(a['ret'], b['ret'])
    rows, _, _, _ = simulate({'A': a, 'B': b}, wp, 'A', capital=1e6, pct=PCT)
    return pd.Series([r['daily_return'] for r in rows], index=[r['date'] for r in rows])


def pair_joined(rec_sh_map):
    all_legs = [(s, c) for s in STRATEGIES for c in CFGS]
    rows = []
    import itertools
    for (sa, ca), (sb, cb) in itertools.combinations(all_legs, 2):
        hist_s = pair_series(sa, ca, sb, cb, 'historical')
        rec_s = [pair_series(sa, ca, sb, cb, 'recent', i) for i in range(5)]
        sh, ret = joined_metrics([(hist_s, r) for r in rec_s])
        if sh != sh:
            continue
        na, nb = '%s/%s' % (sa, ca), '%s/%s' % (sb, cb)
        if rec_sh_map[nb] > rec_sh_map[na]:
            na, nb = nb, na
        rows.append({'A': na, 'B': nb, 'joined_sh': sh, 'joined_ret': ret})
    rows.sort(key=lambda x: x['joined_sh'], reverse=True)
    return rows


def write_legs_md(legs, rec_rank, hist_rank):
    lines = ['# Top 15 configs — joined period\n']
    lines.append('Joined = historical (2015–2019) ++ recent (2024–2025) daily returns as one '
                 'series; single annualized Sharpe and return. Reported value = mean over the 5 '
                 'recent start-pairs. Per-window ranks (rec #/hist #) are the separate-window '
                 'ranks for reference.\n')
    lines.append('| Rank(joined) | Config | Joined Sh | Joined Ret% | Rec# | Hist# | Rec Sh | Hist Sh |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|---:|')
    for i, l in enumerate(sorted(legs, key=lambda x: x['joined_sh'], reverse=True)[:15], 1):
        lines.append('| %d | `%s` | %.2f | %+.2f%% | %d | %d | %.2f | %.2f |'
                     % (i, l['name'], l['joined_sh'], l['joined_ret'] * 100,
                        rec_rank[l['name']], hist_rank[l['name']], l['rec_sh'], l['hist_sh']))
    lines.append('')
    out = os.path.join(JOINT, '_JOINED_PER_PERIOD.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', out)


def write_pairs_md(rows):
    lines = ['# Top 20 config pairs — joined period (mechanism A)\n']
    lines.append('Joined = historical (2015–2019) ++ recent (2024–2025) trade-event replay '
                 'returns as one series; single annualized Sharpe and return. Reported value = '
                 'mean over the 5 recent start-pairs. Ranked by joined Sharpe. A = recent-strong, '
                 'B = historical-strong (same convention as the separate evaluation).\n')
    lines.append('| # | Leg A | Leg B | Joined Sh | Joined Ret% |')
    lines.append('|---|---|---:|---:|---:|')
    for i, r in enumerate(rows[:20], 1):
        lines.append('| %d | `%s` | `%s` | %.2f | %+.2f%% |'
                     % (i, r['A'], r['B'], r['joined_sh'], r['joined_ret'] * 100))
    lines.append('')
    out = os.path.join(JOINT, '_JOINED_CONFIG_PAIRS.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', out)


def write_csvs(legs, pair_rows):
    pd.DataFrame(legs).to_csv(os.path.join(JOINT, 'joined_legs.csv'), index=False)
    pd.DataFrame(pair_rows).to_csv(os.path.join(JOINT, 'joined_pairs.csv'), index=False)
    print('wrote', os.path.join(JOINT, 'joined_legs.csv'))
    print('wrote', os.path.join(JOINT, 'joined_pairs.csv'))


def main():
    os.makedirs(JOINT, exist_ok=True)
    print('computing joined leg metrics...')
    legs = leg_joined()
    rank_keys = leg_metrics()
    rec_rank = dense_ranks(rank_keys, 'rec_sh')
    hist_rank = dense_ranks(rank_keys, 'hist_sh')
    write_legs_md(legs, rec_rank, hist_rank)

    print('computing joined pair metrics (496 pairs x 6 windows)...')
    rec_sh_map = {l['name']: l['rec_sh'] for l in legs}
    pair_rows = pair_joined(rec_sh_map)
    write_pairs_md(pair_rows)
    write_csvs(legs, pair_rows)


if __name__ == '__main__':
    main()