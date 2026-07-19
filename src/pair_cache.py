import os
import pickle
import pandas as pd
from typing import Dict, Tuple, Optional

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
