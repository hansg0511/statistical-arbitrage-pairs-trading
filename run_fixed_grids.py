"""Run the aligned-window grids into fixed_diagnosis/<section>/.

Recent grids trade 2024-01-01..2025-12-31 (start shifted back by sel_months);
historical grids trade 2015-01-01..2019-12-31. The 12m grids start 10 months
earlier than their 2m counterparts so both trade the identical window.

Sections (mirrors RESEARCH_PIPELINE 05..10b):
  05  core 2m  mp=5  pct=0.18  recent
  06  core 2m  mp=20 pct=0.045 recent
  07  sp500 2m mp=20 pct=0.045 recent
  08a core 2m  mp=20 pct=0.045 historical
  08b core 12m mp=20 pct=0.045 historical
  09a sp500 2m mp=20 pct=0.045 historical
  09b sp500 12m mp=20 pct=0.045 historical
  10  core 2m  same_sector_slide1m_bd7 pct=0.25 recent (start-fragility sweep)
  10a core 12m mp=20 pct=0.045 recent
  10b sp500 12m mp=20 pct=0.045 recent

Run order: historical first (08a,08b,09a,09b), then recent.
Usage: python run_fixed_grids.py [--only 08b] [--skip 10b] [--workers N]
"""
import subprocess, json, os, sys, threading, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.result_validation import validate_run_output

EARNINGS_CORE = 'research/earnings_cache/earnings_dates.pkl'
EARNINGS_SP500 = EARNINGS_CORE
CACHE_DIR = 'research/cache'
BASE = 'fixed_diagnosis'


def snapshot_path(snapshot_dir, cfg):
    if not snapshot_dir:
        return None
    period = 'historical' if cfg['end'] == '2020-01-01' else 'recent'
    selection_suffix = '_12m' if cfg['sel'] == 12 else ''
    return os.path.join(
        snapshot_dir, f"{cfg['universe']}_{period}{selection_suffix}.pkl"
    )


def _grid(earnings):
    e = ['--earnings_screen', '--earnings_block_days', '7', '--earnings_cache', earnings]
    return [
        ('same_sector_slide3m_noscreen', []),
        ('same_sector_slide3m_bd7',      list(e)),
        ('same_sector_slide1m_noscreen', ['--slide_months', '1']),
        ('same_sector_slide1m_bd7',      ['--slide_months', '1'] + list(e)),
        ('cross_sector_slide3m_noscreen', ['--cross_sector', '--return_divergence', '0.10']),
        ('cross_sector_slide3m_bd7',      ['--cross_sector', '--return_divergence', '0.10'] + list(e)),
        ('cross_sector_slide1m_noscreen', ['--cross_sector', '--return_divergence', '0.10', '--slide_months', '1']),
        ('cross_sector_slide1m_bd7',      ['--cross_sector', '--return_divergence', '0.10', '--slide_months', '1'] + list(e)),
    ]

SECTIONS = {
    '05': dict(universe='core', sel=2, max_pairs=5, pct=0.18,
               starts=['2023-11-01', '2023-12-01', '2024-01-01', '2024-02-01', '2024-03-01'],
               end='2026-01-01', earnings=EARNINGS_CORE, grid=_grid(EARNINGS_CORE)),
    '06': dict(universe='core', sel=2, max_pairs=20, pct=0.045,
               starts=['2023-11-01', '2023-12-01', '2024-01-01', '2024-02-01', '2024-03-01'],
               end='2026-01-01', earnings=EARNINGS_CORE, grid=_grid(EARNINGS_CORE)),
    '07': dict(universe='sp500', sel=2, max_pairs=20, pct=0.045,
               starts=['2023-11-01', '2023-12-01', '2024-01-01', '2024-02-01', '2024-03-01'],
               end='2026-01-01', earnings=EARNINGS_SP500, grid=_grid(EARNINGS_SP500)),
    '08a': dict(universe='core', sel=2, max_pairs=20, pct=0.045,
                starts=['2014-11-01'],
                end='2020-01-01', earnings=EARNINGS_CORE, grid=_grid(EARNINGS_CORE)),
    '08b': dict(universe='core', sel=12, max_pairs=20, pct=0.045,
                starts=['2014-01-01'],
                end='2020-01-01', earnings=EARNINGS_CORE, grid=_grid(EARNINGS_CORE)),
    '09a': dict(universe='sp500', sel=2, max_pairs=20, pct=0.045,
                starts=['2014-11-01'],
                end='2020-01-01', earnings=EARNINGS_SP500, grid=_grid(EARNINGS_SP500)),
    '09b': dict(universe='sp500', sel=12, max_pairs=20, pct=0.045,
                starts=['2014-01-01'],
                end='2020-01-01', earnings=EARNINGS_SP500, grid=_grid(EARNINGS_SP500)),
    '10': dict(universe='core', sel=2, max_pairs=20, pct=0.25,
               starts=['2023-11-01', '2023-11-15', '2023-12-01', '2023-12-15',
                       '2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15'],
               end='2026-01-01', earnings=EARNINGS_CORE, grid=_grid(EARNINGS_CORE)[3:4]),
    '10a': dict(universe='core', sel=12, max_pairs=20, pct=0.045,
                starts=['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01'],
                end='2026-01-01', earnings=EARNINGS_CORE, grid=_grid(EARNINGS_CORE)),
    '10b': dict(universe='sp500', sel=12, max_pairs=20, pct=0.045,
                starts=['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01'],
                end='2026-01-01', earnings=EARNINGS_SP500, grid=_grid(EARNINGS_SP500)),
}

RUN_ORDER = ['08a', '08b', '09a', '09b', '05', '06', '07', '10', '10a', '10b']

results = []
lock = threading.Lock()


def run_job(section, sd, label, extra_args, price_snapshot=None, broker_leverage=1.0):
    cfg = SECTIONS[section]
    out_dir = os.path.join(BASE, section, f'{sd}_{label}')
    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        sys.executable, 'run_backtest_parallel.py',
        '--profile', 'baseline',
        '--universe', cfg['universe'],
        '--start', sd,
        '--end', cfg['end'],
        '--output', out_dir,
        '--no-earnings_screen',
        '--max_pairs', str(cfg['max_pairs']),
        '--pct_per_pair', str(cfg['pct']),
        '--broker_leverage', str(broker_leverage),
        '--cache_dir', CACHE_DIR,
        '--sel_months', str(cfg['sel']),
        '--workers', '1',
    ] + (['--price_snapshot', price_snapshot] if price_snapshot else []) + list(extra_args)
    print(f"\n[START] sec{section} {sd} {label}", flush=True)
    print('CMD: ' + ' '.join(cmd), flush=True)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    except Exception as e:
        print(f"  [FAIL] {sd} {label}: {e}", flush=True)
        return
    with open(os.path.join(out_dir, 'run.log'), 'w') as f:
        f.write(result.stdout or '')
        if result.stderr:
            f.write('\n--- STDERR ---\n'); f.write(result.stderr)

    if result.returncode != 0:
        print(f"  [FAIL] sec{section} {sd} {label}: subprocess exit {result.returncode}", flush=True)
        return

    validation = validate_run_output(out_dir)
    if not validation['valid']:
        details = '; '.join(validation['reasons'])
        print(f"  [FAIL] sec{section} {sd} {label}: {details}", flush=True)
        return

    metrics_path = os.path.join(out_dir, 'metrics.json')
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            m = json.load(f)
        rec = {'section': section, 'start': sd, 'label': label,
               'return_pct': round(m.get('annualized_return', 0) * 100, 2),
               'sharpe': round(m.get('annualized_sharpe', 0), 2),
               'trades': m.get('total_trades', 0),
               'mean_at': round(m.get('mean_active_trades', 0), 2)}
        with lock:
            results.append(rec)
        print(f"  [DONE] sec{section} {sd} {label}: Sharpe={rec['sharpe']} Ret={rec['return_pct']}%", flush=True)
    else:
        print(f"  [FAIL] sec{section} {sd} {label}: no metrics.json", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', type=str, default=None, help='run one section only')
    parser.add_argument('--skip', type=str, nargs='*', default=[], help='skip sections')
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--force', action='store_true',
                        help='Re-run every job even if metrics.json already exists.')
    parser.add_argument('--pause', type=float, default=0.0,
                        help='Seconds to sleep between job completions (rate-limit cushion).')
    parser.add_argument('--snapshot-dir', type=str, default=None,
                        help='Directory containing scoped price snapshots.')
    parser.add_argument('--broker-leverage', type=float, default=1.0,
                        help='Broker leverage for every launched run.')
    args = parser.parse_args()

    order = [s for s in RUN_ORDER if s not in args.skip]
    if args.only:
        order = [args.only]

    jobs = []
    for section in order:
        cfg = SECTIONS[section]
        for sd in cfg['starts']:
            for label, extra in cfg['grid']:
                out_dir = os.path.join(BASE, section, f'{sd}_{label}')
                needs_run = args.force or not os.path.exists(os.path.join(out_dir, 'metrics.json'))
                if not needs_run and not validate_run_output(out_dir)['valid']:
                    needs_run = True
                if needs_run:
                    price_snapshot = snapshot_path(args.snapshot_dir, cfg)
                    if price_snapshot and not os.path.isfile(price_snapshot):
                        parser.error(f'price snapshot does not exist: {price_snapshot}')
                    jobs.append((section, sd, label, extra, price_snapshot, args.broker_leverage))

    total = sum(len(SECTIONS[s]['starts']) * len(SECTIONS[s]['grid']) for s in order)
    print(f"Sections: {order}")
    print(f"Total runs: {total}; new: {len(jobs)}; running {args.workers} at a time", flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(run_job, *j): j for j in jobs}
        for i, _ in enumerate(as_completed(futures)):
            if args.pause and i < len(jobs) - 1:
                import time as _t; _t.sleep(args.pause)

    if results:
        out = os.path.join(BASE, '_run_log.txt')
        with open(out, 'w') as f:
            for r in sorted(results, key=lambda x: (x['section'], x['start'], x['label'])):
                f.write(f"sec{r['section']} {r['start']} {r['label']:36s} sharpe={r['sharpe']:.2f} ret={r['return_pct']:.2f}% trades={r['trades']} at={r['mean_at']}\n")
        print(f"\nLogged {len(results)} results -> {out}", flush=True)


if __name__ == '__main__':
    main()
