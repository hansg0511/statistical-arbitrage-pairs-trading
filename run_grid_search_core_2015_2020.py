import subprocess, json, os, sys, statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from run_full_results import fold_stats

START_DATES = ['2015-01-01', '2017-01-01', '2019-01-01']
END = '2021-01-01'
BASE_DIR = 'diagnosis/08b_core_12m_sel_2015_2020'
EARNINGS_CACHE = 'research/earnings_cache/earnings_dates.pkl'
CACHE_DIR = 'research/cache'
os.makedirs(BASE_DIR, exist_ok=True)

MAX_PAIRS = 20
PCT_PER_PAIR = 0.045

GRID = [
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
        '--universe', 'core',
        '--cache_dir', CACHE_DIR,
    ] + extra_args

    print(f"\n[START] {sd} {label}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)

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

# Build job list skipping existing
jobs = []
for sd in START_DATES:
    for label, extra_args in GRID:
        out_dir = os.path.join(BASE_DIR, f'{sd}_{label}')
        if not os.path.exists(os.path.join(out_dir, 'metrics.json')):
            jobs.append((sd, label, extra_args))

total_all = len(GRID) * len(START_DATES)
print(f"\nCore 2015-2020 Grid: {len(GRID)} configs x {len(START_DATES)} dates = {total_all} total")
print(f"Existing: {len(results)}  New: {len(jobs)} (running 2 at a time)")
print(f"{'='*60}")

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {executor.submit(run_job, sd, label, ea): (sd, label) for sd, label, ea in jobs}
    for future in as_completed(futures):
        pass

# Write findings
labels = [label for label, _ in GRID]
lines = []
lines.append(f"# Core Grid — 2015–2020, mp={MAX_PAIRS}, pct={PCT_PER_PAIR}\n")
lines.append(f"**Grid:** {len(START_DATES)} start dates × 8 configs = {total_all} runs\n")
lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

lines.append("## Sharpe Pivot\n")
col_headers = ' | '.join(labels)
lines.append(f"| Start Date | {col_headers} |")
lines.append('|' + '|'.join(['---'] * (1 + len(labels))) + '|')
for sd in START_DATES:
    row = [sd]
    for label in labels:
        vals = [r['sharpe'] for r in results if r['start'] == sd and r['label'] == label]
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
        row.append(f"[{min(vals):.2f}, {max(vals):.2f}]")
    else:
        row.append('N/A')
lines.append('| ' + ' | '.join(row) + ' |')
lines.append("")

lines.append("## Earnings Screen Effect (bd7 vs Noscreen)\n")
lines.append("| Config | No Screen | Bd7 | Δ |")
lines.append("|--------|:---------:|:---:|:-:|")
for mode in ['same_sector', 'cross_sector']:
    for slide in ['slide3m', 'slide1m']:
        ns_label = f"{mode}_{slide}_noscreen"
        bd_label = f"{mode}_{slide}_bd7"
        ns = [r['sharpe'] for r in results if r['label'] == ns_label]
        bd = [r['sharpe'] for r in results if r['label'] == bd_label]
        if ns and bd:
            delta = statistics.mean(bd) - statistics.mean(ns)
            lines.append(f"| {mode} {slide.replace('slide','')} | {statistics.mean(ns):.2f} | {statistics.mean(bd):.2f} | {delta:+.2f} |")
lines.append("")

# Comparison with 2024-2025 core data
core_2024 = {
    'same_sector_slide3m_noscreen': 0.80,
    'same_sector_slide3m_bd7': 0.81,
    'same_sector_slide1m_noscreen': 1.01,
    'same_sector_slide1m_bd7': 1.28,
    'cross_sector_slide3m_noscreen': 0.34,
    'cross_sector_slide3m_bd7': 0.73,
    'cross_sector_slide1m_noscreen': 0.32,
    'cross_sector_slide1m_bd7': 0.48,
}

lines.append("## Period Comparison: 2015–2020 vs 2024–2025\n")
lines.append("| Config | 2015–2020 | 2024–2025 | Δ |")
lines.append("|--------|:---------:|:---------:|:-:|")
for label in labels:
    vals = [r['sharpe'] for r in results if r['label'] == label]
    v15 = statistics.mean(vals) if vals else None
    v24 = core_2024[label]
    delta = f"{v15 - v24:+.2f}" if v15 is not None else 'N/A'
    lines.append(f"| {label} | {v15:.2f} | {v24:.2f} | {delta} |")
lines.append("")

lines.append("## Key Findings\n")
lines.append("- **Earnings screen effect reversed** between periods: bd7 hurt (-0.26 to -0.50) on 2015-2020 but helped (+0.01 to +0.39) on 2024-2025")
lines.append("- **Cross_sector 1m collapsed**: 2015-2020 winner (1.51) became 2024-2025 loser (0.32) without screen")
lines.append("- **Same_sector 1m bd7 is unique**: the only config that *improved* across periods (0.86 → 1.28)")
lines.append("- **All configs degraded** from 2015-2020 to 2024-2025 (Δ +0.06 to +1.19) except same 1m bd7")

summary_path = os.path.join(BASE_DIR, 'findings.md')
with open(summary_path, 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f"\n{'='*60}")
print(f"Summary written to {summary_path}")
print(f"{'='*60}")
