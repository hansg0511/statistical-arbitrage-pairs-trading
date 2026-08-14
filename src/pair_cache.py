import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, List, Set

CacheKey = Tuple[str, str, str, bool]
FilteredCacheKey = Tuple[str, str, str, bool, float]

class PairSelectionCache:
    """
    Caches pair selection results.
    
    Two tiers:
      - _data (pair_selection_cache.pkl): keyed by (universe, sel_start, sel_end, same_sector)
      - _filtered (pair_selection_filtered.pkl): keyed by (universe, sel_start, sel_end, same_sector, threshold)
    
    Filtered cache stores results after return-divergence filtering, so re-running
    with the same threshold skips the filter step entirely.
    """
    def __init__(self, cache_dir: str = 'research/cache'):
        self.cache_dir = cache_dir
        self.cache_path = os.path.join(cache_dir, 'pair_selection_cache.pkl')
        self.filtered_path = os.path.join(cache_dir, 'pair_selection_filtered.pkl')
        self._data: Dict[CacheKey, pd.DataFrame] = {}
        self._filtered: Dict[FilteredCacheKey, pd.DataFrame] = {}
        os.makedirs(cache_dir, exist_ok=True)
        self._load()
        self._load_filtered()

    def _load(self):
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'rb') as f:
                    self._data = pickle.load(f)
            except Exception:
                self._data = {}

    def _load_filtered(self):
        if os.path.exists(self.filtered_path):
            try:
                with open(self.filtered_path, 'rb') as f:
                    self._filtered = pickle.load(f)
            except Exception:
                self._filtered = {}

    def save(self):
        with open(self.cache_path, 'wb') as f:
            pickle.dump(self._data, f)
        with open(self.filtered_path, 'wb') as f:
            pickle.dump(self._filtered, f)

    def get(self, key: CacheKey) -> Optional[pd.DataFrame]:
        df = self._data.get(key)
        if df is not None:
            return df.copy()
        return None

    def set(self, key: CacheKey, df: pd.DataFrame):
        self._data[key] = df.copy()

    def get_filtered(self, key: FilteredCacheKey) -> Optional[pd.DataFrame]:
        df = self._filtered.get(key)
        if df is not None:
            return df.copy()
        return None

    def set_filtered(self, key: FilteredCacheKey, df: pd.DataFrame):
        self._filtered[key] = df.copy()

    def clear(self):
        self._data = {}
        self._filtered = {}


class PoolCache:
    """
    Universe-free pool cache keyed by bare ``sel_start``.

    Pools are seeded with the full superset of candidate pairs (cointegration
    metrics, unfiltered rows) for a given selection window. Universe / sector /
    p-value / divergence filtering is deferred to load time via :meth:`select`.
    """
    def __init__(self, path: str, prefiltered: bool = False):
        self.path = path
        self.prefiltered = prefiltered
        self._data: Dict[str, pd.DataFrame] = {}
        if path and os.path.exists(path):
            with open(path, 'rb') as f:
                self._data = pickle.load(f)

    def get_pool(self, sel_start) -> Optional[pd.DataFrame]:
        df = self._data.get(str(sel_start))
        return df.copy() if df is not None else None

    def keys(self) -> List[str]:
        return sorted(self._data.keys())

    def has(self, sel_start) -> bool:
        return str(sel_start) in self._data

    def set(self, sel_start, df: pd.DataFrame):
        self._data[str(sel_start)] = df.copy()

    def save(self):
        if not self.path:
            return
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'wb') as f:
            pickle.dump(self._data, f)

    def select(self, sel_start, universe: str, sector_map, cross_sector: bool,
               pvalue: float = 0.05, return_divergence: Optional[float] = None,
               log_space: bool = True) -> pd.DataFrame:
        """
        Load the pool for ``sel_start`` and apply universe / sector / p-value /
        divergence masks. Returns an empty DataFrame if the window is missing.

        ``universe`` can be 'core' or 'sp500'. For ``cross_sector=False`` pairs
        are restricted to those whose tickers share a sector in ``sector_map``.
        """
        pool = self.get_pool(sel_start)
        empty = pd.DataFrame()
        if pool is None or pool.empty:
            return empty

        ticker_set = set()
        for sector, tickers in list(sector_map.items()):
            ticker_set.update(tickers)

        df = pool.copy()
        df = df[df['pair'].apply(lambda p: all(t in ticker_set for t in p.split('-')))]

        if df.empty:
            return df

        if not cross_sector:
            ticker_to_sector = {}
            for sector, tickers in sector_map.items():
                for t in tickers:
                    ticker_to_sector[t] = sector
            df = df[df['pair'].apply(
                lambda p: ticker_to_sector.get(p.split('-')[0]) == ticker_to_sector.get(p.split('-')[1])
            )]

        if df.empty:
            return df

        # Reproduce the seeding filter (PairSelector.select_pairs): significance
        # is always applied in log space, while the half-life filter uses the raw
        # half_life column. This is idempotent on pre-filtered core pools and
        # correctly prunes the unfiltered sp500 superset pools. Filtering on
        # half_life_log would wrongly drop rows whose raw half_life is valid but
        # whose log-space half-life is NaN (e.g. MDLZ-MO in 2015-02).
        #
        # Pre-filtered pools (core_2m) are a verbatim copy of the already-filtered
        # cache, so skipping the pvalue/half-life filter here preserves rows the
        # cache kept with NaN raw half_life (e.g. GE-MS in 2024-05-15).
        if not self.prefiltered:
            pcol = 'cointegration_pvalue_log' if 'cointegration_pvalue_log' in df.columns else 'cointegration_pvalue'
            hlcol = 'half_life' if 'half_life' in df.columns else 'half_life_log'
            if pcol in df.columns and hlcol in df.columns:
                df = df[(df[pcol] < pvalue) & (df[hlcol] > 0)]

        if return_divergence is not None and not df.empty:
            # Divergence requires live price data; the caller applies it
            # separately after selection. Nothing to do here.
            pass

        if df.empty:
            return df
        if 'cointegration_pvalue_log' in df.columns:
            return df.sort_values('cointegration_pvalue_log', ascending=True)
        return df.sort_values('cointegration_pvalue', ascending=True)
