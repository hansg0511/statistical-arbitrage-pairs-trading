"""Decompose the old winner's V1/V2 performance by gross exposure.

This focused experiment reads the preserved old-winner raw runs, trade logs,
daily marks, and the exact price snapshots recorded by those runs. It performs
only the two-leg recent replay for the five preserved starts and both existing
combined mechanisms. It does not run the standalone strategy generator or the
full strategy/book matrix.

The combined replay is the existing autopsy replay with additional marked
position exposure accounting. V1 quantities are reconstructed from the V1
reference-leg sizing convention using the matched V2 entry metadata, because
the archived V1 trade logs predate the later exposure metadata fields.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.run_combined_backtest import metrics as replay_metrics  # noqa: E402
from research.run_old_winner_v1_v2_autopsy import (  # noqa: E402
    LEG_SPECS,
    V1_ROOT,
    V2_ROOT,
    _match_trades,
    allocator_path,
    load_leg_run,
    simulate_trace,
)


AUTOPSY_ROOT = ROOT / "results" / "old_winner_v1_v2_autopsy"
DAILY_CONTRIBUTIONS_PATH = AUTOPSY_ROOT / "daily_contributions_recent.csv"
COMBINED_SERIES_PATH = AUTOPSY_ROOT / "combined_return_series.csv"
ALLOCATOR_PATH_PATH = AUTOPSY_ROOT / "allocator_path.csv"
COUNTERFACTUAL_PATH = AUTOPSY_ROOT / "counterfactual_results.csv"
PUBLIC_SCORE_PATH = ROOT / "results" / "final" / "rankings" / "clean40_pair_scores.csv"

OUTPUT_PATH = AUTOPSY_ROOT / "gross_exposure_comparison_recent.csv"
COUNTERFACTUAL_OUTPUT_PATH = AUTOPSY_ROOT / "gross_exposure_matched_counterfactuals.csv"
SUMMARY_JSON_PATH = AUTOPSY_ROOT / "gross_exposure_summary.json"
SUMMARY_MD_PATH = AUTOPSY_ROOT / "gross_exposure_summary.md"

INITIAL_CAPITAL = 1_000_000.0
SIZING_BUDGET = 250_000.0
EPSILON = 1e-9
METRIC_COLUMNS = ("annualized_return", "annualized_volatility", "sharpe", "max_drawdown")
EXPOSURE_TOLERANCE = 1e-6


def _git_value(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _num(value, default=float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result


def _finite(value) -> bool:
    return math.isfinite(_num(value))


def _iso(value) -> str:
    return pd.Timestamp(value).date().isoformat()


def _timestamp(value) -> pd.Timestamp:
    return pd.Timestamp(value).normalize()


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...], path: Path) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{path} is missing columns: {missing}")


def _run_path(version: str, leg: str, start_index: int) -> Path:
    spec = LEG_SPECS[leg]
    root = V1_ROOT if version == "v1" else V2_ROOT
    start = spec["recent_starts"][start_index]
    return root / spec["recent_section"] / f"{start}_{spec['config']}"


def _load_metrics(path: Path) -> dict:
    with (path / "metrics.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def _close_frame(snapshot_path: Path) -> pd.DataFrame:
    frame = pd.read_pickle(snapshot_path)
    close = frame["Close"] if isinstance(frame.columns, pd.MultiIndex) else frame
    close = close.copy()
    close.index = pd.to_datetime(close.index).normalize()
    return close.sort_index()


def _resolve_pair_tickers(pair: str, columns) -> tuple[str, str]:
    available = {str(column) for column in columns}
    for split in range(1, len(pair) - 1):
        left = pair[:split]
        right = pair[split + 1 :]
        if left in available and right in available:
            return left, right
    raise ValueError(f"could not resolve tickers for pair {pair!r}")


def _load_snapshots(run_paths: dict[tuple[str, str], Path]) -> tuple[dict, list[dict]]:
    snapshots: dict[str, pd.DataFrame] = {}
    provenance = []
    for (version, leg), run_path in sorted(run_paths.items()):
        metrics = _load_metrics(run_path)
        raw_path = Path(metrics.get("price_snapshot", ""))
        if not raw_path.is_file():
            raise FileNotFoundError(
                f"preserved price snapshot is missing for {version}/{leg}: {raw_path}"
            )
        key = str(raw_path.resolve())
        if key not in snapshots:
            snapshots[key] = _close_frame(raw_path)
        actual_hash = _sha256(raw_path)
        expected_hash = metrics.get("price_snapshot_sha256")
        provenance.append(
            {
                "version": version,
                "leg": leg,
                "run_path": str(run_path.relative_to(ROOT)),
                "snapshot_path": str(raw_path),
                "snapshot_sha256": actual_hash,
                "expected_snapshot_sha256": expected_hash,
                "hash_match": actual_hash == expected_hash,
            }
        )
    return snapshots, provenance


def _price(close: pd.DataFrame, date: pd.Timestamp, ticker: str) -> float:
    if date not in close.index or ticker not in close.columns:
        raise ValueError(f"missing marked price for {ticker} on {_iso(date)}")
    value = close.at[date, ticker]
    if not _finite(value):
        raise ValueError(f"non-finite marked price for {ticker} on {_iso(date)}")
    return float(value)


def _audit_sides(v2_run: dict) -> dict[tuple, tuple[str, str]]:
    audit = v2_run.get("sizing_audit", pd.DataFrame())
    if audit.empty:
        raise ValueError("V2 sizing audit is required to recover per-leg trade sides")
    required = {"date", "pair", "fold_id", "side1", "side2", "status"}
    if not required.issubset(audit.columns):
        raise ValueError(f"V2 sizing audit is missing side columns: {sorted(required - set(audit.columns))}")
    submitted = audit[audit["status"].astype(str).eq("orders_submitted")].copy()
    sides = {}
    for _, row in submitted.iterrows():
        key = (
            int(_num(row["fold_id"])),
            str(row["pair"]),
            _timestamp(row["date"]),
        )
        value = (str(row["side1"]), str(row["side2"]))
        if key in sides and sides[key] != value:
            raise ValueError(f"conflicting sides in V2 sizing audit for {key}")
        sides[key] = value
    return sides


def _native_metadata(
    pair: dict,
    version: str,
    close: pd.DataFrame,
    sides: tuple[str, str],
) -> dict:
    common_raw = pair["v2_raw"]
    raw = pair["v1_raw"] if version == "v1" else common_raw
    if version == "v1":
        size1 = _num(pair["v1_size1"])
        size2 = _num(pair["v1_size2"])
    else:
        size1 = _num(common_raw.get("size1"))
        size2 = _num(common_raw.get("size2"))
    if not _finite(size1) or not _finite(size2):
        raise ValueError(f"missing native sizes for {pair['pair']} ({version})")
    entry_price1 = _num(common_raw.get("entry_price1"), _num(common_raw.get("sizing_price1")))
    entry_price2 = _num(common_raw.get("entry_price2"), _num(common_raw.get("sizing_price2")))
    ticker1, ticker2 = _resolve_pair_tickers(pair["pair"], close.columns)
    entry = _timestamp(pair["entry"])
    snapshot_price1 = _price(close, entry, ticker1)
    snapshot_price2 = _price(close, entry, ticker2)
    if abs(snapshot_price1 - entry_price1) > EPSILON or abs(snapshot_price2 - entry_price2) > EPSILON:
        raise ValueError(
            f"entry price mismatch for {pair['pair']} ({version}) on {_iso(entry)}"
        )
    target_notional = _num(raw.get("target_notional"), SIZING_BUDGET)
    if not _finite(target_notional) or target_notional <= 0:
        target_notional = SIZING_BUDGET
    return {
        "key": pair["key"],
        "pair": pair["pair"],
        "version": version,
        "size1": float(size1),
        "size2": float(size2),
        "side1": sides[0],
        "side2": sides[1],
        "ticker1": ticker1,
        "ticker2": ticker2,
        "entry": _timestamp(pair["entry"]),
        "exit": _timestamp(pair["exit"]),
        "target_notional": float(target_notional),
        "entry_price1": float(entry_price1),
        "entry_price2": float(entry_price2),
        "entry_price1_snapshot_difference": float(snapshot_price1 - entry_price1),
        "entry_price2_snapshot_difference": float(snapshot_price2 - entry_price2),
    }


def _empty_exposure() -> dict[str, float]:
    return {
        "a_long": 0.0,
        "a_short": 0.0,
        "b_long": 0.0,
        "b_short": 0.0,
    }


def _add_exposure(destination: dict[str, float], book_leg: str, side: str, value: float) -> None:
    if side not in ("long", "short"):
        raise ValueError(f"unknown trade side: {side!r}")
    destination[f"{book_leg.lower()}_{side}"] += abs(float(value))


def _position_exposure(
    trace: dict,
    leg_data: dict,
    metadata: dict[tuple, dict],
    close_by_leg: dict[str, pd.DataFrame],
    dates: list[pd.Timestamp],
) -> tuple[dict[pd.Timestamp, dict[str, float]], dict[pd.Timestamp, dict[str, float]]]:
    """Return end-of-day and beginning-of-interval marked exposure.

    End-of-day exposure follows the source backtest's market-order timing:
    positions are live from the first observed close after the entry signal
    through the exit signal date, before the close order fills. The beginning
    exposure is priced at the prior observed close and supports the PnL interval
    represented by the date's daily PnL.
    """
    eod = {date: _empty_exposure() for date in dates}
    beginning = {date: _empty_exposure() for date in dates}
    date_index = list(dates)
    for book_leg in ("A", "B"):
        close = close_by_leg[book_leg]
        for trade in leg_data[book_leg]["trades"]:
            key = trade["trade_key"]
            allocation = _num(trace["allocations"].get(key), 0.0)
            if not _finite(allocation) or allocation <= 0:
                continue
            meta = metadata[key]
            scale = allocation / meta["target_notional"]
            if not _finite(scale) or scale <= 0:
                raise ValueError(f"invalid replay allocation for {meta['pair']}")
            lo = bisect.bisect_right(date_index, meta["entry"])
            hi = bisect.bisect_right(date_index, meta["exit"])
            for index in range(lo, hi):
                date = date_index[index]
                price1 = _price(close, date, meta["ticker1"])
                price2 = _price(close, date, meta["ticker2"])
                _add_exposure(
                    eod[date],
                    book_leg,
                    meta["side1"],
                    meta["size1"] * scale * price1,
                )
                _add_exposure(
                    eod[date],
                    book_leg,
                    meta["side2"],
                    meta["size2"] * scale * price2,
                )

            # The close-to-close PnL on an exit date is supported by the
            # prior close, so include the position through its exit date here.
            begin_lo = bisect.bisect_right(date_index, meta["entry"])
            begin_hi = bisect.bisect_right(date_index, meta["exit"])
            for index in range(begin_lo, begin_hi):
                date = date_index[index]
                prior_date = date_index[index - 1]
                price1 = _price(close, prior_date, meta["ticker1"])
                price2 = _price(close, prior_date, meta["ticker2"])
                _add_exposure(
                    beginning[date],
                    book_leg,
                    meta["side1"],
                    meta["size1"] * scale * price1,
                )
                _add_exposure(
                    beginning[date],
                    book_leg,
                    meta["side2"],
                    meta["size2"] * scale * price2,
                )
    return eod, beginning


def _validate_native_v2_exposure(
    run_path: Path,
    v2_run: dict,
    metadata: dict[tuple, dict],
    close: pd.DataFrame,
    start_index: int,
    leg: str,
) -> dict:
    exposure_path = run_path / "daily_exposure.csv"
    if not exposure_path.is_file():
        raise FileNotFoundError(f"missing preserved V2 exposure file: {exposure_path}")
    native = pd.read_csv(exposure_path, parse_dates=["date"])
    required = ("date", "fold_id", "gross_long", "gross_short", "gross_exposure", "open_pairs")
    _require_columns(native, required, exposure_path)
    native["date"] = pd.to_datetime(native["date"]).dt.normalize()
    native["fold_id"] = pd.to_numeric(native["fold_id"], errors="raise").astype(int)
    if native.duplicated(["date", "fold_id"]).any():
        raise ValueError(f"duplicate V2 exposure observations in {exposure_path}")

    calculated = {}
    for _, row in native.iterrows():
        date = row["date"]
        fold_id = int(row["fold_id"])
        long_exposure = 0.0
        short_exposure = 0.0
        open_pairs = 0
        for trade in v2_run["trades"]:
            if int(trade["fold_id"]) != fold_id:
                continue
            if not (trade["entry"] < date <= trade["exit"]):
                continue
            meta = metadata[trade["trade_key"]]
            price1 = _price(close, date, meta["ticker1"])
            price2 = _price(close, date, meta["ticker2"])
            leg1 = meta["size1"] * price1
            leg2 = meta["size2"] * price2
            if meta["side1"] == "long":
                long_exposure += leg1
            else:
                short_exposure += leg1
            if meta["side2"] == "long":
                long_exposure += leg2
            else:
                short_exposure += leg2
            open_pairs += 1
        calculated[(date, fold_id)] = {
            "gross_long": long_exposure,
            "gross_short": short_exposure,
            "gross_exposure": long_exposure + short_exposure,
            "open_pairs": open_pairs,
        }

    max_differences = {column: 0.0 for column in required[2:]}
    mismatch_count = 0
    for _, row in native.iterrows():
        expected = calculated[(row["date"], int(row["fold_id"]))]
        differences = {
            column: abs(float(row[column]) - float(expected[column]))
            for column in ("gross_long", "gross_short", "gross_exposure")
        }
        differences["open_pairs"] = abs(int(row["open_pairs"]) - expected["open_pairs"])
        for column, difference in differences.items():
            max_differences[column] = max(max_differences[column], float(difference))
        if any(difference > EXPOSURE_TOLERANCE for difference in differences.values()):
            mismatch_count += 1

    return {
        "start_index": start_index,
        "leg": leg,
        "run_path": str(run_path.relative_to(ROOT)),
        "rows": int(len(native)),
        "mismatch_rows": mismatch_count,
        "max_abs_differences": max_differences,
        "status": "pass" if mismatch_count == 0 else "fail",
    }


def _gross(exposure: dict[str, float], book_leg: str | None = None) -> float:
    if book_leg:
        prefix = book_leg.lower()
        return float(exposure[f"{prefix}_long"] + exposure[f"{prefix}_short"])
    return float(
        exposure["a_long"]
        + exposure["a_short"]
        + exposure["b_long"]
        + exposure["b_short"]
    )


def _net(exposure: dict[str, float], book_leg: str | None = None) -> float:
    if book_leg:
        prefix = book_leg.lower()
        return float(exposure[f"{prefix}_long"] - exposure[f"{prefix}_short"])
    return float(
        exposure["a_long"]
        + exposure["b_long"]
        - exposure["a_short"]
        - exposure["b_short"]
    )


def _trace_map(trace: dict) -> dict[pd.Timestamp, dict]:
    return {_timestamp(row["date"]): row for row in trace["rows"]}


def _aligned_max_difference(left: pd.Series, right: pd.Series) -> float:
    merged = pd.concat(
        [left.rename("left"), right.rename("right")],
        axis=1,
        join="inner",
        sort=False,
    ).dropna()
    if merged.empty:
        raise ValueError("cannot compare empty or non-overlapping allocator paths")
    return float((merged["left"] - merged["right"]).abs().max())


def _series_metrics(series: pd.Series) -> dict[str, float | int]:
    result = replay_metrics(series)
    return {
        "final_equity": float((1.0 + series).prod()),
        "cumulative_return": float((1.0 + series).prod() - 1.0),
        "annualized_return": float(result["ann_ret"]),
        "annualized_volatility": float(result["ann_vol"]),
        "sharpe": float(result["sharpe"]),
        "max_drawdown": float(result["mdd"]),
        "n_days": int(series.dropna().shape[0]),
    }


def _account_path(
    pnls: pd.Series, dates: pd.DatetimeIndex
) -> tuple[pd.Series, pd.Series, pd.Series]:
    equity = []
    returns = []
    current = INITIAL_CAPITAL
    for index, pnl in enumerate(pnls.astype(float)):
        previous = current
        current = current + float(pnl)
        equity.append(current)
        returns.append(0.0 if index == 0 else float(pnl) / previous)
    return (
        pd.Series(returns, index=dates),
        pd.Series(equity, index=dates),
        pd.Series(pnls.to_numpy(dtype=float), index=dates),
    )


def _scale_pnl(pnl: float, source_gross: float, target_gross: float) -> float:
    if source_gross > EPSILON:
        return float(pnl * target_gross / source_gross)
    if abs(pnl) <= EPSILON:
        return 0.0
    return float("nan")


def _efficiency_index(values: pd.Series) -> pd.Series:
    running = 1.0
    output = []
    for value in values.astype(float):
        if math.isfinite(value):
            if 1.0 + value <= 0:
                output.append(float("nan"))
                running = float("nan")
            elif math.isfinite(running):
                running *= 1.0 + value
                output.append(running)
            else:
                output.append(float("nan"))
        else:
            output.append(running)
    return pd.Series(output, index=values.index)


def _corr(left: pd.Series, right: pd.Series) -> float | None:
    valid = left.notna() & right.notna()
    if valid.sum() < 2 or left[valid].nunique() < 2 or right[valid].nunique() < 2:
        return None
    return float(left[valid].corr(right[valid]))


def _distribution(values: pd.Series) -> dict:
    values = pd.to_numeric(values, errors="coerce").dropna().astype(float)
    if values.empty:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "p25": None,
            "p75": None,
            "p95": None,
            "maximum": None,
        }
    return {
        "count": int(len(values)),
        "mean": float(values.mean()),
        "median": float(values.median()),
        "p25": float(values.quantile(0.25)),
        "p75": float(values.quantile(0.75)),
        "p95": float(values.quantile(0.95)),
        "maximum": float(values.max()),
    }


def _efficiency_stats(values: pd.Series) -> dict:
    active = pd.to_numeric(values, errors="coerce").dropna().astype(float)
    result = _distribution(active)
    result.update(
        {
            "mean_return_on_gross": float(active.mean()) if not active.empty else None,
            "median_return_on_gross": float(active.median()) if not active.empty else None,
            "standard_deviation": float(active.std()) if len(active) > 1 else None,
            "cumulative_arithmetic_return_on_gross": float(active.sum())
            if not active.empty
            else None,
            "diagnostic_efficiency_index_final": float((1.0 + active).prod())
            if not active.empty
            else None,
            "efficiency_sharpe_like": (
                float(active.mean() / active.std() * math.sqrt(252))
                if len(active) > 1 and active.std() > 0
                else None
            ),
        }
    )
    return result


def _leverage_stats(frame: pd.DataFrame, version: str) -> dict:
    active = frame[frame[f"{version}_total_gross_exposure"] > EPSILON]
    leverage = active[f"{version}_gross_leverage"]
    result = _distribution(leverage)
    result["active_days"] = int(len(active))
    result["active_fraction"] = float(len(active) / len(frame)) if len(frame) else None
    for threshold in (0.5, 1.0, 1.5, 2.0):
        result[f"fraction_above_{threshold:g}x"] = (
            float((leverage > threshold).mean()) if len(leverage) else None
        )
    return result


def _ratio_stats(frame: pd.DataFrame) -> dict:
    valid = frame[frame["v2_total_gross_exposure"] > EPSILON].copy()
    ratio = valid["v1_total_gross_exposure"] / valid["v2_total_gross_exposure"]
    return _distribution(ratio)


def _build_counterfactual_row(group: dict) -> dict:
    frame = group["frame"]
    diff_mask = frame["v1_a_weight"] != frame["v2_a_weight"]
    same_mask = ~diff_mask
    v1_pnl = frame["v1_daily_pnl"].astype(float)
    v2_pnl = frame["v2_daily_pnl"].astype(float)
    v1_return = frame["v1_account_return"].astype(float)
    v2_return = frame["v2_account_return"].astype(float)
    matched_pnl = frame["v1_matched_to_v2_daily_pnl"].astype(float)
    reverse_pnl = frame["v2_matched_to_v1_daily_pnl"].astype(float)
    matched_return = frame["v1_matched_to_v2_account_return"].astype(float)
    reverse_return = frame["v2_matched_to_v1_account_return"].astype(float)
    metrics = group["metrics"]
    actual_gap = metrics["actual_v1"]["final_equity"] - metrics["actual_v2"]["final_equity"]
    matched_gap = metrics["v1_matched_to_v2"]["final_equity"] - metrics["actual_v2"]["final_equity"]
    reverse_gap = metrics["actual_v1"]["final_equity"] - metrics["v2_matched_to_v1"]["final_equity"]

    def removed_pct(gap: float) -> float | None:
        return (
            float(100.0 * (actual_gap - gap) / actual_gap)
            if abs(actual_gap) > EPSILON
            else None
        )

    return {
        "start_index": group["start_index"],
        "start_A": group["start_A"],
        "start_B": group["start_B"],
        "mechanism": group["mechanism"],
        "different_weight_days": int(diff_mask.sum()),
        "identical_weight_days": int(same_mask.sum()),
        "actual_v1_minus_v2_pnl_different_weight_days": float(
            (v1_pnl[diff_mask] - v2_pnl[diff_mask]).sum()
        ),
        "actual_v1_minus_v2_pnl_identical_weight_days": float(
            (v1_pnl[same_mask] - v2_pnl[same_mask]).sum()
        ),
        "matched_v1_to_v2_minus_v2_pnl_different_weight_days": float(
            (matched_pnl[diff_mask] - v2_pnl[diff_mask]).sum()
        ),
        "matched_v1_to_v2_minus_v2_pnl_identical_weight_days": float(
            (matched_pnl[same_mask] - v2_pnl[same_mask]).sum()
        ),
        "reverse_v1_minus_v2_matched_pnl_different_weight_days": float(
            (v1_pnl[diff_mask] - reverse_pnl[diff_mask]).sum()
        ),
        "reverse_v1_minus_v2_matched_pnl_identical_weight_days": float(
            (v1_pnl[same_mask] - reverse_pnl[same_mask]).sum()
        ),
        "actual_v1_minus_v2_return_different_weight_days": float(
            (v1_return[diff_mask] - v2_return[diff_mask]).sum()
        ),
        "actual_v1_minus_v2_return_identical_weight_days": float(
            (v1_return[same_mask] - v2_return[same_mask]).sum()
        ),
        "matched_v1_to_v2_minus_v2_return_different_weight_days": float(
            (matched_return[diff_mask] - v2_return[diff_mask]).sum()
        ),
        "matched_v1_to_v2_minus_v2_return_identical_weight_days": float(
            (matched_return[same_mask] - v2_return[same_mask]).sum()
        ),
        "reverse_v1_minus_v2_matched_return_different_weight_days": float(
            (v1_return[diff_mask] - reverse_return[diff_mask]).sum()
        ),
        "reverse_v1_minus_v2_matched_return_identical_weight_days": float(
            (v1_return[same_mask] - reverse_return[same_mask]).sum()
        ),
        "actual_v1_final_equity": metrics["actual_v1"]["final_equity"],
        "actual_v2_final_equity": metrics["actual_v2"]["final_equity"],
        "v1_matched_to_v2_final_equity": metrics["v1_matched_to_v2"]["final_equity"],
        "v2_matched_to_v1_final_equity": metrics["v2_matched_to_v1"]["final_equity"],
        "actual_v1_minus_v2_final_equity_gap": actual_gap,
        "v1_matched_to_v2_minus_v2_final_equity_gap": matched_gap,
        "v2_matched_to_v1_minus_v1_final_equity_gap": -reverse_gap,
        "v1_advantage_removed_by_matching_to_v2_pct": removed_pct(matched_gap),
        "v1_advantage_removed_by_matching_v2_to_v1_pct": removed_pct(reverse_gap),
    }


def _scenario_columns(prefix: str, values: dict) -> dict:
    return {
        f"{prefix}_{metric}": values[metric]
        for metric in (
            "final_equity",
            "cumulative_return",
            "annualized_return",
            "annualized_volatility",
            "sharpe",
            "max_drawdown",
            "n_days",
        )
    }


def _write_plots(frame: pd.DataFrame, output_root: Path) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    representative = frame[frame["start_index"].eq(2)].copy()
    paths = []
    plot_specs = (
        (
            "gross_exposure_plot_1_actual_equity.png",
            "Actual combined account equity, start_index=2",
            ("v1_account_equity", "V1 actual"),
            ("v2_account_equity", "V2 actual"),
        ),
        (
            "gross_exposure_plot_2_leverage.png",
            "Actual gross leverage, start_index=2",
            ("v1_gross_leverage", "V1 actual"),
            ("v2_gross_leverage", "V2 actual"),
        ),
        (
            "gross_exposure_plot_3_efficiency.png",
            "Return-on-gross diagnostic efficiency index, start_index=2",
            ("v1_efficiency_index", "V1 efficiency index"),
            ("v2_efficiency_index", "V2 efficiency index"),
        ),
        (
            "gross_exposure_plot_4_v1_matched_to_v2.png",
            "V1 exposure-matched to V2 gross vs V2 actual, start_index=2",
            ("v1_matched_to_v2_account_equity", "V1 matched to V2 gross"),
            ("v2_account_equity", "V2 actual"),
        ),
        (
            "gross_exposure_plot_5_v1_actual_vs_matched.png",
            "V1 actual vs V1 matched to V2 gross, start_index=2",
            ("v1_account_equity", "V1 actual"),
            ("v1_matched_to_v2_account_equity", "V1 matched to V2 gross"),
        ),
    )
    for filename, title, *series_specs in plot_specs:
        figure, axis = plt.subplots(figsize=(12, 6))
        for mechanism in ("A", "B"):
            subset = representative[representative["mechanism"].eq(mechanism)].sort_values("date")
            for column, label in series_specs:
                axis.plot(
                    subset["date"],
                    subset[column],
                    label=f"{label}, mechanism {mechanism}",
                )
        axis.set_title(title)
        axis.set_xlabel("Date")
        axis.grid(True, alpha=0.25)
        axis.legend()
        figure.autofmt_xdate()
        path = output_root / filename
        figure.tight_layout()
        figure.savefig(path, dpi=140)
        plt.close(figure)
        paths.append(str(path.relative_to(ROOT)))
    return paths


def _build_summary_markdown(summary: dict) -> str:
    leverage = summary["leverage_summary"]
    efficiency = summary["return_on_gross_summary"]
    counterfactual = summary["counterfactual_summary"]
    conclusions = summary["conclusions"]
    lines = [
        "# Gross-Exposure Comparison",
        "",
        "This focused experiment used the preserved old-winner raw runs and exact",
        "archived price snapshots. It performed no full-matrix rerun.",
        "",
        "## Validation",
        "",
        f"- Overall status: **{summary['status']}**",
        f"- Focused traces run: **{summary['focused_trace_count']}**; full matrix rerun: **{summary['full_matrix_rerun']}**",
        f"- Daily PnL reconciliation: **{summary['validation']['daily_pnl_reconciliation_status']}**",
        f"- Marked exposure reconstruction: **{summary['validation']['marked_exposure_status']}**",
        f"- Native V2 daily-exposure reconciliation: **{summary['validation']['native_v2_exposure_status']}**",
        f"- Previous return/path consistency: **{summary['validation']['previous_outputs_status']}**",
        f"- V2 gross-budget invariants: **{summary['validation']['v2_gross_budget_status']}**",
        f"- Protected public hash unchanged: **{summary['protected_public_score_unchanged']}**",
        "",
        "Exposure timing convention: positions are live from the first observed",
        "close after the entry signal through the exit signal date, before the close",
        "order fills. Return-on-gross uses beginning-of-interval marked exposure,",
        "priced at the prior observed close; zero-support observations are NaN.",
        "",
        "## Leverage",
        "",
        "| Scope | V1 mean | V1 median | V1 p95 | V1 max | V2 mean | V2 median | V2 p95 | V2 max |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scope in ("A", "B", "all"):
        v1 = leverage[scope]["v1"]
        v2 = leverage[scope]["v2"]
        lines.append(
            f"| {scope} | {v1['mean']:.4f} | {v1['median']:.4f} | {v1['p95']:.4f} | {v1['maximum']:.4f} | "
            f"{v2['mean']:.4f} | {v2['median']:.4f} | {v2['p95']:.4f} | {v2['maximum']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Return On Gross",
            "",
            "| Scope | V1 mean | V1 median | V1 efficiency Sharpe-like | V2 mean | V2 median | V2 efficiency Sharpe-like |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for scope in ("A", "B", "all"):
        v1 = efficiency[scope]["v1"]
        v2 = efficiency[scope]["v2"]
        lines.append(
            f"| {scope} | {v1['mean_return_on_gross']:.8f} | {v1['median_return_on_gross']:.8f} | "
            f"{v1['efficiency_sharpe_like'] if v1['efficiency_sharpe_like'] is not None else float('nan'):.4f} | "
            f"{v2['mean_return_on_gross']:.8f} | {v2['median_return_on_gross']:.8f} | "
            f"{v2['efficiency_sharpe_like'] if v2['efficiency_sharpe_like'] is not None else float('nan'):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Exposure-Matched Counterfactuals",
            "",
            "The detailed per-start/per-mechanism metrics are in",
            "`gross_exposure_matched_counterfactuals.csv`. Matching is performed",
            "daily by scaling V1 or V2 trade-level PnL by the ratio of target to",
            "source beginning-of-interval gross exposure.",
            "",
            "| Scope | Actual V1 Sharpe | Actual V2 Sharpe | V1 matched-to-V2 Sharpe | V2 matched-to-V1 Sharpe | Mean V1 gap removed by V1->V2 matching |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in counterfactual:
        lines.append(
            f"| {row['scope']} | {row['actual_v1_sharpe']:.4f} | {row['actual_v2_sharpe']:.4f} | "
            f"{row['v1_matched_to_v2_sharpe']:.4f} | {row['v2_matched_to_v1_sharpe']:.4f} | "
            f"{row['mean_v1_advantage_removed_by_matching_to_v2_pct']:.2f}% |"
        )
    lines.extend(
        [
            "",
            "## Conclusions",
            "",
        ]
    )
    for index, conclusion in enumerate(conclusions.values(), 1):
        lines.append(f"{index}. {conclusion}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- `gross_exposure_comparison_recent.csv`",
            "- `gross_exposure_matched_counterfactuals.csv`",
            "- `gross_exposure_summary.json`",
            "- Representative PNGs listed in the JSON summary",
            "",
        ]
    )
    return "\n".join(lines)


def run(output_path: Path = OUTPUT_PATH) -> dict:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    public_hash_before = _sha256(PUBLIC_SCORE_PATH)
    daily_contributions = pd.read_csv(DAILY_CONTRIBUTIONS_PATH, parse_dates=["date"])
    combined_series = pd.read_csv(COMBINED_SERIES_PATH, parse_dates=["date"])
    allocator = pd.read_csv(ALLOCATOR_PATH_PATH, parse_dates=["rebalance_month"])
    counterfactual_expected = pd.read_csv(COUNTERFACTUAL_PATH)
    counterfactual_expected = counterfactual_expected[
        counterfactual_expected["window"].eq("recent")
        & counterfactual_expected["scope"].eq("run")
    ].copy()
    counterfactual_expected["start_index"] = pd.to_numeric(
        counterfactual_expected["start_index"], errors="raise"
    ).astype(int)

    output_rows = []
    counterfactual_rows = []
    group_records = []
    metric_checks = []
    pnl_checks = []
    exposure_checks = []
    native_v2_exposure_checks = []
    path_checks = []
    v2_budget_checks = []
    snapshot_provenance = []
    price_differences = []

    for start_index, (start_a, start_b) in enumerate(
        zip(LEG_SPECS["A"]["recent_starts"], LEG_SPECS["B"]["recent_starts"])
    ):
        run_paths = {
            (version, leg): _run_path(version, leg, start_index)
            for version in ("v1", "v2")
            for leg in ("A", "B")
        }
        snapshots, provenance = _load_snapshots(run_paths)
        snapshot_provenance.extend(provenance)
        close_by_source = {
            (version, leg): snapshots[
                str(Path(_load_metrics(run_paths[(version, leg)])[
                    "price_snapshot"
                ]).resolve())
            ]
            for version in ("v1", "v2")
            for leg in ("A", "B")
        }
        v1_runs = {
            leg: load_leg_run(V1_ROOT, leg, "recent", start_index)
            for leg in ("A", "B")
        }
        v2_runs = {
            leg: load_leg_run(V2_ROOT, leg, "recent", start_index)
            for leg in ("A", "B")
        }
        pairs_by_leg = {
            leg: _match_trades(v1_runs[leg], v2_runs[leg])
            for leg in ("A", "B")
        }
        sides_by_leg = {
            leg: _audit_sides(v2_runs[leg])
            for leg in ("A", "B")
        }
        for leg in ("A", "B"):
            for pair in pairs_by_leg[leg]:
                pair["leg"] = leg
                v2_raw = pair["v2_raw"]
                budget = _num(v2_raw.get("pair_gross_budget"), SIZING_BUDGET)
                gross = _num(v2_raw.get("gross_entry_exposure"))
                sizing_gross = _num(v2_raw.get("sizing_gross_exposure"), gross)
                v2_budget_checks.append(
                    {
                        "start_index": start_index,
                        "leg": leg,
                        "pair": pair["pair"],
                        "pair_gross_budget": budget,
                        "gross_entry_exposure": gross,
                        "sizing_gross_exposure": sizing_gross,
                        "budget_enforced": bool(v2_raw.get("pair_gross_budget_enforced", True)),
                        "budget_headroom": budget - gross,
                        "gross_metadata_difference": abs(gross - sizing_gross),
                    }
                )

        v1_data = {
            leg: {
                "trades": v1_runs[leg]["trades"],
                "folds": v1_runs[leg]["folds"],
                "ret": v1_runs[leg]["ret"],
            }
            for leg in ("A", "B")
        }
        v2_data = {
            leg: {
                "trades": v2_runs[leg]["trades"],
                "folds": v2_runs[leg]["folds"],
                "ret": v2_runs[leg]["ret"],
            }
            for leg in ("A", "B")
        }
        v1_weight, _ = allocator_path(v1_data["A"]["ret"], v1_data["B"]["ret"])
        v2_weight, _ = allocator_path(v2_data["A"]["ret"], v2_data["B"]["ret"])
        allocator_run = allocator[allocator["start_index"].eq(start_index)].sort_values(
            "rebalance_month"
        )
        existing_v1_path = pd.Series(
            allocator_run["v1_a_weight"].to_numpy(dtype=float),
            index=pd.to_datetime(allocator_run["rebalance_month"]),
        )
        existing_v2_path = pd.Series(
            allocator_run["v2_a_weight"].to_numpy(dtype=float),
            index=pd.to_datetime(allocator_run["rebalance_month"]),
        )
        path_checks.append(
            {
                "start_index": start_index,
                "v1_monthly_max_abs_difference": _aligned_max_difference(
                    v1_weight, existing_v1_path
                )
                if not v1_weight.empty
                else 0.0,
                "v2_monthly_max_abs_difference": _aligned_max_difference(
                    v2_weight, existing_v2_path
                )
                if not v2_weight.empty
                else 0.0,
            }
        )

        metadata_by_version = {"v1": {}, "v2": {}}
        for version in ("v1", "v2"):
            for leg in ("A", "B"):
                close = close_by_source[(version, leg)]
                for pair in pairs_by_leg[leg]:
                    entry_key = (
                        int(pair["key"][0]),
                        str(pair["key"][1]),
                        _timestamp(pair["key"][2]),
                    )
                    if entry_key not in sides_by_leg[leg]:
                        raise ValueError(
                            f"missing V2 side metadata for {entry_key}"
                        )
                    metadata = _native_metadata(
                        pair,
                        version,
                        close,
                        sides_by_leg[leg][entry_key],
                    )
                    metadata_by_version[version][metadata["key"]] = metadata
                    price_differences.extend(
                        [
                            abs(metadata["entry_price1_snapshot_difference"]),
                            abs(metadata["entry_price2_snapshot_difference"]),
                        ]
                    )
        for leg in ("A", "B"):
            native_v2_exposure_checks.append(
                _validate_native_v2_exposure(
                    run_paths[("v2", leg)],
                    v2_runs[leg],
                    {
                        trade["trade_key"]: metadata_by_version["v2"][trade["trade_key"]]
                        for trade in v2_runs[leg]["trades"]
                    },
                    close_by_source[("v2", leg)],
                    start_index,
                    leg,
                )
            )

        for mechanism in ("A", "B"):
            v1_trace = simulate_trace(v1_data, v1_weight, mechanism)
            v2_trace = simulate_trace(v2_data, v2_weight, mechanism)
            v1_map = _trace_map(v1_trace)
            v2_map = _trace_map(v2_trace)
            if set(v1_map) != set(v2_map):
                raise ValueError(
                    f"V1/V2 trace date mismatch for start_index={start_index}, mechanism={mechanism}"
                )
            dates = sorted(v1_map)
            v1_exposure, v1_support = _position_exposure(
                v1_trace,
                v1_data,
                metadata_by_version["v1"],
                {leg: close_by_source[("v1", leg)] for leg in ("A", "B")},
                dates,
            )
            v2_exposure, v2_support = _position_exposure(
                v2_trace,
                v2_data,
                metadata_by_version["v2"],
                {leg: close_by_source[("v2", leg)] for leg in ("A", "B")},
                dates,
            )

            v1_pnl = pd.Series([float(v1_map[date]["pnl"]) for date in dates], index=dates)
            v2_pnl = pd.Series([float(v2_map[date]["pnl"]) for date in dates], index=dates)
            v1_return = pd.Series([float(v1_map[date]["daily_return"]) for date in dates], index=dates)
            v2_return = pd.Series([float(v2_map[date]["daily_return"]) for date in dates], index=dates)
            v1_equity = pd.Series([float(v1_map[date]["total_capital"]) for date in dates], index=dates)
            v2_equity = pd.Series([float(v2_map[date]["total_capital"]) for date in dates], index=dates)

            v1_support_gross = pd.Series([_gross(v1_support[date]) for date in dates], index=dates)
            v2_support_gross = pd.Series([_gross(v2_support[date]) for date in dates], index=dates)
            v1_total_gross = pd.Series([_gross(v1_exposure[date]) for date in dates], index=dates)
            v2_total_gross = pd.Series([_gross(v2_exposure[date]) for date in dates], index=dates)
            v1_matched_pnl = pd.Series(
                [
                    _scale_pnl(v1_pnl.loc[date], v1_support_gross.loc[date], v2_support_gross.loc[date])
                    for date in dates
                ],
                index=dates,
            )
            v2_matched_pnl = pd.Series(
                [
                    _scale_pnl(v2_pnl.loc[date], v2_support_gross.loc[date], v1_support_gross.loc[date])
                    for date in dates
                ],
                index=dates,
            )
            if v1_matched_pnl.isna().any() or v2_matched_pnl.isna().any():
                raise ValueError(
                    f"nonzero PnL without supporting gross exposure for start_index={start_index}, mechanism={mechanism}"
                )
            v1_matched_return, v1_matched_equity, _ = _account_path(
                v1_matched_pnl, pd.DatetimeIndex(dates)
            )
            v2_matched_return, v2_matched_equity, _ = _account_path(
                v2_matched_pnl, pd.DatetimeIndex(dates)
            )
            v1_efficiency = pd.Series(
                [
                    float(v1_pnl.loc[date] / v1_support_gross.loc[date])
                    if v1_support_gross.loc[date] > EPSILON
                    else float("nan")
                    for date in dates
                ],
                index=dates,
            )
            v2_efficiency = pd.Series(
                [
                    float(v2_pnl.loc[date] / v2_support_gross.loc[date])
                    if v2_support_gross.loc[date] > EPSILON
                    else float("nan")
                    for date in dates
                ],
                index=dates,
            )
            v1_eod = pd.DataFrame([v1_exposure[date] for date in dates], index=dates)
            v2_eod = pd.DataFrame([v2_exposure[date] for date in dates], index=dates)
            v1_support_frame = pd.DataFrame([v1_support[date] for date in dates], index=dates)
            v2_support_frame = pd.DataFrame([v2_support[date] for date in dates], index=dates)

            daily_run = daily_contributions[
                daily_contributions["start_index"].eq(start_index)
                & daily_contributions["mechanism"].eq(mechanism)
            ].copy()
            daily_run["date"] = pd.to_datetime(daily_run["date"]).dt.normalize()
            daily_run = daily_run.set_index("date").sort_index()
            combined_run = combined_series[
                combined_series["window"].eq("recent")
                & combined_series["start_index"].eq(start_index)
                & combined_series["mechanism"].eq(mechanism)
            ].copy()
            combined_run["date"] = pd.to_datetime(combined_run["date"]).dt.normalize()
            combined_v1 = combined_run[combined_run["case"].eq("case_1_v1_sizing_v1_allocator")].set_index("date")["daily_return"]
            combined_v2 = combined_run[combined_run["case"].eq("case_2_v2_sizing_v2_allocator")].set_index("date")["daily_return"]
            combined_v1 = combined_v1.astype(float).reindex(dates)
            combined_v2 = combined_v2.astype(float).reindex(dates)
            trace_pnl_v1 = pd.Series(
                [
                    sum(float(values.get(date, 0.0)) for values in v1_trace["trade_daily_pnl"].values())
                    for date in dates
                ],
                index=dates,
            )
            trace_pnl_v2 = pd.Series(
                [
                    sum(float(values.get(date, 0.0)) for values in v2_trace["trade_daily_pnl"].values())
                    for date in dates
                ],
                index=dates,
            )
            pnl_checks.append(
                {
                    "start_index": start_index,
                    "mechanism": mechanism,
                    "v1_trace_trade_pnl_max_abs_difference": float((trace_pnl_v1 - v1_pnl).abs().max()),
                    "v2_trace_trade_pnl_max_abs_difference": float((trace_pnl_v2 - v2_pnl).abs().max()),
                    "v1_existing_daily_pnl_max_abs_difference": float(
                        (v1_pnl - daily_run["v1_total_pnl"].astype(float).reindex(dates)).abs().max()
                    ),
                    "v2_existing_daily_pnl_max_abs_difference": float(
                        (v2_pnl - daily_run["v2_total_pnl"].astype(float).reindex(dates)).abs().max()
                    ),
                    "v1_existing_return_max_abs_difference": float(
                        (v1_return - combined_v1).abs().max()
                    ),
                    "v2_existing_return_max_abs_difference": float(
                        (v2_return - combined_v2).abs().max()
                    ),
                }
            )
            exposure_checks.append(
                {
                    "start_index": start_index,
                    "mechanism": mechanism,
                    "v1_nonnegative_exposure": bool((v1_eod >= 0).all().all()),
                    "v2_nonnegative_exposure": bool((v2_eod >= 0).all().all()),
                    "v1_support_nonnegative": bool((v1_support_frame >= 0).all().all()),
                    "v2_support_nonnegative": bool((v2_support_frame >= 0).all().all()),
                    "v1_eod_rows": int(len(v1_eod)),
                    "v2_eod_rows": int(len(v2_eod)),
                }
            )

            rows = []
            for date in dates:
                v1_eod_values = v1_exposure[date]
                v2_eod_values = v2_exposure[date]
                v1_support_values = v1_support[date]
                v2_support_values = v2_support[date]
                v1_book_net = _net(v1_eod_values)
                v2_book_net = _net(v2_eod_values)
                v1_a_weight = float(v1_trace["weight_by_day"].get(date, 0.5))
                v2_a_weight = float(v2_trace["weight_by_day"].get(date, 0.5))
                rows.append(
                    {
                        "date": _iso(date),
                        "start_index": start_index,
                        "start_A": start_a,
                        "start_B": start_b,
                        "mechanism": mechanism,
                        "v1_daily_pnl": float(v1_pnl.loc[date]),
                        "v2_daily_pnl": float(v2_pnl.loc[date]),
                        "v1_account_return": float(v1_return.loc[date]),
                        "v2_account_return": float(v2_return.loc[date]),
                        "v1_account_equity": float(v1_equity.loc[date]),
                        "v2_account_equity": float(v2_equity.loc[date]),
                        "v1_a_long_exposure": v1_eod_values["a_long"],
                        "v1_a_short_exposure": v1_eod_values["a_short"],
                        "v1_a_total_gross_exposure": _gross(v1_eod_values, "A"),
                        "v1_b_long_exposure": v1_eod_values["b_long"],
                        "v1_b_short_exposure": v1_eod_values["b_short"],
                        "v1_b_total_gross_exposure": _gross(v1_eod_values, "B"),
                        "v1_total_gross_exposure": _gross(v1_eod_values),
                        "v1_net_exposure": v1_book_net,
                        "v1_gross_leverage": _gross(v1_eod_values) / float(v1_equity.loc[date])
                        if v1_equity.loc[date] > 0
                        else float("nan"),
                        "v2_a_long_exposure": v2_eod_values["a_long"],
                        "v2_a_short_exposure": v2_eod_values["a_short"],
                        "v2_a_total_gross_exposure": _gross(v2_eod_values, "A"),
                        "v2_b_long_exposure": v2_eod_values["b_long"],
                        "v2_b_short_exposure": v2_eod_values["b_short"],
                        "v2_b_total_gross_exposure": _gross(v2_eod_values, "B"),
                        "v2_total_gross_exposure": _gross(v2_eod_values),
                        "v2_net_exposure": _net(v2_eod_values),
                        "v2_gross_leverage": _gross(v2_eod_values) / float(v2_equity.loc[date])
                        if v2_equity.loc[date] > 0
                        else float("nan"),
                        "v1_pnl_supporting_a_gross_exposure": _gross(v1_support_values, "A"),
                        "v1_pnl_supporting_b_gross_exposure": _gross(v1_support_values, "B"),
                        "v1_pnl_supporting_total_gross_exposure": _gross(v1_support_values),
                        "v2_pnl_supporting_a_gross_exposure": _gross(v2_support_values, "A"),
                        "v2_pnl_supporting_b_gross_exposure": _gross(v2_support_values, "B"),
                        "v2_pnl_supporting_total_gross_exposure": _gross(v2_support_values),
                        "v1_return_on_gross": float(v1_efficiency.loc[date]),
                        "v2_return_on_gross": float(v2_efficiency.loc[date]),
                        "v1_a_weight": v1_a_weight,
                        "v1_b_weight": 1.0 - v1_a_weight,
                        "v2_a_weight": v2_a_weight,
                        "v2_b_weight": 1.0 - v2_a_weight,
                        "v1_minus_v2_gross_leverage": (
                            _gross(v1_eod_values) / float(v1_equity.loc[date])
                            - _gross(v2_eod_values) / float(v2_equity.loc[date])
                        ),
                        "v1_minus_v2_account_return": float(v1_return.loc[date] - v2_return.loc[date]),
                        "v1_v2_total_gross_exposure_ratio": (
                            _gross(v1_eod_values) / _gross(v2_eod_values)
                            if _gross(v2_eod_values) > EPSILON
                            else float("nan")
                        ),
                        "v1_matched_to_v2_daily_pnl": float(v1_matched_pnl.loc[date]),
                        "v1_matched_to_v2_account_return": float(v1_matched_return.loc[date]),
                        "v1_matched_to_v2_account_equity": float(v1_matched_equity.loc[date]),
                        "v1_matched_to_v2_gross_exposure": _gross(v2_eod_values),
                        "v2_matched_to_v1_daily_pnl": float(v2_matched_pnl.loc[date]),
                        "v2_matched_to_v1_account_return": float(v2_matched_return.loc[date]),
                        "v2_matched_to_v1_account_equity": float(v2_matched_equity.loc[date]),
                        "v2_matched_to_v1_gross_exposure": _gross(v1_eod_values),
                        "v1_efficiency_index": float(_efficiency_index(v1_efficiency).loc[date]),
                        "v2_efficiency_index": float(_efficiency_index(v2_efficiency).loc[date]),
                    }
                )
            frame = pd.DataFrame(rows)
            output_rows.extend(rows)
            scenario_series = {
                "actual_v1": v1_return,
                "actual_v2": v2_return,
                "v1_matched_to_v2": v1_matched_return,
                "v2_matched_to_v1": v2_matched_return,
            }
            group = {
                "start_index": start_index,
                "start_A": start_a,
                "start_B": start_b,
                "mechanism": mechanism,
                "frame": frame,
                "metrics": {
                    scenario: _series_metrics(series)
                    for scenario, series in scenario_series.items()
                },
            }
            group_records.append(group)
            row = _build_counterfactual_row(group)
            for scenario, values in group["metrics"].items():
                row.update(_scenario_columns(scenario, values))
            counterfactual_rows.append(row)

            for case, series in (("case_1_v1_sizing_v1_allocator", v1_return), ("case_2_v2_sizing_v2_allocator", v2_return)):
                expected = counterfactual_expected[
                    counterfactual_expected["start_index"].eq(start_index)
                    & counterfactual_expected["mechanism"].eq(mechanism)
                    & counterfactual_expected["case"].eq(case)
                ]
                if len(expected) != 1:
                    raise ValueError(f"missing expected counterfactual row for {start_index}/{mechanism}/{case}")
                expected_row = expected.iloc[0]
                actual_metrics = _series_metrics(series)
                differences = {
                    metric: abs(actual_metrics[metric] - float(expected_row[metric]))
                    for metric in METRIC_COLUMNS
                }
                metric_checks.append(
                    {
                        "start_index": start_index,
                        "mechanism": mechanism,
                        "case": case,
                        "differences": differences,
                        "status": "pass" if max(differences.values()) <= EPSILON else "fail",
                    }
                )

    output_frame = pd.DataFrame(output_rows)
    output_frame.to_csv(output_path, index=False)
    counterfactual_frame = pd.DataFrame(counterfactual_rows)
    counterfactual_frame.to_csv(COUNTERFACTUAL_OUTPUT_PATH, index=False)

    output_frame["date"] = pd.to_datetime(output_frame["date"])
    leverage_summary = {}
    return_on_gross_summary = {}
    ratio_summary = {}
    bucket_rows = []
    correlation_summary = {}
    for scope in ("A", "B", "all"):
        scoped = output_frame if scope == "all" else output_frame[output_frame["mechanism"].eq(scope)]
        leverage_summary[scope] = {
            "v1": _leverage_stats(scoped, "v1"),
            "v2": _leverage_stats(scoped, "v2"),
        }
        return_on_gross_summary[scope] = {
            "v1": _efficiency_stats(scoped["v1_return_on_gross"]),
            "v2": _efficiency_stats(scoped["v2_return_on_gross"]),
        }
        ratio_summary[scope] = _ratio_stats(scoped)
        correlation_summary[scope] = {
            "gross_leverage_difference_vs_account_return_difference": _corr(
                scoped["v1_minus_v2_gross_leverage"],
                scoped["v1_minus_v2_account_return"],
            ),
            "gross_exposure_difference_vs_account_return_difference": _corr(
                scoped["v1_total_gross_exposure"] - scoped["v2_total_gross_exposure"],
                scoped["v1_minus_v2_account_return"],
            ),
        }
        excess = scoped["v1_gross_leverage"] - scoped["v2_gross_leverage"]
        bucket = pd.Series(
            np.select(
                [excess <= 0.25, excess <= 0.50, excess <= 1.00],
                ["<= 0.25x", "0.25-0.50x", "0.50-1.00x"],
                default="> 1.00x",
            ),
            index=scoped.index,
        )
        for label in ("<= 0.25x", "0.25-0.50x", "0.50-1.00x", "> 1.00x"):
            subset = scoped[bucket.eq(label)]
            bucket_rows.append(
                {
                    "scope": scope,
                    "bucket": label,
                    "observation_count": int(len(subset)),
                    "average_v1_gross_leverage": float(subset["v1_gross_leverage"].mean()) if len(subset) else None,
                    "average_v2_gross_leverage": float(subset["v2_gross_leverage"].mean()) if len(subset) else None,
                    "average_excess_v1_gross_leverage": float(excess.loc[subset.index].mean()) if len(subset) else None,
                    "v1_pnl": float(subset["v1_daily_pnl"].sum()) if len(subset) else 0.0,
                    "v2_pnl": float(subset["v2_daily_pnl"].sum()) if len(subset) else 0.0,
                    "v1_minus_v2_return_contribution": float(subset["v1_minus_v2_account_return"].sum()) if len(subset) else 0.0,
                }
            )

    actual_counterfactual = []
    for group in group_records:
        metrics = group["metrics"]
        actual_counterfactual.append(
            {
                "scope": f"start_{group['start_index']}_{group['mechanism']}",
                "actual_v1_sharpe": metrics["actual_v1"]["sharpe"],
                "actual_v2_sharpe": metrics["actual_v2"]["sharpe"],
                "v1_matched_to_v2_sharpe": metrics["v1_matched_to_v2"]["sharpe"],
                "v2_matched_to_v1_sharpe": metrics["v2_matched_to_v1"]["sharpe"],
                "mean_v1_advantage_removed_by_matching_to_v2_pct": counterfactual_rows[
                    len(actual_counterfactual)
                ]["v1_advantage_removed_by_matching_to_v2_pct"],
            }
        )
    for mechanism in ("A", "B"):
        scoped = [group for group in group_records if group["mechanism"] == mechanism]
        actual_counterfactual.append(
            {
                "scope": mechanism,
                "actual_v1_sharpe": float(np.mean([group["metrics"]["actual_v1"]["sharpe"] for group in scoped])),
                "actual_v2_sharpe": float(np.mean([group["metrics"]["actual_v2"]["sharpe"] for group in scoped])),
                "v1_matched_to_v2_sharpe": float(np.mean([group["metrics"]["v1_matched_to_v2"]["sharpe"] for group in scoped])),
                "v2_matched_to_v1_sharpe": float(np.mean([group["metrics"]["v2_matched_to_v1"]["sharpe"] for group in scoped])),
                "mean_v1_advantage_removed_by_matching_to_v2_pct": float(
                    np.nanmean([
                        row["v1_advantage_removed_by_matching_to_v2_pct"]
                        for row in counterfactual_rows
                        if row["mechanism"] == mechanism
                    ])
                ),
            }
        )

    aggregate_scoped = group_records
    actual_counterfactual.append(
        {
            "scope": "all",
            "actual_v1_sharpe": float(np.mean([group["metrics"]["actual_v1"]["sharpe"] for group in aggregate_scoped])),
            "actual_v2_sharpe": float(np.mean([group["metrics"]["actual_v2"]["sharpe"] for group in aggregate_scoped])),
            "v1_matched_to_v2_sharpe": float(np.mean([group["metrics"]["v1_matched_to_v2"]["sharpe"] for group in aggregate_scoped])),
            "v2_matched_to_v1_sharpe": float(np.mean([group["metrics"]["v2_matched_to_v1"]["sharpe"] for group in aggregate_scoped])),
            "mean_v1_advantage_removed_by_matching_to_v2_pct": float(
                np.nanmean([row["v1_advantage_removed_by_matching_to_v2_pct"] for row in counterfactual_rows])
            ),
        }
    )

    actual_all_gap = counterfactual_frame["actual_v1_minus_v2_final_equity_gap"].mean()
    matched_all_gap = counterfactual_frame["v1_matched_to_v2_minus_v2_final_equity_gap"].mean()
    actual_all_pnl_diff = output_frame["v1_daily_pnl"].sum() - output_frame["v2_daily_pnl"].sum()
    matched_all_pnl_diff = output_frame["v1_matched_to_v2_daily_pnl"].sum() - output_frame["v2_daily_pnl"].sum()
    differing_days = int((output_frame["v1_a_weight"] != output_frame["v2_a_weight"]).sum())
    equal_days = int(len(output_frame) - differing_days)
    validation = {
        "daily_pnl_reconciliation_status": "pass"
        if all(
            max(
                row["v1_trace_trade_pnl_max_abs_difference"],
                row["v2_trace_trade_pnl_max_abs_difference"],
                row["v1_existing_daily_pnl_max_abs_difference"],
                row["v2_existing_daily_pnl_max_abs_difference"],
                row["v1_existing_return_max_abs_difference"],
                row["v2_existing_return_max_abs_difference"],
            )
            <= EPSILON
            for row in pnl_checks
        )
        else "fail",
        "marked_exposure_status": "pass"
        if all(
            row["v1_nonnegative_exposure"]
            and row["v2_nonnegative_exposure"]
            and row["v1_support_nonnegative"]
            and row["v2_support_nonnegative"]
            for row in exposure_checks
        )
        and max(price_differences, default=0.0) <= EPSILON
        else "fail",
        "native_v2_exposure_status": "pass"
        if all(row["status"] == "pass" for row in native_v2_exposure_checks)
        else "fail",
        "previous_outputs_status": "pass"
        if all(
            row["v1_monthly_max_abs_difference"] <= EPSILON
            and row["v2_monthly_max_abs_difference"] <= EPSILON
            for row in path_checks
        )
        and all(row["status"] == "pass" for row in metric_checks)
        else "fail",
        "v2_gross_budget_status": "pass"
        if all(
            row["budget_enforced"]
            and row["budget_headroom"] >= -EPSILON
            and row["gross_metadata_difference"] <= EPSILON
            for row in v2_budget_checks
        )
        else "fail",
        "daily_pnl_checks": pnl_checks,
        "marked_exposure_checks": exposure_checks,
        "native_v2_exposure_checks": native_v2_exposure_checks,
        "allocator_path_checks": path_checks,
        "counterfactual_metric_checks": metric_checks,
        "v2_budget_checks": v2_budget_checks,
        "snapshot_provenance": snapshot_provenance,
        "max_entry_price_snapshot_difference": max(price_differences, default=0.0),
    }
    public_hash_after = _sha256(PUBLIC_SCORE_PATH)
    plot_paths = _write_plots(output_frame, AUTOPSY_ROOT)

    conclusions = {
        "v1_exposure": (
            f"V1/V2 total marked gross exposure ratio had pooled median "
            f"{ratio_summary['all']['median']:.3f}x and p95 {ratio_summary['all']['p95']:.3f}x "
            "on V2-active observations."
        ),
        "v1_leverage": (
            f"Pooled active-day mean gross leverage was "
            f"{leverage_summary['all']['v1']['mean']:.3f}x for V1 versus "
            f"{leverage_summary['all']['v2']['mean']:.3f}x for V2; the p95 values were "
            f"{leverage_summary['all']['v1']['p95']:.3f}x and {leverage_summary['all']['v2']['p95']:.3f}x."
        ),
        "return_on_gross": (
            f"Mean return-on-gross was {return_on_gross_summary['all']['v1']['mean_return_on_gross']:.8f} "
            f"for V1 versus {return_on_gross_summary['all']['v2']['mean_return_on_gross']:.8f} for V2 "
            "on observations with supporting exposure."
        ),
        "exposure_match": (
            f"Matching V1 daily gross to V2 reduced the mean final V1-minus-V2 equity gap "
            f"from {actual_all_gap:.6f} to {matched_all_gap:.6f}; the mean removed share was "
            f"{actual_counterfactual[-1]['mean_v1_advantage_removed_by_matching_to_v2_pct']:.2f}%."
        ),
        "leverage_only": (
            "V1 was not simply a more leveraged V2 if the exposure-matched V1 gap remains "
            "positive; the counterfactual table reports the per-start result rather than "
            "assuming a universal causal percentage."
        ),
        "hr_weighting": (
            "The remaining gap after matching total gross is the evidence available for "
            "V1 internal HR-dependent weighting/economics; it should not be conflated with "
            "the separate Clean40 allocator-path effect."
        ),
        "clean40_connection": (
            f"The prior differing-weight mask covers {differing_days} pooled observations "
            f"versus {equal_days} identical-weight observations; this experiment provides "
            "matched and unmatched comparisons within that same mask."
        ),
        "future_convention": (
            "V2 remains the cleaner convention for future cross-pair and cross-book "
            "comparison because it fixes total pair gross exposure, while V1 remains a "
            "useful historical control."
        ),
    }
    status = "pass"
    if (
        any(value != "pass" for key, value in validation.items() if key.endswith("_status"))
        or public_hash_before != public_hash_after
    ):
        status = "fail"
    summary = {
        "status": status,
        "branch": _git_value("branch", "--show-current"),
        "source_mode": "focused_old_winner_replay_with_marked_exposure; no_full_matrix",
        "focused_trace_count": len(group_records),
        "full_matrix_rerun": False,
        "canonical_outputs_written": False,
        "selected_book": {
            "A": "sp500-12m/cross_sector_slide1m_noscreen",
            "B": "sp500-2m/cross_sector_slide3m_bd7",
        },
        "timing_convention": {
            "account_return": "trace daily PnL divided by prior account equity",
            "eod_exposure": "positions live from the first observed close after entry through the exit signal date",
            "return_on_gross": "daily PnL divided by beginning-of-interval marked gross exposure priced at the prior observed close",
            "zero_support": "NaN for return-on-gross; nonzero PnL without support fails validation",
            "same_day_entries_exits": "no same-day trades in the preserved recent inputs",
        },
        "raw_data_availability": {
            "v1_daily_exposure_file": "missing; reconstructed from preserved trade logs and snapshots",
            "v2_daily_exposure_file": "present in preserved V2 runs; native position-price inputs were also available",
            "price_snapshots": "present and hash-checked against each run metrics.json",
        },
        "output_rows": int(len(output_frame)),
        "output_columns": list(output_frame.columns),
        "validation": validation,
        "leverage_summary": leverage_summary,
        "gross_exposure_ratio_summary": ratio_summary,
        "return_on_gross_summary": return_on_gross_summary,
        "leverage_return_buckets": bucket_rows,
        "correlation_summary": correlation_summary,
        "counterfactual_summary": actual_counterfactual,
        "counterfactual_full_rows": counterfactual_rows,
        "pooled_period_attribution": {
            "differing_weight_days": differing_days,
            "identical_weight_days": equal_days,
            "actual_v1_minus_v2_pnl": float(actual_all_pnl_diff),
            "matched_v1_to_v2_minus_v2_pnl": float(matched_all_pnl_diff),
            "mean_actual_final_equity_gap": float(actual_all_gap),
            "mean_matched_final_equity_gap": float(matched_all_gap),
        },
        "representative_plots": plot_paths,
        "conclusions": conclusions,
        "protected_public_score_sha256_before": public_hash_before,
        "protected_public_score_sha256_after": public_hash_after,
        "protected_public_score_unchanged": public_hash_before == public_hash_after,
    }
    SUMMARY_JSON_PATH.write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    SUMMARY_MD_PATH.write_text(_build_summary_markdown(summary), encoding="utf-8")
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args(argv)
    summary = run(args.out)
    print(f"Validation: {summary['status']}")
    print(f"Wrote {args.out}")
    print(f"Wrote {COUNTERFACTUAL_OUTPUT_PATH}")
    print(f"Wrote {SUMMARY_JSON_PATH}")
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
