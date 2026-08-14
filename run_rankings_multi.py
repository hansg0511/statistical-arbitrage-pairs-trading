import os, sys, pickle
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))

from src.data_loader import DataLoader
from src.pair_selection import PairSelector
from src.walk_forward import FoldBuilder
from src.constants import TICKERS_CORE, SECTOR_MAP_CORE

START_DATES = ['2023-12-01', '2023-12-15', '2024-01-01', '2024-01-15', '2024-02-01']
END = '2026-01-01'
CACHE_PATH = 'research/cache/pair_selection_cache.pkl'
SEL_MONTHS = 2
TEST_MONTHS = 3
PVALUE = 0.05
LOG_SPACE = True

# Configs to run: (cross_sector, slide_months, out_dir_name)
CONFIGS = [
    (True, 1, '03a_cross_sector_slide1m'),
    (True, 3, '03b_cross_sector_slide3m'),
    (False, 1, '03c_same_sector_slide1m'),
]

lock = __import__('threading').Lock()

def run_config(cross_sector, slide, label):
    same_sector_only = not cross_sector
    base_dir = os.path.join('diagnosis', label)
    os.makedirs(base_dir, exist_ok=True)

    # Load shared cache
    with lock:
        with open(CACHE_PATH, 'rb') as f:
            cache = pickle.load(f)

    loader = DataLoader(TICKERS_CORE, start=START_DATES[0], end=END, use_warmup=True)
    master_df = loader.fetch_prices()
    if master_df.empty:
        print(f"[FAIL] {label}: No data")
        return

    # Prepare price data for divergence filter
    close_prices = master_df['Close'] if isinstance(master_df.columns, pd.MultiIndex) else master_df

    selector = PairSelector(pvalue_threshold=PVALUE)
    cache_modified = False

    for sd in START_DATES:
        out_dir = os.path.join(base_dir, sd)
        os.makedirs(out_dir, exist_ok=True)

        fb = FoldBuilder(sd, END, SEL_MONTHS, 0, TEST_MONTHS, slide)
        folds_ok = 0

        for i, fold in enumerate(fb.folds):
            sel_start, sel_end, _, _, test_start, test_end = fold
            key = ('core', str(sel_start), str(sel_end), same_sector_only)

            if key in cache:
                df = cache[key].copy()
                src = 'cache'
            else:
                df = selector.select_pairs(
                    master_df, SECTOR_MAP_CORE,
                    str(sel_start), str(sel_end),
                    same_sector_only=same_sector_only,
                    return_divergence_threshold=None,  # cache stores without divergence
                    log_space=LOG_SPACE
                )
                with lock:
                    cache[key] = df
                    cache_modified = True
                src = 'computed'

            # Apply return divergence filter (matches backtest logic)
            if cross_sector and not df.empty:
                sel_data = close_prices.loc[str(sel_start):str(sel_end)]
                mask = []
                for _, row in df.iterrows():
                    t1, t2 = row['pair'].split('-')
                    if t1 in sel_data.columns and t2 in sel_data.columns:
                        r1 = sel_data[t1].iloc[-1] / sel_data[t1].iloc[0] - 1
                        r2 = sel_data[t2].iloc[-1] / sel_data[t2].iloc[0] - 1
                        mask.append(abs(r1 - r2) <= 0.1)
                    else:
                        mask.append(False)
                df = df[mask].reset_index(drop=True)

            out_path = os.path.join(out_dir, f'pair_ranking_fold{i}.csv')
            if df.empty:
                pd.DataFrame(columns=[
                    'pair', 'sector', 'rank',
                    'cointegration_pvalue_log', 'half_life_log', 'correlation'
                ]).to_csv(out_path, index=False)
            else:
                out = df[['pair', 'sector', 'cointegration_pvalue_log', 'half_life_log', 'correlation']].copy()
                out.insert(2, 'rank', range(1, len(out) + 1))
                out.to_csv(out_path, index=False)
                folds_ok += 1

        print(f"  {label} {sd}: {folds_ok}/{len(fb.folds)} folds, {src if folds_ok > 0 else 'no data'}")

    if cache_modified:
        with lock:
            with open(CACHE_PATH, 'wb') as f:
                pickle.dump(cache, f)
        print(f"  {label}: cache updated")

    print(f"[DONE] {label}")

print(f"Running 3 configs x 5 start dates (2 concurrent)")
print(f"{'='*60}")

with ThreadPoolExecutor(max_workers=2) as ex:
    futures = {ex.submit(run_config, cs, sl, lbl): lbl for cs, sl, lbl in CONFIGS}
    for future in as_completed(futures):
        pass

print(f"\n{'='*60}")
print("All done")
