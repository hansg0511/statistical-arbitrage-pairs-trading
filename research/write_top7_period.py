"""Write fixed_diagnosis/separate/_TOP15_PER_PERIOD.md (top-15 legs per window) and
fixed_diagnosis/separate/_TOP15_CONFIG_PAIRS.md (top-15 legs pairs, leg A = recent-strong,
leg B = historical-strong, with per-period ranks).

Per-leg metrics come from _sweep_pct25/<sec>/<start>_<cfg>/metrics.json:
  recent = mean over the 5 aligned start-pairs of the strategy
  hist   = single historical start (08a/09a: 2014-11-01; 08b/09b: 2014-01-01)
Ranks are across the full 32-leg universe per window.

Pairs come from the consolidated sweep (research/pair_sweep_consolidated.py),
mechanism A, read from fixed_diagnosis/separate/_COMBINED_BOOK_CONSOLIDATED.md
(top-20 by score = min(recent, hist)), taking the top 15.

Usage: python research/write_top7_period.py
"""
import os
import json
import statistics

BASE = 'fixed_diagnosis'
SWEEP = os.path.join(BASE, '_sweep_pct25')
SEPARATE = os.path.join(BASE, 'separate')

CFGS = ['same_sector_slide3m_noscreen', 'same_sector_slide3m_bd7',
        'same_sector_slide1m_noscreen', 'same_sector_slide1m_bd7',
        'cross_sector_slide3m_noscreen', 'cross_sector_slide3m_bd7',
        'cross_sector_slide1m_noscreen', 'cross_sector_slide1m_bd7']

STARTS_2M = ['2023-11-01', '2023-12-01', '2024-01-01', '2024-02-01', '2024-03-01']
STARTS_12M = ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01']

STRATEGIES = {
    'core-2m':   ('06', '08a', '2014-11-01', STARTS_2M),
    'sp500-2m':  ('07', '09a', '2014-11-01', STARTS_2M),
    'core-12m':  ('10a', '08b', '2014-01-01', STARTS_12M),
    'sp500-12m': ('10b', '09b', '2014-01-01', STARTS_12M),
}


def load_metrics(sec, start, cfg):
    p = os.path.join(SWEEP, sec, '%s_%s' % (start, cfg), 'metrics.json')
    with open(p, encoding='utf-8') as f:
        m = json.load(f)
    return m['annualized_sharpe'], m['annualized_return']


def leg_metrics():
    legs = []
    for strat, (rsec, hsec, hstart, starts) in STRATEGIES.items():
        for cfg in CFGS:
            rec_sh = []
            rec_ret = []
            for st in starts:
                sh, ret = load_metrics(rsec, st, cfg)
                rec_sh.append(sh)
                rec_ret.append(ret)
            hist_sh, hist_ret = load_metrics(hsec, hstart, cfg)
            legs.append({
                'strat': strat, 'cfg': cfg, 'name': '%s/%s' % (strat, cfg),
                'rec_sh': statistics.mean(rec_sh), 'rec_ret': statistics.mean(rec_ret),
                'hist_sh': hist_sh, 'hist_ret': hist_ret,
            })
    return legs


def dense_ranks(legs, key):
    order = sorted(legs, key=lambda l: l[key], reverse=True)
    ranks = {}
    prev = None
    for i, l in enumerate(order):
        if prev is None or abs(order[i - 1][key] - l[key]) > 1e-9:
            rank = i + 1
            prev = l[key]
        ranks[l['name']] = rank
    return ranks


def fmt_pct(x):
    return '%+.2f%%' % (x * 100)


def write_period_md(legs, rec_rank, hist_rank):
    lines = []
    lines.append('# Top 15 configs per period\n')
    lines.append('Universe: 32 legs = 4 strategies (core-2m, sp500-2m, core-12m, sp500-12m) x 8 '
                 'configs (same/cross-sector x slide 1m/3m x bd7/noscreen), pct=0.25.\n')
    lines.append('Recent = mean annualized Sharpe/return over the 5 aligned start-pairs '
                 '(2m: 2023-11..2024-03; 12m: 2023-01..2023-05). Historical = single aligned start '
                 '(08a/09a: 2014-11-01; 08b/09b: 2014-01-01). Ranks across the full 32-leg set.\n')

    lines.append('## Recent — top 15\n')
    lines.append('| Rank(rec) | Config | Recent Sh | Recent Ret% | Rank(hist) | Hist Sh | Hist Ret% |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|')
    for l in sorted(legs, key=lambda x: x['rec_sh'], reverse=True)[:15]:
        lines.append('| %d | `%s` | %.2f | %s | %d | %.2f | %s |'
                     % (rec_rank[l['name']], l['name'], l['rec_sh'], fmt_pct(l['rec_ret']),
                        hist_rank[l['name']], l['hist_sh'], fmt_pct(l['hist_ret'])))
    lines.append('')

    lines.append('## Historical — top 15\n')
    lines.append('| Rank(hist) | Config | Hist Sh | Hist Ret% | Rank(rec) | Recent Sh | Recent Ret% |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|')
    for l in sorted(legs, key=lambda x: x['hist_sh'], reverse=True)[:15]:
        lines.append('| %d | `%s` | %.2f | %s | %d | %.2f | %s |'
                     % (hist_rank[l['name']], l['name'], l['hist_sh'], fmt_pct(l['hist_ret']),
                        rec_rank[l['name']], l['rec_sh'], fmt_pct(l['rec_ret'])))
    lines.append('')

    out = os.path.join(SEPARATE, '_TOP15_PER_PERIOD.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', out)


def load_pair_rows():
    src = os.path.join(SEPARATE, '_COMBINED_BOOK_CONSOLIDATED.md')
    with open(src, encoding='utf-8') as f:
        txt = f.read()
    seg = txt.split('## Mechanism A — top 20 pairs')[1].split('##')[0]
    rows = []
    for line in seg.splitlines():
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if len(cells) < 6 or ' + ' not in cells[0]:
            continue
        a, b = cells[0].split(' + ')
        rows.append({'a': a, 'b': b, 'recent': float(cells[1]),
                     'hist': float(cells[3]), 'score': float(cells[4]),
                     'rec_ret': float(cells[5].replace('%', '')) / 100,
                     'hist_ret': float(cells[6].replace('%', '')) / 100})
    return rows[:15]


def write_pairs_md(legs, rec_rank, hist_rank):
    by_name = {l['name']: l for l in legs}
    rows = load_pair_rows()

    lines = []
    lines.append('# Top 15 config pairs (mechanism A)\n')
    lines.append('Pairs from the consolidated sweep (trade-event replay, pct=0.25), ranked by '
                 'score = min(recent, hist) pair Sharpe. Convention: **leg A = recent-strong**, '
                 '**leg B = historical-strong**. Salient ranks shown per leg. Pair returns (%) are '
                 'the pair book\'s annualized return in each window.\n')
    lines.append('## How to read\n')
    lines.append('Pair rank is NOT leg rank. Pairs are combined in a shared-account momentum replay '
                 '(mechanism A: monthly re-tilt of fold capital to causal 63d-trailing-Sharpe '
                 'weights, clamped to [0.25, 0.75]) and ranked by score = min(pair recent, pair '
                 'historical) Sharpe of the **pair** book. The single-leg and pair rankings are '
                 'different objects; use the tables below for the current values rather than '
                 'assuming the strongest individual leg forms the strongest pair.\n')
    lines.append('Pair rec Ret% / Pair hist Ret% are the pair book\'s annualized return in each '
                 'window.\n')

    lines.append('| # | Leg A (recent-strong) | A Rec# | A Rec Sh | A Ret% | A Hist# | '
                 'Leg B (hist-strong) | B Hist# | B Hist Sh | B Ret% | B Rec# | '
                 'Pair rec Sh | Pair rec Ret% | Pair hist Sh | Pair hist Ret% | Score |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    for i, r in enumerate(rows, 1):
        la, lb = by_name[r['a']], by_name[r['b']]
        if la['rec_sh'] >= lb['rec_sh']:
            A, B = la, lb
        else:
            A, B = lb, la
        lines.append('| %d | `%s` | %d | %.2f | %s | %d | `%s` | %d | %.2f | %s | %d | '
                     '%.2f | %s | %.2f | %s | %.2f |'
                     % (i, A['name'], rec_rank[A['name']], A['rec_sh'], fmt_pct(A['rec_ret']),
                        hist_rank[A['name']], B['name'], hist_rank[B['name']], B['hist_sh'],
                        fmt_pct(B['hist_ret']), rec_rank[B['name']],
                        r['recent'], fmt_pct(r['rec_ret']),
                        r['hist'], fmt_pct(r['hist_ret']), r['score']))
    lines.append('')

    out = os.path.join(SEPARATE, '_TOP15_CONFIG_PAIRS.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', out)


def main():
    legs = leg_metrics()
    rec_rank = dense_ranks(legs, 'rec_sh')
    hist_rank = dense_ranks(legs, 'hist_sh')
    write_period_md(legs, rec_rank, hist_rank)
    write_pairs_md(legs, rec_rank, hist_rank)


if __name__ == '__main__':
    main()
