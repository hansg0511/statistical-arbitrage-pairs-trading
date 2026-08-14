"""Run the 12-month selection grid on the CORE universe, 2015-2020 (08b redo).

This is the corrected 08b: core universe + 12-month selection from the SP500
superset pool (sp500_12m.pkl), with the sector mask applied for real this time.
The original 08b consumed 12m sp500 pairs via the huck-cache shadow bug, which
bypassed the sector mask and the core ticker mask. With the bug fixed, running
--profile baseline --sel_months 12 --universe core routes through
pool_path_for(12) -> sp500_12m.pkl, and PoolCache.select() applies the core
ticker mask, the same_sector/cross_sector mask, and the p<0.05 log filter.
"""
import subprocess, json, os, sys, threading
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
lock = threading.Lock()


def run_job(sd, label, extra_args):
    out_dir = os.path.join(BASE_DIR, f'{sd}_{label}')
    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        sys.executable, 'run_backtest_parallel.py',
        '--profile', 'baseline',
        '--universe', 'core',
        '--start', sd,
        '--end', END,
        '--output', out_dir,
        '--no-earnings_screen',
        '--max_pairs', str(MAX_PAIRS),
        '--pct_per_pair', str(PCT_PER_PAIR),
        '--cache_dir', CACHE_DIR,
        '--sel_months', '12',
        '--workers', '1',
    ] + extra_args
    print(f"\n[START] {sd} {label}")
    print('CMD: ' + ' '.join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)

    metrics_path = os.path.join(out_dir, 'metrics.json')
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            m = json.load(f)
        rec = {
            'start': sd, 'label': label,
            'return_pct': round(m.get('annualized_return', 0) * 100, 2),
            'sharpe': round(m.get('annualized_sharpe', 0), 2),
            'trades': m.get('total_trades', 0),
            'mean_at': round(m.get('mean_active_trades', 0), 2),
        }
        with lock:
            results.append(rec)
        print(f"  [DONE] {sd} {label}: Return={rec['return_pct']}% Sharpe={rec['sharpe']} Trades={rec['trades']}")
    else:
        print(f"  [FAIL] {sd} {label}: no metrics.json")
        if result.returncode != 0:
            print(f"  STDERR: {result.stderr[-1000:] if result.stderr else 'N/A'}")
    with open(os.path.join(out_dir, 'run.log'), 'w') as f:
        f.write(result.stdout or '')
        if result.stderr:
            f.write('\n--- STDERR ---\n'); f.write(result.stderr)


jobs = []
for sd in START_DATES:
    for label, extra_args in GRID:
        out_dir = os.path.join(BASE_DIR, f'{sd}_{label}')
        if not os.path.exists(os.path.join(out_dir, 'metrics.json')):
            jobs.append((sd, label, extra_args))

total = len(GRID) * len(START_DATES)
print(f"8 configs x {len(START_DATES)} dates = {total}; new = {len(jobs)}; running 4 at a time\n{'='*60}")

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {executor.submit(run_job, sd, label, ea): (sd, label) for sd, label, ea in jobs}
    for _ in as_completed(futures):
        pass

print(f"\nDONE. {len(results)} results written to {BASE_DIR}")
for r in sorted(results, key=lambda x: (x['start'], x['label'])):
    print(f"{r['start']} {r['label']:32s} ret={r['return_pct']}% sharpe={r['sharpe']} trades={r['trades']}")
