"""Reusable construction of selection-window pair pools."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from itertools import combinations
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from src.pair_selection import PairSelector


def close_prices_from_frame(prices: pd.DataFrame) -> pd.DataFrame:
    """Return the close-price table from either supported input shape."""
    if isinstance(prices.columns, pd.MultiIndex):
        if "Close" not in prices.columns.get_level_values(0):
            raise ValueError("price data has no Close columns")
        return prices["Close"]
    return prices


def selection_windows(
    start: str, stop: str, selection_months: int
) -> list[tuple[str, str]]:
    """Create month-stepped selection windows with stable ISO keys."""
    if selection_months < 1:
        raise ValueError("selection_months must be positive")
    current = pd.Timestamp(start)
    final = pd.Timestamp(stop)
    windows = []
    while current <= final:
        end = current + pd.DateOffset(months=selection_months) - pd.Timedelta(days=1)
        windows.append((current.date().isoformat(), end.date().isoformat()))
        current += pd.DateOffset(months=1)
    return windows


def _candidate_pairs(
    close_prices: pd.DataFrame,
    sector_map: Mapping[str, Sequence[str]],
    tickers: Iterable[str],
    cross_sector: bool,
) -> list[tuple[str, str, str]]:
    available = set(close_prices.columns).intersection(tickers)
    if cross_sector:
        groups = [("Cross-Sector", sorted(available))]
    else:
        groups = [
            (sector, sorted(available.intersection(sector_tickers)))
            for sector, sector_tickers in sector_map.items()
        ]
    return [
        (first, second, sector)
        for sector, group in groups
        for first, second in combinations(group, 2)
    ]


def _analyze_candidate(
    candidate: tuple[str, str, str], close_prices: pd.DataFrame, start: str, end: str
) -> dict[str, Any] | None:
    first, second, sector = candidate
    left = close_prices[first].loc[start:end].dropna()
    right = close_prices[second].loc[start:end].dropna()
    if len(left) < 20 or len(right) < 20:
        return None
    try:
        stats = PairSelector.analyze_pair(left, right)
    except Exception:
        return None
    return {
        "pair": f"{first}-{second}",
        "sector": sector,
        **stats,
        "period": f"{start} to {end}",
    }


def _passes_return_divergence(
    close_prices: pd.DataFrame,
    first: str,
    second: str,
    start: str,
    end: str,
    threshold: float | None,
) -> bool:
    if threshold is None:
        return True
    left = close_prices[first].loc[start:end].dropna()
    right = close_prices[second].loc[start:end].dropna()
    if left.empty or right.empty:
        return False
    left_return = left.iloc[-1] / left.iloc[0] - 1.0
    right_return = right.iloc[-1] / right.iloc[0] - 1.0
    return bool(
        np.isfinite(left_return)
        and np.isfinite(right_return)
        and abs(left_return - right_return) <= threshold
    )


def build_selection_window(
    prices: pd.DataFrame,
    sector_map: Mapping[str, Sequence[str]],
    tickers: Iterable[str],
    start: str,
    end: str,
    *,
    cross_sector: bool = True,
    return_divergence: float | None = None,
    workers: int = 1,
) -> pd.DataFrame:
    """Analyze one window and return an unfiltered, deterministic pair pool.

    Universe, sector, p-value, and half-life filters remain load-time concerns.
    Return divergence is the exception: it is an optional computational
    prefilter and is recorded in the pool metadata by the CLI builder.
    """
    if workers < 1:
        raise ValueError("workers must be positive")
    close_prices = close_prices_from_frame(prices)
    candidates = _candidate_pairs(close_prices, sector_map, tickers, cross_sector)
    candidates = [
        candidate
        for candidate in candidates
        if _passes_return_divergence(
            close_prices, candidate[0], candidate[1], start, end, return_divergence
        )
    ]

    if workers == 1 or len(candidates) < 2:
        rows = [
            row
            for candidate in candidates
            if (row := _analyze_candidate(candidate, close_prices, start, end)) is not None
        ]
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            rows = [
                row
                for row in executor.map(
                    _analyze_candidate,
                    candidates,
                    [close_prices] * len(candidates),
                    [start] * len(candidates),
                    [end] * len(candidates),
                )
                if row is not None
            ]

    if not rows:
        return pd.DataFrame()
    return (
        pd.DataFrame(rows)
        .sort_values(["cointegration_pvalue_log", "pair"], na_position="last")
        .reset_index(drop=True)
    )
