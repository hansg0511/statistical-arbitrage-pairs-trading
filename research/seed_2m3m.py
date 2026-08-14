import sys; sys.path.insert(0, '.')
import argparse, time, warnings
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from itertools import combinations
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
warnings.filterwarnings('ignore')

from src.constants import TICKERS_SP500, SECTOR_MAP_SP500
from src.data_loader import DataLoader
from src.pair_cache import PairSelectionCache, PoolCache
from src.signal import estimate_ar1

CACHE_DIR = 'research/cache_golden'
POOL_PATH = 'research/cache/sp500_2m.pkl'  # universe-free superset pool
N_WORKERS = 10
THREADS_PER_WORKER = 1
DIVERGENCE = 0.10
SEL_MONTHS = 2
PVALUE = 0.05

_global = {}


def vprint(msg):
    print(msg, flush=True)


def _init(master_df, sector_map):
    if isinstance(master_df.columns, pd.MultiIndex):
        _global['close'] = master_df['Close']
    else:
        _global['close'] = master_df


def _fast_analyze(pair_args):
    """Staged cointegration analysis: raw -> log, bail out early if filter fails."""
    t1_name, t2_name, c1, c2 = pair_args
    combined = pd.concat([c1, c2], axis=1).dropna()
    if len(combined) < 20:
        return None
    s1, s2 = combined.iloc[:, 0], combined.iloc[:, 1]

    try:
        _, pvalue, _ = coint(s1, s2)
        model = sm.OLS(s2, sm.add_constant(s1, has_constant='add')).fit()
        ar1 = estimate_ar1(model.resid)

        s1_log = np.log(s1)
        s2_log = np.log(s2)
        _, pvalue_log, _ = coint(s1_log, s2_log)
        model_log = sm.OLS(s2_log, sm.add_constant(s1_log, has_constant='add')).fit()
        ar1_log = estimate_ar1(model_log.resid)

        if len(model.params) < 2 or len(model_log.params) < 2:
            return None

        return {
            'pair': f'{t1_name}-{t2_name}',
            'cointegration_pvalue': pvalue,
            'correlation': s1.corr(s2),
            'half_life': ar1['half_life'],
            'hedge_ratio': model.params[1],
            'intercept': model.params[0],
            'phi': ar1['phi'],
            'sigma_eq': ar1['sigma_eq'],
            'cointegration_pvalue_log': pvalue_log,
            'correlation_log': s1_log.corr(s2_log),
            'half_life_log': ar1_log['half_life'],
            'hedge_ratio_log': model_log.params[1],
            'intercept_log': model_log.params[0],
            'phi_log': ar1_log['phi'],
            'sigma_eq_log': ar1_log['sigma_eq'],
        }
    except Exception:
        return None


def _process(sel_start, sel_end):
    try:
        return _process_impl(sel_start, sel_end)
    except Exception as e:
        import traceback
        vprint(f"  [ERROR] _process({sel_start}, {sel_end}): {e}")
        vprint(traceback.format_exc())
        return None


def _process_impl(sel_start, sel_end):
    g = _global
    t0 = time.time()
    close = g['close']
    sel_str = str(sel_start)
    end_str = str(sel_end)

    available = sorted([t for t in close.columns if t in TICKERS_SP500])
    sector_data = close.loc[sel_str:end_str, available]
    vprint(f"  [worker] Window {sel_str} to {end_str}: {len(available)} tickers, {len(sector_data)} days")

    # Fast divergence pre-filter
    t1 = time.time()
    candidates = []
    cols = list(sector_data.columns)
    for i in range(len(cols)):
        c1 = sector_data[cols[i]]
        r1 = c1.iloc[-1] / c1.iloc[0] - 1
        for j in range(i + 1, len(cols)):
            c2 = sector_data[cols[j]]
            r2 = c2.iloc[-1] / c2.iloc[0] - 1
            if abs(r1 - r2) <= DIVERGENCE:
                candidates.append((cols[i], cols[j]))
    vprint(f"  [worker]   divergence filter: {len(candidates)} candidates ({time.time()-t1:.0f}s)")

    # Thread-parallel staged cointegration analysis
    t2 = time.time()
    from concurrent.futures import as_completed
    results = []
    total_candidates = len(candidates)
    done = 0

    with ThreadPoolExecutor(max_workers=THREADS_PER_WORKER) as tex:
        fut_map = {}
        for t1_name, t2_name in candidates:
            pair_args = (t1_name, t2_name, sector_data[t1_name], sector_data[t2_name])
            fut_map[tex.submit(_fast_analyze, pair_args)] = t1_name
        t_submit = time.time()
        if len(candidates) > 0:
            vprint(f"  [worker]   submitted {len(candidates)} coint tasks ({t_submit-t2:.0f}s)")

        for future in as_completed(fut_map):
            done += 1
            result = future.result()
            if result is not None:
                results.append(result)
            if done == 1 or done % 5000 == 0:
                vprint(f"  [worker]   coint tests: {done}/{total_candidates} ({time.time()-t2:.0f}s)")

    vprint(f"  [worker]   coint tests complete: {len(results)}/{total_candidates} passed ({time.time()-t2:.0f}s)")

    df = pd.DataFrame(results)
    if 'sector' in df.columns:
        df.drop(columns=['sector'], inplace=True)

    if not len(results):
        vprint(f"  [worker]   WARNING: 0/{total_candidates} pairs passed for {sel_str}-{end_str}")

    # Store all pairs (filtering is done at load time in run_backtest.py)
    if len(df):
        df = df.sort_values('cointegration_pvalue_log', ascending=True)

    elapsed = time.time() - t0
    vprint(f"  [worker]   total: {elapsed:.0f}s -> {len(df)} pairs")
    return sel_str, df, elapsed


def main():
    parser = argparse.ArgumentParser(description='Seed pair selection cache for golden profile (SP500)')
    parser.add_argument('--test', action='store_true', help='Run 2 windows only')
    parser.add_argument('--workers', type=int, default=N_WORKERS, help='Number of parallel workers')
    parser.add_argument('--resume', action='store_true', help='Skip already-cached windows')
    args = parser.parse_args()

    vprint("Step 1/4: Fetching SP500 prices (2015-01-01 to 2026-01-01)...")
    t0 = time.time()
    loader = DataLoader(TICKERS_SP500, start='2015-01-01', end='2026-01-01', use_warmup=True)
    master_df = loader.fetch_prices()
    vprint(f"  Done: {master_df.shape} in {time.time()-t0:.0f}s")

    vprint("Step 2/4: Building selection windows...")
    all_windows = []
    curr = date(2015, 1, 1)
    stop = date(2015, 5, 1) if args.test else date(2025, 12, 31)
    while True:
        sel_end = curr + relativedelta(months=SEL_MONTHS) - timedelta(days=1)
        if curr > stop:
            break
        all_windows.append((curr, sel_end))
        curr += relativedelta(months=1)
    vprint(f"  Total windows: {len(all_windows)} ({all_windows[0][0]} to {all_windows[-1][1]})")

    pool = PoolCache(POOL_PATH)

    if args.resume and pool._data:
        existing = set(pool._data.keys())
        windows = [(s, e) for (s, e) in all_windows if str(s) not in existing]
        skipped = len(all_windows) - len(windows)
        vprint(f"  Resuming: {skipped} already cached, {len(windows)} remaining")
    else:
        windows = all_windows

    n_workers = min(args.workers, len(windows))
    vprint(f"Step 3/4: Starting pair selection ({n_workers} workers, {THREADS_PER_WORKER} threads/worker)")

    total_all = len(all_windows)
    completed_before = total_all - len(windows)
    total = len(windows)
    start_time = time.time()
    completed = 0

    retry_count = {}
    max_retries = 3
    with ProcessPoolExecutor(max_workers=n_workers, initializer=_init,
                             initargs=(master_df, SECTOR_MAP_SP500)) as ex:
        pending = set()
        fut_win = {}
        for s, e in windows:
            fut = ex.submit(_process, s, e)
            pending.add(fut)
            fut_win[fut] = (s, e)

        from concurrent.futures import as_completed
        while pending:
            for future in as_completed(pending):
                pending.remove(future)
                s, e = fut_win.pop(future)
                try:
                    result = future.result()
                except Exception as exc:
                    vprint(f"\n  [FATAL] Worker process crashed for {s} -> {e}: {exc}")
                    vprint(f"  Saving {len(pool._data)} completed windows and exiting.")
                    vprint(f"  Resuming: python research/seed_2m3m.py --resume --workers {args.workers}")
                    pool.save()
                    return

                if result is None:
                    retry_count[(s, e)] = retry_count.get((s, e), 0) + 1
                    if retry_count[(s, e)] <= max_retries:
                        vprint(f"  [RETRY {retry_count[(s, e)]}/{max_retries}] {s} -> {e}")
                        new_fut = ex.submit(_process, s, e)
                        pending.add(new_fut)
                        fut_win[new_fut] = (s, e)
                    else:
                        vprint(f"  [SKIP] {s} -> {e} failed after {max_retries} retries")
                    break

                sel_key, df, elapsed = result
                pool.set(sel_key, df)
                completed += 1
                total_elapsed = time.time() - start_time
                rate = total_elapsed / completed
                eta = rate * (total - completed) / 60
                overall = completed_before + completed
                vprint(f"[{overall}/{total_all}] {sel_key}  {len(df):>6,} pairs  "
                       f"took={elapsed:.0f}s  elapsed={total_elapsed/60:.1f}m  eta={eta:.0f}m")

                pool.save()
                vprint(f"  -> saved ({len(pool._data)} keys)")
                break

    total_time = time.time() - start_time
    vprint(f"\nStep 4/4: Done. {len(pool._data)} keys, {total_time/60:.1f}min total")
    vprint(f"Pool saved to {POOL_PATH}")


if __name__ == '__main__':
    main()
