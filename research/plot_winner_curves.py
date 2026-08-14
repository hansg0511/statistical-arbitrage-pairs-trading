"""Plot consolidated-sweep winners: equity vs S&P500, deployed-by-leg, weight path.

For each mechanism (A, B) and each of its top-5 winners, a 3-panel figure:
  1. equity curves (book + each individual leg + S&P 500, all start=1.0)
  2. deployed capital per leg (k$) over time  ->  how much time each leg holds
  3. momentum weight path (weight_A, monthly step)

Usage: python research/plot_winner_curves.py [--top 5] [--window both|recent|historical]
"""
import os
import json
import argparse
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research.pair_sweep_consolidated import (  # noqa: E402
    get_leg, weight_path_momentum_causal, simulate, metrics, OUT, BASE,
)

SP500 = os.path.join(BASE, '_combined', 'sp500.csv')
CURVES = os.path.join(OUT, 'curves')


def load_sp500():
    df = pd.read_csv(SP500, parse_dates=['date']).set_index('date')['sp500_close']
    return df.sort_index()


def plot_winner(mech, label, window):
    meta = json.load(open(os.path.join(OUT, mech, label, 'pair.json'), encoding='utf-8'))
    sa, ca = meta['leg_a'].split('/', 1)
    sb, cb = meta['leg_b'].split('/', 1)

    a = get_leg(sa, ca, window, 0)
    b = get_leg(sb, cb, window, 0)
    wp = weight_path_momentum_causal(a['ret'], b['ret'])
    rows, ledger, _, _ = simulate({'A': a, 'B': b}, wp, mech, capital=1e6, pct=meta['pct'])
    rr = pd.DataFrame(rows).set_index('date')
    ld = pd.DataFrame(ledger).set_index('date')
    m = metrics(rr['daily_return'])

    dates = rr.index
    sp = load_sp500().reindex(dates).ffill()
    sp = sp / sp.iloc[0]
    book_eq = (1 + rr['daily_return']).cumprod()
    legA_eq = (1 + a['ret'].reindex(dates).ffill().fillna(0.0)).cumprod()
    legB_eq = (1 + b['ret'].reindex(dates).ffill().fillna(0.0)).cumprod()

    fig, axes = plt.subplots(3, 1, figsize=(13, 11), sharex=True)

    ax = axes[0]
    ax.plot(book_eq.index, book_eq.values, label='combined book', lw=1.6, color='C0')
    ax.plot(legA_eq.index, legA_eq.values, label='leg A only', lw=1.1, color='C2')
    ax.plot(legB_eq.index, legB_eq.values, label='leg B only', lw=1.1, color='C3')
    ax.plot(sp.index, sp.values, label='S&P 500', lw=1.1, alpha=0.8, color='#666')
    ax.set_ylabel('equity (start = 1.0)')
    ax.set_title('%s | %s | %s  (Sharpe %.2f, ann %+.1f%%/yr, vol %.1f%%, MDD %.1f%%)'
                 % (mech, label, window, m['sharpe'], m['ann_ret'] * 100,
                    m['ann_vol'] * 100, m['mdd'] * 100))
    ax.legend(loc='best', fontsize=8)
    ax.grid(alpha=0.3)

    ax = axes[1]
    ax.plot(ld.index, ld['legA_deployed'] / 1e3, label='leg A gross notional', lw=1.2)
    ax.plot(ld.index, ld['legB_deployed'] / 1e3, label='leg B gross notional', lw=1.2)
    ax.plot(ld.index, ld['total_deployed'] / 1e3, label='gross notional (long+short)',
            lw=0.9, ls='--', color='k', alpha=0.6)
    ax.plot(rr.index, rr['total_capital'] / 1e3, label='total capital (equity)',
            lw=1.2, ls=':', color='C1')
    ax.set_ylabel('(k$ = 000s)')
    ax.set_title('deployed = gross long+short notional; pairs are cash-neutral, so it can '
                 'exceed the 1,000k capital without using that much cash', fontsize=9)
    ax.legend(loc='best', fontsize=8)
    ax.grid(alpha=0.3)

    ax = axes[2]
    wdaily = wp.reindex(dates).ffill().fillna(0.5)
    ax.step(wdaily.index, wdaily.values, where='post', label='weight_A (target)', color='C0', lw=1.1)
    ax.axhline(0.5, color='k', ls=':', lw=0.8)
    ax.set_ylabel('weight_A')
    ax.set_ylim(0, 1)
    ax.legend(loc='best', fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_xlabel('date')

    fig.tight_layout()
    outdir = os.path.join(CURVES, mech)
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, '%s_%s.png' % (label, window))
    fig.savefig(p, dpi=110)
    plt.close(fig)
    print('wrote %s | %s + %s' % (p, meta['leg_a'], meta['leg_b']))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--top', type=int, default=5)
    ap.add_argument('--window', default='both', choices=['recent', 'historical', 'both'])
    args = ap.parse_args()

    windows = ['recent', 'historical'] if args.window == 'both' else [args.window]
    for mech in ['A', 'B']:
        for i in range(1, args.top + 1):
            label = 'pair_%02d' % i
            if not os.path.exists(os.path.join(OUT, mech, label, 'pair.json')):
                print('skip', mech, label, '(no pair.json)')
                continue
            for window in windows:
                plot_winner(mech, label, window)


if __name__ == '__main__':
    main()
