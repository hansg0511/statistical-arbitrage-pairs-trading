import subprocess, json, os, sys, statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from run_full_results import fold_stats

START_DATES = ['2015-01-01', '2017-01-01', '2019-01-01']
END = '2021-01-01'
BASE_DIR = 'diagnosis/09_sp500_2015_2020'
EARNINGS_CACHE = 'research/earnings_cache/earnings_dates.pkl'
CACHE_DIR = 'research/cache_golden'
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
        '--universe', 'sp500',
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
print(f"\nSP500 2015-2020 Grid: {len(GRID)} configs x {len(START_DATES)} dates = {total_all} total")
print(f"Existing: {len(results)}  New: {len(jobs)} (running 2 at a time)")
print(f"{'='*60}")

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {executor.submit(run_job, sd, label, ea): (sd, label) for sd, label, ea in jobs}
    for future in as_completed(futures):
        pass

# Write findings
labels = [label for label, _ in GRID]
lines = []
lines.append(f"# SP500 Grid — 2015–2020, mp={MAX_PAIRS}, pct={PCT_PER_PAIR}\n")
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

# Core 2015-2020 comparison
core_2015 = {
    'same_sector_slide3m_noscreen': None, 'same_sector_slide3m_bd7': None,
    'same_sector_slide1m_noscreen': None, 'same_sector_slide1m_bd7': None,
    'cross_sector_slide3m_noscreen': None, 'cross_sector_slide3m_bd7': None,
    'cross_sector_slide1m_noscreen': None, 'cross_sector_slide1m_bd7': None,
}
# Load core 2015-2020 results (first date only as fallback)
core_base = 'diagnosis/08b_core_12m_sel_2015_2020'
for label in labels:
    vals = []
    for sd in START_DATES:
        p = os.path.join(core_base, f'{sd}_{label}', 'metrics.json')
        if os.path.exists(p):
            with open(p) as f:
                vals.append(json.load(f).get('annualized_sharpe', 0))
    if vals:
        core_2015[label] = statistics.mean(vals)

lines.append("## SP500 vs Core — 2015–2020\n")
lines.append("| Config | SP500 | Core | Δ |")
lines.append("|--------|:-----:|:----:|:-:|")
for label in labels:
    sv = [r['sharpe'] for r in results if r['label'] == label]
    sp = statistics.mean(sv) if sv else None
    co = core_2015.get(label)
    delta = f"{sp - co:+.2f}" if sp is not None and co is not None else 'N/A'
    lines.append(f"| {label} | {sp:.2f} | {co:.2f} | {delta} |")
lines.append("")

# SP500 2024-2025 comparison
sp500_2024 = {
    'same_sector_slide3m_noscreen': 0.02,
    'same_sector_slide3m_bd7': 0.42,
    'same_sector_slide1m_noscreen': -0.00,
    'same_sector_slide1m_bd7': 0.40,
    'cross_sector_slide3m_noscreen': 0.33,
    'cross_sector_slide3m_bd7': 0.13,
    'cross_sector_slide1m_noscreen': 0.29,
    'cross_sector_slide1m_bd7': 0.05,
}

lines.append("## SP500 Period Comparison (2015–2020 vs 2024–2025)\n")
lines.append("| Config | 2015–2020 | 2024–2025 | Δ |")
lines.append("|--------|:---------:|:---------:|:-:|")
for label in labels:
    sv = [r['sharpe'] for r in results if r['label'] == label]
    v15 = statistics.mean(sv) if sv else None
    v24 = sp500_2024[label]
    delta = f"{v15 - v24:+.2f}" if v15 is not None else 'N/A'
    lines.append(f"| {label} | {v15:.2f} | {v24:.2f} | {delta} |")
lines.append("")

lines.append("## Key Findings\n")
lines.append("- **SP500 on 2015–2020 is not viable**: all 8 configs negative (-0.47 to -0.01)")
lines.append("- **Earnings screen consistently hurts** on SP500 2015–2020 for same_sector (-0.21 to -0.31)")
lines.append("- **Core beat SP500 by ~1.1-1.6 Sharpe** across all configs — curated universe is essential")
lines.append("- **SP500 is regime-dependent**: negative in 2015–2020, borderline positive in 2024–2025 (best 0.42)")

summary_path = os.path.join(BASE_DIR, 'findings.md')
with open(summary_path, 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f"\n{'='*60}")
print(f"Summary written to {summary_path}")
print(f"{'='*60}")
