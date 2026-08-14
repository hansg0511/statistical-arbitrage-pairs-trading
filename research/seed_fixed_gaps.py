"""Seed the pool keys missing for the fixed-period (aligned-window) reruns.

Fills every gap needed by fixed_diagnosis:
  - sp500_12m.pkl:  sel_starts 2014-01-01..2014-12-01 (12 keys) and
                    sel_starts 2023-01-01..2023-11-01 (11 keys)
  - sp500_2m.pkl:   sel_starts 2014-11-01, 2014-12-01
  - core_2m.pkl:    sel_starts 2014-11-01, 2014-12-01

Writes to the seeded source files (sp500_12m_recent.pkl, the golden/core
pair-selection caches); run research/rebuild_pools.py afterwards to fold the
new keys into the merged pool files used by run_backtest_parallel.
"""
import sys; sys.path.insert(0, '.')
import argparse, time, os, pickle, warnings
from datetime import date
from dateutil.relativedelta import relativedelta
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
warnings.filterwarnings('ignore')

from src.constants import TICKERS_SP500, SECTOR_MAP_SP500, TICKERS_CORE, SECTOR_MAP_CORE
from src.data_loader import DataLoader
from src.pair_cache import PoolCache, PairSelectionCache
from src.signal import estimate_ar1

CACHE_DIR = 'research/cache'
GOLDEN_DIR = 'research/cache_golden'
POOL_12M_RECENT = os.path.join(CACHE_DIR, 'sp500_12m_recent.pkl')
GOLDEN_CACHE = os.path.join(GOLDEN_DIR, 'pair_selection_cache.pkl')
CORE_CACHE = os.path.join(CACHE_DIR, 'pair_selection_cache.pkl')
N_WORKERS = 8
THREADS_PER_WORKER = 1
DIVERGENCE = 0.10
PVALUE = 0.05

_global = {}


def vprint(msg):
    print(msg, flush=True)


def _init(master_df, sector_map, ticker_list):
    if isinstance(master_df.columns, pd.MultiIndex):
        _global['close'] = master_df['Close']
    else:
        _global['close'] = master_df
    _global['sector_map'] = sector_map
    _global['ticker_list'] = ticker_list


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
    ticker_list = g['ticker_list']
    sel_str = str(sel_start)
    end_str = str(sel_end)

    available = sorted([t for t in close.columns if t in ticker_list])
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
    if not len(results):
        vprint(f"  [worker]   WARNING: 0/{total_candidates} pairs passed for {sel_str}-{end_str}")

    if len(df):
        df = df.sort_values('cointegration_pvalue_log', ascending=True)

    elapsed = time.time() - t0
    vprint(f"  [worker]   total: {elapsed:.0f}s -> {len(df)} pairs")
    return sel_str, df, elapsed


def run_windows(master_df, ticker_list, sector_map, windows, existing, label, n_workers=N_WORKERS):
    """Process windows in parallel, returning {sel_start: df} for new keys."""
    out = {}
    todo = [(s, e) for (s, e) in windows if str(s) not in existing]
    vprint(f"  {label}: {len(windows)} windows, {len(todo)} new")
    if not todo:
        return out

    n_workers = min(n_workers, len(todo))
    start_time = time.time()
    completed = 0
    retry_count = {}
    max_retries = 3
    with ProcessPoolExecutor(max_workers=n_workers, initializer=_init,
                             initargs=(master_df, sector_map, ticker_list)) as ex:
        pending = set()
        fut_win = {}
        for s, e in todo:
            fut = ex.submit(_process, s, e)
            pending.add(fut)
            fut_win[fut] = (s, e)

        while pending:
            for future in as_completed(pending):
                pending.remove(future)
                s, e = fut_win.pop(future)
                try:
                    result = future.result()
                except Exception as exc:
                    vprint(f"\n  [FATAL] Worker crashed for {s} -> {e}: {exc}")
                    return out
                if result is None:
                    retry_count[(s, e)] = retry_count.get((s, e), 0) + 1
                    if retry_count[(s, e)] <= max_retries:
                        vprint(f"  [RETRY {retry_count[(s,e)]}/{max_retries}] {s} -> {e}")
                        new_fut = ex.submit(_process, s, e)
                        pending.add(new_fut)
                        fut_win[new_fut] = (s, e)
                    else:
                        vprint(f"  [SKIP] {s} -> {e} failed after {max_retries} retries")
                    break
                sel_key, df, elapsed = result
                out[sel_key] = df
                completed += 1
                total_elapsed = time.time() - start_time
                rate = total_elapsed / completed
                eta = rate * (len(todo) - completed) / 60
                vprint(f"[{completed}/{len(todo)}] {sel_key}  {len(df):>6,} pairs  "
                       f"took={elapsed:.0f}s  elapsed={total_elapsed/60:.1f}m  eta={eta:.0f}m")
                break
    return out


def make_windows(start_date, stop_date, sel_months):
    windows = []
    curr = start_date
    while True:
        sel_end = curr + relativedelta(months=sel_months) - relativedelta(days=1)
        if curr > stop_date:
            break
        windows.append((curr, sel_end))
        curr += relativedelta(months=1)
    return windows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=N_WORKERS)
    parser.add_argument('--skip-12m-hist', action='store_true')
    parser.add_argument('--skip-12m-recent', action='store_true')
    parser.add_argument('--skip-2m', action='store_true')
    args = parser.parse_args()
    workers = args.workers

    # ============ 12m gaps (SP500 superset) -> sp500_12m_recent.pkl ============
    pool_recent = PoolCache(POOL_12M_RECENT)

    if not args.skip_12m_hist:
        # Historical gap: sel 2014-01..2014-12. Selection window spans 12 months,
        # so fetch from 2013-10-01 (warmup) through 2015-12-31.
        vprint("STEP 1/3: 12m historical gap (2014-01-01..2014-12-01)")
        t0 = time.time()
        loader = DataLoader(TICKERS_SP500, start='2013-10-01', end='2016-01-01', use_warmup=True)
        master = loader.fetch_prices()
        vprint(f"  fetched {master.shape} in {time.time()-t0:.0f}s")
        windows = make_windows(date(2014, 1, 1), date(2014, 12, 1), 12)
        new = run_windows(master, TICKERS_SP500, SECTOR_MAP_SP500, windows, set(pool_recent._data), '12m-hist', n_workers=workers)
        for k, df in new.items():
            pool_recent.set(k, df)
        pool_recent.save()
        vprint(f"  saved {len(new)} historical keys -> {POOL_12M_RECENT}")

    if not args.skip_12m_recent:
        # Recent gap: sel 2023-01..2023-11 (pool already has 2023-12 onward).
        vprint("STEP 2/3: 12m recent gap (2023-01-01..2023-11-01)")
        t0 = time.time()
        loader = DataLoader(TICKERS_SP500, start='2022-10-01', end='2025-01-01', use_warmup=True)
        master = loader.fetch_prices()
        vprint(f"  fetched {master.shape} in {time.time()-t0:.0f}s")
        windows = make_windows(date(2023, 1, 1), date(2023, 11, 1), 12)
        new = run_windows(master, TICKERS_SP500, SECTOR_MAP_SP500, windows, set(pool_recent._data), '12m-recent', n_workers=workers)
        for k, df in new.items():
            pool_recent.set(k, df)
        pool_recent.save()
        vprint(f"  saved {len(new)} recent keys -> {POOL_12M_RECENT}")

    # ============ 2m gaps -> golden + core pair-selection caches ============
    if not args.skip_2m:
        vprint("STEP 3/3: 2m gaps (2014-11-01, 2014-12-01) for sp500_2m and core_2m")
        t0 = time.time()
        loader = DataLoader(TICKERS_SP500, start='2014-09-01', end='2015-03-31', use_warmup=True)
        master = loader.fetch_prices()
        vprint(f"  fetched SP500 {master.shape} in {time.time()-t0:.0f}s")
        windows = make_windows(date(2014, 11, 1), date(2014, 12, 1), 2)
        start_to_end = {str(s): str(e) for s, e in windows}

        # --- golden cache (sp500_2m superset pool source; rows UNFILTERED) ---
        gc = PairSelectionCache(GOLDEN_DIR)
        new_g = run_windows(master, TICKERS_SP500, SECTOR_MAP_SP500, windows, set(), '2m-sp500-golden', n_workers=workers)
        for k, df in new_g.items():
            gc.set(('sp500', k, start_to_end[k], False), df)
        gc.save()
        vprint(f"  saved {len(new_g)} golden keys -> {GOLDEN_CACHE}")

        # --- core cache (core_2m pool source; pool is PREFILTERED, so rows
        #     must already satisfy pvalue_log<0.05 and half_life>0) ---
        loader_c = DataLoader(TICKERS_CORE, start='2014-09-01', end='2015-03-31', use_warmup=True)
        master_c = loader_c.fetch_prices()
        vprint(f"  fetched CORE {master_c.shape} in {time.time()-t0:.0f}s")
        cc = PairSelectionCache(CACHE_DIR)
        new_c = run_windows(master_c, TICKERS_CORE, SECTOR_MAP_CORE, windows, set(), '2m-core', n_workers=workers)
        ticker_to_sector = {}
        for sector, tickers in SECTOR_MAP_CORE.items():
            for t in tickers:
                ticker_to_sector[t] = sector

        def same_sector_mask(df):
            return df['pair'].apply(
                lambda p: ticker_to_sector.get(p.split('-')[0]) == ticker_to_sector.get(p.split('-')[1])
            )

        for k, df in new_c.items():
            if df is None or len(df) == 0:
                continue
            df = df[
                (df['cointegration_pvalue_log'] < PVALUE) & (df['half_life'] > 0)
            ].copy()
            df['sector'] = df['pair'].apply(
                lambda p: ticker_to_sector.get(p.split('-')[0], 'Unknown'))
            df['period'] = f'{k} to {start_to_end[k]}'
            df = df.sort_values('cointegration_pvalue_log', ascending=True)
            cc.set(('core', k, start_to_end[k], False), df)
            same = df[same_sector_mask(df)]
            if len(same):
                cc.set(('core', k, start_to_end[k], True), same)
            vprint(f"  [core {k}] filtered to {len(df)} pairs, same-sector {len(same)}")
        cc.save()
        vprint(f"  saved {len(new_c)} core keys -> {CORE_CACHE}")

    vprint("\nDONE. Run:  python research/rebuild_pools.py")


if __name__ == '__main__':
    main()
