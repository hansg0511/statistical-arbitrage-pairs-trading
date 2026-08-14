"""Systematic pair sweep: every 2-strategy combination scored on both windows.

A "strategy" is (universe, sel_months, config) with a recent run (5 starts) and
a historical run (1 start):
  core-2m  : recent=06, hist=08a
  sp500-2m : recent=07, hist=09a
  core-12m : recent=10a, hist=08b
  sp500-12m: recent=10b, hist=09b

For each pair we build a 50/50 combined book:
  recent : mean combined Sharpe over the 5 aligned start-pairs
  hist   : combined Sharpe on the single historical window
Then rank pairs by max(min(recent_sh, hist_sh)) -- "strong in its regime, not
terrible in the other". No hand-picking.

Usage: python research/pair_sweep.py [--top N] [--momentum]
"""
import os
import math
import argparse
import itertools
import warnings
import pandas as pd

warnings.filterwarnings('ignore', category=RuntimeWarning)

BASE = 'fixed_diagnosis'
CFGS = ['same_sector_slide3m_noscreen', 'same_sector_slide3m_bd7',
        'same_sector_slide1m_noscreen', 'same_sector_slide1m_bd7',
        'cross_sector_slide3m_noscreen', 'cross_sector_slide3m_bd7',
        'cross_sector_slide1m_noscreen', 'cross_sector_slide1m_bd7']

# 2m recent starts and 12m recent starts, aligned by index (both trade from
# start+sel_months -> identical calendar windows).
STARTS_2M = ['2023-11-01', '2023-12-01', '2024-01-01', '2024-02-01', '2024-03-01']
STARTS_12M = ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01']

# strategy -> (recent_section, hist_section, recent_start_list)
STRATEGIES = {
    'core-2m':  ('06', '08a', STARTS_2M),
    'sp500-2m': ('07', '09a', STARTS_2M),
    'core-12m': ('10a', '08b', STARTS_12M),
    'sp500-12m': ('10b', '09b', STARTS_12M),
}

LOOKBACK = 63
STEP = 0.10
WMIN, WMAX = 0.25, 0.75


def sharpe(x, periods=252):
    x = x.dropna()
    if len(x) == 0:
        return float('nan')
    return x.mean() / x.std() * math.sqrt(periods)


def load(sec, start, cfg):
    p = os.path.join(BASE, sec, '%s_%s' % (start, cfg), 'daily_returns.csv')
    df = pd.read_csv(p, parse_dates=['date']).set_index('date')
    return df['daily_return']


def weight_path_momentum(a, b):
    w = 0.5
    out = []
    for m in a.index.to_period('M').unique():
        cutoff = m.to_timestamp() + pd.DateOffset(months=1)
        sa = sharpe(a[a.index < cutoff][-LOOKBACK:])
        sb = sharpe(b[b.index < cutoff][-LOOKBACK:])
        if not math.isnan(sa) and not math.isnan(sb):
            if sa > sb:
                w = min(w + STEP, WMAX)
            elif sb > sa:
                w = max(w - STEP, WMIN)
        out.append((pd.Timestamp(m.to_timestamp()), w))
    return pd.Series(dict(out))


def combine(a, b, wseries):
    w = wseries.reindex(a.index.union(b.index), method='ffill').fillna(0.5)
    r = w * a.reindex(a.index.union(b.index)).fillna(0.0) + \
        (1 - w) * b.reindex(a.index.union(b.index)).fillna(0.0)
    return r.dropna()


def pair_metrics(strat_a, cfg_a, strat_b, cfg_b, use_momentum=False):
    """Return (recent_mean_sh, recent_range, hist_sh, hist_ret)."""
    rsec_a, hsec_a, starts_a = STRATEGIES[strat_a]
    rsec_b, hsec_b, starts_b = STRATEGIES[strat_b]

    # recent: 5 aligned start-pairs (index-aligned; both trade same windows)
    recent_shs = []
    for sa, sb in zip(starts_a, starts_b):
        a = load(rsec_a, sa, cfg_a)
        b = load(rsec_b, sb, cfg_b)
        if use_momentum:
            wm = weight_path_momentum(a, b)
            r = combine(a, b, wm)
        else:
            r = 0.5 * a.reindex(a.index.union(b.index)).fillna(0.0) + \
                0.5 * b.reindex(a.index.union(b.index)).fillna(0.0)
            r = r.dropna()
        recent_shs.append(sharpe(r))
    recent_mean = sum(recent_shs) / len(recent_shs)

    # historical: single aligned window
    a = load(hsec_a, '2014-11-01' if starts_a is STARTS_2M else '2014-01-01', cfg_a)
    b = load(hsec_b, '2014-11-01' if starts_b is STARTS_2M else '2014-01-01', cfg_b)
    if use_momentum:
        wm = weight_path_momentum(a, b)
        r = combine(a, b, wm)
    else:
        r = 0.5 * a.reindex(a.index.union(b.index)).fillna(0.0) + \
            0.5 * b.reindex(a.index.union(b.index)).fillna(0.0)
        r = r.dropna()
    hist_sh = sharpe(r)
    n = len(r)
    hist_ret = (1 + r).prod() ** (252 / n) - 1 if n > 0 else float('nan')

    return recent_mean, (min(recent_shs), max(recent_shs)), hist_sh, hist_ret


def combined_series(strat_a, cfg_a, strat_b, cfg_b, window, use_momentum):
    """Return the combined daily return Series for one window ('recent'|'historical')."""
    rsec_a, hsec_a, starts_a = STRATEGIES[strat_a]
    rsec_b, hsec_b, starts_b = STRATEGIES[strat_b]
    if window == 'recent':
        a = load(rsec_a, starts_a[0], cfg_a)
        b = load(rsec_b, starts_b[0], cfg_b)
    else:
        a = load(hsec_a, '2014-11-01' if starts_a is STARTS_2M else '2014-01-01', cfg_a)
        b = load(hsec_b, '2014-11-01' if starts_b is STARTS_2M else '2014-01-01', cfg_b)
    if use_momentum:
        wm = weight_path_momentum(a, b)
        return combine(a, b, wm)
    return 0.5 * a.reindex(a.index.union(b.index)).fillna(0.0) + \
        0.5 * b.reindex(a.index.union(b.index)).fillna(0.0)


def write_combined_csv(strat_a, cfg_a, strat_b, cfg_b, window, label, use_momentum):
    r = combined_series(strat_a, cfg_a, strat_b, cfg_b, window, use_momentum).dropna()
    d = os.path.join(BASE, '_combined', 'sweep_%s' % label, window)
    os.makedirs(d, exist_ok=True)
    cap = 1_000_000.0
    rows = []
    for ts, rv in r.items():
        pnl = cap * rv
        cap += pnl
        rows.append({'date': ts.date(), 'pnl': pnl, 'total_capital': cap, 'daily_return': rv})
    pd.DataFrame(rows).to_csv(os.path.join(d, 'daily_returns.csv'), index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--top', type=int, default=20)
    ap.add_argument('--momentum', action='store_true')
    ap.add_argument('--report', action='store_true', help='write _COMBINED_BOOK.md + winner CSVs')
    args = ap.parse_args()

    legs = [(s, c) for s in STRATEGIES for c in CFGS]
    results = []
    for (sa, ca), (sb, cb) in itertools.combinations(legs, 2):
        rm, rng, hs, hr = pair_metrics(sa, ca, sb, cb, use_momentum=args.momentum)
        if math.isnan(hs):
            continue
        results.append({
            'A': '%s/%s' % (sa, ca), 'B': '%s/%s' % (sb, cb),
            'recent': rm, 'r_lo': rng[0], 'r_hi': rng[1],
            'hist': hs, 'hist_ret': hr * 100, 'score': min(rm, hs),
        })

    results.sort(key=lambda x: x['score'], reverse=True)
    scheme = 'momentum' if args.momentum else 'static50'
    print('Scheme: %s | %d pairs' % (scheme, len(results)))
    print('%-58s | %6s | %9s | %6s | %7s' % ('PAIR', 'recent', 'range', 'hist', 'score'))
    print('-' * 100)
    for r in results[:args.top]:
        print('%-58s | %6.2f | %5.2f-%5.2f | %6.2f | %7.2f'
              % (r['A'] + '  +  ' + r['B'], r['recent'], r['r_lo'], r['r_hi'],
                 r['hist'], r['score']))
    print()
    print('Top 5 by RECENT only:')
    for r in sorted(results, key=lambda x: x['recent'], reverse=True)[:5]:
        print('  %-58s recent=%.2f hist=%.2f' % (r['A'] + ' + ' + r['B'], r['recent'], r['hist']))
    print('Top 5 by HIST only:')
    for r in sorted(results, key=lambda x: x['hist'], reverse=True)[:5]:
        print('  %-58s recent=%.2f hist=%.2f' % (r['A'] + ' + ' + r['B'], r['recent'], r['hist']))

    if args.report:
        winners = results[:5]
        lines = []
        lines.append('# Combined two-leg book: systematic pair sweep (%s)\n' % scheme)
        lines.append('All %d strategy pairs scored on both windows. Recent = mean Sharpe over the '
                     '5 aligned start-pairs (2024-01-02..2025-12-31); historical = single aligned '
                     'window (2015-01-02..2019-12-31). Score = min(recent, hist) Sharpe — "strong in '
                     'its regime, not terrible in the other".\n' % len(results))
        lines.append('## Top 20 pairs\n')
        lines.append('| Pair | Recent | Range | Hist | Score |')
        lines.append('|---|---:|---:|---:|---:|')
        for r in results[:20]:
            lines.append('| %s + %s | %.2f | %.2f–%.2f | %.2f | %.2f |'
                         % (r['A'], r['B'], r['recent'], r['r_lo'], r['r_hi'], r['hist'], r['score']))
        lines.append('')
        lines.append('## Top 5 by recent only\n')
        for r in sorted(results, key=lambda x: x['recent'], reverse=True)[:5]:
            lines.append('- %s + %s: recent %.2f, hist %.2f'
                         % (r['A'], r['B'], r['recent'], r['hist']))
        lines.append('')
        lines.append('## Top 5 by historical only\n')
        for r in sorted(results, key=lambda x: x['hist'], reverse=True)[:5]:
            lines.append('- %s + %s: recent %.2f, hist %.2f'
                         % (r['A'], r['B'], r['recent'], r['hist']))
        lines.append('')
        lines.append('## Winners — combined daily_returns.csv written\n')
        lines.append('CSVs at `fixed_diagnosis/_combined/sweep_<scheme>/<window>/daily_returns.csv`.')
        for i, r in enumerate(winners):
            label = '%s_%02d' % (scheme, i + 1)
            a_strat, a_cfg = r['A'].split('/', 1)
            b_strat, b_cfg = r['B'].split('/', 1)
            write_combined_csv(a_strat, a_cfg, b_strat, b_cfg, 'recent', label, args.momentum)
            write_combined_csv(a_strat, a_cfg, b_strat, b_cfg, 'historical', label, args.momentum)
            lines.append('- **%d.** `%s` + `%s` → recent %.2f, hist %.2f (label `%s`)'
                         % (i + 1, r['A'], r['B'], r['recent'], r['hist'], label))
        lines.append('')
        lines.append('**Caveat:** pnl is bookkeeping-combined from existing leg backtests '
                     '(1M start, weight arithmetic). No consolidated trade log; cross-sleeve '
                     'slippage/cash drag not simulated.')
        out_path = os.path.join(BASE, '_COMBINED_BOOK.md')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        print('wrote', out_path)


if __name__ == '__main__':
    main()
