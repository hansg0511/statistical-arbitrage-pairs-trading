import os, re, csv, json, glob, statistics
from datetime import datetime

GRIDS = [
    ('Core',     '2024-2025', 'diagnosis/05_grid_search'),
    ('SP500',    '2024-2025', 'diagnosis/07_grid_search_sp500'),
    ('Core',     '2015-2020', 'diagnosis/08b_core_12m_sel_2015_2020'),
    ('SP500',    '2015-2020', 'diagnosis/09_sp500_2015_2020'),
]


def fold_stats(out_dir, max_pairs=20):
    """Per-fold trades + pairs aggregates for a run dir.

    Pairs come from the oos_fold_summary.csv 'pairs' column when present,
    else parsed from run.log 'Selected N pairs' lines.
    Returns (trades, pairs, fill_rate) where trades/pairs are {min, mean, max}.
    """
    csv_path = os.path.join(out_dir, 'oos_fold_summary.csv')
    fold_trades = []
    fold_pairs = []
    if os.path.exists(csv_path):
        rows = list(csv.DictReader(open(csv_path)))
        fold_trades = [int(r['trades']) for r in rows]
        if rows and 'pairs' in rows[0]:
            ps = []
            for r in rows:
                v = (r.get('pairs') or '').strip()
                ps.append(int(v) if v else 0)
            if any(ps):
                fold_pairs = ps

    if not fold_pairs:
        log_path = os.path.join(out_dir, 'run.log')
        if os.path.exists(log_path):
            fold_pairs = [int(m) for m in re.findall(r'Selected (\d+) pairs', open(log_path).read())]

    def stats(xs):
        if not xs:
            return {'min': None, 'mean': None, 'max': None}
        return {'min': min(xs), 'mean': statistics.mean(xs), 'max': max(xs)}

    fill_rate = (sum(1 for p in fold_pairs if p >= max_pairs) / len(fold_pairs)) if fold_pairs else 0.0
    return stats(fold_trades), stats(fold_pairs), fill_rate


def analyze_run(out_dir):
    metrics = json.load(open(os.path.join(out_dir, 'metrics.json')))
    name = os.path.basename(out_dir)
    start_date, label = name.split('_', 1)

    max_pairs = metrics.get('max_pairs', 20)
    n_folds = metrics.get('total_folds', 0)
    ts, ps, fill_rate = fold_stats(out_dir, max_pairs)

    return {
        'dir': os.path.basename(out_dir),
        'start': start_date,
        'label': label,
        'universe': metrics.get('universe'),
        'cross_sector': metrics.get('cross_sector'),
        'slide': metrics.get('slide_months'),
        'sharpe': metrics.get('annualized_sharpe', 0),
        'return_pct': metrics.get('annualized_return', 0) * 100,
        'total_trades': metrics.get('total_trades', 0),
        'mean_active': metrics.get('mean_active_trades', 0),
        'total_days': metrics.get('total_days', 0),
        'days_lt10': metrics.get('days_active_lt10', 0),
        'max_pairs': max_pairs,
        'n_folds': n_folds,
        'trades_min': ts['min'], 'trades_mean': ts['mean'], 'trades_max': ts['max'],
        'pairs_min': ps['min'], 'pairs_mean': ps['mean'], 'pairs_max': ps['max'],
        'fill_rate': fill_rate,
    }


def collect_runs(base_dir):
    runs = []
    for d in sorted(glob.glob(os.path.join(base_dir, '*'))):
        if os.path.isdir(d) and os.path.exists(os.path.join(d, 'metrics.json')):
            r = analyze_run(d)
            r['grid'] = base_dir
            runs.append(r)
    return runs


def main():
    out = []
    out.append('# Full Backtest Results — Robust Mean Reversion\n')
    out.append(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}\n')
    out.append('**Setup:** mp=20, pct/pair=4.5%, entryZ=2.2, exitZ=1.0, stopZ=4.5, log-space coint, hr_thresh=0.8')
    out.append('**Source:** existing `metrics.json` + `oos_fold_summary.csv` (+ `run.log` pair parse for pre-`pairs`-column runs). No backtests re-run.\n')
    out.append('**Combo key:** `same/cross_sector`, `slide1m/3m`, `bd7` = 7-day earnings screen, `noscreen` = none.\n')

    all_runs = []
    for universe, period, base in GRIDS:
        runs = collect_runs(base)
        all_runs.extend(runs)
        labels = sorted(set(r['label'] for r in runs), key=lambda l: (l.split('_')[0], l.split('_')[1]))
        dates = sorted(set(r['start'] for r in runs))

        out.append(f'\n---\n\n## {universe} — {period}\n')
        out.append(f'**Runs:** {len(runs)} ({len(labels)} configs x {len(dates)} start dates)\n')

        out.append('\n### Sharpe Pivot (start date x config)\n')
        col_headers = ' | '.join(labels)
        out.append(f'| Start Date | {col_headers} |')
        out.append('|' + '|'.join(['---'] * (1 + len(labels))) + '|')
        for d in dates:
            row = [d]
            for lab in labels:
                vals = [r['sharpe'] for r in runs if r['start'] == d and r['label'] == lab]
                row.append(f"{vals[0]:.2f}" if vals else 'N/A')
            out.append('| ' + ' | '.join(row) + ' |')

        out.append('\n### Per-Run Detail\n')
        out.append('| Start | Config | Sharpe | Ret% | Folds | Trades total | Trades/fold (min-m-mean-max) | Pairs/fold (min-m-mean-max) | Fill-rate% | Active-trades mean | Days<10 act |')
        out.append('|-------|--------|:------:|:----:|:-----:|:------------:|:------------------------------:|:------------------------------:|:----------:|:----------------:|:-----------:|')
        for r in runs:
            tm = f"{r['trades_min']}-{r['trades_mean']:.1f}-{r['trades_max']}" if r['trades_min'] is not None else 'N/A'
            pm = f"{r['pairs_min']}-{r['pairs_mean']:.1f}-{r['pairs_max']}" if r['pairs_min'] is not None else 'N/A'
            out.append(
                f"| {r['start']} | {r['label']} | {r['sharpe']:.2f} | {r['return_pct']:.2f} "
                f"| {r['n_folds']} | {r['total_trades']} | {tm} | {pm} "
                f"| {r['fill_rate']*100:.1f}% | {r['mean_active']:.1f} | {r['days_lt10']}/{r['total_days']} |"
            )

        out.append('\n### Config Aggregates (across start dates)\n')
        out.append('| Config | Runs | Sharpe mean | Std | Min | Max | Trades mean | Pairs mean | Pairs min | Pairs max | Fill-rate% |')
        out.append('|--------|:----:|:-----------:|:---:|:---:|:---:|:-----------:|:----------:|:---------:|:---------:|:----------:|')
        for lab in labels:
            rs = [r for r in runs if r['label'] == lab]
            sh = [r['sharpe'] for r in rs]
            pm = [r['pairs_mean'] for r in rs if r['pairs_mean'] is not None]
            pr = [r['pairs_min'] for r in rs if r['pairs_min'] is not None]
            px = [r['pairs_max'] for r in rs if r['pairs_max'] is not None]
            fr = [r['fill_rate'] for r in rs]
            sd = statistics.stdev(sh) if len(sh) > 1 else 0.0
            out.append(
                f"| {lab} | {len(rs)} | {statistics.mean(sh):.2f} | {sd:.2f} | {min(sh):.2f} | {max(sh):.2f} "
                f"| {statistics.mean([r['total_trades'] for r in rs]):.0f} "
                f"| {statistics.mean(pm):.1f} | {min(pr):.0f} | {max(px):.0f} "
                f"| {statistics.mean(fr)*100:.1f}% |"
            )

    out.append('\n---\n\n## Cross-Grid Aggregate (32 combos)\n')
    out.append('| Universe | Period | Config | Runs | Sharpe mean | Std | Min | Max | Trades mean | Pairs mean | Fill-rate% |')
    out.append('|----------|--------|--------|:----:|:-----------:|:---:|:---:|:---:|:-----------:|:----------:|:----------:|')
    for universe, period, base in GRIDS:
        runs = [r for r in all_runs if r['grid'] == base]
        labels = sorted(set(r['label'] for r in runs), key=lambda l: (l.split('_')[0], l.split('_')[1]))
        for lab in labels:
            rs = [r for r in runs if r['label'] == lab]
            sh = [r['sharpe'] for r in rs]
            pm = [r['pairs_mean'] for r in rs if r['pairs_mean'] is not None]
            fr = [r['fill_rate'] for r in rs]
            sd = statistics.stdev(sh) if len(sh) > 1 else 0.0
            out.append(
                f"| {universe} | {period} | {lab} | {len(rs)} | {statistics.mean(sh):.2f} | {sd:.2f} "
                f"| {min(sh):.2f} | {max(sh):.2f} | {statistics.mean([r['total_trades'] for r in rs]):.0f} "
                f"| {statistics.mean(pm):.1f} | {statistics.mean(fr)*100:.1f}% |"
            )

    out.append('\n')
    path = os.path.join('diagnosis', 'full_results.md')
    with open(path, 'w') as f:
        f.write('\n'.join(out))
    print(f'Written {path} ({len(all_runs)} runs)')


if __name__ == '__main__':
    main()
