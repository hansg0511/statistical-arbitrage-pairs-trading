import subprocess, json, os, sys, statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

START_DATES = ['2023-12-01', '2023-12-15', '2024-01-01', '2024-01-15', '2024-02-01']
END = '2026-01-01'
BASE_DIR = 'diagnosis/04_max_pairs_sweep'

MAX_PAIRS_CONFIG = [
    (5, 0.18),
    (10, 0.09),
    (20, 0.045),
    (50, 0.018),
]

SECTORS = [
    ('same_sector', []),
    ('cross_sector', ['--cross_sector', '--return_divergence', '0.10']),
]

results = []
lock = __import__('threading').Lock()

# Load existing results
for sd in START_DATES:
    for sector_label, _ in SECTORS:
        for max_pairs, _ in MAX_PAIRS_CONFIG:
            out_dir = os.path.join(BASE_DIR, f'{sd}_{sector_label}_mp{max_pairs}')
            metrics_path = os.path.join(out_dir, 'metrics.json')
            if os.path.exists(metrics_path):
                with open(metrics_path) as f:
                    m = json.load(f)
                rec = {
                    'start': sd,
                    'sector': sector_label,
                    'max_pairs': max_pairs,
                    'pct_per_pair': None,
                    'return_pct': round(m.get('annualized_return', 0) * 100, 2),
                    'sharpe': round(m.get('annualized_sharpe', 0), 2),
                    'trades': m.get('total_trades', 0),
                    'mean_at': round(m.get('mean_active_trades', 0), 2),
                }
                results.append(rec)

def run_job(sd, sector_label, extra_args, max_pairs, pct):
    out_dir = os.path.join(BASE_DIR, f'{sd}_{sector_label}_mp{max_pairs}')
    os.makedirs(out_dir, exist_ok=True)

    cmd = [
        sys.executable, 'run_backtest_parallel.py',
        '--profile', 'baseline',
        '--start', sd,
        '--end', END,
        '--output', out_dir,
        '--no-earnings_screen',
        '--max_pairs', str(max_pairs),
        '--pct_per_pair', str(pct),
    ] + extra_args

    print(f"\n[START] {sd} {sector_label} mp={max_pairs} pct={pct}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

    metrics_path = os.path.join(out_dir, 'metrics.json')
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            m = json.load(f)
        rec = {
            'start': sd,
            'sector': sector_label,
            'max_pairs': max_pairs,
            'pct_per_pair': pct,
            'return_pct': round(m.get('annualized_return', 0) * 100, 2),
            'sharpe': round(m.get('annualized_sharpe', 0), 2),
            'trades': m.get('total_trades', 0),
            'mean_at': round(m.get('mean_active_trades', 0), 2),
        }
        with lock:
            results.append(rec)
        print(f"  [DONE] {sd} {sector_label} mp={max_pairs}: Sharpe={rec['sharpe']}, Trades={rec['trades']}, AT={rec['mean_at']}")
    else:
        print(f"  [FAIL] {sd} {sector_label} mp={max_pairs}: no metrics.json")
        if result.returncode != 0:
            print(f"  STDERR: {result.stderr[-1000:] if result.stderr else 'N/A'}")

    log_path = os.path.join(out_dir, 'run.log')
    with open(log_path, 'w') as f:
        f.write(result.stdout or '')
        if result.stderr:
            f.write('\n--- STDERR ---\n')
            f.write(result.stderr)

jobs = []
for sd in START_DATES:
    for sector_label, extra_args in SECTORS:
        for max_pairs, pct in MAX_PAIRS_CONFIG:
            out_dir = os.path.join(BASE_DIR, f'{sd}_{sector_label}_mp{max_pairs}')
            if not os.path.exists(os.path.join(out_dir, 'metrics.json')):
                jobs.append((sd, sector_label, extra_args, max_pairs, pct))

print(f"Resume: {len(jobs)} remaining jobs (running 2 at a time)")
print(f"{'='*60}")

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {executor.submit(run_job, sd, sl, ea, mp, pct): (sd, sl, mp) for sd, sl, ea, mp, pct in jobs}
    for future in as_completed(futures):
        pass

# Write findings (same as original)
labels_mp = [mp for mp, _ in MAX_PAIRS_CONFIG]
lines = []
lines.append(f"# Max Pairs Sweep — same_sector vs cross_sector\n")
lines.append(f"**Grid:** {len(START_DATES)} start dates × {len(SECTORS)} sector modes × {len(MAX_PAIRS_CONFIG)} max_pairs = {len(jobs) + len([r for r in results if r['pct_per_pair'] is not None])} runs (resume: {len(jobs)} new)\n")
lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

for sector_label in ['same_sector', 'cross_sector']:
    lines.append(f"## {sector_label} — Sharpe Pivot\n")
    col_headers = ' | '.join([f'mp={mp}' for mp in labels_mp])
    lines.append(f"| Start Date | {col_headers} |")
    sep = '|' + '|'.join(['---'] * (1 + len(labels_mp))) + '|'
    lines.append(sep)

    for sd in START_DATES:
        row = [sd]
        for mp in labels_mp:
            vals = [r['sharpe'] for r in results if r['start'] == sd and r['sector'] == sector_label and r['max_pairs'] == mp]
            row.append(str(vals[0]) if vals else 'N/A')
        lines.append('| ' + ' | '.join(row) + ' |')
    lines.append("")

    lines.append(f"## {sector_label} — Trades Pivot\n")
    col_headers = ' | '.join([f'mp={mp}' for mp in labels_mp])
    lines.append(f"| Start Date | {col_headers} |")
    lines.append(sep)
    for sd in START_DATES:
        row = [sd]
        for mp in labels_mp:
            vals = [r['trades'] for r in results if r['start'] == sd and r['sector'] == sector_label and r['max_pairs'] == mp]
            row.append(str(vals[0]) if vals else 'N/A')
        lines.append('| ' + ' | '.join(row) + ' |')
    lines.append("")

    lines.append(f"## {sector_label} — Mean Active Trades Pivot\n")
    col_headers = ' | '.join([f'mp={mp}' for mp in labels_mp])
    lines.append(f"| Start Date | {col_headers} |")
    lines.append(sep)
    for sd in START_DATES:
        row = [sd]
        for mp in labels_mp:
            vals = [r['mean_at'] for r in results if r['start'] == sd and r['sector'] == sector_label and r['max_pairs'] == mp]
            row.append(str(vals[0]) if vals else 'N/A')
        lines.append('| ' + ' | '.join(row) + ' |')
    lines.append("")

    lines.append(f"## {sector_label} — Aggregate Summary\n")
    lines.append("| Metric | " + " | ".join([f"mp={mp}" for mp in labels_mp]) + " |")
    lines.append("|--------|" + "|".join(["---"] * len(labels_mp)) + "|")

    for metric_key, metric_name, fmt in [
        ('sharpe', 'Mean Sharpe', '.2f'),
        ('trades', 'Mean Trades', '.1f'),
        ('return_pct', 'Mean Return %', '.2f'),
        ('mean_at', 'Mean Active Trades', '.2f'),
    ]:
        row = [metric_name]
        for mp in labels_mp:
            vals = [r[metric_key] for r in results if r['sector'] == sector_label and r['max_pairs'] == mp]
            if vals:
                row.append(f"{statistics.mean(vals):{fmt}}")
            else:
                row.append('N/A')
        lines.append('| ' + ' | '.join(row) + ' |')

    lines.append("")
    lines.append(f"## {sector_label} — Stability (Sharpe Std & Range)\n")
    lines.append("| Metric | " + " | ".join([f"mp={mp}" for mp in labels_mp]) + " |")
    lines.append("|--------|" + "|".join(["---"] * len(labels_mp)) + "|")

    row = ['Sharpe Std']
    for mp in labels_mp:
        vals = [r['sharpe'] for r in results if r['sector'] == sector_label and r['max_pairs'] == mp]
        if vals and len(vals) > 1:
            row.append(f"{statistics.stdev(vals):.2f}")
        elif vals:
            row.append('0.00')
        else:
            row.append('N/A')
    lines.append('| ' + ' | '.join(row) + ' |')

    row = ['Sharpe Range']
    for mp in labels_mp:
        vals = [r['sharpe'] for r in results if r['sector'] == sector_label and r['max_pairs'] == mp]
        if vals:
            row.append(f"[{min(vals):.2f}, {max(vals):.2f}]")
        else:
            row.append('N/A')
    lines.append('| ' + ' | '.join(row) + ' |')
    lines.append("")

lines.append("## Cross-Sector vs Same-Sector Comparison (Sharpe)\n")
lines.append("| max_pairs | same_sector Mean | cross_sector Mean | same_sector Std | cross_sector Std |")
lines.append("|-----------|-----------------|-------------------|-----------------|------------------|")
for mp in labels_mp:
    ss_vals = [r['sharpe'] for r in results if r['sector'] == 'same_sector' and r['max_pairs'] == mp]
    cs_vals = [r['sharpe'] for r in results if r['sector'] == 'cross_sector' and r['max_pairs'] == mp]
    ss_mean = f"{statistics.mean(ss_vals):.2f}" if ss_vals else 'N/A'
    cs_mean = f"{statistics.mean(cs_vals):.2f}" if cs_vals else 'N/A'
    ss_std = f"{statistics.stdev(ss_vals):.2f}" if ss_vals and len(ss_vals) > 1 else 'N/A'
    cs_std = f"{statistics.stdev(cs_vals):.2f}" if cs_vals and len(cs_vals) > 1 else 'N/A'
    lines.append(f"| {mp} | {ss_mean} | {cs_mean} | {ss_std} | {cs_std} |")

summary_path = os.path.join(BASE_DIR, 'findings.md')
with open(summary_path, 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f"\n{'='*60}")
print(f"Summary written to {summary_path}")
print(f"{'='*60}")
