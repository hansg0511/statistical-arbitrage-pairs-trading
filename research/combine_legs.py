"""Combine two strategy legs into a single book and compare allocation schemes.

Tests several leg pairs so a book can be chosen that is strong in its own
regime and not terrible elsewhere.

Legs are already-run backtests in fixed_diagnosis/. Each pair defines its
recent-window legs and historical-window legs (aligned windows by construction):
  recent    : 2024-01-02 -> 2025-12-31
  historical: 2015-01-02 -> 2019-12-31  (unlabeled sanity check)

Schemes:
  static50   : 50/50 fixed weights
  voltarget  : weight proportional to 1/sigma (full-window vol), fixed
  momentum   : monthly rebalance, trailing 63d Sharpe signal, +-10% step toward
               the winner, clamped to [0.25, 0.75]

Pure arithmetic over existing return streams -- NO backtest is run.
pnl is bookkeeping-combined (capital = 1M start), not a consolidated trade book.
"""
import os
import math
import glob
import pandas as pd

BASE = 'fixed_diagnosis'
OUT = os.path.join(BASE, '_combined')
LOOKBACK = 63
STEP = 0.10
WMIN, WMAX = 0.25, 0.75

# pair name -> dict: {recent: (secA,startA,cfgA,secB,startB,cfgB,labelA,labelB),
#                      historical: (...)}
PAIRS = {
    'recent-best': {
        'recent': ('06', '2023-11-01', 'same_sector_slide1m_bd7',
                   '10b', '2023-01-01', 'same_sector_slide1m_noscreen',
                   'core-2m same 1m bd7', 'sp500-12m same 1m noscreen'),
        'historical': ('08a', '2014-11-01', 'same_sector_slide1m_bd7',
                       '09b', '2014-01-01', 'same_sector_slide1m_noscreen',
                       'core-2m same 1m bd7', 'sp500-12m same 1m noscreen'),
    },
    'both-era': {
        'recent': ('06', '2023-11-01', 'cross_sector_slide3m_bd7',
                   '10b', '2023-01-01', 'same_sector_slide1m_noscreen',
                   'core-2m cross 3m bd7', 'sp500-12m same 1m noscreen'),
        'historical': ('08a', '2014-11-01', 'cross_sector_slide3m_bd7',
                       '09b', '2014-01-01', 'same_sector_slide1m_noscreen',
                       'core-2m cross 3m bd7', 'sp500-12m same 1m noscreen'),
    },
    'cross-era': {
        'recent': ('07', '2023-11-01', 'cross_sector_slide3m_bd7',
                   '06', '2023-11-01', 'same_sector_slide1m_bd7',
                   'sp500-2m cross 3m bd7', 'core-2m same 1m bd7'),
        'historical': ('09a', '2014-11-01', 'cross_sector_slide3m_bd7',
                       '08a', '2014-11-01', 'same_sector_slide1m_bd7',
                       'sp500-2m cross 3m bd7', 'core-2m same 1m bd7'),
    },
}


def load_leg(sec, start, cfg):
    p = os.path.join(BASE, sec, '%s_%s' % (start, cfg), 'daily_returns.csv')
    df = pd.read_csv(p, parse_dates=['date'])
    df = df.set_index('date')[['daily_return']].rename(columns={'daily_return': 'r'})
    return df['r']


def sharpe(x, periods=252):
    if len(x) == 0:
        return float('nan')
    return x.mean() / x.std() * math.sqrt(periods)


def metrics(returns):
    r = returns.dropna()
    n = len(r)
    ann_ret = (1 + r).prod() ** (252 / n) - 1 if n > 0 else float('nan')
    ann_vol = r.std() * math.sqrt(252)
    sh = sharpe(r)
    dd = (1 + r).cumprod().div((1 + r).cumprod().cummax()) - 1
    return {'ann_ret': ann_ret, 'ann_vol': ann_vol, 'sharpe': sh, 'mdd': dd.min()}


def weight_path_momentum(a, b):
    """Return monthly Series of weight-on-A."""
    w = 0.5
    out = []
    months = a.index.to_period('M').unique()
    for m in months:
        mask = a.index < (m.to_timestamp() + pd.DateOffset(months=1))
        cur_a = a[mask][-LOOKBACK:]
        cur_b = b[mask][-LOOKBACK:]
        sa, sb = sharpe(cur_a), sharpe(cur_b)
        if not math.isnan(sa) and not math.isnan(sb):
            if sa > sb:
                w = min(w + STEP, WMAX)
            elif sb > sa:
                w = max(w - STEP, WMIN)
        out.append((pd.Timestamp(m.to_timestamp()), w))
    return pd.Series(dict(out))


def build_portfolio(a, b, wseries):
    """wseries: date-indexed weight on A (step function). Combine daily returns."""
    w = wseries.reindex(a.index.union(b.index), method='ffill').fillna(0.5)
    r = w * a.reindex(a.index.union(b.index)).fillna(0.0) + \
        (1 - w) * b.reindex(a.index.union(b.index)).fillna(0.0)
    return r.dropna()


def to_csv(returns, pair, window, label):
    d = os.path.join(OUT, pair, window, label)
    os.makedirs(d, exist_ok=True)
    cap = 1_000_000.0
    rows = []
    for ts, r in returns.items():
        pnl = cap * r
        cap += pnl
        rows.append({'date': ts.date(), 'pnl': pnl, 'total_capital': cap, 'daily_return': r})
    pd.DataFrame(rows).to_csv(os.path.join(d, 'daily_returns.csv'), index=False)


def analyze_pair(pair_name, window, spec, report):
    a = load_leg(spec[0], spec[1], spec[2])
    b = load_leg(spec[3], spec[4], spec[5])
    labA, labB = spec[6], spec[7]
    j = pd.concat([a, b], axis=1, keys=['A', 'B']).dropna()
    corr = j['A'].corr(j['B'])

    report.append('| Leg | ann ret | ann vol | Sharpe | mdd |')
    report.append('|---|---:|---:|---:|---:|')
    for k, lab in [('A', labA), ('B', labB)]:
        m = metrics(j[k])
        report.append('| %s | %.2f%% | %.2f%% | %.2f | %.1f%% |'
                      % (lab, m['ann_ret'] * 100, m['ann_vol'] * 100, m['sharpe'], m['mdd'] * 100))
    report.append('')

    r50 = 0.5 * j['A'] + 0.5 * j['B']
    m50 = metrics(r50)
    to_csv(r50, pair_name, window, 'static50')

    volA, volB = j['A'].std(), j['B'].std()
    wv = (1 / volA) / (1 / volA + 1 / volB)
    rvt = wv * j['A'] + (1 - wv) * j['B']
    mvt = metrics(rvt)
    to_csv(rvt, pair_name, window, 'voltarg')

    wmom = weight_path_momentum(j['A'], j['B'])
    rmom = build_portfolio(j['A'], j['B'], wmom)
    mmom = metrics(rmom)
    to_csv(rmom, pair_name, window, 'momentum')

    report.append('| Scheme | weight-on-A | ann ret | ann vol | Sharpe | mdd |')
    report.append('|---|---:|---:|---:|---:|---:|')
    report.append('| static 50/50 | 0.50 | %.2f%% | %.2f%% | %.2f | %.1f%% |'
                  % (m50['ann_ret'] * 100, m50['ann_vol'] * 100, m50['sharpe'], m50['mdd'] * 100))
    report.append('| vol-targeted | %.2f | %.2f%% | %.2f%% | %.2f | %.1f%% |'
                  % (wv, mvt['ann_ret'] * 100, mvt['ann_vol'] * 100, mvt['sharpe'], mvt['mdd'] * 100))
    report.append('| momentum (63d Sharpe, +/-10%% step, 25-75%%) | %.2f-%.2f | %.2f%% | %.2f%% | %.2f | %.1f%% |'
                  % (wmom.min(), wmom.max(), mmom['ann_ret'] * 100, mmom['ann_vol'] * 100,
                     mmom['sharpe'], mmom['mdd'] * 100))
    report.append('')

    wp = pd.DataFrame({'weight_A': wmom})
    os.makedirs(os.path.join(OUT, pair_name, window, 'momentum'), exist_ok=True)
    wp.to_csv(os.path.join(OUT, pair_name, window, 'momentum', 'weight_path.csv'))

    m = j.resample('M').apply(lambda x: (1 + x).prod() - 1)
    r50m = r50.resample('M').apply(lambda x: (1 + x).prod() - 1)
    rvtm = rvt.resample('M').apply(lambda x: (1 + x).prod() - 1)
    rmomm = rmom.resample('M').apply(lambda x: (1 + x).prod() - 1)
    report.append('**Complementarity (monthly):** net book return on months when a leg loses\n')
    report.append('| Leg failing | months | leg mean | 50/50 | vol-targ | momentum |')
    report.append('|---|---:|---:|---:|---:|---:|')
    for legname, col in [('A', 'A'), ('B', 'B')]:
        sub = m[m[col] < 0]
        report.append('| %s | %d | %+.2f%% | %+.2f%% | %+.2f%% | %+.2f%% |'
                      % (legname, len(sub), sub[col].mean() * 100,
                         r50m[sub.index].mean() * 100, rvtm[sub.index].mean() * 100,
                         rmomm[sub.index].mean() * 100))
    both = m[(m['A'] < 0) & (m['B'] < 0)]
    if len(both):
        report.append('| both | %d | A %+.2f%% / B %+.2f%% | %+.2f%% | %+.2f%% | %+.2f%% |'
                      % (len(both), both['A'].mean() * 100, both['B'].mean() * 100,
                         r50m[both.index].mean() * 100, rvtm[both.index].mean() * 100,
                         rmomm[both.index].mean() * 100))
    report.append('')
    return {'static50': m50, 'voltarg': mvt, 'momentum': mmom, 'corr': corr,
            'labA': labA, 'labB': labB}


def main():
    os.makedirs(OUT, exist_ok=True)
    report = []
    report.append('# Combined two-leg book: pair comparison\n')
    report.append('Pure weight arithmetic over existing leg backtests (no backtest run). '
                  'Recent window 2024-01-02..2025-12-31; historical 2015-01-02..2019-12-31 '
                  '(unlabeled sanity check).\n')

    summary = {}
    for pair_name, windows in PAIRS.items():
        report.append('## Pair: %s\n' % pair_name)
        for wname in ['recent', 'historical']:
            spec = windows[wname]
            report.append('### %s window\n' % wname)
            res = analyze_pair(pair_name, wname, spec, report)
            summary[(pair_name, wname)] = res
            report.append('---\n')

    report.append('## Cross-window summary (static 50/50 Sharpe)\n')
    report.append('| Pair | Recent Sharpe | Historical Sharpe | corr(recent) | corr(hist) |')
    report.append('|---|---:|---:|---:|---:|')
    for p in PAIRS:
        r = summary[(p, 'recent')]['static50']['sharpe']
        h = summary[(p, 'historical')]['static50']['sharpe']
        cr = summary[(p, 'recent')]['corr']
        ch = summary[(p, 'historical')]['corr']
        report.append('| %s | %.2f | %.2f | %.2f | %.2f |' % (p, r, h, cr, ch))
    report.append('')
    report.append('**Reading:** a pair that is positive in *both* windows is more '
                  'likely to hold up outside the recent regime. Sharpe is the '
                  'full-window (untrimmed) number.')
    report.append('')
    report.append('**Caveat:** pnl is bookkeeping-combined from two independent leg backtests '
                  '(1M start, weight arithmetic). No consolidated trade log; cross-sleeve '
                  'slippage/cash drag not simulated.')
    report.append('Combined daily_returns.csv per scheme in `fixed_diagnosis/_combined/<pair>/<window>/<scheme>/`.')

    out_path = os.path.join(BASE, '_COMBINED_BOOK.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report) + '\n')
    print('wrote', out_path)
    for f in sorted(glob.glob(os.path.join(OUT, '**', 'daily_returns.csv'), recursive=True)):
        print('  ', f)


if __name__ == '__main__':
    main()
