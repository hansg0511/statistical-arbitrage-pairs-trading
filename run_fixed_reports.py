"""Write per-section findings.md reports into fixed_diagnosis/<section>/.

Reads metrics.json (trimmed Sharpe/ret) plus recomputes untrimmed Sharpe/ret
from daily_returns.csv so each report shows both the fully-active trading
window and the engine-trimmed headline numbers. Also verifies the actual
trading window per run.

Usage: python run_fixed_reports.py [--section 08b]
"""
import glob, os, json, statistics, argparse
import pandas as pd
import numpy as np
from src.result_validation import validate_run_output

BASE = 'fixed_diagnosis'
SECTIONS = ['05', '06', '07', '08a', '08b', '09a', '09b', '10', '10a', '10b']

META = {
    '05':  dict(universe='core', sel=2, mp=5, pct=0.18, period='recent'),
    '06':  dict(universe='core', sel=2, mp=20, pct=0.045, period='recent'),
    '07':  dict(universe='sp500', sel=2, mp=20, pct=0.045, period='recent'),
    '08a': dict(universe='core', sel=2, mp=20, pct=0.045, period='historical'),
    '08b': dict(universe='core', sel=12, mp=20, pct=0.045, period='historical'),
    '09a': dict(universe='sp500', sel=2, mp=20, pct=0.045, period='historical'),
    '09b': dict(universe='sp500', sel=12, mp=20, pct=0.045, period='historical'),
    '10':  dict(universe='core', sel=2, mp=20, pct=0.25, period='recent'),
    '10a': dict(universe='core', sel=12, mp=20, pct=0.045, period='recent'),
    '10b': dict(universe='sp500', sel=12, mp=20, pct=0.045, period='recent'),
}

CONFIG_ORDER = [
    'same_sector_slide3m_noscreen', 'same_sector_slide3m_bd7',
    'same_sector_slide1m_noscreen', 'same_sector_slide1m_bd7',
    'cross_sector_slide3m_noscreen', 'cross_sector_slide3m_bd7',
    'cross_sector_slide1m_noscreen', 'cross_sector_slide1m_bd7',
]


def load_run(section, sd, label):
    d = os.path.join(BASE, section, f'{sd}_{label}')
    validation = validate_run_output(d)
    if not validation['valid']:
        details = '; '.join(validation['reasons'])
        raise RuntimeError(f'invalid run output {d}: {details}')
    mp = os.path.join(d, 'metrics.json')
    if not os.path.exists(mp):
        return None
    m = json.load(open(mp))
    # untrimmed stats from daily_returns.csv
    csvp = os.path.join(d, 'daily_returns.csv')
    untrimmed_sharpe = untrimmed_ret = None
    first = last = None
    ndays = 0
    if os.path.exists(csvp):
        df = pd.read_csv(csvp).sort_values('date').reset_index(drop=True)
        s = df['daily_return']
        ndays = len(s)
        if ndays > 0:
            untrimmed_sharpe = s.mean() / s.std() * np.sqrt(252) if s.std() > 0 else 0.0
            cum = (1 + s).prod() - 1
            untrimmed_ret = (1 + cum) ** (252 / ndays) - 1
            first, last = str(df['date'].iloc[0]), str(df['date'].iloc[-1])
    return {
        'start': sd, 'label': label,
        'sharpe': m.get('annualized_sharpe', 0),
        'ret': m.get('annualized_return', 0) * 100,
        'trades': m.get('total_trades', 0),
        'at': m.get('mean_active_trades', 0),
        'folds': m.get('total_folds', 0),
        'total_days': m.get('total_days', 0),
        'u_sharpe': untrimmed_sharpe,
        'u_ret': untrimmed_ret * 100 if untrimmed_ret is not None else None,
        'first': first, 'last': last, 'ndays': ndays,
    }


def by_config(section, runs):
    out = {}
    for r in runs:
        out.setdefault(r['label'], []).append(r)
    return out


def config_means(runs):
    labels = []
    for r in runs:
        if r['label'] not in labels:
            labels.append(r['label'])
    rows = []
    for lab in labels:
        vals = [r for r in runs if r['label'] == lab]
        sharpe = statistics.mean(r['sharpe'] for r in vals)
        ret = statistics.mean(r['ret'] for r in vals)
        trades = statistics.mean(r['trades'] for r in vals)
        at = statistics.mean(r['at'] for r in vals)
        u_sharpe = statistics.mean(r['u_sharpe'] for r in vals if r['u_sharpe'] is not None)
        u_ret = statistics.mean(r['u_ret'] for r in vals if r['u_ret'] is not None)
        rows.append({'label': lab, 'sharpe': sharpe, 'ret': ret, 'trades': trades,
                     'at': at, 'u_sharpe': u_sharpe, 'u_ret': u_ret})
    rows.sort(key=lambda x: -x['sharpe'])
    return rows


def write_section(section):
    meta = META[section]
    out_dir = os.path.join(BASE, section)
    runs = []
    for f in sorted(glob.glob(os.path.join(out_dir, '*', 'metrics.json'))):
        d = os.path.dirname(f)
        name = os.path.basename(d)
        sd, label = name.split('_', 1)
        r = load_run(section, sd, label)
        if r:
            runs.append(r)
    if not runs:
        print(f'[skip] {section}: no runs')
        return

    starts = sorted(set(r['start'] for r in runs))
    labels = CONFIG_ORDER
    present_labels = sorted(set(r['label'] for r in runs))
    labels = [l for l in CONFIG_ORDER if l in present_labels] or sorted(present_labels)

    lines = []
    lines.append(f"# Section {section} — {meta['universe']} {meta['sel']}m, mp={meta['mp']}, pct={meta['pct']} ({meta['period']})\n")
    lines.append(f"**Runs:** {len(runs)} | **Starts:** {len(starts)} | **Configs:** {len(labels)}\n")

    # window verification from first run per start
    lines.append("## Trading windows (untrimmed, from daily_returns.csv)\n")
    lines.append("| Start | First trade | Last trade | Days |")
    lines.append("|---|---|---|---|")
    for sd in starts:
        r = next((r for r in runs if r['start'] == sd), None)
        lines.append(f"| {sd} | {r['first']} | {r['last']} | {r['ndays']} |")
    lines.append("")

    lines.append("## Sharpe Pivot (trimmed, per start date)\n")
    lines.append("| Config | " + " | ".join(starts) + " | Mean |")
    lines.append("|---|" + "|".join(["---"] * len(starts)) + "|---|")
    for lab in labels:
        row = [lab]
        vals = []
        for sd in starts:
            v = next((r['sharpe'] for r in runs if r['start'] == sd and r['label'] == lab), None)
            row.append(f"{v:.2f}" if v is not None else 'N/A')
            if v is not None:
                vals.append(v)
        row.append(f"{statistics.mean(vals):.2f}" if vals else 'N/A')
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    lines.append("## Aggregate (trimmed mean per config)\n")
    lines.append("| Config | Sharpe | Ret% | Trades | AT |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in config_means(runs):
        lines.append(f"| {row['label']} | {row['sharpe']:.2f} | {row['ret']:.2f} | {row['trades']:.1f} | {row['at']:.2f} |")
    lines.append("")

    lines.append("## Untrimmed full-window (mean per config)\n")
    lines.append("| Config | Sharpe | Ret% |")
    lines.append("|---|---:|---:|")
    for row in config_means(runs):
        lines.append(f"| {row['label']} | {row['u_sharpe']:.2f} | {row['u_ret']:.2f} |")
    lines.append("")

    best = max(config_means(runs), key=lambda x: x['sharpe'])
    lines.append(f"**Best config (trimmed Sharpe):** `{best['label']}` = {best['sharpe']:.2f} / {best['ret']:.2f}%\n")

    out = os.path.join(out_dir, 'findings.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'wrote {out} ({len(runs)} runs)')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--section', default=None)
    args = parser.parse_args()
    secs = [args.section] if args.section else SECTIONS
    for s in secs:
        write_section(s)


if __name__ == '__main__':
    main()
