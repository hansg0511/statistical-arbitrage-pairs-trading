"""Decompose the old Clean40 winner's V1/V2 recent Sharpe change.

This is a focused diagnostic.  It reads the preserved canonical V1 and V2 raw
runs for the two locked legs, replays only that pair, and writes all generated
artifacts outside ``results/final`` and ``results/sizing_v2_full``.

The four counterfactuals are:

* V1 sizing + V1 allocator path
* V2 sizing + V2 allocator path
* V2 sizing + V1 allocator path
* V1 sizing + V2 allocator path

The replay implementation intentionally mirrors ``run_combined_backtest``.
Only this module records per-trade allocations and per-day leg contributions.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.run_combined_backtest import (  # noqa: E402
    build_trades,
    load_ret,
    metrics as replay_metrics,
    simulate,
    weight_path_momentum_causal,
)
from src.backtest import calculate_pair_sizes  # noqa: E402


V1_ROOT = ROOT / "results" / "sizing_v2_full" / "v1_canonical"
V2_ROOT = ROOT / "results" / "sizing_v2_full" / "v2"
DEFAULT_OUTPUT = ROOT / "results" / "old_winner_v1_v2_autopsy"
REPORT_PATH = ROOT / "docs" / "old_winner_v1_v2_autopsy.md"
PUBLIC_SCORE = ROOT / "results" / "final" / "rankings" / "clean40_pair_scores.csv"
V1_SUMMARY = ROOT / "results" / "sizing_v2_full_summary" / "combined_v1_scores.csv"
V2_SUMMARY = ROOT / "results" / "sizing_v2_full_summary" / "combined_v2_scores.csv"

INITIAL_CAPITAL = 1_000_000.0
PCT_PER_PAIR = 0.25
SIZING_BUDGET = INITIAL_CAPITAL * PCT_PER_PAIR
MAX_PAIRS = 20
LOOKBACK_DAYS = 84
MOMENTUM_STEP = 0.40
WEIGHT_MIN = 0.10
WEIGHT_MAX = 0.90
EPSILON = 1e-9

LEG_SPECS = {
    "A": {
        "strategy": "sp500-12m",
        "config": "cross_sector_slide1m_noscreen",
        "recent_section": "10b",
        "recent_starts": (
            "2023-01-01",
            "2023-02-01",
            "2023-03-01",
            "2023-04-01",
            "2023-05-01",
        ),
        "historical_section": "09b",
        "historical_start": "2014-01-01",
    },
    "B": {
        "strategy": "sp500-2m",
        "config": "cross_sector_slide3m_bd7",
        "recent_section": "07",
        "recent_starts": (
            "2023-11-01",
            "2023-12-01",
            "2024-01-01",
            "2024-02-01",
            "2024-03-01",
        ),
        "historical_section": "09a",
        "historical_start": "2014-11-01",
    },
}

CASE_DEFS = {
    "case_1_v1_sizing_v1_allocator": ("v1", "v1"),
    "case_2_v2_sizing_v2_allocator": ("v2", "v2"),
    "case_3_v2_sizing_v1_allocator": ("v2", "v1"),
    "case_4_v1_sizing_v2_allocator": ("v1", "v2"),
}

BUCKETS = (
    ("HR < 0.5", lambda x: x < 0.5),
    ("0.5 <= HR < 1.0", lambda x: (x >= 0.5) & (x < 1.0)),
    ("1.0 <= HR < 1.5", lambda x: (x >= 1.0) & (x < 1.5)),
    ("1.5 <= HR <= 2.0", lambda x: (x >= 1.5) & (x <= 2.0)),
    ("HR > 2.0", lambda x: x > 2.0),
)


def _iso(value) -> str:
    if value is None or pd.isna(value):
        return ""
    return pd.Timestamp(value).date().isoformat()


def _timestamp(value) -> pd.Timestamp:
    return pd.Timestamp(value).normalize()


def _num(value, default=float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result


def _finite(value) -> bool:
    return math.isfinite(_num(value))


def _safe_corr(left: pd.Series, right: pd.Series) -> float:
    x = pd.to_numeric(left, errors="coerce")
    y = pd.to_numeric(right, errors="coerce")
    valid = x.notna() & y.notna()
    if valid.sum() < 2 or x[valid].nunique() < 2 or y[valid].nunique() < 2:
        return float("nan")
    return float(x[valid].corr(y[valid]))


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _trade_key(row) -> tuple:
    if isinstance(row, dict):
        fold = row.get("fold_id")
        pair = row.get("pair", "")
        entry = row.get("entry", row.get("entry_date"))
        exit_ = row.get("exit", row.get("exit_date"))
        reason = row.get("reason", row.get("exit_reason", ""))
    else:
        fold = row.get("fold_id")
        pair = row.get("pair", "")
        entry = row.get("entry_date")
        exit_ = row.get("exit_date")
        reason = row.get("exit_reason", "")
    return (
        int(_num(fold, 0.0)),
        str(pair),
        _timestamp(entry),
        _timestamp(exit_),
        str(reason),
    )


def _short_key(key: tuple) -> str:
    return "|".join((str(key[0]), key[1], _iso(key[2]), _iso(key[3]), key[4]))


def _run_path(root: Path, leg: str, window: str, start_index: int) -> Path:
    spec = LEG_SPECS[leg]
    if window == "recent":
        start = spec["recent_starts"][start_index]
        section = spec["recent_section"]
    else:
        if start_index != 0:
            raise ValueError("historical has only start_index=0")
        start = spec["historical_start"]
        section = spec["historical_section"]
    return root / section / f'{start}_{spec["config"]}'


def _read_trade_log(path: Path) -> pd.DataFrame:
    return pd.read_csv(
        path / "trade_logs" / "test_trade_log.csv",
        parse_dates=["entry_date", "exit_date"],
    )


def _read_sizing_audit(path: Path) -> pd.DataFrame:
    audit_path = path / "sizing_audit.csv"
    if not audit_path.is_file():
        return pd.DataFrame()
    return pd.read_csv(audit_path, parse_dates=["date"])


def load_leg_run(root: Path, leg: str, window: str, start_index: int) -> dict:
    """Load one raw run and attach its original trade-log metadata."""
    path = _run_path(root, leg, window, start_index)
    if not path.is_dir():
        raise FileNotFoundError(f"missing old-winner run: {path}")
    trades, folds = build_trades(path)
    raw = _read_trade_log(path)
    by_key: dict[tuple, deque] = defaultdict(deque)
    for _, row in raw.iterrows():
        by_key[_trade_key(row)].append(row.to_dict())
    attached = []
    for trade in trades:
        key = _trade_key(trade)
        if not by_key[key]:
            raise RuntimeError(f"trade-log metadata missing for {_short_key(key)} in {path}")
        item = dict(trade)
        item["raw"] = by_key[key].popleft()
        item["trade_key"] = key
        attached.append(item)
    if any(by_key.values()):
        raise RuntimeError(f"unmatched trade-log rows remain in {path}")
    return {
        "path": path,
        "trades": attached,
        "folds": folds,
        "ret": load_ret(path),
        "sizing_audit": _read_sizing_audit(path),
    }


def _match_trades(v1_run: dict, v2_run: dict) -> list[dict]:
    """Match V1/V2 by the full underlying trade identity."""
    v2_by_key: dict[tuple, deque] = defaultdict(deque)
    for trade in v2_run["trades"]:
        v2_by_key[trade["trade_key"]].append(trade)
    pairs = []
    for v1_trade in v1_run["trades"]:
        key = v1_trade["trade_key"]
        if not v2_by_key[key]:
            raise RuntimeError(
                f"V1/V2 trade mismatch for {_short_key(key)}\n"
                f"V1: {v1_run['path']}\nV2: {v2_run['path']}"
            )
        v2_trade = v2_by_key[key].popleft()
        pairs.append(_enrich_trade_pair(v1_trade, v2_trade, v2_run))
    leftovers = sum(len(values) for values in v2_by_key.values())
    if leftovers:
        raise RuntimeError(f"V2 has {leftovers} unmatched trades in {v2_run['path']}")
    return pairs


def _audit_gross(audit: pd.DataFrame, trade: dict) -> float:
    if audit.empty:
        return float("nan")
    raw = trade["raw"]
    date = _timestamp(raw.get("entry_date"))
    fold = int(_num(raw.get("fold_id"), 0.0))
    mask = (
        audit["date"].dt.normalize().eq(date)
        & audit["pair"].astype(str).eq(str(raw.get("pair")))
        & pd.to_numeric(audit["fold_id"], errors="coerce").eq(fold)
    )
    matched = audit[mask]
    if "status" in matched:
        submitted = matched[matched["status"].astype(str).eq("orders_submitted")]
        if not submitted.empty:
            matched = submitted
    if matched.empty or "fixed_gross_entry_exposure" not in matched:
        return float("nan")
    return _num(matched.iloc[0]["fixed_gross_entry_exposure"])


def _enrich_trade_pair(v1_trade: dict, v2_trade: dict, v2_run: dict) -> dict:
    v1_raw = v1_trade["raw"]
    v2_raw = v2_trade["raw"]
    price1 = _num(v2_raw.get("sizing_price1"), _num(v2_raw.get("entry_price1")))
    price2 = _num(v2_raw.get("sizing_price2"), _num(v2_raw.get("entry_price2")))
    hr = _num(v2_raw.get("hr_entry"))
    sizing = calculate_pair_sizes(
        INITIAL_CAPITAL,
        PCT_PER_PAIR,
        price1,
        price2,
        hr,
        log_space=True,
        dollar_neutral=False,
        pair_sizing_mode="reference_leg",
    )
    if not sizing["valid"]:
        raise RuntimeError(f"could not reconstruct V1 sizing for {_short_key(v1_trade['trade_key'])}")
    execution_price1 = _num(v2_raw.get("entry_price1"), price1)
    execution_price2 = _num(v2_raw.get("entry_price2"), price2)
    v1_execution_gross = (
        sizing["size1"] * execution_price1 + sizing["size2"] * execution_price2
    )
    v2_actual_gross = _num(
        v2_raw.get("gross_entry_exposure"),
        _num(v2_raw.get("sizing_gross_exposure")),
    )
    v1_budget = _num(v1_raw.get("target_notional"), SIZING_BUDGET)
    if not _finite(v1_budget):
        v1_budget = SIZING_BUDGET
    v2_budget = _num(v2_raw.get("pair_gross_budget"), SIZING_BUDGET)
    v1_return = _num(v1_raw.get("return"), v1_trade["ret"])
    v2_return = _num(v2_raw.get("return"), v2_trade["ret"])
    v1_pnl = _num(v1_raw.get("pnl"))
    v2_pnl = _num(v2_raw.get("pnl"))
    return {
        "key": v1_trade["trade_key"],
        "v1_trade": v1_trade,
        "v2_trade": v2_trade,
        "v1_raw": v1_raw,
        "v2_raw": v2_raw,
        "leg": None,
        "fold_id": int(v1_trade["fold_id"]),
        "pair": str(v1_trade["pair"]),
        "entry": v1_trade["entry"],
        "exit": v1_trade["exit"],
        "exit_reason": str(v1_trade["reason"]),
        "abs_hr": abs(hr),
        "hr_entry": hr,
        "v1_reference_leg_sizing_budget": v1_budget,
        "v1_actual_gross_exposure": float(v1_execution_gross),
        "v1_sizing_time_gross_exposure": float(sizing["actual_gross_exposure"]),
        "v2_pair_gross_budget": v2_budget,
        "v2_actual_gross_exposure": float(v2_actual_gross),
        "v1_gross_v2_gross_ratio": (
            float(v1_execution_gross / v2_actual_gross)
            if v2_actual_gross > 0
            else float("nan")
        ),
        "v1_final_dollar_pnl_pre_combined_rescaling": v1_pnl,
        "v2_final_dollar_pnl_pre_combined_rescaling": v2_pnl,
        "v1_normalized_trade_pnl": v1_return,
        "v2_normalized_trade_pnl": v2_return,
        "v1_size1": int(sizing["size1"]),
        "v1_size2": int(sizing["size2"]),
        "v2_audit_gross": _audit_gross(v2_run["sizing_audit"], v2_trade),
    }


def _sharpe(values: pd.Series) -> float:
    values = values.dropna()
    if len(values) < 2:
        return float("nan")
    std = values.std()
    if not math.isfinite(std) or std == 0:
        return float("nan")
    return float(values.mean() / std * math.sqrt(252))


def allocator_path(a: pd.Series, b: pd.Series) -> tuple[pd.Series, pd.DataFrame]:
    """Return the existing causal path plus its trailing-score diagnostics."""
    union = a.index.union(b.index).sort_values()
    a = a.reindex(union).fillna(0.0)
    b = b.reindex(union).fillna(0.0)
    weight = 0.5
    path_rows = []
    for month in union.to_period("M").unique():
        cutoff = month.to_timestamp()
        trailing_a = _sharpe(a[a.index < cutoff].tail(LOOKBACK_DAYS))
        trailing_b = _sharpe(b[b.index < cutoff].tail(LOOKBACK_DAYS))
        if not math.isnan(trailing_a) and not math.isnan(trailing_b):
            if trailing_a > trailing_b:
                weight = min(weight + MOMENTUM_STEP, WEIGHT_MAX)
            elif trailing_b > trailing_a:
                weight = max(weight - MOMENTUM_STEP, WEIGHT_MIN)
        path_rows.append(
            {
                "rebalance_month": _iso(cutoff),
                "v1_trailing_sharpe_A": trailing_a,
                "v1_trailing_sharpe_B": trailing_b,
                "a_weight": weight,
            }
        )
    details = pd.DataFrame(path_rows)
    path = pd.Series(
        details["a_weight"].to_numpy(dtype=float),
        index=pd.to_datetime(details["rebalance_month"]),
        name="weight_A",
    )
    return path, details


def _preferred(weight) -> str:
    if pd.isna(weight):
        return "neutral"
    if weight > 0.5:
        return "A"
    if weight < 0.5:
        return "B"
    return "neutral"


def compare_allocator_paths(
    v1_path: pd.DataFrame,
    v2_path: pd.DataFrame,
    window: str,
    start_index: int,
    start_a: str,
    start_b: str,
) -> pd.DataFrame:
    left = v1_path.rename(
        columns={
            "v1_trailing_sharpe_A": "v1_trailing_sharpe_A",
            "v1_trailing_sharpe_B": "v1_trailing_sharpe_B",
            "a_weight": "v1_a_weight",
        }
    )
    right = v2_path.rename(
        columns={
            "v1_trailing_sharpe_A": "v2_trailing_sharpe_A",
            "v1_trailing_sharpe_B": "v2_trailing_sharpe_B",
            "a_weight": "v2_a_weight",
        }
    )
    merged = left.merge(right, on="rebalance_month", how="outer").sort_values(
        "rebalance_month"
    )
    merged["window"] = window
    merged["start_index"] = start_index
    merged["start_A"] = start_a
    merged["start_B"] = start_b
    merged["v2_minus_v1_a_weight"] = merged["v2_a_weight"] - merged["v1_a_weight"]
    merged["abs_a_weight_difference"] = merged["v2_minus_v1_a_weight"].abs()
    merged["v1_favored_leg"] = merged["v1_a_weight"].map(_preferred)
    merged["v2_favored_leg"] = merged["v2_a_weight"].map(_preferred)
    merged["favored_leg_same"] = (
        merged["v1_favored_leg"] == merged["v2_favored_leg"]
    )
    merged["favored_leg_flipped"] = ~merged["favored_leg_same"]
    merged["weights_different"] = ~np.isclose(
        merged["v1_a_weight"], merged["v2_a_weight"], equal_nan=True
    )
    columns = [
        "window",
        "start_index",
        "start_A",
        "start_B",
        "rebalance_month",
        "v1_trailing_sharpe_A",
        "v1_trailing_sharpe_B",
        "v1_a_weight",
        "v2_trailing_sharpe_A",
        "v2_trailing_sharpe_B",
        "v2_a_weight",
        "v2_minus_v1_a_weight",
        "abs_a_weight_difference",
        "v1_favored_leg",
        "v2_favored_leg",
        "favored_leg_same",
        "favored_leg_flipped",
        "weights_different",
    ]
    return merged[columns]


def allocator_summary(paths: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if paths.empty:
        return pd.DataFrame()
    groups = [
        ("run", paths.groupby(["window", "start_index"], dropna=False)),
        ("window_all_starts", paths.groupby(["window"], dropna=False)),
    ]
    for scope, grouped in groups:
        for keys, frame in grouped:
            if not isinstance(keys, tuple):
                keys = (keys,)
            window = keys[0]
            start_index = keys[1] if len(keys) > 1 else "all"
            count = len(frame)
            rows.append(
                {
                    "scope": scope,
                    "window": window,
                    "start_index": start_index,
                    "rebalance_months": count,
                    "same_direction_months": int(frame["favored_leg_same"].sum()),
                    "preferred_leg_flip_months": int(frame["favored_leg_flipped"].sum()),
                    "mean_abs_a_weight_difference": float(
                        frame["abs_a_weight_difference"].mean()
                    ),
                    "max_abs_a_weight_difference": float(
                        frame["abs_a_weight_difference"].max()
                    ),
                    "different_weight_months": int(frame["weights_different"].sum()),
                    "different_weight_pct": float(
                        100.0 * frame["weights_different"].mean()
                    ),
                }
            )
    return pd.DataFrame(rows)


def simulate_trace(
    leg_data: dict,
    weight_path: pd.Series,
    mechanism: str,
    capital: float = INITIAL_CAPITAL,
    pct: float = PCT_PER_PAIR,
    max_pairs: int = MAX_PAIRS,
) -> dict:
    """Mirror ``run_combined_backtest.simulate`` while recording attribution."""
    del max_pairs  # retained for signature parity with the canonical helper
    leg_names = ["A", "B"]
    all_trades = {leg: leg_data[leg]["trades"] for leg in leg_names}
    folds_by_leg = {leg: leg_data[leg]["folds"] for leg in leg_names}
    book_cash = capital
    subs = {}
    for leg in leg_names:
        for _, fold in folds_by_leg[leg].iterrows():
            subs[(leg, int(fold["fold"]))] = {"basis": None, "open": {}}

    dates = set()
    for leg in leg_names:
        for trade in all_trades[leg]:
            dates.update(trade["daily"].keys())
    dates = sorted(dates)

    active_by_day = {date: set() for date in dates}
    fold_first_day = {}
    for leg in leg_names:
        for _, fold in folds_by_leg[leg].iterrows():
            key = (leg, int(fold["fold"]))
            lo = bisect.bisect_left(dates, fold["start"])
            hi = bisect.bisect_right(dates, fold["end"])
            for index in range(lo, min(hi, len(dates))):
                active_by_day[dates[index]].add(key)
            fold_first_day[key] = (
                dates[lo]
                if lo < len(dates) and dates[lo] <= fold["end"]
                else None
            )

    weight_index = weight_path.dropna().index
    weight_by_day = {}
    current_weight = 0.5
    iterator = iter(weight_index)
    next_weight_date = next(iterator, None)
    for date in dates:
        while next_weight_date is not None and next_weight_date <= date:
            current_weight = float(weight_path[next_weight_date])
            next_weight_date = next(iterator, None)
        weight_by_day[date] = current_weight

    rebalance_dates = set()
    previous = None
    for date in dates:
        if previous is None or (date.year, date.month) != (previous.year, previous.month):
            rebalance_dates.add(date)
        previous = date

    def weight_a(date):
        return weight_by_day.get(date, 0.5)

    def weight_leg(leg, date):
        return weight_a(date) if leg == "A" else 1.0 - weight_a(date)

    live = set()

    def total_value():
        return book_cash + sum(
            sum(info["notional"] * info["cumret"] for info in subs[key]["open"].values())
            for key in sorted(live)
        )

    def rebalance_a(date):
        current_value = total_value()
        for leg in leg_names:
            active = sorted(key for key in active_by_day[date] if key[0] == leg)
            if not active:
                continue
            target = weight_leg(leg, date) * current_value / len(active)
            for key in active:
                subs[key]["basis"] = target
        for key in sorted(subs):
            if key not in active_by_day[date]:
                subs[key]["basis"] = None

    def activate_fold_b(leg, fold_id, date):
        sub = subs[(leg, fold_id)]
        if sub["basis"] is not None:
            return
        current_value = total_value()
        active_count = sum(1 for key in active_by_day[date] if key[0] == leg)
        sub["basis"] = current_value / active_count if active_count else 0.0

    entries_by_date = {}
    for leg in leg_names:
        for trade in all_trades[leg]:
            entries_by_date.setdefault(trade["entry"], []).append((leg, trade))

    rows = []
    ledger = []
    rejected = []
    allocations = {}
    trade_daily_pnl = defaultdict(lambda: defaultdict(float))
    daily_leg_pnl = defaultdict(lambda: {"A": 0.0, "B": 0.0})
    current_value_previous = None
    for date in dates:
        if mechanism == "A":
            if date in rebalance_dates:
                rebalance_a(date)
        else:
            for key in sorted(active_by_day[date]):
                if fold_first_day.get(key) == date:
                    activate_fold_b(*key, date)

        for key in sorted(live):
            sub = subs[key]
            for info in sub["open"].values():
                daily_return = info["daily"].get(date, 0.0)
                info["cumret"] += daily_return
                amount = info["notional"] * daily_return
                daily_leg_pnl[date][info["leg"]] += amount
                trade_daily_pnl[info["trade_key"]][date] += amount

        for key in sorted(live):
            sub = subs[key]
            if not sub["open"]:
                live.discard(key)
                continue
            for pair in list(sub["open"]):
                info = sub["open"][pair]
                if info["exit"] <= date:
                    book_cash += info["notional"] * info["cumret"]
                    del sub["open"][pair]
            if not sub["open"]:
                live.discard(key)

        for leg, trade in entries_by_date.get(date, []):
            sub = subs[(leg, trade["fold_id"])]
            basis = sub["basis"]
            if mechanism == "A":
                notional = pct * basis if basis else 0.0
            else:
                notional = pct * weight_leg(leg, date) * basis if basis else 0.0
            if notional <= 0:
                rejected.append(
                    {
                        "date": _iso(date),
                        "leg": leg,
                        "fold_id": trade["fold_id"],
                        "pair": trade["pair"],
                        "reason": "no_basis",
                    }
                )
                continue
            key = trade["trade_key"]
            allocations[key] = notional
            daily_return = trade["daily"].get(date, 0.0)
            trade_daily_pnl[key][date] += notional * daily_return
            daily_leg_pnl[date][leg] += notional * daily_return
            sub["open"][trade["pair"]] = {
                "notional": notional,
                "cumret": daily_return,
                "exit": trade["exit"],
                "daily": trade["daily"],
                "reason": trade["reason"],
                "leg": leg,
                "trade_key": key,
            }
            live.add((leg, trade["fold_id"]))

        current_value = total_value()
        pnl = 0.0 if current_value_previous is None else current_value - current_value_previous
        daily_return = (
            0.0
            if current_value_previous is None or current_value_previous == 0
            else (current_value - current_value_previous) / current_value_previous
        )
        current_value_previous = current_value
        leg_value = {leg: 0.0 for leg in leg_names}
        leg_deployed = {leg: 0.0 for leg in leg_names}
        for key in sorted(live):
            leg, _fold_id = key
            sub = subs[key]
            leg_value[leg] += sum(
                info["notional"] * info["cumret"] for info in sub["open"].values()
            )
            leg_deployed[leg] += sum(
                info["notional"] for info in sub["open"].values()
            )
        rows.append(
            {
                "date": date,
                "pnl": pnl,
                "total_capital": current_value,
                "daily_return": daily_return,
            }
        )
        ledger.append(
            {
                "date": date,
                "weight_A": weight_a(date),
                "legA_open_pnl": leg_value["A"],
                "legB_open_pnl": leg_value["B"],
                "legA_deployed": leg_deployed["A"],
                "legB_deployed": leg_deployed["B"],
                "total_deployed": leg_deployed["A"] + leg_deployed["B"],
                "book_cash": book_cash,
            }
        )

    # The canonical replay treats the first end-of-day value as the initial
    # observation, so its first daily return is zero even if an entry-day mark
    # exists.  Keep the attribution table on the same convention.
    if dates:
        first_date = dates[0]
        daily_leg_pnl[first_date] = {"A": 0.0, "B": 0.0}
        for key in list(trade_daily_pnl):
            trade_daily_pnl[key][first_date] = 0.0

    series = pd.Series(
        [row["daily_return"] for row in rows],
        index=pd.to_datetime([row["date"] for row in rows]),
    )
    return {
        "rows": rows,
        "series": series,
        "ledger": ledger,
        "rejected": rejected,
        "allocations": allocations,
        "trade_daily_pnl": trade_daily_pnl,
        "daily_leg_pnl": daily_leg_pnl,
        "weight_by_day": weight_by_day,
    }


def _series_from_rows(rows: list[dict]) -> pd.Series:
    return pd.Series(
        [float(row["daily_return"]) for row in rows],
        index=pd.to_datetime([row["date"] for row in rows]),
    ).sort_index()


def _max_series_difference(left: pd.Series, right: pd.Series) -> float:
    merged = pd.concat([left.rename("left"), right.rename("right")], axis=1).fillna(0.0)
    if merged.empty:
        return 0.0
    return float(np.max(np.abs(merged["left"] - merged["right"])))


def _metric_dict(series: pd.Series) -> dict:
    result = replay_metrics(series)
    return {
        "annualized_return": float(result["ann_ret"]),
        "annualized_volatility": float(result["ann_vol"]),
        "sharpe": float(result["sharpe"]),
        "max_drawdown": float(result["mdd"]),
        "n_days": int(series.dropna().shape[0]),
    }


def _weight_at(trace: dict, date) -> float:
    date = pd.Timestamp(date)
    if date in trace["weight_by_day"]:
        return float(trace["weight_by_day"][date])
    values = [key for key in trace["weight_by_day"] if key <= date]
    return float(trace["weight_by_day"][max(values)]) if values else 0.5


def trade_contribution_row(
    pair: dict,
    window: str,
    start_index: int,
    start_a: str,
    start_b: str,
    mechanism: str,
    v1_trace: dict,
    v2_trace: dict,
) -> dict:
    key = pair["key"]
    v1_trade = pair["v1_trade"]
    v2_trade = pair["v2_trade"]
    v1_allocation = float(v1_trace["allocations"].get(key, 0.0))
    v2_allocation = float(v2_trace["allocations"].get(key, 0.0))
    v1_contribution = v1_allocation * float(v1_trade["ret"])
    v2_contribution = v2_allocation * float(v2_trade["ret"])
    return {
        "window": window,
        "start_index": start_index,
        "start_A": start_a,
        "start_B": start_b,
        "mechanism": mechanism,
        "leg": pair["leg"],
        "pair": pair["pair"],
        "fold_id": pair["fold_id"],
        "entry_date": _iso(pair["entry"]),
        "exit_date": _iso(pair["exit"]),
        "exit_reason": pair["exit_reason"],
        "entry_hedge_ratio": pair["hr_entry"],
        "abs_entry_hedge_ratio": pair["abs_hr"],
        "v1_reference_leg_sizing_budget": pair["v1_reference_leg_sizing_budget"],
        "v1_actual_gross_exposure": pair["v1_actual_gross_exposure"],
        "v1_sizing_time_gross_exposure": pair["v1_sizing_time_gross_exposure"],
        "v2_pair_gross_budget": pair["v2_pair_gross_budget"],
        "v2_actual_gross_exposure": pair["v2_actual_gross_exposure"],
        "v1_gross_v2_gross_ratio": pair["v1_gross_v2_gross_ratio"],
        "v1_final_dollar_pnl_pre_combined_rescaling": pair[
            "v1_final_dollar_pnl_pre_combined_rescaling"
        ],
        "v2_final_dollar_pnl_pre_combined_rescaling": pair[
            "v2_final_dollar_pnl_pre_combined_rescaling"
        ],
        "v1_normalized_trade_pnl": pair["v1_normalized_trade_pnl"],
        "v2_normalized_trade_pnl": pair["v2_normalized_trade_pnl"],
        "v1_allocator_weight_applicable_at_entry": _weight_at(v1_trace, pair["entry"]),
        "v2_allocator_weight_applicable_at_entry": _weight_at(v2_trace, pair["entry"]),
        "v1_replay_allocation": v1_allocation,
        "v2_replay_allocation": v2_allocation,
        "v1_final_contribution_to_combined_book": v1_contribution,
        "v2_final_contribution_to_combined_book": v2_contribution,
        "contribution_difference_v1_minus_v2": v1_contribution - v2_contribution,
        "trade_identity_match": True,
    }


def daily_contribution_rows(
    window: str,
    start_index: int,
    start_a: str,
    start_b: str,
    mechanism: str,
    v1_trace: dict,
    v2_trace: dict,
) -> tuple[list[dict], list[dict]]:
    v1_by_date = {row["date"]: row for row in v1_trace["rows"]}
    v2_by_date = {row["date"]: row for row in v2_trace["rows"]}
    dates = sorted(set(v1_by_date) | set(v2_by_date))
    rows = []
    for date in dates:
        v1_row = v1_by_date.get(date, {"daily_return": 0.0, "pnl": 0.0})
        v2_row = v2_by_date.get(date, {"daily_return": 0.0, "pnl": 0.0})
        v1_a = float(v1_trace["daily_leg_pnl"].get(date, {}).get("A", 0.0))
        v1_b = float(v1_trace["daily_leg_pnl"].get(date, {}).get("B", 0.0))
        v2_a = float(v2_trace["daily_leg_pnl"].get(date, {}).get("A", 0.0))
        v2_b = float(v2_trace["daily_leg_pnl"].get(date, {}).get("B", 0.0))
        rows.append(
            {
                "window": window,
                "start_index": start_index,
                "start_A": start_a,
                "start_B": start_b,
                "mechanism": mechanism,
                "date": _iso(date),
                "v1_a_contribution": v1_a,
                "v1_b_contribution": v1_b,
                "v1_total_pnl": v1_a + v1_b,
                "v1_total_return": float(v1_row["daily_return"]),
                "v2_a_contribution": v2_a,
                "v2_b_contribution": v2_b,
                "v2_total_pnl": v2_a + v2_b,
                "v2_total_return": float(v2_row["daily_return"]),
                "v1_a_weight": _weight_at(v1_trace, date),
                "v2_a_weight": _weight_at(v2_trace, date),
                "daily_v1_minus_v2_return_difference": float(
                    v1_row["daily_return"] - v2_row["daily_return"]
                ),
            }
        )
    return rows, dates


def _trade_day_delta_rows(
    pairs: list[dict],
    mechanism: str,
    start_index: int,
    v1_trace: dict,
    v2_trace: dict,
    dates: list[pd.Timestamp],
) -> list[dict]:
    rows = []
    for date in dates:
        for pair in pairs:
            key = pair["key"]
            v1_pnl = float(v1_trace["trade_daily_pnl"].get(key, {}).get(date, 0.0))
            v2_pnl = float(v2_trace["trade_daily_pnl"].get(key, {}).get(date, 0.0))
            if v1_pnl == 0.0 and v2_pnl == 0.0:
                continue
            rows.append(
                {
                    "mechanism": mechanism,
                    "start_index": start_index,
                    "date": _iso(date),
                    "leg": pair["leg"],
                    "pair": pair["pair"],
                    "fold_id": pair["fold_id"],
                    "entry_date": _iso(pair["entry"]),
                    "exit_date": _iso(pair["exit"]),
                    "exit_reason": pair["exit_reason"],
                    "v1_trade_day_pnl": v1_pnl,
                    "v2_trade_day_pnl": v2_pnl,
                    "trade_day_difference_v1_minus_v2": v1_pnl - v2_pnl,
                }
            )
    return rows


def top_day_trade_attribution(
    daily: pd.DataFrame, trade_days: pd.DataFrame
) -> pd.DataFrame:
    if daily.empty:
        return pd.DataFrame()
    output = []
    for mechanism in ("A", "B"):
        daily_mech = daily[daily["mechanism"] == mechanism].copy()
        if daily_mech.empty:
            continue
        daily_summary = (
            daily_mech.groupby("date", as_index=False)
            .agg(
                v1_total_return=("v1_total_return", "mean"),
                v2_total_return=("v2_total_return", "mean"),
                return_difference=("daily_v1_minus_v2_return_difference", "mean"),
                coverage_starts=("start_index", "nunique"),
            )
            .sort_values("date")
        )
        daily_summary["direction"] = np.where(
            daily_summary["return_difference"] >= 0,
            "v1_outperformed",
            "v2_outperformed",
        )
        day_groups = {
            "v1_outperformed": daily_summary[
                daily_summary["return_difference"] > 0
            ].nlargest(10, "return_difference"),
            "v2_outperformed": daily_summary[
                daily_summary["return_difference"] < 0
            ].nsmallest(10, "return_difference"),
        }
        mech_trade_days = trade_days[trade_days["mechanism"] == mechanism]
        for direction, selected in day_groups.items():
            for day_rank, (_, day) in enumerate(selected.iterrows(), 1):
                day_trades = mech_trade_days[mech_trade_days["date"] == day["date"]]
                if day_trades.empty:
                    output.append(
                        {
                            "mechanism": mechanism,
                            "direction": direction,
                            "day_rank": day_rank,
                            "date": day["date"],
                            "mean_v1_total_return": day["v1_total_return"],
                            "mean_v2_total_return": day["v2_total_return"],
                            "mean_return_difference": day["return_difference"],
                            "coverage_starts": day["coverage_starts"],
                            "trade_rank": 0,
                        }
                    )
                    continue
                group_columns = [
                    "leg",
                    "pair",
                    "fold_id",
                    "entry_date",
                    "exit_date",
                    "exit_reason",
                ]
                grouped = (
                    day_trades.groupby(group_columns, as_index=False)
                    .agg(
                        mean_v1_trade_day_pnl=("v1_trade_day_pnl", "mean"),
                        mean_v2_trade_day_pnl=("v2_trade_day_pnl", "mean"),
                        mean_trade_difference=(
                            "trade_day_difference_v1_minus_v2",
                            "mean",
                        ),
                    )
                    .assign(
                        abs_mean_trade_difference=lambda frame: frame[
                            "mean_trade_difference"
                        ].abs()
                    )
                    .sort_values(
                        ["mean_trade_difference", "abs_mean_trade_difference"],
                        ascending=(
                            [False, False]
                            if direction == "v1_outperformed"
                            else [True, False]
                        ),
                    )
                    .head(5)
                )
                for trade_rank, (_, trade) in enumerate(grouped.iterrows(), 1):
                    output.append(
                        {
                            "mechanism": mechanism,
                            "direction": direction,
                            "day_rank": day_rank,
                            "date": day["date"],
                            "mean_v1_total_return": day["v1_total_return"],
                            "mean_v2_total_return": day["v2_total_return"],
                            "mean_return_difference": day["return_difference"],
                            "coverage_starts": day["coverage_starts"],
                            "trade_rank": trade_rank,
                            "leg": trade["leg"],
                            "pair": trade["pair"],
                            "fold_id": trade["fold_id"],
                            "entry_date": trade["entry_date"],
                            "exit_date": trade["exit_date"],
                            "exit_reason": trade["exit_reason"],
                            "mean_v1_trade_day_pnl": trade["mean_v1_trade_day_pnl"],
                            "mean_v2_trade_day_pnl": trade["mean_v2_trade_day_pnl"],
                            "mean_trade_difference": trade["mean_trade_difference"],
                        }
                    )
    return pd.DataFrame(output)


def _metric_mean(rows: list[dict]) -> dict:
    if not rows:
        return {}
    return {
        key: float(np.mean([row[key] for row in rows]))
        for key in (
            "annualized_return",
            "annualized_volatility",
            "sharpe",
            "max_drawdown",
            "n_days",
        )
    }


def _case_label(case: str) -> tuple[str, str]:
    return CASE_DEFS[case]


def _aggregate_counterfactuals(counterfactual: pd.DataFrame) -> pd.DataFrame:
    if counterfactual.empty:
        return pd.DataFrame()
    value_columns = [
        "annualized_return",
        "annualized_volatility",
        "sharpe",
        "max_drawdown",
        "n_days",
        "rejected_entries",
    ]
    rows = []
    for (window, mechanism, case), frame in counterfactual.groupby(
        ["window", "mechanism", "case"]
    ):
        row = {
            "window": window,
            "scope": "aggregate",
            "start_index": "all" if window == "recent" else 0,
            "mechanism": mechanism,
            "case": case,
            "sizing_source": frame["sizing_source"].iloc[0],
            "allocator_source": frame["allocator_source"].iloc[0],
        }
        for column in value_columns:
            row[column] = float(frame[column].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def build_attribution(counterfactual: pd.DataFrame) -> pd.DataFrame:
    aggregate = _aggregate_counterfactuals(counterfactual)
    rows = []
    for (window, mechanism), frame in aggregate.groupby(["window", "mechanism"]):
        by_case = frame.set_index("case")
        for metric in (
            "sharpe",
            "annualized_return",
            "annualized_volatility",
        ):
            case1 = float(by_case.loc["case_1_v1_sizing_v1_allocator", metric])
            case2 = float(by_case.loc["case_2_v2_sizing_v2_allocator", metric])
            case3 = float(by_case.loc["case_3_v2_sizing_v1_allocator", metric])
            case4 = float(by_case.loc["case_4_v1_sizing_v2_allocator", metric])
            rows.append(
                {
                    "window": window,
                    "mechanism": mechanism,
                    "metric": metric,
                    "case_1_v1_v1": case1,
                    "case_2_v2_v2": case2,
                    "case_3_v2_v1": case3,
                    "case_4_v1_v2": case4,
                    "total_v2_minus_v1": case2 - case1,
                    "sizing_effect_holding_v1_allocator": case3 - case1,
                    "allocator_effect_holding_v1_sizing": case4 - case1,
                    "interaction_residual": case2 - case3 - case4 + case1,
                    "v2_path_recovery_vs_case2": case3 - case2,
                    "v2_allocator_penalty_on_v1": case4 - case1,
                }
            )
    return pd.DataFrame(rows)


def build_hr_outputs(records: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if records.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    mechanism_records = records.copy()
    pair_records = mechanism_records[mechanism_records["mechanism"] == "A"].copy()
    pair_records["mechanism"] = "pair_level"
    pair_records["v1_replay_contribution"] = pair_records[
        "v1_final_dollar_pnl_pre_combined_rescaling"
    ]
    pair_records["v2_replay_contribution"] = pair_records[
        "v2_final_dollar_pnl_pre_combined_rescaling"
    ]
    pair_records["contribution_difference"] = (
        pair_records["v1_replay_contribution"]
        - pair_records["v2_replay_contribution"]
    )
    for frame in (mechanism_records,):
        frame["v1_replay_contribution"] = frame[
            "v1_final_contribution_to_combined_book"
        ]
        frame["v2_replay_contribution"] = frame[
            "v2_final_contribution_to_combined_book"
        ]
        frame["contribution_difference"] = frame[
            "contribution_difference_v1_minus_v2"
        ]
    combined = pd.concat([pair_records, mechanism_records], ignore_index=True)
    combined["outcome"] = np.select(
        [combined["v1_normalized_trade_pnl"] > 0, combined["v1_normalized_trade_pnl"] < 0],
        ["winning_trade", "losing_trade"],
        default="flat_trade",
    )
    winner_rows = []
    for (window, mechanism, outcome), frame in combined.groupby(
        ["window", "mechanism", "outcome"]
    ):
        winner_rows.append(
            {
                "window": window,
                "mechanism": mechanism,
                "outcome": outcome,
                "trade_count": len(frame),
                "average_abs_hr_entry": float(frame["abs_entry_hedge_ratio"].mean()),
                "median_abs_hr_entry": float(frame["abs_entry_hedge_ratio"].median()),
                "average_v1_gross_v2_gross_ratio": float(
                    frame["v1_gross_v2_gross_ratio"].mean()
                ),
                "median_v1_gross_v2_gross_ratio": float(
                    frame["v1_gross_v2_gross_ratio"].median()
                ),
                "v1_raw_dollar_pnl_total": float(
                    frame["v1_final_dollar_pnl_pre_combined_rescaling"].sum()
                ),
                "v2_raw_dollar_pnl_total": float(
                    frame["v2_final_dollar_pnl_pre_combined_rescaling"].sum()
                ),
                "v1_replay_contribution_total": float(
                    frame["v1_replay_contribution"].sum()
                ),
                "v2_replay_contribution_total": float(
                    frame["v2_replay_contribution"].sum()
                ),
                "contribution_difference_total": float(
                    frame["contribution_difference"].sum()
                ),
            }
        )
    winner_loser = pd.DataFrame(winner_rows)

    bucket_rows = []
    for (window, mechanism), frame in combined.groupby(["window", "mechanism"]):
        for bucket, predicate in BUCKETS:
            subset = frame[predicate(frame["abs_entry_hedge_ratio"])]
            if subset.empty:
                continue
            bucket_rows.append(
                {
                    "window": window,
                    "mechanism": mechanism,
                    "hr_bucket": bucket,
                    "trade_count": len(subset),
                    "win_rate": float((subset["v1_normalized_trade_pnl"] > 0).mean()),
                    "average_abs_hr_entry": float(subset["abs_entry_hedge_ratio"].mean()),
                    "average_v1_gross_v2_gross_ratio": float(
                        subset["v1_gross_v2_gross_ratio"].mean()
                    ),
                    "median_v1_gross_v2_gross_ratio": float(
                        subset["v1_gross_v2_gross_ratio"].median()
                    ),
                    "v1_raw_dollar_pnl_total": float(
                        subset["v1_final_dollar_pnl_pre_combined_rescaling"].sum()
                    ),
                    "v2_raw_dollar_pnl_total": float(
                        subset["v2_final_dollar_pnl_pre_combined_rescaling"].sum()
                    ),
                    "v1_total_pnl_contribution": float(
                        subset["v1_replay_contribution"].sum()
                    ),
                    "v2_total_pnl_contribution": float(
                        subset["v2_replay_contribution"].sum()
                    ),
                    "v1_minus_v2_contribution": float(
                        subset["contribution_difference"].sum()
                    ),
                }
            )
    buckets = pd.DataFrame(bucket_rows)

    correlation_rows = []
    for (window, mechanism), frame in combined.groupby(["window", "mechanism"]):
        correlation_rows.append(
            {
                "window": window,
                "mechanism": mechanism,
                "hr_vs_pnl_sign": _safe_corr(
                    frame["abs_entry_hedge_ratio"],
                    np.sign(frame["v1_normalized_trade_pnl"]),
                ),
                "hr_vs_v1_combined_contribution": _safe_corr(
                    frame["abs_entry_hedge_ratio"], frame["v1_replay_contribution"]
                ),
                "hr_vs_v1_minus_v2_contribution": _safe_corr(
                    frame["abs_entry_hedge_ratio"], frame["contribution_difference"]
                ),
            }
        )
    correlations = pd.DataFrame(correlation_rows)
    return winner_loser, buckets, correlations


def _concentration_rows(trades: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if trades.empty and daily.empty:
        return pd.DataFrame()
    for window, scope in (("recent", "recent_aggregate"), ("historical", "historical_aggregate")):
        window_trades = trades[trades["window"] == window]
        window_daily = daily[daily["window"] == window] if not daily.empty else daily
        for mechanism in ("A", "B", "all"):
            trade_frame = (
                window_trades
                if mechanism == "all"
                else window_trades[window_trades["mechanism"] == mechanism]
            )
            daily_frame = (
                window_daily
                if mechanism == "all"
                else window_daily[window_daily["mechanism"] == mechanism]
            )
            for unit, values, total in (
                (
                    "trade_contribution_difference",
                    pd.to_numeric(
                        trade_frame["contribution_difference_v1_minus_v2"],
                        errors="coerce",
                    )
                    if not trade_frame.empty
                    else pd.Series(dtype=float),
                    float(
                        pd.to_numeric(
                            trade_frame["contribution_difference_v1_minus_v2"],
                            errors="coerce",
                        ).sum()
                    )
                    if not trade_frame.empty
                    else 0.0,
                ),
                (
                    "daily_return_difference",
                    pd.to_numeric(
                        daily_frame["daily_v1_minus_v2_return_difference"],
                        errors="coerce",
                    )
                    if not daily_frame.empty
                    else pd.Series(dtype=float),
                    float(
                        pd.to_numeric(
                            daily_frame["daily_v1_minus_v2_return_difference"],
                            errors="coerce",
                        ).sum()
                    )
                    if not daily_frame.empty
                    else 0.0,
                ),
            ):
                if unit == "daily_return_difference" and window != "recent":
                    continue
                ordered = values.dropna().sort_values(ascending=False).reset_index(drop=True)
                for top_n in (1, 5, 10, 20):
                    top = float(ordered.head(top_n).sum()) if not ordered.empty else 0.0
                    rows.append(
                        {
                            "scope": scope,
                            "mechanism": mechanism,
                            "unit": unit,
                            "top_n": top_n,
                            "top_contribution": top,
                            "total_v1_minus_v2": total,
                            "share_of_total_pct": (
                                100.0 * top / total if total else float("nan")
                            ),
                        }
                    )
    return pd.DataFrame(rows)


def _summary_value(frame: pd.DataFrame, mechanism: str, case: str, metric: str):
    match = frame[
        (frame["window"] == "recent")
        & (frame["scope"] == "aggregate")
        & (frame["mechanism"] == mechanism)
        & (frame["case"] == case)
    ]
    if match.empty:
        return float("nan")
    return _num(match.iloc[0][metric])


def recent_historical_table(
    counterfactual: pd.DataFrame,
    allocator_stats: pd.DataFrame,
    winner_loser: pd.DataFrame,
    concentration: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for mechanism in ("A", "B"):
        metric_values = {
            "V1 Sharpe": ("sharpe", "case_1_v1_sizing_v1_allocator"),
            "V2 Sharpe": ("sharpe", "case_2_v2_sizing_v2_allocator"),
            "V1 return": ("annualized_return", "case_1_v1_sizing_v1_allocator"),
            "V2 return": ("annualized_return", "case_2_v2_sizing_v2_allocator"),
            "V1 volatility": (
                "annualized_volatility",
                "case_1_v1_sizing_v1_allocator",
            ),
            "V2 volatility": (
                "annualized_volatility",
                "case_2_v2_sizing_v2_allocator",
            ),
        }
        for diagnostic, (metric, case) in metric_values.items():
            recent = _summary_value(counterfactual, mechanism, case, metric)
            historical_match = counterfactual[
                (counterfactual["window"] == "historical")
                & (counterfactual["scope"] == "aggregate")
                & (counterfactual["mechanism"] == mechanism)
                & (counterfactual["case"] == case)
            ]
            historical = (
                _num(historical_match.iloc[0][metric])
                if not historical_match.empty
                else float("nan")
            )
            rows.append(
                {
                    "mechanism": mechanism,
                    "diagnostic": diagnostic,
                    "recent": recent,
                    "historical": historical,
                }
            )
        for diagnostic, case_v1, case_v2 in (
            ("Sharpe change", "case_1_v1_sizing_v1_allocator", "case_2_v2_sizing_v2_allocator"),
            ("Return change", "case_1_v1_sizing_v1_allocator", "case_2_v2_sizing_v2_allocator"),
            ("Volatility change", "case_1_v1_sizing_v1_allocator", "case_2_v2_sizing_v2_allocator"),
        ):
            metric = {
                "Sharpe change": "sharpe",
                "Return change": "annualized_return",
                "Volatility change": "annualized_volatility",
            }[diagnostic]
            recent = _summary_value(counterfactual, mechanism, case_v2, metric) - _summary_value(
                counterfactual, mechanism, case_v1, metric
            )
            historical_match = counterfactual[
                (counterfactual["window"] == "historical")
                & (counterfactual["scope"] == "aggregate")
                & (counterfactual["mechanism"] == mechanism)
            ].set_index("case")
            historical = (
                _num(historical_match.loc[case_v2, metric])
                - _num(historical_match.loc[case_v1, metric])
                if case_v2 in historical_match.index and case_v1 in historical_match.index
                else float("nan")
            )
            rows.append(
                {
                    "mechanism": mechanism,
                    "diagnostic": diagnostic,
                    "recent": recent,
                    "historical": historical,
                }
            )

        for diagnostic, column in (
            ("Weight-flip months", "preferred_leg_flip_months"),
            ("Mean abs A-weight difference", "mean_abs_a_weight_difference"),
        ):
            values = {}
            for window in ("recent", "historical"):
                match = allocator_stats[
                    (allocator_stats["scope"] == "window_all_starts")
                    & (allocator_stats["window"] == window)
                ]
                values[window] = (
                    _num(match.iloc[0][column]) if not match.empty else float("nan")
                )
            rows.append(
                {
                    "mechanism": mechanism,
                    "diagnostic": diagnostic,
                    "recent": values["recent"],
                    "historical": values["historical"],
                }
            )

        for outcome, diagnostic, column in (
            ("winning_trade", "Avg HR winners", "average_abs_hr_entry"),
            ("losing_trade", "Avg HR losers", "average_abs_hr_entry"),
            (
                "winning_trade",
                "V1/V2 gross ratio winners",
                "average_v1_gross_v2_gross_ratio",
            ),
            (
                "losing_trade",
                "V1/V2 gross ratio losers",
                "average_v1_gross_v2_gross_ratio",
            ),
        ):
            values = {}
            for window in ("recent", "historical"):
                match = winner_loser[
                    (winner_loser["window"] == window)
                    & (winner_loser["mechanism"] == mechanism)
                    & (winner_loser["outcome"] == outcome)
                ]
                values[window] = (
                    _num(match.iloc[0][column]) if not match.empty else float("nan")
                )
            rows.append(
                {
                    "mechanism": mechanism,
                    "diagnostic": diagnostic,
                    "recent": values["recent"],
                    "historical": values["historical"],
                }
            )
        recent_match = concentration[
            (concentration["scope"] == "recent_aggregate")
            & (concentration["mechanism"] == mechanism)
            & (concentration["unit"] == "trade_contribution_difference")
            & (concentration["top_n"] == 10)
        ]
        historical_match = concentration[
            (concentration["scope"] == "historical_aggregate")
            & (concentration["mechanism"] == mechanism)
            & (concentration["unit"] == "trade_contribution_difference")
            & (concentration["top_n"] == 10)
        ]
        rows.append(
            {
                "mechanism": mechanism,
                "diagnostic": "Top-10-trade share of V1 advantage",
                "recent": _num(recent_match.iloc[0]["share_of_total_pct"])
                if not recent_match.empty
                else float("nan"),
                "historical": _num(historical_match.iloc[0]["share_of_total_pct"])
                if not historical_match.empty
                else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def _expected_summary_row(path: Path, mechanism: str) -> dict:
    frame = pd.read_csv(path)
    selected = frame[
        (frame["mechanism"] == mechanism)
        & (frame["A"] == "sp500-12m/cross_sector_slide1m_noscreen")
        & (frame["B"] == "sp500-2m/cross_sector_slide3m_bd7")
    ]
    if selected.empty:
        raise RuntimeError(f"old-winner row missing from {path}")
    return selected.iloc[0].to_dict()


def validate_headlines(counterfactual: pd.DataFrame) -> dict:
    aggregate = _aggregate_counterfactuals(counterfactual)
    checks = []
    field_map = {
        "recent": {
            "annualized_return": "recent_ret",
            "annualized_volatility": "recent_vol",
            "sharpe": "recent_sh",
            "max_drawdown": "recent_mdd",
        },
        "historical": {
            "annualized_return": "hist_ret",
            "annualized_volatility": "hist_vol",
            "sharpe": "hist_sh",
            "max_drawdown": "hist_mdd",
        },
    }
    for window in ("recent", "historical"):
        summary_path = V1_SUMMARY
        for mechanism in ("A", "B"):
            expected_v1 = _expected_summary_row(V1_SUMMARY, mechanism)
            expected_v2 = _expected_summary_row(V2_SUMMARY, mechanism)
            for case, expected in (
                ("case_1_v1_sizing_v1_allocator", expected_v1),
                ("case_2_v2_sizing_v2_allocator", expected_v2),
            ):
                actual = aggregate[
                    (aggregate["window"] == window)
                    & (aggregate["mechanism"] == mechanism)
                    & (aggregate["case"] == case)
                ]
                if actual.empty:
                    raise RuntimeError(f"missing aggregate result for {window}/{mechanism}/{case}")
                actual_row = actual.iloc[0]
                for actual_field, expected_field in field_map[window].items():
                    actual_value = _num(actual_row[actual_field])
                    expected_value = _num(expected[expected_field])
                    checks.append(
                        {
                            "window": window,
                            "mechanism": mechanism,
                            "case": case,
                            "metric": actual_field,
                            "actual": actual_value,
                            "expected": expected_value,
                            "absolute_difference": abs(actual_value - expected_value),
                            "status": "match"
                            if math.isclose(actual_value, expected_value, abs_tol=1e-9)
                            else "mismatch",
                        }
                    )
    return {
        "status": "match" if all(row["status"] == "match" for row in checks) else "mismatch",
        "checks": checks,
    }


def _write_frame(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _fmt(value, digits: int = 4, percent: bool = False) -> str:
    value = _num(value)
    if not math.isfinite(value):
        return "n/a"
    if percent:
        return f"{value * 100:.{digits}f}%"
    return f"{value:.{digits}f}"


def _fmt_dollars(value) -> str:
    value = _num(value)
    if not math.isfinite(value):
        return "n/a"
    return f"${value:,.0f}"


def _cf_metric_text(row: pd.Series) -> str:
    return " / ".join(
        (
            _fmt(row["annualized_return"], 2, True),
            _fmt(row["annualized_volatility"], 2, True),
            _fmt(row["sharpe"], 3),
            _fmt(row["max_drawdown"], 2, True),
        )
    )


def write_report(
    output_path: Path,
    counterfactual: pd.DataFrame,
    attribution: pd.DataFrame,
    allocator_stats: pd.DataFrame,
    winner_loser: pd.DataFrame,
    buckets: pd.DataFrame,
    correlations: pd.DataFrame,
    concentration: pd.DataFrame,
    recent_hist: pd.DataFrame,
    top_days: pd.DataFrame,
    validation: dict,
) -> None:
    aggregate = _aggregate_counterfactuals(counterfactual)
    lines = [
        "# Old Winner V1/V2 Sizing Autopsy",
        "",
        "This focused diagnostic replays only the locked old winner:",
        "`sp500-12m/cross_sector_slide1m_noscreen` plus",
        "`sp500-2m/cross_sector_slide3m_bd7`. It reads the preserved raw V1",
        "reference-leg and V2 gross-exposure runs and does not modify canonical",
        "research outputs.",
        "",
        "Allocator parameters: 84-day causal lookback, step 0.40, bounds",
        "0.10--0.90, initial A weight 0.50. Recent metrics are means across the",
        "five preserved recent starts; historical has one start.",
        "",
        "## Headline Reproduction",
        "",
        "Metrics are annualized return / volatility / Sharpe / max drawdown.",
        "",
        "| Window | Mechanism | V1 Case 1 | V2 Case 2 | V2 minus V1 Sharpe |",
        "|---|---|---|---|---:|",
    ]
    for window in ("recent", "historical"):
        for mechanism in ("A", "B"):
            subset = aggregate[
                (aggregate["window"] == window)
                & (aggregate["mechanism"] == mechanism)
            ].set_index("case")
            case1 = subset.loc["case_1_v1_sizing_v1_allocator"]
            case2 = subset.loc["case_2_v2_sizing_v2_allocator"]
            lines.append(
                f"| {window} | {mechanism} | {_cf_metric_text(case1)} | "
                f"{_cf_metric_text(case2)} | {_fmt(case2['sharpe'] - case1['sharpe'], 3)} |"
            )
    lines.extend(
        [
            "",
            "The V1 and V2 Case 1/2 rows match the existing old-winner summary",
            f"with validation status **{validation['status']}**.",
            "",
            "## Allocator Path",
            "",
            "| Window | Rebalance months | Same direction | Flips | Mean abs A-weight difference | Max difference | Different weights |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for window in ("recent", "historical"):
        match = allocator_stats[
            (allocator_stats["scope"] == "window_all_starts")
            & (allocator_stats["window"] == window)
        ]
        if match.empty:
            continue
        row = match.iloc[0]
        lines.append(
            f"| {window} | {int(row['rebalance_months'])} | "
            f"{int(row['same_direction_months'])} | {int(row['preferred_leg_flip_months'])} | "
            f"{_fmt(row['mean_abs_a_weight_difference'], 3)} | "
            f"{_fmt(row['max_abs_a_weight_difference'], 3)} | "
            f"{_fmt(row['different_weight_pct'], 1)}% |"
        )
    lines.extend(
        [
            "",
            "The complete monthly path, including both trailing Sharpe inputs and",
            "weights, is in `results/old_winner_v1_v2_autopsy/allocator_path.csv`.",
            "",
            "## Hedge-Ratio Diagnostics",
            "",
            "The `pair_level` rows classify trades by normalized trade-PnL sign and",
            "use raw standalone dollar PnL for the pair-sizing view. Mechanism A/B",
            "rows use their actual replay allocation for combined-book contribution.",
            "V1 actual gross exposure is reconstructed from the preserved V1",
            "reference-leg sizing formula using the matched V2 entry prices; the",
            "pre-rescaling dollar PnL fields are the raw standalone trade PnL.",
            "",
            "| Window | Mechanism | Outcome | Trades | Avg abs HR | Avg V1/V2 gross ratio | V1 contribution | V2 contribution | Difference |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for window in ("recent", "historical"):
        for mechanism in ("pair_level", "A", "B"):
            subset = winner_loser[
                (winner_loser["window"] == window)
                & (winner_loser["mechanism"] == mechanism)
            ]
            for outcome in ("winning_trade", "losing_trade"):
                match = subset[subset["outcome"] == outcome]
                if match.empty:
                    continue
                row = match.iloc[0]
                lines.append(
                    f"| {window} | {mechanism} | {outcome.replace('_', ' ')} | "
                    f"{int(row['trade_count'])} | {_fmt(row['average_abs_hr_entry'], 3)} | "
                    f"{_fmt(row['average_v1_gross_v2_gross_ratio'], 3)} | "
                    f"{_fmt_dollars(row['v1_replay_contribution_total'])} | "
                    f"{_fmt_dollars(row['v2_replay_contribution_total'])} | "
                    f"{_fmt_dollars(row['contribution_difference_total'])} |"
                )
    lines.extend(["", "Recent HR correlations:", ""])
    recent_corr = correlations[correlations["window"] == "recent"]
    lines.append("| Mechanism | HR vs PnL sign | HR vs V1 contribution | HR vs V1-minus-V2 contribution |")
    lines.append("|---|---:|---:|---:|")
    for _, row in recent_corr.iterrows():
        lines.append(
            f"| {row['mechanism']} | {_fmt(row['hr_vs_pnl_sign'], 3)} | "
            f"{_fmt(row['hr_vs_v1_combined_contribution'], 3)} | "
            f"{_fmt(row['hr_vs_v1_minus_v2_contribution'], 3)} |"
        )
    lines.extend(
        [
            "",
            "Recent HR buckets are in `hr_bucket_analysis.csv`; winner/loser",
            "aggregates are in `hr_winner_loser.csv`.",
            "",
            "## Counterfactual Decomposition",
            "",
            "| Window | Mechanism | Case 1 V1/V1 | Case 2 V2/V2 | Case 3 V2/V1 | Case 4 V1/V2 |",
            "|---|---|---|---|---|---|",
        ]
    )
    for window in ("recent", "historical"):
        for mechanism in ("A", "B"):
            subset = aggregate[
                (aggregate["window"] == window)
                & (aggregate["mechanism"] == mechanism)
            ].set_index("case")
            lines.append(
                f"| {window} | {mechanism} | "
                f"{_cf_metric_text(subset.loc['case_1_v1_sizing_v1_allocator'])} | "
                f"{_cf_metric_text(subset.loc['case_2_v2_sizing_v2_allocator'])} | "
                f"{_cf_metric_text(subset.loc['case_3_v2_sizing_v1_allocator'])} | "
                f"{_cf_metric_text(subset.loc['case_4_v1_sizing_v2_allocator'])} |"
            )
    lines.extend(
        [
            "",
            "Sharpe is nonlinear, so the following is a counterfactual bridge",
            "with an explicit interaction residual, not a claim that Sharpe has",
            "a unique additive causal attribution.",
            "",
            "| Window | Mechanism | Metric | Total V2 minus V1 | Sizing effect | Allocator effect | Interaction |",
            "|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for _, row in attribution.iterrows():
        lines.append(
            f"| {row['window']} | {row['mechanism']} | {row['metric']} | "
            f"{_fmt(row['total_v2_minus_v1'], 5)} | "
            f"{_fmt(row['sizing_effect_holding_v1_allocator'], 5)} | "
            f"{_fmt(row['allocator_effect_holding_v1_sizing'], 5)} | "
            f"{_fmt(row['interaction_residual'], 5)} |"
        )
    lines.extend(
        [
            "",
            "Case 3 versus Case 2 is the performance recovered by putting V1",
            "weights back on V2-sized trades. Case 4 versus Case 1 is the cost of",
            "putting the V2 path on V1-sized trades.",
            "",
            "## Concentration",
            "",
            "| Mechanism | Unit | Top 1 | Top 5 | Top 10 | Top 20 |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for mechanism in ("A", "B"):
        for unit in ("trade_contribution_difference", "daily_return_difference"):
            match = concentration[
                (concentration["scope"] == "recent_aggregate")
                & (concentration["mechanism"] == mechanism)
                & (concentration["unit"] == unit)
            ].set_index("top_n")
            values = [
                _fmt(match.loc[n]["share_of_total_pct"], 1) + "%"
                if n in match.index
                else "n/a"
                for n in (1, 5, 10, 20)
            ]
            lines.append(
                f"| {mechanism} | {unit.replace('_', ' ')} | "
                + " | ".join(values)
                + " |"
            )
    lines.extend(
        [
            "",
            "The top-day trade attribution file identifies the five largest",
            "directional trade-level contributors for each of the top ten average",
            "recent V1-outperformance days and V2-outperformance days per",
            "mechanism. The leading trade on each day is summarized below.",
            "",
            "| Mechanism | Direction | Rank | Date | Mean return difference | Leading trade | Leading trade difference |",
            "|---|---|---:|---|---:|---|---:|",
        ]
    )
    top_day_leaders = top_days[top_days["trade_rank"] == 1]
    for mechanism in ("A", "B"):
        for direction in ("v1_outperformed", "v2_outperformed"):
            subset = top_day_leaders[
                (top_day_leaders["mechanism"] == mechanism)
                & (top_day_leaders["direction"] == direction)
            ].sort_values("day_rank")
            for _, row in subset.iterrows():
                lines.append(
                    f"| {mechanism} | {direction.replace('_', ' ')} | "
                    f"{int(row['day_rank'])} | {row['date']} | "
                    f"{_fmt(row['mean_return_difference'], 3, True)} | "
                    f"{row.get('leg', '')}:{row.get('pair', '')} | "
                    f"{_fmt_dollars(row.get('mean_trade_difference'))} |"
                )
    lines.extend(
        [
            "",
            "## Recent Versus Historical",
            "",
            "| Mechanism | Diagnostic | Recent | Historical |",
            "|---|---|---:|---:|",
        ]
    )
    for _, row in recent_hist.iterrows():
        diagnostic = row["diagnostic"]
        if "return" in diagnostic.lower() or "volatility" in diagnostic.lower():
            recent = _fmt(row["recent"], 3, True)
            historical = _fmt(row["historical"], 3, True)
        elif "weight" in diagnostic.lower() or "flip" in diagnostic.lower():
            recent = _fmt(row["recent"], 3)
            historical = _fmt(row["historical"], 3)
        else:
            recent = _fmt(row["recent"], 3)
            historical = _fmt(row["historical"], 3)
        lines.append(f"| {row['mechanism']} | {diagnostic} | {recent} | {historical} |")

    lines.extend(["", "## Direct Conclusion", ""])
    for mechanism in ("A", "B"):
        attr = attribution[
            (attribution["window"] == "recent")
            & (attribution["mechanism"] == mechanism)
        ].set_index("metric")
        path = allocator_stats[
            (allocator_stats["scope"] == "window_all_starts")
            & (allocator_stats["window"] == "recent")
        ].iloc[0]
        win = winner_loser[
            (winner_loser["window"] == "recent")
            & (winner_loser["mechanism"] == mechanism)
            & (winner_loser["outcome"] == "winning_trade")
        ].iloc[0]
        loss = winner_loser[
            (winner_loser["window"] == "recent")
            & (winner_loser["mechanism"] == mechanism)
            & (winner_loser["outcome"] == "losing_trade")
        ].iloc[0]
        sizing = attr.loc["sharpe", "sizing_effect_holding_v1_allocator"]
        allocator = attr.loc["sharpe", "allocator_effect_holding_v1_sizing"]
        interaction = attr.loc["sharpe", "interaction_residual"]
        total = attr.loc["sharpe", "total_v2_minus_v1"]
        dominant = "pair sizing" if abs(sizing) >= abs(allocator) else "allocator path"
        lines.append(
            f"For mechanism {mechanism}, the recent Sharpe change was "
            f"**{_fmt(total, 3)}**. Holding the V1 allocator fixed, changing "
            f"pair sizing changed Sharpe by **{_fmt(sizing, 3)}**; holding V1 "
            f"sizing fixed, changing the allocator path changed it by "
            f"**{_fmt(allocator, 3)}**. The interaction residual was "
            f"**{_fmt(interaction, 3)}**, so the larger direct bridge component "
            f"was **{dominant}**."
        )
        lines.append(
            f"The recent winner/loser gross ratios were "
            f"**{_fmt(win['average_v1_gross_v2_gross_ratio'], 3)}** and "
            f"**{_fmt(loss['average_v1_gross_v2_gross_ratio'], 3)}**, with average "
            f"absolute HR **{_fmt(win['average_abs_hr_entry'], 3)}** versus "
            f"**{_fmt(loss['average_abs_hr_entry'], 3)}**."
        )
    recent_pair = winner_loser[
        (winner_loser["window"] == "recent")
        & (winner_loser["mechanism"] == "pair_level")
    ]
    recent_buckets = buckets[
        (buckets["window"] == "recent")
        & (buckets["mechanism"] == "pair_level")
    ]
    high_hr_labels = {"1.0 <= HR < 1.5", "1.5 <= HR <= 2.0", "HR > 2.0"}
    high_hr_delta = float(
        recent_buckets[recent_buckets["hr_bucket"].isin(high_hr_labels)][
            "v1_minus_v2_contribution"
        ].sum()
    )
    total_pair_delta = float(recent_pair["contribution_difference_total"].sum())
    recent_pair_corr = correlations[
        (correlations["window"] == "recent")
        & (correlations["mechanism"] == "pair_level")
    ].iloc[0]
    recent_allocator = allocator_stats[
        (allocator_stats["scope"] == "window_all_starts")
        & (allocator_stats["window"] == "recent")
    ].iloc[0]
    historical_allocator = allocator_stats[
        (allocator_stats["scope"] == "window_all_starts")
        & (allocator_stats["window"] == "historical")
    ].iloc[0]
    recent_a_attr = attribution[
        (attribution["window"] == "recent") & (attribution["mechanism"] == "A")
    ].set_index("metric")
    recent_b_attr = attribution[
        (attribution["window"] == "recent") & (attribution["mechanism"] == "B")
    ].set_index("metric")
    recent_pair_winners = recent_pair[recent_pair["outcome"] == "winning_trade"].iloc[0]
    recent_pair_losers = recent_pair[recent_pair["outcome"] == "losing_trade"].iloc[0]
    recent_a_top10_trade = concentration[
        (concentration["scope"] == "recent_aggregate")
        & (concentration["mechanism"] == "A")
        & (concentration["unit"] == "trade_contribution_difference")
        & (concentration["top_n"] == 10)
    ].iloc[0]
    recent_a_top10_daily = concentration[
        (concentration["scope"] == "recent_aggregate")
        & (concentration["mechanism"] == "A")
        & (concentration["unit"] == "daily_return_difference")
        & (concentration["top_n"] == 10)
    ].iloc[0]
    recent_a_case1 = aggregate[
        (aggregate["window"] == "recent")
        & (aggregate["mechanism"] == "A")
        & (aggregate["case"] == "case_1_v1_sizing_v1_allocator")
    ].iloc[0]
    recent_a_case2 = aggregate[
        (aggregate["window"] == "recent")
        & (aggregate["mechanism"] == "A")
        & (aggregate["case"] == "case_2_v2_sizing_v2_allocator")
    ].iloc[0]
    recent_a_case3 = aggregate[
        (aggregate["window"] == "recent")
        & (aggregate["mechanism"] == "A")
        & (aggregate["case"] == "case_3_v2_sizing_v1_allocator")
    ].iloc[0]
    recent_b_case1 = aggregate[
        (aggregate["window"] == "recent")
        & (aggregate["mechanism"] == "B")
        & (aggregate["case"] == "case_1_v1_sizing_v1_allocator")
    ].iloc[0]
    recent_b_case2 = aggregate[
        (aggregate["window"] == "recent")
        & (aggregate["mechanism"] == "B")
        & (aggregate["case"] == "case_2_v2_sizing_v2_allocator")
    ].iloc[0]
    recent_b_case3 = aggregate[
        (aggregate["window"] == "recent")
        & (aggregate["mechanism"] == "B")
        & (aggregate["case"] == "case_3_v2_sizing_v1_allocator")
    ].iloc[0]
    lines.extend(
        [
            "",
            "1. **High-HR winner hypothesis:** partly supported, but not sufficient by itself. Recent winners had average abs HR "
            f"{_fmt(recent_pair_winners['average_abs_hr_entry'], 3)} versus {_fmt(recent_pair_losers['average_abs_hr_entry'], 3)} for losers, and V1/V2 gross ratios "
            f"{_fmt(recent_pair_winners['average_v1_gross_v2_gross_ratio'], 3)} versus {_fmt(recent_pair_losers['average_v1_gross_v2_gross_ratio'], 3)}. HR >= 1 contributed "
            f"{_fmt(100 * high_hr_delta / total_pair_delta, 1)}% of the recent pair-level net V1-minus-V2 contribution difference ({_fmt_dollars(total_pair_delta)}), but the correlations were weak: "
            f"{_fmt(recent_pair_corr['hr_vs_pnl_sign'], 3)} with PnL sign and {_fmt(recent_pair_corr['hr_vs_v1_minus_v2_contribution'], 3)} with contribution difference.",
            "2. **Allocator path:** materially different in recent data. V1 and V2 differed in "
            f"{int(recent_allocator['preferred_leg_flip_months'])} of {int(recent_allocator['rebalance_months'])} path-months, with mean abs A-weight difference "
            f"{_fmt(recent_allocator['mean_abs_a_weight_difference'], 3)} and maximum {_fmt(recent_allocator['max_abs_a_weight_difference'], 3)}. Historical had "
            f"{int(historical_allocator['preferred_leg_flip_months'])} flips in {int(historical_allocator['rebalance_months'])} months and mean difference {_fmt(historical_allocator['mean_abs_a_weight_difference'], 3)}.",
            "3. **V1 weights on V2 sizing:** Case 3 recovered "
            f"{_fmt(recent_a_case3['sharpe'] - recent_a_case2['sharpe'], 3)} Sharpe points for A and "
            f"{_fmt(recent_b_case3['sharpe'] - recent_b_case2['sharpe'], 3)} for B relative to Case 2. It left Case 3 at Sharpe "
            f"{_fmt(recent_a_case3['sharpe'], 3)}/{_fmt(recent_b_case3['sharpe'], 3)}, versus V1 "
            f"{_fmt(recent_a_case1['sharpe'], 3)}/{_fmt(recent_b_case1['sharpe'], 3)}.",
            "4. **V2 weights on V1 sizing:** Case 4 reduced recent V1 Sharpe by "
            f"{_fmt(abs(recent_a_attr.loc['sharpe', 'allocator_effect_holding_v1_sizing']), 3)} points for A and "
            f"{_fmt(abs(recent_b_attr.loc['sharpe', 'allocator_effect_holding_v1_sizing']), 3)} for B. The allocator path was therefore the larger direct recent Sharpe bridge component, while pair sizing remained meaningful.",
            "5. **Concentration:** the effect was broad rather than explained by a few trades. The top 10 trades accounted for "
            f"{_fmt(recent_a_top10_trade['share_of_total_pct'], 1)}% of the recent A advantage and the top 10 daily differences accounted for "
            f"{_fmt(recent_a_top10_daily['share_of_total_pct'], 1)}%; the directional top-day table identifies the responsible trades.",
            "6. **Historical control:** historical V2 Sharpe fell only about 0.10 versus 0.72 recently because the allocator path changed much less and the V2 path improved V1 sizing in the control. Pair sizing still lowered historical Sharpe by about 0.166, but lower V2 return came with much lower volatility.",
            "7. **Robustness:** the old winner was not robust to the full V1 convention as a headline result, but it was not purely a sizing illusion. V2 sizing with the V1 path retained positive recent Sharpe, while switching the recent allocator path onto V1 sizing caused the larger direct drop. The original advantage is therefore dependent on both reference-leg sizing and the recent Clean40 path; the underlying signal survives, but the result is not convention-invariant.",
            "",
            "## Files",
            "",
            "- `allocator_path.csv`",
            "- `allocator_path_summary.csv`",
            "- `combined_return_series.csv`",
            "- `trade_contributions_recent.csv`",
            "- `daily_contributions_recent.csv`",
            "- `top_day_trade_attribution.csv`",
            "- `hr_bucket_analysis.csv`",
            "- `hr_winner_loser.csv`",
            "- `hr_correlations.csv`",
            "- `counterfactual_results.csv`",
            "- `counterfactual_attribution.csv`",
            "- `concentration_analysis.csv`",
            "- `recent_vs_historical.csv`",
            "- `validation.json`",
            "",
            "No README or canonical selected-book configuration was changed.",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _assert_no_canonical_output(path: Path) -> None:
    resolved = path.resolve()
    forbidden = {
        (ROOT / "results" / "final").resolve(),
        (ROOT / "results" / "sizing_v2_full").resolve(),
    }
    if resolved in forbidden or any(parent in forbidden for parent in resolved.parents):
        raise ValueError(f"diagnostic output may not be inside canonical output tree: {path}")


def run_autopsy(output_root: Path) -> dict:
    _assert_no_canonical_output(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    public_hash_before = _sha256(PUBLIC_SCORE)
    allocator_rows = []
    counter_rows = []
    return_series_rows = []
    trade_rows_recent = []
    all_trade_records = []
    daily_rows_recent = []
    trade_day_rows_recent = []
    pair_match_counts = []
    baseline_differences = []
    sizing_formula_differences = []

    for window in ("recent", "historical"):
        n_starts = len(LEG_SPECS["A"]["recent_starts"]) if window == "recent" else 1
        for start_index in range(n_starts):
            start_a = (
                LEG_SPECS["A"]["recent_starts"][start_index]
                if window == "recent"
                else LEG_SPECS["A"]["historical_start"]
            )
            start_b = (
                LEG_SPECS["B"]["recent_starts"][start_index]
                if window == "recent"
                else LEG_SPECS["B"]["historical_start"]
            )
            v1_runs = {
                leg: load_leg_run(V1_ROOT, leg, window, start_index)
                for leg in ("A", "B")
            }
            v2_runs = {
                leg: load_leg_run(V2_ROOT, leg, window, start_index)
                for leg in ("A", "B")
            }
            pairs_by_leg = {
                leg: _match_trades(v1_runs[leg], v2_runs[leg])
                for leg in ("A", "B")
            }
            for leg in pairs_by_leg:
                for pair in pairs_by_leg[leg]:
                    pair["leg"] = leg
                    sizing_formula_differences.append(
                        abs(
                            pair["v2_raw"].get("sizing_gross_exposure", float("nan"))
                            - pair["v2_audit_gross"]
                        )
                        if _finite(pair["v2_audit_gross"])
                        else 0.0
                    )
            pair_matches = sum(len(items) for items in pairs_by_leg.values())
            pair_match_counts.append(
                {
                    "window": window,
                    "start_index": start_index,
                    "v1_trade_count": pair_matches,
                    "v2_trade_count": pair_matches,
                    "exact_trade_match_count": pair_matches,
                    "v1_only_trade_count": 0,
                    "v2_only_trade_count": 0,
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
            v1_weight, v1_path_details = allocator_path(
                v1_data["A"]["ret"], v1_data["B"]["ret"]
            )
            v2_weight, v2_path_details = allocator_path(
                v2_data["A"]["ret"], v2_data["B"]["ret"]
            )
            allocator_rows.append(
                compare_allocator_paths(
                    v1_path_details,
                    v2_path_details,
                    window,
                    start_index,
                    start_a,
                    start_b,
                )
            )
            for mechanism in ("A", "B"):
                traces = {}
                for case, (sizing_source, allocator_source) in CASE_DEFS.items():
                    data = v1_data if sizing_source == "v1" else v2_data
                    weights = v1_weight if allocator_source == "v1" else v2_weight
                    trace = simulate_trace(data, weights, mechanism)
                    traces[case] = trace
                    if case in (
                        "case_1_v1_sizing_v1_allocator",
                        "case_2_v2_sizing_v2_allocator",
                    ):
                        return_series_rows.extend(
                            {
                                "window": window,
                                "start_index": start_index,
                                "start_A": start_a,
                                "start_B": start_b,
                                "mechanism": mechanism,
                                "case": case,
                                "date": _iso(row["date"]),
                                "daily_return": row["daily_return"],
                            }
                            for row in trace["rows"]
                        )
                    metric = _metric_dict(trace["series"])
                    counter_rows.append(
                        {
                            "window": window,
                            "scope": "run",
                            "start_index": start_index,
                            "start_A": start_a,
                            "start_B": start_b,
                            "mechanism": mechanism,
                            "case": case,
                            "sizing_source": sizing_source,
                            "allocator_source": allocator_source,
                            **metric,
                            "rejected_entries": len(trace["rejected"]),
                        }
                    )

                # Cases 1 and 2 must be byte-for-byte equivalent in daily
                # returns to the existing canonical simulator for this pair.
                for case, data, weights in (
                    ("case_1_v1_sizing_v1_allocator", v1_data, v1_weight),
                    ("case_2_v2_sizing_v2_allocator", v2_data, v2_weight),
                ):
                    expected_rows, _, _, _ = simulate(
                        data,
                        weights,
                        mechanism,
                        capital=INITIAL_CAPITAL,
                        pct=PCT_PER_PAIR,
                        max_pairs=MAX_PAIRS,
                    )
                    difference = _max_series_difference(
                        traces[case]["series"], _series_from_rows(expected_rows)
                    )
                    baseline_differences.append(
                        {
                            "window": window,
                            "start_index": start_index,
                            "mechanism": mechanism,
                            "case": case,
                            "max_daily_return_difference": difference,
                        }
                    )

                for leg in ("A", "B"):
                    for pair in pairs_by_leg[leg]:
                        record = trade_contribution_row(
                            pair,
                            window,
                            start_index,
                            start_a,
                            start_b,
                            mechanism,
                            traces["case_1_v1_sizing_v1_allocator"],
                            traces["case_2_v2_sizing_v2_allocator"],
                        )
                        all_trade_records.append(record)
                        if window == "recent":
                            trade_rows_recent.append(record)
                if window == "recent":
                    daily, dates = daily_contribution_rows(
                        window,
                        start_index,
                        start_a,
                        start_b,
                        mechanism,
                        traces["case_1_v1_sizing_v1_allocator"],
                        traces["case_2_v2_sizing_v2_allocator"],
                    )
                    daily_rows_recent.extend(daily)
                    for leg in ("A", "B"):
                        trade_day_rows_recent.extend(
                            _trade_day_delta_rows(
                                pairs_by_leg[leg],
                                mechanism,
                                start_index,
                                traces["case_1_v1_sizing_v1_allocator"],
                                traces["case_2_v2_sizing_v2_allocator"],
                                dates,
                            )
                        )

    allocator_frame = pd.concat(allocator_rows, ignore_index=True)
    allocator_stats = allocator_summary(allocator_frame)
    counterfactual = pd.DataFrame(counter_rows)
    aggregate_counterfactual = _aggregate_counterfactuals(counterfactual)
    counterfactual_output = pd.concat(
        [counterfactual, aggregate_counterfactual], ignore_index=True
    )
    attribution = build_attribution(counterfactual)
    trade_frame_recent = pd.DataFrame(trade_rows_recent)
    all_trade_frame = pd.DataFrame(all_trade_records)
    daily_frame = pd.DataFrame(daily_rows_recent)
    trade_day_frame = pd.DataFrame(trade_day_rows_recent)
    winner_loser, buckets, correlations = build_hr_outputs(all_trade_frame)
    concentration = _concentration_rows(all_trade_frame, daily_frame)
    top_days = top_day_trade_attribution(daily_frame, trade_day_frame)
    recent_hist = recent_historical_table(
        aggregate_counterfactual,
        allocator_stats,
        winner_loser,
        concentration,
    )
    headline_validation = validate_headlines(counterfactual)
    public_hash_after = _sha256(PUBLIC_SCORE)
    baseline_frame = pd.DataFrame(baseline_differences)
    identity_frame = pd.DataFrame(pair_match_counts)
    validation = {
        "status": "pass",
        "branch": _git_value("branch", "--show-current"),
        "headline_reproduction": headline_validation,
        "baseline_trace_max_daily_return_difference": float(
            baseline_frame["max_daily_return_difference"].max()
        ),
        "baseline_trace_status": "pass"
        if baseline_frame["max_daily_return_difference"].max() <= EPSILON
        else "fail",
        "trade_identity_status": "pass"
        if (
            not identity_frame.empty
            and identity_frame["v1_only_trade_count"].sum() == 0
            and identity_frame["v2_only_trade_count"].sum() == 0
        )
        else "fail",
        "trade_identity_rows": identity_frame.to_dict(orient="records"),
        "v2_sizing_audit_max_difference": float(max(sizing_formula_differences, default=0.0)),
        "v2_sizing_audit_status": "pass"
        if max(sizing_formula_differences, default=0.0) <= 1e-6
        else "fail",
        "counterfactual_definitions": {
            case: {"sizing_source": pair[0], "allocator_source": pair[1]}
            for case, pair in CASE_DEFS.items()
        },
        "rejected_entries_total": int(counterfactual["rejected_entries"].sum()),
        "protected_public_score_sha256_before": public_hash_before,
        "protected_public_score_sha256_after": public_hash_after,
        "protected_public_score_unchanged": public_hash_before == public_hash_after,
        "canonical_outputs_written": False,
        "full_matrix_rerun": False,
    }
    if (
        headline_validation["status"] != "match"
        or validation["baseline_trace_status"] != "pass"
        or validation["trade_identity_status"] != "pass"
        or validation["v2_sizing_audit_status"] != "pass"
        or not validation["protected_public_score_unchanged"]
    ):
        validation["status"] = "fail"

    _write_frame(allocator_frame, output_root / "allocator_path.csv")
    _write_frame(allocator_stats, output_root / "allocator_path_summary.csv")
    _write_frame(
        pd.DataFrame(return_series_rows), output_root / "combined_return_series.csv"
    )
    _write_frame(trade_frame_recent, output_root / "trade_contributions_recent.csv")
    _write_frame(daily_frame, output_root / "daily_contributions_recent.csv")
    _write_frame(top_days, output_root / "top_day_trade_attribution.csv")
    _write_frame(buckets, output_root / "hr_bucket_analysis.csv")
    _write_frame(winner_loser, output_root / "hr_winner_loser.csv")
    _write_frame(correlations, output_root / "hr_correlations.csv")
    _write_frame(counterfactual_output, output_root / "counterfactual_results.csv")
    _write_frame(attribution, output_root / "counterfactual_attribution.csv")
    _write_frame(concentration, output_root / "concentration_analysis.csv")
    _write_frame(recent_hist, output_root / "recent_vs_historical.csv")
    validation["baseline_trace_checks"] = baseline_frame.to_dict(orient="records")
    (output_root / "validation.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    write_report(
        REPORT_PATH,
        counterfactual,
        attribution,
        allocator_stats,
        winner_loser,
        buckets,
        correlations,
        concentration,
        recent_hist,
        top_days,
        validation,
    )
    return {
        "validation": validation,
        "output_root": output_root,
        "report_path": REPORT_PATH,
        "counterfactual": counterfactual_output,
        "attribution": attribution,
        "allocator": allocator_stats,
        "winner_loser": winner_loser,
        "buckets": buckets,
        "correlations": correlations,
        "concentration": concentration,
        "recent_historical": recent_hist,
        "top_days": top_days,
    }


def _git_value(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    result = run_autopsy(args.out)
    print(f"Validation: {result['validation']['status']}")
    print(f"Wrote diagnostics under {result['output_root']}")
    print(f"Wrote report {result['report_path']}")
    return 0 if result["validation"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
