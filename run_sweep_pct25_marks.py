"""Re-run the sweep sections at pct=0.25 into fixed_diagnosis/_sweep_pct25/<sec>/<start>_<cfg>/

Same walk-forward configs as run_fixed_grids.py (sections 06,07,08a,08b,09a,09b,10a,10b) but
pct_per_pair=0.25, so each run emits trade_marks.csv for the consolidated book / pair sweep.

Verification: pct does not change trade *decisions*, so every trade in the existing 0.045 grid
trade log must appear in the 0.25 trade log with identical (pair, entry_date, exit_date,
exit_reason, return). 0.25 may add trades where 0.045 hit zero_size.

Usage:
  python run_sweep_pct25_marks.py [--workers N] [--only SEC] [--skip SEC ...] [--verify]
"""
import subprocess, json, os, sys, threading, argparse, time, pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.result_validation import validate_run_output

EARNINGS_CORE = 'research/earnings_cache/earnings_dates.pkl'
EARNINGS_SP500 = EARNINGS_CORE
CACHE_DIR = 'research/cache'
BASE = 'fixed_diagnosis'
OUT_ROOT = os.path.join(BASE, '_sweep_pct25')
PCT = 0.25


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
        ('same_sector_slide3m_bd7', list(e)),
        ('same_sector_slide1m_noscreen', ['--slide_months', '1']),
        ('same_sector_slide1m_bd7', ['--slide_months', '1'] + list(e)),
        ('cross_sector_slide3m_noscreen', ['--cross_sector', '--return_divergence', '0.10']),
        ('cross_sector_slide3m_bd7', ['--cross_sector', '--return_divergence', '0.10'] + list(e)),
        ('cross_sector_slide1m_noscreen', ['--cross_sector', '--return_divergence', '0.10', '--slide_months', '1']),
        ('cross_sector_slide1m_bd7', ['--cross_sector', '--return_divergence', '0.10', '--slide_months', '1'] + list(e)),
    ]

SECTIONS = {
    '06': dict(universe='core', sel=2,
               starts=['2023-11-01', '2023-12-01', '2024-01-01', '2024-02-01', '2024-03-01'],
               end='2026-01-01', earnings=EARNINGS_CORE, grid=_grid(EARNINGS_CORE)),
    '07': dict(universe='sp500', sel=2,
               starts=['2023-11-01', '2023-12-01', '2024-01-01', '2024-02-01', '2024-03-01'],
               end='2026-01-01', earnings=EARNINGS_SP500, grid=_grid(EARNINGS_SP500)),
    '08a': dict(universe='core', sel=2, starts=['2014-11-01'],
                end='2020-01-01', earnings=EARNINGS_CORE, grid=_grid(EARNINGS_CORE)),
    '08b': dict(universe='core', sel=12, starts=['2014-01-01'],
                end='2020-01-01', earnings=EARNINGS_CORE, grid=_grid(EARNINGS_CORE)),
    '09a': dict(universe='sp500', sel=2, starts=['2014-11-01'],
                end='2020-01-01', earnings=EARNINGS_SP500, grid=_grid(EARNINGS_SP500)),
    '09b': dict(universe='sp500', sel=12, starts=['2014-01-01'],
                end='2020-01-01', earnings=EARNINGS_SP500, grid=_grid(EARNINGS_SP500)),
    '10a': dict(universe='core', sel=12,
                starts=['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01'],
                end='2026-01-01', earnings=EARNINGS_CORE, grid=_grid(EARNINGS_CORE)),
    '10b': dict(universe='sp500', sel=12,
                starts=['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01'],
                end='2026-01-01', earnings=EARNINGS_SP500, grid=_grid(EARNINGS_SP500)),
}

results = []
lock = threading.Lock()


def out_dir(section, sd, label):
    return os.path.join(OUT_ROOT, section, f'{sd}_{label}')


def has_rejected_orders(output_dir):
    """A pct=0.25 mark run is unusable when it contains failed entry orders.

    Older attempts predate the leverage setup and can leave a rejected-orders
    artifact behind even though the directory has metrics and trade marks.
    """
    path = os.path.join(output_dir, 'rejected_orders.csv')
    if not os.path.exists(path):
        return False
    try:
        return not pd.read_csv(path).empty
    except (OSError, pd.errors.EmptyDataError):
        return True


def run_job(section, sd, label, extra_args, price_snapshot=None):
    cfg = SECTIONS[section]
    od = out_dir(section, sd, label)
    os.makedirs(od, exist_ok=True)
    cmd = [
        sys.executable, 'run_backtest_parallel.py',
        '--profile', 'baseline',
        '--universe', cfg['universe'],
        '--start', sd,
        '--end', cfg['end'],
        '--output', od,
        '--no-earnings_screen',
        '--max_pairs', '20',
        '--pct_per_pair', str(PCT),
        '--broker_leverage', '100',
        '--cache_dir', CACHE_DIR,
        '--sel_months', str(cfg['sel']),
        '--workers', '1',
    ] + (['--price_snapshot', price_snapshot] if price_snapshot else []) + list(extra_args)
    print(f"[START] sec{section} {sd} {label}", flush=True)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    except Exception as e:
        print(f"  [FAIL] {sd} {label}: {e}", flush=True)
        return
    with open(os.path.join(od, 'run.log'), 'w') as f:
        f.write(result.stdout or '')
        if result.stderr:
            f.write('\n--- STDERR ---\n')
            f.write(result.stderr)
    if result.returncode != 0:
        print(f"  [FAIL] sec{section} {sd} {label}: subprocess exit {result.returncode}", flush=True)
        return
    validation = validate_run_output(od)
    if not validation['valid']:
        details = '; '.join(validation['reasons'])
        print(f"  [FAIL] sec{section} {sd} {label}: {details}", flush=True)
        return
    mp = os.path.join(od, 'metrics.json')
    if os.path.exists(mp):
        with open(mp) as f:
            m = json.load(f)
        rec = {'section': section, 'start': sd, 'label': label,
               'sharpe': round(m.get('annualized_sharpe', 0), 2),
               'trades': m.get('total_trades', 0),
               'marks': os.path.exists(os.path.join(od, 'trade_marks.csv'))}
        with lock:
            results.append(rec)
        print(f"  [DONE] sec{section} {sd} {label}: Sharpe={rec['sharpe']} trades={rec['trades']} marks={rec['marks']}", flush=True)
    else:
        print(f"  [FAIL] sec{section} {sd} {label}: no metrics.json", flush=True)


def verify_one(section, sd, label):
    """0.25 trade log must contain every 0.045 trade (pair, entry, exit, reason, return)."""
    new = out_dir(section, sd, label)
    old = os.path.join(BASE, section, f'{sd}_{label}')
    np_ = os.path.join(new, 'trade_logs', 'test_trade_log.csv')
    op_ = os.path.join(old, 'trade_logs', 'test_trade_log.csv')
    if not os.path.exists(np_) or not os.path.exists(op_):
        return section, sd, label, 'SKIP(missing log)'
    ndf = pd.read_csv(np_)
    odf = pd.read_csv(op_)

    nk = set(zip(ndf['pair'].astype(str), ndf['entry_date'].astype(str),
                 ndf['exit_date'].astype(str), ndf['exit_reason'].astype(str)))
    miss = sum(1 for _, r in odf.iterrows()
               if (str(r['pair']), str(r['entry_date']), str(r['exit_date']),
                   str(r['exit_reason'])) not in nk)

    o_map = {(str(r['pair']), str(r['entry_date']), str(r['exit_date']),
              str(r['exit_reason'])): float(r['return']) for _, r in odf.iterrows()}
    max_ret_diff = 0.0
    for _, r in ndf.iterrows():
        k = (str(r['pair']), str(r['entry_date']), str(r['exit_date']), str(r['exit_reason']))
        if k in o_map:
            max_ret_diff = max(max_ret_diff, abs(o_map[k] - float(r['return'])))
    ret_bad = int(max_ret_diff > 1e-2)  # allow data-revision drift (~1e-4); catch real config errors

    if miss == 0 and ret_bad == 0:
        return section, sd, label, f'OK (0.045={len(odf)} trades, 0.25={len(ndf)})'
    return section, sd, label, f'MISMATCH old={len(odf)} new={len(ndf)} missing={miss} ret_bad={ret_bad}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--only', type=str, default=None)
    ap.add_argument('--skip', type=str, nargs='*', default=[])
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--force', action='store_true',
                    help='Re-run every job even if trade_marks.csv already exists.')
    ap.add_argument('--pause', type=float, default=15.0,
                    help='Seconds to sleep between completed jobs (rate-limit cushion).')
    ap.add_argument('--snapshot-dir', type=str, default=None,
                    help='Directory containing scoped price snapshots.')
    args = ap.parse_args()

    order = [s for s in SECTIONS if s not in args.skip]
    if args.only:
        order = [args.only]

    if args.verify:
        print('Verifying 0.25 trade logs against 0.045 originals...')
        bad = 0
        for section in order:
            cfg = SECTIONS[section]
            for sd in cfg['starts']:
                for label, _ in cfg['grid']:
                    sec, sd_, lab, status = verify_one(section, sd, label)
                    if not status.startswith('OK'):
                        bad += 1
                        print(f'  {sec} {sd_} {lab:36s} {status}')
        print(f'Verify done. non-OK: {bad}')
        return

    jobs = []
    for section in order:
        cfg = SECTIONS[section]
        for sd in cfg['starts']:
            for label, extra in cfg['grid']:
                od = out_dir(section, sd, label)
                needs_run = args.force or not os.path.exists(os.path.join(od, 'trade_marks.csv'))
                if not needs_run and not validate_run_output(od)['valid']:
                    needs_run = True
                if not needs_run and has_rejected_orders(od):
                    needs_run = True
                if needs_run:
                    price_snapshot = snapshot_path(args.snapshot_dir, cfg)
                    if price_snapshot and not os.path.isfile(price_snapshot):
                        ap.error(f'price snapshot does not exist: {price_snapshot}')
                    jobs.append((section, sd, label, extra, price_snapshot))

    total = sum(len(SECTIONS[s]['starts']) * len(SECTIONS[s]['grid']) for s in order)
    print(f"Sections: {order} | total {total} | remaining {len(jobs)} | workers {args.workers}", flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(run_job, *j): j for j in jobs}
        for i, _ in enumerate(as_completed(futures)):
            if args.pause and i < len(jobs) - 1:
                time.sleep(args.pause)

    done = [r for r in results if r['marks']]
    print(f"\nCompleted {len(done)} runs with marks.")
    out = os.path.join(BASE, '_sweep_pct25_runlog.txt')
    with open(out, 'w') as f:
        for r in sorted(results, key=lambda x: (x['section'], x['start'], x['label'])):
            f.write(f"sec{r['section']} {r['start']} {r['label']:36s} sharpe={r['sharpe']:.2f} trades={r['trades']} marks={r['marks']}\n")
    print('log ->', out)


if __name__ == '__main__':
    main()
