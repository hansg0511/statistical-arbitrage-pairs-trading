"""Build a metadata-bearing selection pool from a price snapshot or yfinance."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

if __package__ in {None, ""}:  # Support both `python scripts/...` and `python -m ...`.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import POOL_12M, POOL_2M, POOL_CORE
from src.constants import (
    SECTOR_MAP_CORE,
    SECTOR_MAP_SP500,
    TICKERS_CORE,
    TICKERS_SP500,
)
from src.data_loader import DataLoader, load_or_fetch_prices
from src.pair_cache import PoolCache, PoolCacheError
from src.pool_builder import build_selection_window, close_prices_from_frame, selection_windows


def _default_output(selection_months: int, universe: str) -> str:
    if selection_months == 12 and universe == "sp500":
        return POOL_12M
    if selection_months == 2 and universe == "sp500":
        return POOL_2M
    return POOL_CORE


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection-start", required=True)
    parser.add_argument("--selection-stop", required=True)
    parser.add_argument("--selection-months", type=int, required=True)
    parser.add_argument("--universe", choices=["core", "sp500"], default="sp500")
    parser.add_argument("--same-sector", action="store_true")
    parser.add_argument("--return-divergence", type=float, default=None)
    parser.add_argument("--price-snapshot")
    parser.add_argument("--write-price-snapshot")
    parser.add_argument("--fetch-start")
    parser.add_argument("--fetch-end")
    parser.add_argument("--output")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    if args.price_snapshot and args.write_price_snapshot:
        parser.error("use either --price-snapshot or --write-price-snapshot")
    return args


def build_pool(argv=None) -> int:
    args = _parse_args(argv)
    tickers = TICKERS_SP500 if args.universe == "sp500" else TICKERS_CORE
    sector_map = SECTOR_MAP_SP500 if args.universe == "sp500" else SECTOR_MAP_CORE
    windows = selection_windows(
        args.selection_start, args.selection_stop, args.selection_months
    )
    if not windows:
        raise ValueError("selection range produced no windows")

    fetch_start = args.fetch_start or (
        pd.Timestamp(args.selection_start) - pd.Timedelta(days=300)
    ).date().isoformat()
    fetch_end = args.fetch_end or (
        pd.Timestamp(windows[-1][1]) + pd.Timedelta(days=8)
    ).date().isoformat()
    loader = DataLoader(tickers, start=fetch_start, end=fetch_end, use_warmup=False)
    prices, snapshot = load_or_fetch_prices(
        loader, args.price_snapshot, args.write_price_snapshot
    )
    close_prices = close_prices_from_frame(prices)

    output_path = args.output or _default_output(args.selection_months, args.universe)
    metadata = {
        "builder": "scripts.build_pair_pool",
        "universe": args.universe,
        "selection_months": args.selection_months,
        "cross_sector": not args.same_sector,
        "return_divergence_applied": args.return_divergence is not None,
        "return_divergence": args.return_divergence,
        "price_snapshot": snapshot,
    }
    try:
        pool = PoolCache(output_path)
    except PoolCacheError:
        raise
    if args.resume and os.path.isfile(output_path) and not pool.metadata:
        raise PoolCacheError(
            f"cannot resume legacy pool without metadata: {output_path}"
        )
    pool.metadata.update(metadata)

    pending = [window for window in windows if not (args.resume and pool.has(window[0]))]
    for index, (start, end) in enumerate(pending, 1):
        frame = build_selection_window(
            close_prices,
            sector_map,
            tickers,
            start,
            end,
            cross_sector=not args.same_sector,
            return_divergence=args.return_divergence,
            workers=args.workers,
        )
        pool.set(start, frame)
        pool.save()
        print(f"[{index}/{len(pending)}] {start} to {end}: {len(frame)} pairs")
    print(f"Saved {len(pool.keys())} windows to {Path(output_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build_pool())
