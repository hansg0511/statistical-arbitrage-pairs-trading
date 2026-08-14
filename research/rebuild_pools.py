import sys; sys.path.insert(0, '.')
import os
import pickle
import argparse
import pandas as pd

from src.constants import SECTOR_MAP_CORE

CACHE_DIR = 'research/cache'

POOL_12M = os.path.join(CACHE_DIR, 'sp500_12m.pkl')
POOL_12M_RECENT = os.path.join(CACHE_DIR, 'sp500_12m_recent.pkl')
POOL_2M = os.path.join(CACHE_DIR, 'sp500_2m.pkl')
POOL_CORE = os.path.join(CACHE_DIR, 'core_2m.pkl')


def rekey_sp500_12m(src):
    # huck2015_pvalues.pkl is already keyed by bare sel_start; copy verbatim.
    with open(src, 'rb') as f:
        data = pickle.load(f)
    return data


def rekey_sp500_2m(src):
    # golden cache keyed by ('sp500', sel_start, sel_end, False) -> bare sel_start
    with open(src, 'rb') as f:
        raw = pickle.load(f)
    out = {}
    for key, df in raw.items():
        sel_start = key[1]
        if sel_start in out:
            out[sel_start] = pd.concat([out[sel_start], df]).drop_duplicates(subset='pair').reset_index(drop=True)
        else:
            out[sel_start] = df.copy().reset_index(drop=True)
    return out


def rekey_core_2m(src):
    # core cache keyed by ('core', sel_start, sel_end, same_sector). Merge the
    # cross-sector (False) and same-sector (True) pools per sel_start into one
    # frame, adding a sector column derived from SECTOR_MAP_CORE.
    with open(src, 'rb') as f:
        raw = pickle.load(f)
    ticker_to_sector = {}
    for sector, tickers in SECTOR_MAP_CORE.items():
        for t in tickers:
            ticker_to_sector[t] = sector
    out = {}
    for key, df in raw.items():
        sel_start = key[1]
        df = df.copy()
        df['sector'] = df['pair'].apply(
            lambda p: ticker_to_sector.get(p.split('-')[0], 'Unknown')
        )
        try:
            cur = out[sel_start]
            merged = pd.concat([cur, df]).drop_duplicates(subset='pair').reset_index(drop=True)
            out[sel_start] = merged
        except KeyError:
            out[sel_start] = df.reset_index(drop=True)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()

    def save(path, obj):
        if args.test:
            print(f"[dry] would write {path}: {len(obj)} keys")
        else:
            with open(path, 'wb') as f:
                pickle.dump(obj, f)
            print(f"wrote {path}: {len(obj)} keys")

    # 1) sp500_12m.pkl (merged: historical 2015-2020 + recent 2023-2025)
    src_12 = os.path.join(CACHE_DIR, 'huck2015_pvalues.pkl')
    data_12 = rekey_sp500_12m(src_12)

    # Fold the recent 12m windows (2023-12-01..2025-10-01) into the same file so
    # the 12m pool covers both eras (no overlapping keys). Recent rows lack the
    # informational `period` / `*_norm` columns; align them to the historical schema.
    hist_cols = list(next(iter(data_12.values())).columns)
    if os.path.exists(POOL_12M_RECENT):
        with open(POOL_12M_RECENT, 'rb') as f:
            recent = pickle.load(f)
        for k, df in recent.items():
            if k in data_12:
                continue
            for col in hist_cols:
                if col not in df.columns:
                    df = df.copy()
                    df[col] = pd.NA
            data_12[k] = df[hist_cols].reset_index(drop=True)
    save(POOL_12M, data_12)

    # 2) sp500_2m.pkl (superset pool, divergence 0.10 baked at seed)
    src_2m = os.path.join('research/cache_golden', 'pair_selection_cache.pkl')
    data_2m = rekey_sp500_2m(src_2m)
    save(POOL_2M, data_2m)

    # 3) core_2m.pkl (no divergence, pvalue<0.05 baked, merges same+cross)
    src_core = os.path.join(CACHE_DIR, 'pair_selection_cache.pkl')
    data_core = rekey_core_2m(src_core)
    save(POOL_CORE, data_core)


if __name__ == '__main__':
    main()