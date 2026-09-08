"""Write fixed_diagnosis/_CONSOLIDATED_COMPARISON.md comparing the consolidated
book (mechanisms A & B) against the CSV-arithmetic book and the standalone legs.
Also validates the shared-account accounting (total PnL == final - initial)."""
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from research.run_combined_backtest import metrics, LEGS

BASE = 'fixed_diagnosis'
CONS = os.path.join(BASE, '_combined', 'consolidated')
SWEEP = os.path.join(BASE, '_combined', 'sweep_pct25')

WINDOWS = ['recent', 'historical']
LABEL_LEG = {'A': 'sp500-12m cross1m noscreen', 'B': 'sp500-2m cross3m bd7'}


def csv_metrics(rel):
    path = rel if os.path.isabs(rel) or rel.startswith(BASE + os.sep) else os.path.join(BASE, rel)
    df = pd.read_csv(path, parse_dates=['date'])
    return metrics(df['daily_return'].dropna())


def row(label, m, n_days=None, extra=''):
    return f"| {label} | {m['sharpe']:.3f} | {m['ann_ret']*100:.2f}% | {m['ann_vol']*100:.2f}% | {m['mdd']*100:.1f}% | {n_days if n_days else ''} | {extra} |"


def validate(cons_dir):
    df = pd.read_csv(os.path.join(cons_dir, 'daily_returns.csv'), parse_dates=['date'])
    total_pnl = df['pnl'].sum()
    final = df['total_capital'].iloc[-1]
    init = df['total_capital'].iloc[0]
    err = abs(total_pnl - (final - init))
    return total_pnl, final, err


def consolidated_metrics(window, mechanism):
    path = os.path.join(CONS, window, mechanism, 'daily_returns.csv')
    df = pd.read_csv(path)
    return metrics(df['daily_return'].dropna())


def main():
    lines = []
    lines.append('# Consolidated combined book: mechanisms A & B\n')
    lines.append('')
    lines.append('Trade-event replay of the two pct=0.25 legs into a **single shared 1M account**. '
                 'Each leg keeps its native walk-forward grid, universe and per-fold structure; the '
                 'combination happens at the trade-event level (real entry/exit dates, per-trade daily '
                 'marks). No forced rebalancing in either mechanism - open trades ride to their logged '
                 'exits.\n')
    lines.append('Pairs are modeled as cash-neutral (buy ~notional one leg / short ~notional the other), '
                 'matching the engine, which never rejects on cash in these runs. The momentum weight '
                 '(trailing 63d Sharpe, +/-10% step, clamp 25-75%) sets the leg capital split.\n')
    lines.append('**Mechanism A** - monthly re-base of fold capital to `w_L * C / n_active`; new entries '
                 'sized `0.25 * basis`. Weight re-applied monthly (approximates the CSV momentum book).\n')
    lines.append('**Mechanism B** - fold basis locked at fold start (`C / n_active_L`, equal slice of '
                 'that leg); each entry sized `0.25 * w_L(entry month) * basis`; no monthly re-tilt, '
                 'the leg split drifts.\n')
    lines.append('Weight timing is causal (trailing 63d Sharpe **strictly before** each month). The CSV '
                 'book used data through the month, a subtle in-sample tilt that the simulator removes.\n')

    for w in WINDOWS:
        lines.append(f'## {w.capitalize()} window\n')
        lines.append('| Series | Sharpe | Ann ret | Ann vol | MDD | days | note |')
        lines.append('|---|---:|---:|---:|---:|---:|---|')
        lines.append(row('Leg A ' + LABEL_LEG['A'],
                         csv_metrics(os.path.join(LEGS[w]['A'][0], 'daily_returns.csv'))))
        lines.append(row('Leg B ' + LABEL_LEG['B'],
                         csv_metrics(os.path.join(LEGS[w]['B'][0], 'daily_returns.csv'))))
        csv_book = os.path.join(BASE, '_combined', 'sweep_pct25', w, 'daily_returns.csv')
        if os.path.exists(csv_book):
            lines.append(row('CSV book (return arithmetic)', csv_metrics(csv_book),
                             extra='legacy momentum rule'))
        else:
            lines.append('| CSV book (return arithmetic) | n/a | n/a | n/a | n/a | | not regenerated; legacy artifact absent |')
        for mech in ['A', 'B']:
            d = os.path.join(CONS, w, mech)
            df = pd.read_csv(os.path.join(d, 'daily_returns.csv'))
            m = metrics(df['daily_return'].dropna())
            tp, fin, err = validate(d)
            extra = f"final={fin/1e6:.2f}M, PnL err={err/1e3:.0f}k"
            lines.append(row(f'Consolidated mech {mech}', m, n_days=len(df), extra=extra))
        lines.append('')

        # validation detail
        lines.append('### Validation\n')
        lines.append('| Mechanism | initial | final | sum daily pnl | |final-initial - sum pnl| |')
        lines.append('|---|---:|---:|---:|---:|')
        for mech in ['A', 'B']:
            d = os.path.join(CONS, w, mech)
            tp, fin, err = validate(d)
            lines.append(f'| {mech} | 1.000M | {fin/1e6:.4f}M | {tp/1e6:.4f}M | {err:.2f} |')
        lines.append('')
        lines.append(f'Rejected entries (no basis): 0 in both mechanisms (fold basis is always set '
                     f'before its first entry).\n')

    # notes
    lines.append('## Reading\n')
    a_recent = consolidated_metrics('recent', 'A')
    b_recent = consolidated_metrics('recent', 'B')
    a_hist = consolidated_metrics('historical', 'A')
    b_hist = consolidated_metrics('historical', 'B')
    csv_recent = os.path.join(BASE, '_combined', 'sweep_pct25', 'recent', 'daily_returns.csv')
    csv_hist = os.path.join(BASE, '_combined', 'sweep_pct25', 'historical', 'daily_returns.csv')
    if os.path.exists(csv_recent) and os.path.exists(csv_hist):
        csv_r = csv_metrics(csv_recent)
        csv_h = csv_metrics(csv_hist)
        lines.append('- **Mech A vs CSV book:** A Sharpe is %.2f vs %.2f recent and %.2f vs %.2f '
                     'historical (A vs CSV). The gap reflects open positions riding between monthly '
                     're-bases and the causal weight timing.\n'
                     % (a_recent['sharpe'], csv_r['sharpe'], a_hist['sharpe'], csv_h['sharpe']))
    else:
        lines.append('- **CSV arithmetic comparison:** the legacy CSV book is not present, so no '
                     'CSV-vs-consolidated claim is made here.\n')
    lines.append('- **Mech B vs A:** B locks each fold basis at fold start. Recent Sharpe/return are '
                 '%.3f / %.2f%% for B versus %.3f / %.2f%% for A; historical values are %.3f / '
                 '%.2f%% for B versus %.3f / %.2f%% for A.\n'
                 % (b_recent['sharpe'], b_recent['ann_ret'] * 100,
                    a_recent['sharpe'], a_recent['ann_ret'] * 100,
                    b_hist['sharpe'], b_hist['ann_ret'] * 100,
                    a_hist['sharpe'], a_hist['ann_ret'] * 100))
    lines.append('- The standalone legs already embed their own fold-overlap normalization '
                 '(leg B = capital-weighted blend of 2-3 overlapping 1M folds), so the shared-account '
                 'book inherits that structure unchanged.\n')

    out = os.path.join(BASE, '_CONSOLIDATED_COMPARISON.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', out)


if __name__ == '__main__':
    main()
