import subprocess, json, os, sys, statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from run_full_results import fold_stats

START_DATES = ['2023-12-01', '2023-12-15', '2024-01-01', '2024-01-15', '2024-02-01']
END = '2026-01-01'
BASE_DIR = 'diagnosis/05_grid_search'
EARNINGS_CACHE = 'research/earnings_cache/earnings_dates.pkl'
os.makedirs(BASE_DIR, exist_ok=True)

MAX_PAIRS = 20
PCT_PER_PAIR = 0.045

GRID = [
    # (label, extra_args)
    ('same_sector_slide3m_noscreen', []),
    ('same_sector_slide3m_bd7',      ['--earnings_screen', '--earnings_block_days', '7', '--earnings_cache', EARNINGS_CACHE]),
    ('same_sector_slide1m_noscreen', ['--slide_months', '1']),
    ('same_sector_slide1m_bd7',      ['--slide_months', '1', '--earnings_screen', '--earnings_block_days', '7', '--earnings_cache', EARNINGS_CACHE]),
    ('cross_sector_slide3m_noscreen', ['--cross_sector', '--return_divergence', '0.10']),
    ('cross_sector_slide3m_bd7',      ['--cross_sector', '--return_divergence', '0.10', '--earnings_screen', '--earnings_block_days', '7', '--earnings_cache', EARNINGS_CACHE]),
    ('cross_sector_slide1m_noscreen', ['--cross_sector', '--return_divergence', '0.10', '--slide_months', '1']),
    ('cross_sector_slide1m_bd7',      ['--cross_sector', '--return_divergence', '0.10', '--slide_months', '1', '--earnings_screen', '--earnings_block_days', '7', '--earnings_cache', EARNINGS_CACHE]),
]

results = []
lock = __import__('threading').Lock()

def run_job(sd, label, extra_args):
    out_dir = os.path.join(BASE_DIR, f'{sd}_{label}')
    os.makedirs(out_dir, exist_ok=True)

    cmd = [
        sys.executable, 'run_backtest_parallel.py',
        '--profile', 'baseline',
        '--start', sd,
        '--end', END,
        '--output', out_dir,
        '--no-earnings_screen',
        '--max_pairs', str(MAX_PAIRS),
        '--pct_per_pair', str(PCT_PER_PAIR),
    ] + extra_args

    print(f"\n[START] {sd} {label}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

    metrics_path = os.path.join(out_dir, 'metrics.json')
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            m = json.load(f)
        rec = {
            'start': sd,
            'label': label,
            'return_pct': round(m.get('annualized_return', 0) * 100, 2),
            'sharpe': round(m.get('annualized_sharpe', 0), 2),
            'trades': m.get('total_trades', 0),
            'mean_at': round(m.get('mean_active_trades', 0), 2),
        }
        with lock:
            results.append(rec)
        print(f"  [DONE] {sd} {label}: Sharpe={rec['sharpe']}, Trades={rec['trades']}, AT={rec['mean_at']}")
    else:
        print(f"  [FAIL] {sd} {label}: no metrics.json")
        if result.returncode != 0:
            print(f"  STDERR: {result.stderr[-1000:] if result.stderr else 'N/A'}")

    log_path = os.path.join(out_dir, 'run.log')
    with open(log_path, 'w') as f:
        f.write(result.stdout or '')
        if result.stderr:
            f.write('\n--- STDERR ---\n')
            f.write(result.stderr)

# Load existing results
for sd in START_DATES:
    for label, _ in GRID:
        out_dir = os.path.join(BASE_DIR, f'{sd}_{label}')
        metrics_path = os.path.join(out_dir, 'metrics.json')
        if os.path.exists(metrics_path):
            with open(metrics_path) as f:
                m = json.load(f)
            rec = {
                'start': sd,
                'label': label,
                'return_pct': round(m.get('annualized_return', 0) * 100, 2),
                'sharpe': round(m.get('annualized_sharpe', 0), 2),
                'trades': m.get('total_trades', 0),
                'mean_at': round(m.get('mean_active_trades', 0), 2),
            }
            results.append(rec)

# Build job list skipping existing
jobs = []
for sd in START_DATES:
    for label, extra_args in GRID:
        out_dir = os.path.join(BASE_DIR, f'{sd}_{label}')
        if not os.path.exists(os.path.join(out_dir, 'metrics.json')):
            jobs.append((sd, label, extra_args))

print(f"Grid: {len(GRID)} configs x {len(START_DATES)} dates = {len(GRID) * len(START_DATES)} total")
print(f"Existing: {len(results)}  New: {len(jobs)} (running 2 at a time)")
print(f"{'='*60}")

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {executor.submit(run_job, sd, label, ea): (sd, label) for sd, label, ea in jobs}
    for future in as_completed(futures):
        pass

# Write findings
labels = [label for label, _ in GRID]
lines = []
lines.append(f"# Grid Search — mp={MAX_PAIRS}, pct={PCT_PER_PAIR}\n")
lines.append(f"**Grid:** {len(START_DATES)} start dates × 8 configs = {len(GRID) * len(START_DATES)} runs\n")
lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

lines.append("## Sharpe Pivot\n")
col_headers = ' | '.join(labels)
lines.append(f"| Start Date | {col_headers} |")
sep = '|' + '|'.join(['---'] * (1 + len(labels))) + '|'
lines.append(sep)
for sd in START_DATES:
    row = [sd]
    for label in labels:
        vals = [r['sharpe'] for r in results if r['start'] == sd and r['label'] == label]
        row.append(str(vals[0]) if vals else 'N/A')
    lines.append('| ' + ' | '.join(row) + ' |')
lines.append("")

lines.append("## Trades Pivot\n")
col_headers = ' | '.join(labels)
lines.append(f"| Start Date | {col_headers} |")
lines.append(sep)
for sd in START_DATES:
    row = [sd]
    for label in labels:
        vals = [r['trades'] for r in results if r['start'] == sd and r['label'] == label]
        row.append(str(vals[0]) if vals else 'N/A')
    lines.append('| ' + ' | '.join(row) + ' |')
lines.append("")

lines.append("## Mean Active Trades Pivot\n")
col_headers = ' | '.join(labels)
lines.append(f"| Start Date | {col_headers} |")
lines.append(sep)
for sd in START_DATES:
    row = [sd]
    for label in labels:
        vals = [r['mean_at'] for r in results if r['start'] == sd and r['label'] == label]
        row.append(str(vals[0]) if vals else 'N/A')
    lines.append('| ' + ' | '.join(row) + ' |')
lines.append("")

lines.append("## Aggregate Summary\n")
lines.append("| Metric | " + " | ".join(labels) + " |")
lines.append("|--------|" + "|".join(["---"] * len(labels)) + "|")
for metric_key, metric_name, fmt in [
    ('sharpe', 'Mean Sharpe', '.2f'),
    ('trades', 'Mean Trades', '.1f'),
    ('return_pct', 'Mean Return %', '.2f'),
    ('mean_at', 'Mean Active Trades', '.2f'),
]:
    row = [metric_name]
    for label in labels:
        vals = [r[metric_key] for r in results if r['label'] == label]
        if vals:
            row.append(f"{statistics.mean(vals):{fmt}}")
        else:
            row.append('N/A')
    lines.append('| ' + ' | '.join(row) + ' |')

# Per-fold pairs & trades aggregates from oos_fold_summary.csv / run.log
def _fold_rows(out_dir):
    t, p, fr = fold_stats(out_dir, MAX_PAIRS)
    return {'t_min': t['min'], 't_mean': t['mean'], 't_max': t['max'],
            'p_min': p['min'], 'p_mean': p['mean'], 'p_max': p['max'], 'fill': fr}

fold_by_label = {}
for sd in START_DATES:
    for label, _ in GRID:
        out_dir = os.path.join(BASE_DIR, f'{sd}_{label}')
        if os.path.exists(os.path.join(out_dir, 'metrics.json')):
            fold_by_label.setdefault(label, []).append(_fold_rows(out_dir))

for agg, name, fmt in [
    ('p_mean', 'Pairs/fold Mean', '.1f'),
    ('p_min', 'Pairs/fold Min', '.0f'),
    ('p_max', 'Pairs/fold Max', '.0f'),
    ('fill', 'Fill-rate % (all 20)', '.1f'),
    ('t_mean', 'Trades/fold Mean', '.1f'),
    ('t_min', 'Trades/fold Min', '.0f'),
    ('t_max', 'Trades/fold Max', '.0f'),
]:
    row = [name]
    for label in labels:
        vals = [r[agg] for r in fold_by_label.get(label, []) if r[agg] is not None]
        if vals:
            v = statistics.mean(vals) * 100 if agg == 'fill' else statistics.mean(vals)
            row.append(f"{v:{fmt}}")
        else:
            row.append('N/A')
    lines.append('| ' + ' | '.join(row) + ' |')
lines.append("")

lines.append("## Stability (Sharpe Std & Range)\n")
lines.append("| Metric | " + " | ".join(labels) + " |")
lines.append("|--------|" + "|".join(["---"] * len(labels)) + "|")
row = ['Sharpe Std']
for label in labels:
    vals = [r['sharpe'] for r in results if r['label'] == label]
    if vals and len(vals) > 1:
        row.append(f"{statistics.stdev(vals):.2f}")
    elif vals:
        row.append('0.00')
    else:
        row.append('N/A')
lines.append('| ' + ' | '.join(row) + ' |')
row = ['Sharpe Range']
for label in labels:
    vals = [r['sharpe'] for r in results if r['label'] == label]
    if vals:
        minv = min(vals)
        maxv = max(vals)
        row.append(f"[{minv:.2f}, {maxv:.2f}]")
    else:
        row.append('N/A')
lines.append('| ' + ' | '.join(row) + ' |')
lines.append("")

lines.append("## Same-Sector Only — Slide × Screen\n")
ss_labels = [l for l in labels if l.startswith('same_sector')]
lines.append("| Metric | " + " | ".join(ss_labels) + " |")
lines.append("|--------|" + "|".join(["---"] * len(ss_labels)) + "|")
for metric_key, metric_name, fmt in [
    ('sharpe', 'Mean Sharpe', '.2f'),
    ('sharpe', 'Sharpe Std', '.2f'),
    ('mean_at', 'Mean Active Trades', '.2f'),
]:
    row = [metric_name]
    for label in ss_labels:
        vals = [r[metric_key] for r in results if r['label'] == label]
        row.append(f"{statistics.mean(vals):{fmt}}" if vals and (metric_key != 'sharpe' or len(vals) > 1 or metric_name != 'Sharpe Std') else ('N/A'))
    if metric_name == 'Sharpe Std':
        row = ['Sharpe Std']
        for label in ss_labels:
            vals = [r['sharpe'] for r in results if r['label'] == label]
            if vals and len(vals) > 1:
                row.append(f"{statistics.stdev(vals):.2f}")
            else:
                row.append('N/A')
    lines.append('| ' + ' | '.join(row) + ' |')
lines.append("")

lines.append("## Cross-Sector Only — Slide × Screen\n")
cs_labels = [l for l in labels if l.startswith('cross_sector')]
lines.append("| Metric | " + " | ".join(cs_labels) + " |")
lines.append("|--------|" + "|".join(["---"] * len(cs_labels)) + "|")
for metric_key, metric_name, fmt in [
    ('sharpe', 'Mean Sharpe', '.2f'),
    ('mean_at', 'Mean Active Trades', '.2f'),
]:
    row = [metric_name]
    for label in cs_labels:
        vals = [r[metric_key] for r in results if r['label'] == label]
        row.append(f"{statistics.mean(vals):{fmt}}" if vals else 'N/A')
    lines.append('| ' + ' | '.join(row) + ' |')
row = ['Sharpe Std']
for label in cs_labels:
    vals = [r['sharpe'] for r in results if r['label'] == label]
    if vals and len(vals) > 1:
        row.append(f"{statistics.stdev(vals):.2f}")
    else:
        row.append('N/A')
lines.append('| ' + ' | '.join(row) + ' |')
lines.append("")

lines.append("## Earnings Screen Effect (Delta)\n")
lines.append("| Config | Sharpe Δ (screen - no_screen) |")
lines.append("|--------|------|")
for sector_slide in ['same_sector_slide3m', 'same_sector_slide1m', 'cross_sector_slide3m', 'cross_sector_slide1m']:
    no_label = f'{sector_slide}_noscreen'
    bd_label = f'{sector_slide}_bd7'
    no_vals = [r['sharpe'] for r in results if r['label'] == no_label]
    bd_vals = [r['sharpe'] for r in results if r['label'] == bd_label]
    if no_vals and bd_vals:
        delta = statistics.mean(bd_vals) - statistics.mean(no_vals)
        lines.append(f"| {sector_slide} | {delta:+.2f} |")
lines.append("")

lines.append("## Slide 1m vs 3m Effect (Delta)\n")
lines.append("| Config | Sharpe Δ (1m - 3m) |")
lines.append("|--------|------|")
for sector_screen in ['same_sector_noscreen', 'same_sector_bd7', 'cross_sector_noscreen', 'cross_sector_bd7']:
    s3_label = f'{sector_screen.replace("_noscreen", "_slide3m_noscreen").replace("_bd7", "_slide3m_bd7")}'
    s1_label = f'{sector_screen.replace("_noscreen", "_slide1m_noscreen").replace("_bd7", "_slide1m_bd7")}'
    s3_vals = [r['sharpe'] for r in results if r['label'] == s3_label]
    s1_vals = [r['sharpe'] for r in results if r['label'] == s1_label]
    if s3_vals and s1_vals:
        delta = statistics.mean(s1_vals) - statistics.mean(s3_vals)
        lines.append(f"| {sector_screen} | {delta:+.2f} |")

summary_path = os.path.join(BASE_DIR, 'findings.md')
with open(summary_path, 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f"\n{'='*60}")
print(f"Summary written to {summary_path}")
print(f"{'='*60}")
