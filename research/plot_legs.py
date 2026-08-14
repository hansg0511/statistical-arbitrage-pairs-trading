"""Plot equity curves of two strategy legs on the same graph.

Usage: python research/plot_legs.py [--window recent|historical] [--combined] [--pct25] [--sp500]
"""
import os
import math
import argparse
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = 'fixed_diagnosis'

# (section, start, config, label)
PAIRS = {
    'recent': [
        ('06', '2023-11-01', 'cross_sector_slide3m_bd7', 'core-2m cross 3m bd7'),
        ('10b', '2023-01-01', 'cross_sector_slide1m_noscreen', 'sp500-12m cross 1m noscreen'),
    ],
    'historical': [
        ('08a', '2014-11-01', 'cross_sector_slide3m_bd7', 'core-2m cross 3m bd7'),
        ('09b', '2014-01-01', 'cross_sector_slide1m_noscreen', 'sp500-12m cross 1m noscreen'),
    ],
}

# (start, config, label) under _pct25/
PCT25 = {
    'recent': [
        ('2023-11-01', 'cross_sector_slide3m_bd7', 'core-2m cross 3m bd7'),
        ('2023-01-01', 'cross_sector_slide1m_noscreen', 'sp500-12m cross 1m noscreen'),
    ],
    'historical': [
        ('2014-11-01', 'cross_sector_slide3m_bd7', 'core-2m cross 3m bd7'),
        ('2014-01-01', 'cross_sector_slide1m_noscreen', 'sp500-12m cross 1m noscreen'),
    ],
}

LOOKBACK = 63
STEP = 0.10
WMIN, WMAX = 0.25, 0.75


def load(path):
    df = pd.read_csv(path, parse_dates=['date']).set_index('date')
    return df['daily_return']


def sp500_buy_hold():
    ff = pd.read_pickle('research/ff_factors/ff_daily.pkl')
    return (ff['Mkt-RF'] + ff['RF']).dropna()


def sharpe(x):
    x = x.dropna()
    if len(x) == 0:
        return float('nan')
    return x.mean() / x.std() * math.sqrt(252)


def weight_path_momentum(a, b):
    w = 0.5
    out = []
    for m in a.index.to_period('M').unique():
        cutoff = m.to_timestamp() + pd.DateOffset(months=1)
        sa = sharpe(a[a.index < cutoff].tail(LOOKBACK))
        sb = sharpe(b[b.index < cutoff].tail(LOOKBACK))
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


def write_combined_csv(r, label, window):
    d = os.path.join(BASE, '_combined', label, window)
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
    ap.add_argument('--window', default='recent', choices=['recent', 'historical'])
    ap.add_argument('--out', default=None)
    ap.add_argument('--combined', action='store_true',
                    help='overlay the combined momentum book (sweep_momentum_02)')
    ap.add_argument('--pct25', action='store_true',
                    help='use pct=0.25 runs from _pct25/ instead of the pct=0.045 grids')
    ap.add_argument('--sp500', action='store_true',
                    help='overlay S&P 500 buy-and-hold (Mkt-RF + RF from FF daily factors)')
    args = ap.parse_args()

    if args.pct25:
        legs = []
        for sd, cfg, lab in PCT25[args.window]:
            p = os.path.join(BASE, '_pct25', '%s_%s' % (sd, cfg), 'daily_returns.csv')
            legs.append((load(p), lab))
    else:
        legs = []
        for sec, sd, cfg, lab in PAIRS[args.window]:
            p = os.path.join(BASE, sec, '%s_%s' % (sd, cfg), 'daily_returns.csv')
            legs.append((load(p), lab))

    plt.figure(figsize=(11, 5.5))
    a, labA = legs[0]
    b, labB = legs[1]
    for r, lab in legs:
        eq = (1 + r).cumprod()
        plt.plot(eq.index, eq.values, label='%s  (final %.2f)' % (lab, eq.iloc[-1]))

    if args.sp500:
        mkt = sp500_buy_hold()
        x0 = min(r.index.min() for r, _ in legs)
        x1 = max(r.index.max() for r, _ in legs)
        mkt = mkt.loc[x0:x1]
        eq_m = (1 + mkt).cumprod()
        plt.plot(eq_m.index, eq_m.values, color='darkred', lw=1.6, ls='--',
                 label='S&P 500 buy & hold  (final %.2f)' % eq_m.iloc[-1])

    plot_combined = args.combined
    if args.pct25:
        wm = weight_path_momentum(a, b)
        rmom = combine(a, b, wm)
        eq = (1 + rmom).cumprod()
        plt.plot(eq.index, eq.values, color='black', lw=2.2, ls='-',
                 label='combined momentum  (final %.2f)' % eq.iloc[-1])
        # static 50/50 baseline (shows the rotation's contribution)
        r50 = 0.5 * a.reindex(a.index.union(b.index)).fillna(0.0) + \
            0.5 * b.reindex(a.index.union(b.index)).fillna(0.0)
        eq50 = (1 + r50).cumprod()
        plt.plot(eq50.index, eq50.values, color='gray', lw=1.4, ls='--',
                 label='static 50/50  (final %.2f)' % eq50.iloc[-1])
        write_combined_csv(rmom, 'sweep_pct25', args.window)
        plot_combined = True
    elif args.combined:
        cp = os.path.join(BASE, '_combined', 'sweep_momentum_02', args.window, 'daily_returns.csv')
        df = pd.read_csv(cp, parse_dates=['date']).set_index('date')
        eq = (1 + df['daily_return']).cumprod()
        plt.plot(eq.index, eq.values, color='black', lw=2.2, ls='-',
                 label='combined momentum  (final %.2f)' % eq.iloc[-1])

    plt.axhline(1.0, color='gray', lw=0.8, ls='--')
    tag = '  (with combined book)' if plot_combined else ''
    pct_tag = '  (pct=0.25)' if args.pct25 else ''
    sp_tag = '  (vs S&P 500)' if args.sp500 else ''
    plt.title('Equity curves — %s window%s%s%s' % (args.window, tag, pct_tag, sp_tag))
    plt.ylabel('Growth of $1')
    plt.legend(loc='best')
    plt.grid(alpha=0.3)
    plt.tight_layout()

    name = 'legs_%s.png' % args.window
    if plot_combined:
        name = 'legs_combined_%s.png' % args.window
    if args.pct25:
        name = 'legs_pct25_%s.png' % args.window
    out = args.out or os.path.join(BASE, '_combined', name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    plt.savefig(out, dpi=150)
    print('saved', out)


if __name__ == '__main__':
    main()
