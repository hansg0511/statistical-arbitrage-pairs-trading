import os, sys
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))

from src.data_loader import DataLoader
from src.pair_selection import PairSelector
from src.walk_forward import FoldBuilder
from src.constants import TICKERS_CORE, SECTOR_MAP_CORE

START_DATES = ['2023-12-01', '2023-12-15', '2024-01-01', '2024-01-15', '2024-02-01']
END = '2026-01-01'
BASE_DIR = 'diagnosis/03_pair_stability'
SEL_MONTHS = 2
TEST_MONTHS = 3
SLIDE_MONTHS = 3
PVALUE = 0.05
LOG_SPACE = True

def run_start_date(sd):
    out_dir = os.path.join(BASE_DIR, sd)
    os.makedirs(out_dir, exist_ok=True)

    loader = DataLoader(TICKERS_CORE, start=sd, end=END, use_warmup=True)
    master_df = loader.fetch_prices()
    if master_df.empty:
        print(f"[FAIL] {sd}: No data fetched")
        return

    fb = FoldBuilder(sd, END, SEL_MONTHS, 0, TEST_MONTHS, SLIDE_MONTHS)
    selector = PairSelector(pvalue_threshold=PVALUE)
    rows_written = 0

    for i, fold in enumerate(fb.folds):
        sel_start, sel_end, _, _, test_start, test_end = fold
        viable_pairs = selector.select_pairs(
            master_df, SECTOR_MAP_CORE,
            str(sel_start), str(sel_end),
            same_sector_only=True,
            return_divergence_threshold=None,
            log_space=LOG_SPACE
        )
        out_path = os.path.join(out_dir, f'pair_ranking_fold{i}.csv')
        if viable_pairs.empty:
            pd.DataFrame(columns=[
                'pair', 'sector', 'rank',
                'cointegration_pvalue_log', 'half_life_log', 'correlation'
            ]).to_csv(out_path, index=False)
            print(f"  {sd} Fold {i}: 0 pairs")
        else:
            df_out = viable_pairs[[
                'pair', 'sector', 'cointegration_pvalue_log', 'half_life_log', 'correlation'
            ]].copy()
            df_out.insert(2, 'rank', range(1, len(df_out) + 1))
            df_out.to_csv(out_path, index=False)
            rows_written += len(df_out)
            print(f"  {sd} Fold {i}: {len(df_out)} pairs, best={df_out['pair'].iloc[0]} (p={df_out['cointegration_pvalue_log'].iloc[0]:.3f})")

    print(f"[DONE] {sd}: {rows_written} total pairs across {len(fb.folds)} folds")

print(f"Running rankings for {len(START_DATES)} start dates")
print(f"{'='*60}")

with ThreadPoolExecutor(max_workers=2) as ex:
    futures = {ex.submit(run_start_date, sd): sd for sd in START_DATES}
    for future in as_completed(futures):
        pass

print(f"\n{'='*60}")
print(f"All done. Output in {BASE_DIR}/")
