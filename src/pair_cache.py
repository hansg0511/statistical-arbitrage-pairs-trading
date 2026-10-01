"""Deterministic selection-pool storage and filtering."""

from __future__ import annotations

import os
import pickle
from typing import Any, Dict, List, Mapping, Optional

import numpy as np
import pandas as pd


class PoolCacheError(RuntimeError):
    """Raised when an existing pool cannot be read safely."""


def filter_pairs_by_half_life(
    df: Optional[pd.DataFrame], log_space: bool = True
) -> pd.DataFrame:
    """Keep only pairs with a finite, positive half-life in the active space."""
    if df is None:
        return pd.DataFrame()
    if df.empty:
        return df.copy()

    column = "half_life_log" if log_space else "half_life"
    if column not in df.columns:
        return df.iloc[0:0].copy()

    values = pd.to_numeric(df[column], errors="coerce")
    mask = values.notna()
    mask &= np.isfinite(values.to_numpy(dtype=float))
    mask &= values > 0
    return df.loc[mask].copy()


def filter_pairs_by_return_divergence(
    df: Optional[pd.DataFrame],
    close_prices: pd.DataFrame,
    start: str,
    end: str,
    max_divergence: float,
) -> pd.DataFrame:
    """Apply the explicit cumulative-return prefilter to candidate pairs."""
    if df is None or df.empty:
        return pd.DataFrame() if df is None else df.copy()
    if "pair" not in df.columns:
        return df.iloc[0:0].copy()

    window = close_prices.loc[start:end]
    keep = []
    for pair in df["pair"]:
        tickers = str(pair).split("-")
        if len(tickers) != 2 or any(t not in window.columns for t in tickers):
            keep.append(False)
            continue
        first, second = (window[t].dropna() for t in tickers)
        if first.empty or second.empty:
            keep.append(False)
            continue
        r1 = first.iloc[-1] / first.iloc[0] - 1
        r2 = second.iloc[-1] / second.iloc[0] - 1
        keep.append(np.isfinite(r1) and np.isfinite(r2) and abs(r1 - r2) <= max_divergence)
    return df.loc[keep].copy()


class PoolCache:
    """Window-keyed pair pool with explicit provenance metadata.

    New files are pickled as ``{"schema_version": 1, "metadata": ..., 
    "pools": {selection_start: dataframe}}``. A plain dictionary is accepted
    for reading old local pools, but new writes always use the documented form.
    """

    SCHEMA_VERSION = 1

    def __init__(self, path: str | None, metadata: Optional[Mapping[str, Any]] = None):
        self.path = path
        self.metadata: Dict[str, Any] = dict(metadata or {})
        self._data: Dict[str, pd.DataFrame] = {}
        if not path or not os.path.exists(path):
            return
        try:
            with open(path, "rb") as handle:
                payload = pickle.load(handle)
        except (OSError, pickle.PickleError, EOFError, ValueError, TypeError) as exc:
            raise PoolCacheError(f"cannot read pair pool {path}: {exc}") from exc

        if isinstance(payload, dict) and "pools" in payload:
            version = payload.get("schema_version")
            if version != self.SCHEMA_VERSION:
                raise PoolCacheError(
                    f"unsupported pair-pool schema {version!r} in {path}"
                )
            self.metadata.update(payload.get("metadata") or {})
            pools = payload["pools"]
        else:
            pools = payload
        if not isinstance(pools, dict) or any(
            not isinstance(frame, pd.DataFrame) for frame in pools.values()
        ):
            raise PoolCacheError(f"pair pool has invalid contents: {path}")
        self._data = {str(key): frame.copy() for key, frame in pools.items()}

    @property
    def data(self) -> Dict[str, pd.DataFrame]:
        """Return a defensive copy of the cached windows."""
        return {key: frame.copy() for key, frame in self._data.items()}

    @property
    def divergence_applied(self) -> bool:
        """Whether the builder already applied return-divergence filtering."""
        return bool(self.metadata.get("return_divergence_applied", False))

    @property
    def divergence_threshold(self) -> Optional[float]:
        value = self.metadata.get("return_divergence")
        return float(value) if value is not None else None

    def divergence_matches(self, threshold: Optional[float]) -> bool:
        """Return whether this pool was filtered at the requested threshold."""
        if threshold is None:
            return True
        return self.divergence_applied and self.divergence_threshold == float(threshold)

    def get_pool(self, sel_start: Any) -> Optional[pd.DataFrame]:
        frame = self._data.get(str(sel_start))
        return frame.copy() if frame is not None else None

    def keys(self) -> List[str]:
        return sorted(self._data)

    def has(self, sel_start: Any) -> bool:
        return str(sel_start) in self._data

    def set(self, sel_start: Any, df: pd.DataFrame) -> None:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("pair pool entries must be pandas DataFrames")
        self._data[str(sel_start)] = df.copy()

    def save(self) -> None:
        if not self.path:
            raise ValueError("cannot save a pool without an output path")
        parent = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(parent, exist_ok=True)
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "metadata": dict(self.metadata),
            "pools": self._data,
        }
        with open(self.path, "wb") as handle:
            pickle.dump(payload, handle)

    def select(
        self,
        sel_start: Any,
        universe: str,
        sector_map: Mapping[str, List[str]],
        cross_sector: bool,
        pvalue: float = 0.05,
        log_space: bool = True,
    ) -> pd.DataFrame:
        """Apply universe, sector, significance, and half-life filters.

        Return-divergence is intentionally not an argument here. It is either
        applied while building the pool or applied explicitly by the runner
        with the same price snapshot used for the experiment.
        """
        pool = self.get_pool(sel_start)
        if pool is None or pool.empty or "pair" not in pool.columns:
            return pd.DataFrame(columns=pool.columns if pool is not None else None)

        ticker_to_sector = {
            ticker: sector
            for sector, tickers in sector_map.items()
            for ticker in tickers
        }
        ticker_set = set(ticker_to_sector)

        def in_universe(pair: Any) -> bool:
            parts = str(pair).split("-")
            return len(parts) == 2 and all(t in ticker_set for t in parts)

        df = pool.loc[pool["pair"].map(in_universe)].copy()
        if not cross_sector:
            df = df.loc[
                df["pair"].map(
                    lambda pair: ticker_to_sector.get(str(pair).split("-")[0])
                    == ticker_to_sector.get(str(pair).split("-")[1])
                )
            ]
        if df.empty:
            return df

        pvalue_column = (
            "cointegration_pvalue_log"
            if log_space and "cointegration_pvalue_log" in df.columns
            else "cointegration_pvalue"
        )
        if pvalue_column in df.columns:
            values = pd.to_numeric(df[pvalue_column], errors="coerce")
            df = df.loc[values.notna() & (values < pvalue)]
        df = filter_pairs_by_half_life(df, log_space=log_space)
        if df.empty:
            return df
        return df.sort_values(pvalue_column if pvalue_column in df.columns else "pair")
