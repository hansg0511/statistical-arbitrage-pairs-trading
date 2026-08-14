import os, json, statistics
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

CONFIG = 'same_sector_slide1m_bd7'
GRID_DIRS = {
    '2024-2025': 'diagnosis/05_grid_search',
    '2015-2020': 'diagnosis/08b_core_12m_sel_2015_2020',
}
TRIM_MONTHS = 2  # test_months(3) - slide_months(1)
OUT_CSV = 'diagnosis/best_config_returns.csv'
OUT_DIR = 'diagnosis/best_config_plots'
os.makedirs(OUT_DIR, exist_ok=True)

all_rows = []
period_summaries = []

for period, base in GRID_DIRS.items():
    runs = []
    for d in sorted(os.listdir(base)):
        if d.endswith(f'_{CONFIG}'):
            out_dir = os.path.join(base, d)
            mpath = os.path.join(out_dir, 'metrics.json')
            rpath = os.path.join(out_dir, 'daily_returns.csv')
            if os.path.exists(mpath) and os.path.exists(rpath):
                with open(mpath) as f:
                    m = json.load(f)
                runs.append((d, m, rpath))

    dfs = []
    for d, m, rpath in runs:
        df = pd.read_csv(rpath, parse_dates=['date']).set_index('date')['daily_return']
        # trim (test_months - slide_months) from each end to match metrics.json
        if TRIM_MONTHS > 0 and len(df) > 0:
            cs = df.index[0] + pd.DateOffset(months=TRIM_MONTHS)
            ce = df.index[-1] - pd.DateOffset(months=TRIM_MONTHS)
            df = df[(df.index >= cs) & (df.index <= ce)]
        out = pd.DataFrame({
            'daily_return': df,
            'equity': (1 + df).cumprod(),
            'drawdown': ((1 + df).cumprod() / (1 + df).cumprod().cummax() - 1),
        })
        out.index.name = 'date'
        out = out.reset_index()
        out.insert(0, 'start', d[:10])
        out.insert(1, 'period', period)
        dfs.append(out)
        all_rows.append(out)

    merged = pd.concat(dfs, ignore_index=True)

    # Run-level summary (from trimmed series, matches metrics.json)
    for d, m, rpath in runs:
        df = pd.read_csv(rpath, parse_dates=['date']).set_index('date')['daily_return']
        if TRIM_MONTHS > 0 and len(df) > 0:
            cs = df.index[0] + pd.DateOffset(months=TRIM_MONTHS)
            ce = df.index[-1] - pd.DateOffset(months=TRIM_MONTHS)
            df = df[(df.index >= cs) & (df.index <= ce)]
        eq = (1 + df).cumprod()
        cum = eq.iloc[-1] - 1
        ann = (1 + cum) ** (252 / len(df)) - 1
        vol = df.std() * np.sqrt(252)
        sharpe = df.mean() / df.std() * np.sqrt(252) if df.std() > 0 else 0
        period_summaries.append({
            'period': period,
            'start': d[:10],
            'days': len(df),
            'total_return_pct': cum * 100,
            'ann_return_pct': ann * 100,
            'ann_vol_pct': vol * 100,
            'sharpe': sharpe,
            'max_dd_pct': (eq / eq.cummax() - 1).min() * 100,
            'trades': m['total_trades'],
        })

    # Plot: one panel per start date
    fig, axes = plt.subplots(len(runs), 1, figsize=(10, 2.2 * len(runs)), squeeze=False)
    fig.suptitle(f'{CONFIG} — Core {period} (entryZ=2.2, exitZ=1.0, bd7 earnings screen)', fontsize=13, y=0.995)
    for ax, (d, m, rpath) in zip(axes[:, 0], runs):
        sub = merged[merged['start'] == d[:10]]
        ax.plot(sub['date'], sub['equity'], lw=1.2)
        ax.axhline(1.0, color='gray', lw=0.6, ls='--')
        ax.set_title(f"start {d[:10]}  |  Sharpe {m['annualized_sharpe']:.2f}  |  ann ret {m['annualized_return']*100:.2f}%  |  {len(sub)} days", fontsize=9)
        ax.set_ylabel('Equity ($/ $1)')
        ax.grid(alpha=0.3)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(OUT_DIR, f'equity_{period}.png'), dpi=130)
    plt.close(fig)

all_df = pd.concat(all_rows, ignore_index=True)
all_df.to_csv(OUT_CSV, index=False)

print('=' * 88)
print(f'Best config: {CONFIG} (core universe, bd7 earnings screen, trimmed {TRIM_MONTHS}m per end)')
print(f'CSV: {OUT_CSV} ({len(all_df)} daily rows)')
print('Plots:')
for f in sorted(os.listdir(OUT_DIR)):
    print('  ', os.path.join(OUT_DIR, f))
print()
print(f"{'Period':<10} {'Start':<12} {'Days':>5} {'Total%':>8} {'AnnRet%':>8} {'AnnVol%':>7} {'Sharpe':>6} {'MaxDD%':>7} {'Trades':>6}")
for s in sorted(period_summaries, key=lambda r: (r['period'], r['start'])):
    print(f"{s['period']:<10} {s['start']:<12} {s['days']:>5} {s['total_return_pct']:>8.2f} {s['ann_return_pct']:>8.2f} {s['ann_vol_pct']:>7.2f} {s['sharpe']:>6.2f} {s['max_dd_pct']:>7.1f} {s['trades']:>6}")
print()
for period in GRID_DIRS:
    ss = [s for s in period_summaries if s['period'] == period]
    sh = [s['sharpe'] for s in ss]
    print(f"{period}: mean Sharpe {statistics.mean(sh):.2f} +/- {statistics.stdev(sh):.2f}")
