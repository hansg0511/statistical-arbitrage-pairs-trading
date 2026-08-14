import subprocess, json, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

START_DATES = ['2015-01-01', '2017-01-01', '2019-01-01']
END = '2021-01-01'
BASE_DIR = 'diagnosis/sweep_same_sector_slide1m_bd7_pct025/2015-2020'
EARNINGS_CACHE = 'research/earnings_cache/earnings_dates.pkl'
PCT_PER_PAIR = 0.25
MAX_PAIRS = 20

os.makedirs(BASE_DIR, exist_ok=True)

def run_job(sd):
    out_dir = os.path.join(BASE_DIR, sd)
    os.makedirs(out_dir, exist_ok=True)

    cmd = [
        sys.executable, 'run_backtest_parallel.py',
        '--profile', 'baseline',
        '--start', sd,
        '--end', END,
        '--output', out_dir,
        '--earnings_screen',
        '--earnings_block_days', '7',
        '--earnings_cache', EARNINGS_CACHE,
        '--slide_months', '1',
        '--max_pairs', str(MAX_PAIRS),
        '--pct_per_pair', str(PCT_PER_PAIR),
    ]

    print(f"\n[START] {sd}", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)

    log_path = os.path.join(out_dir, 'run.log')
    with open(log_path, 'w') as f:
        f.write(result.stdout or '')
        if result.stderr:
            f.write('\n--- STDERR ---\n')
            f.write(result.stderr)

    metrics_path = os.path.join(out_dir, 'metrics.json')
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            m = json.load(f)
        print(f"  [DONE] {sd}: Return={m.get('annualized_return',0)*100:.2f}%, "
              f"Sharpe={m.get('annualized_sharpe',0):.2f}, "
              f"Trades={m.get('total_trades',0)}, AT={m.get('mean_active_trades',0):.2f}", flush=True)
    else:
        print(f"  [FAIL] {sd}: no metrics.json")
        if result.returncode != 0:
            print(f"  STDERR: {result.stderr[-1500:] if result.stderr else 'N/A'}", flush=True)

jobs = START_DATES
print(f"Total jobs: {len(jobs)} (running 2 at a time)")
print('=' * 60, flush=True)

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {executor.submit(run_job, sd): sd for sd in jobs}
    for future in as_completed(futures):
        pass

print("\n=== ALL DONE ===", flush=True)
