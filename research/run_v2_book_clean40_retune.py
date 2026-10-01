"""Audit and retune Clean40 on the fixed V2-selected book.

This experiment deliberately keeps the book, pair-generation inputs, trade
identities, and V2 gross-exposure sizing fixed.  It replays the preserved V2
raw runs for the current rank-average leader, first auditing the frozen
84-day/0.40/10-90 allocator and then evaluating a predeclared, lattice-aware
Clean40 grid against a static 50/50 replay.

The archived raw runs require the Python/NumPy environment that created them;
on this workstation that is ``C:\\Python314\\python.exe``.
"""

from __future__ import annotations

import json
import math
import sys
import bisect
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.run_combined_backtest import (  # noqa: E402
    metrics as replay_metrics,
    weight_path_momentum_causal,
)
from research.run_gross_exposure_autopsy import (  # noqa: E402
    _gross,
    _validate_native_v2_exposure,
)
from research.run_old_winner_v1_v2_autopsy import (  # noqa: E402
    simulate_trace,
)
from research.run_selected_book_crosscheck import (  # noqa: E402
    _build_metadata,
    _data_for_version,
    _load_case_runs,
    _resolve_books,
)
from research.research_config import STRATEGIES  # noqa: E402


OUTPUT_ROOT = ROOT / "results" / "v2_book_clean40_retune"
INITIAL_CAPITAL = 1_000_000.0
PCT_PER_PAIR = 0.25
MAX_PAIRS = 20
EPSILON = 1e-9
EXPOSURE_TOLERANCE = 1e-6
MECHANISMS = ("A", "B")
WINDOWS = ("recent", "historical")
RECENT_START_COUNT = 5

CURRENT_LOOKBACK = 84
CURRENT_STEP = 0.4
CURRENT_WMIN = 0.1
CURRENT_WMAX = 0.9
INITIAL_WEIGHT_A = 0.5

# This is the predeclared search space.  Bounds that cannot be reached from
# 0.50 by integer step moves are excluded because the prior research showed
# that clamping to such bounds creates a second, path-dependent lattice.
LOOKBACK_CANDIDATES = (42, 63, 84, 105, 126)
STEP_CANDIDATES = (0.1, 0.2, 0.3, 0.4)
BOUND_CANDIDATES = (
    (0.5, 0.5, "50_50"),
    (0.4, 0.6, "40_60"),
    (0.3, 0.7, "30_70"),
    (0.2, 0.8, "20_80"),
    (0.1, 0.9, "10_90"),
)
MATERIAL_SHARPE_MARGIN = 0.05
PLATEAU_SHARPE_TOLERANCE = 0.05
COST_BPS = (1.0, 5.0, 10.0, 20.0)


def _is_close(left: float, right: float, tolerance: float = 1e-9) -> bool:
    return abs(float(left) - float(right)) <= tolerance


def _lattice_aligned(step: float, wmin: float, wmax: float) -> bool:
    if _is_close(wmin, 0.5) and _is_close(wmax, 0.5):
        return True
    if step <= 0 or not (0.0 <= wmin <= 0.5 <= wmax <= 1.0):
        return False
    lower_steps = (0.5 - wmin) / step
    upper_steps = (wmax - 0.5) / step
    return _is_close(lower_steps, round(lower_steps)) and _is_close(
        upper_steps, round(upper_steps)
    )


def _configuration_grid() -> list[dict]:
    configurations = [
        {
            "name": "static_50_50",
            "kind": "static",
            "lookback_days": None,
            "step": 0.0,
            "weight_min": 0.5,
            "weight_max": 0.5,
            "bounds_label": "50_50",
            "lattice_aligned": True,
            "selection_eligible": False,
        }
    ]
    for lookback in LOOKBACK_CANDIDATES:
        for step in STEP_CANDIDATES:
            for wmin, wmax, bounds_label in BOUND_CANDIDATES[1:]:
                if not _lattice_aligned(step, wmin, wmax):
                    continue
                configurations.append(
                    {
                        "name": (
                            f"lb{lookback}_s{step:.2f}_b{wmin:.2f}_{wmax:.2f}"
                        ),
                        "kind": "dynamic",
                        "lookback_days": lookback,
                        "step": step,
                        "weight_min": wmin,
                        "weight_max": wmax,
                        "bounds_label": bounds_label,
                        "lattice_aligned": True,
                        "selection_eligible": True,
                    }
                )
    return configurations


CONFIGURATIONS = _configuration_grid()
BASELINE_NAME = "lb84_s0.40_b0.10_0.90"


def _iso(value) -> str:
    return pd.Timestamp(value).date().isoformat()


def _num(value, default=0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        try:
            return float(default)
        except (TypeError, ValueError):
            return default
    return result if math.isfinite(result) else float(default)


def _metric_series(returns: pd.Series) -> dict:
    returns = returns.dropna().astype(float)
    metrics = replay_metrics(returns)
    cumulative = float((1.0 + returns).prod() - 1.0) if len(returns) else float("nan")
    return {
        "cumulative_return": cumulative,
        "annualized_return": float(metrics["ann_ret"]),
        "annualized_volatility": float(metrics["ann_vol"]),
        "sharpe": float(metrics["sharpe"]),
        "max_drawdown": float(metrics["mdd"]),
        "n_days": int(len(returns)),
    }


def _start_labels(window: str, start_index: int, book: dict) -> tuple[str, str]:
    def label(leg: tuple[str, str]) -> str:
        spec = STRATEGIES[leg[0]]
        if window == "recent":
            return spec["recent_starts"][start_index]
        return spec["historical_start"]

    return label(book["leg_a"]), label(book["leg_b"])


def _load_context(book: dict, window: str, start_index: int) -> dict:
    paths, runs = _load_case_runs(book, window, start_index)
    source, metadata_by_version, provenance, price_differences = _build_metadata(
        paths, runs
    )
    raw_data = _data_for_version(runs, "v2")
    data = {}
    scoped_metadata = {}
    for leg in ("A", "B"):
        scoped_trades = []
        for trade in raw_data[leg]["trades"]:
            source_key = trade["trade_key"]
            replay_key = (leg, source_key)
            scoped_trade = dict(trade)
            scoped_trade["trade_key"] = replay_key
            scoped_trades.append(scoped_trade)
            metadata = dict(metadata_by_version["v2"][source_key])
            metadata["key"] = replay_key
            scoped_metadata[replay_key] = metadata
        data[leg] = {
            "trades": scoped_trades,
            "folds": raw_data[leg]["folds"],
            "ret": raw_data[leg]["ret"],
        }
    v2_native_checks = []
    for leg in ("A", "B"):
        metadata = {
            trade["trade_key"]: metadata_by_version["v2"][trade["trade_key"]]
            for trade in runs[("v2", leg)]["trades"]
        }
        v2_native_checks.append(
            _validate_native_v2_exposure(
                paths[("v2", leg)],
                runs[("v2", leg)],
                metadata,
                source["close_by_source"][("v2", leg)],
                start_index,
                leg,
            )
        )
    start_a, start_b = _start_labels(window, start_index, book)
    return {
        "book": book,
        "window": window,
        "start_index": start_index,
        "start_A": start_a,
        "start_B": start_b,
        "paths": paths,
        "runs": runs,
        "data": data,
        "metadata": scoped_metadata,
        "close_by_leg": {
            leg: source["close_by_source"][("v2", leg)] for leg in ("A", "B")
        },
        "provenance": provenance,
        "price_differences": price_differences,
        "native_checks": v2_native_checks,
    }


def _static_weight_path(data: dict) -> pd.Series:
    union = data["A"]["ret"].index.union(data["B"]["ret"].index).sort_values()
    months = union.to_period("M").unique()
    return pd.Series(
        INITIAL_WEIGHT_A,
        index=pd.DatetimeIndex([month.to_timestamp() for month in months]),
        name="weight_A",
    )


def _build_exposure_basis(
    data: dict,
    metadata: dict,
    close_by_leg: dict[str, pd.DataFrame],
    dates: list[pd.Timestamp],
) -> dict:
    """Precompute unit-notional marked exposure for repeated allocator replays."""
    date_index = pd.DatetimeIndex(dates)
    date_values = list(date_index)
    trade_keys = []
    target_notionals = []
    eod = []
    beginning = []
    columns = {
        ("A", "long"): 0,
        ("A", "short"): 1,
        ("B", "long"): 2,
        ("B", "short"): 3,
    }

    for book_leg in ("A", "B"):
        close = close_by_leg[book_leg]
        for trade in data[book_leg]["trades"]:
            key = trade["trade_key"]
            meta = metadata[key]
            price_columns = {}
            for ticker in (meta["ticker1"], meta["ticker2"]):
                if ticker not in close.columns:
                    raise ValueError(f"missing marked price column for {ticker}")
                price_columns[ticker] = close.reindex(date_index)[ticker].to_numpy(
                    dtype=float
                )
            lo = bisect.bisect_right(date_values, meta["entry"])
            hi = bisect.bisect_right(date_values, meta["exit"])
            unit_eod = np.zeros((len(date_index), 4), dtype=float)
            unit_beginning = np.zeros((len(date_index), 4), dtype=float)
            if hi > lo:
                active = np.arange(lo, hi)
                prior = active - 1
                for size_key, ticker_key, side_key in (
                    ("size1", "ticker1", "side1"),
                    ("size2", "ticker2", "side2"),
                ):
                    eod_values = (
                        float(meta[size_key]) * price_columns[meta[ticker_key]][active]
                    )
                    beginning_values = (
                        float(meta[size_key])
                        * price_columns[meta[ticker_key]][prior]
                    )
                    if not np.isfinite(eod_values).all() or not np.isfinite(
                        beginning_values
                    ).all():
                        raise ValueError(
                            f"missing marked price for {meta[ticker_key]} on active exposure interval"
                        )
                    column = columns[(book_leg, meta[side_key])]
                    unit_eod[active, column] += eod_values
                    unit_beginning[active, column] += beginning_values
            trade_keys.append(key)
            target_notionals.append(float(meta["target_notional"]))
            eod.append(unit_eod)
            beginning.append(unit_beginning)

    return {
        "dates": date_index,
        "trade_keys": trade_keys,
        "target_notionals": np.asarray(target_notionals, dtype=float),
        "eod": np.asarray(eod, dtype=float),
        "beginning": np.asarray(beginning, dtype=float),
    }


def _cached_position_exposure(trace: dict, basis: dict) -> tuple[dict, dict]:
    scales = np.asarray(
        [
            _num(trace["allocations"].get(key), 0.0) / target
            for key, target in zip(
                basis["trade_keys"], basis["target_notionals"]
            )
        ],
        dtype=float,
    )
    eod_values = np.einsum("i,ijd->jd", scales, basis["eod"], optimize=True)
    beginning_values = np.einsum(
        "i,ijd->jd", scales, basis["beginning"], optimize=True
    )
    names = ("a_long", "a_short", "b_long", "b_short")
    eod = {
        date: {name: float(values[index]) for index, name in enumerate(names)}
        for date, values in zip(basis["dates"], eod_values)
    }
    beginning = {
        date: {name: float(values[index]) for index, name in enumerate(names)}
        for date, values in zip(basis["dates"], beginning_values)
    }
    return eod, beginning


def _weight_path(data: dict, configuration: dict) -> pd.Series:
    if configuration["kind"] == "static":
        return _static_weight_path(data)
    return weight_path_momentum_causal(
        data["A"]["ret"],
        data["B"]["ret"],
        lookback=configuration["lookback_days"],
        step=configuration["step"],
        wmin=configuration["weight_min"],
        wmax=configuration["weight_max"],
    )


def _trade_map(data: dict) -> dict:
    result = {}
    for leg in ("A", "B"):
        for trade in data[leg]["trades"]:
            key = trade["trade_key"]
            if key in result:
                raise ValueError(f"duplicate trade key across legs: {key}")
            result[key] = {**trade, "leg": leg}
    return result


def _trace_daily_frame(
    context: dict,
    trace: dict,
    eod_exposure: dict,
    beginning_exposure: dict,
) -> pd.DataFrame:
    frame = pd.DataFrame(trace["rows"])
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.set_index("date").sort_index()
    frame["gross_exposure"] = [
        _gross(eod_exposure[date]) for date in frame.index
    ]
    frame["beginning_gross_exposure"] = [
        _gross(beginning_exposure[date]) for date in frame.index
    ]
    frame["gross_leverage"] = frame["gross_exposure"] / frame["total_capital"]
    frame["capital_utilization"] = frame["gross_leverage"]
    frame["return_on_gross"] = frame["pnl"].where(
        frame["beginning_gross_exposure"] > EPSILON
    ) / frame["beginning_gross_exposure"].where(
        frame["beginning_gross_exposure"] > EPSILON
    )
    frame["weight_A"] = [
        float(trace["weight_by_day"].get(date, INITIAL_WEIGHT_A))
        for date in frame.index
    ]
    frame["weight_B"] = 1.0 - frame["weight_A"]
    for leg in ("A", "B"):
        frame[f"leg_{leg}_pnl"] = [
            float(trace["daily_leg_pnl"].get(date, {}).get(leg, 0.0))
            for date in frame.index
        ]
    frame["gross_long"] = [
        eod_exposure[date]["a_long"] + eod_exposure[date]["b_long"]
        for date in frame.index
    ]
    frame["gross_short"] = [
        eod_exposure[date]["a_short"] + eod_exposure[date]["b_short"]
        for date in frame.index
    ]
    frame["year"] = frame.index.year
    frame["quarter"] = frame.index.to_period("Q").astype(str)
    return frame


def _allocator_stats(
    trace: dict,
    weight_path: pd.Series,
    configuration: dict,
    daily: pd.DataFrame,
) -> dict:
    path = weight_path.sort_index().astype(float)
    changes = path.diff().abs().fillna(0.0)
    rebalance_changes = changes.iloc[1:]
    daily_weight = daily["weight_A"]
    wmin = configuration["weight_min"]
    wmax = configuration["weight_max"]
    movement = []
    active_change_values = []
    daily_index = pd.DatetimeIndex(daily.index).sort_values()
    for date, change in rebalance_changes.items():
        if not len(daily_index) or date < daily_index[0] or date > daily_index[-1]:
            continue
        daily_position = daily_index.searchsorted(date, side="left")
        if daily_position >= len(daily_index):
            continue
        rebalance_date = daily_index[daily_position]
        if change > EPSILON:
            active_change_values.append(float(change))
            movement.append(
                float(change) * float(daily.loc[rebalance_date, "total_capital"])
            )
    active_path = path
    if len(daily_index):
        active_path = path[
            (path.index >= daily_index[0]) & (path.index <= daily_index[-1])
        ]
    years = max(len(daily) / 252.0, 1.0 / 252.0)
    return {
        "allocator_rebalance_count": int(len(active_change_values)),
        "allocator_abs_weight_turnover": float(sum(active_change_values)),
        "allocator_mean_abs_weight_change": float(np.mean(active_change_values))
        if active_change_values
        else 0.0,
        "allocator_max_abs_weight_change": float(max(active_change_values))
        if active_change_values
        else 0.0,
        "allocator_fraction_at_min_daily": float(
            np.isclose(daily_weight, wmin, atol=EPSILON).mean()
        ),
        "allocator_fraction_at_max_daily": float(
            np.isclose(daily_weight, wmax, atol=EPSILON).mean()
        ),
        "allocator_fraction_at_50_daily": float(
            np.isclose(daily_weight, 0.5, atol=EPSILON).mean()
        ),
        "allocator_rebalances_at_min": int(
            np.isclose(active_path, wmin, atol=EPSILON).sum()
        ),
        "allocator_rebalances_at_max": int(
            np.isclose(active_path, wmax, atol=EPSILON).sum()
        ),
        "allocator_rebalances_at_50": int(
            np.isclose(active_path, 0.5, atol=EPSILON).sum()
        ),
        "allocator_one_way_capital_movement": float(sum(movement)),
        "allocator_annualized_capital_movement": float(sum(movement) / years),
        "allocator_annualized_turnover_ratio": float(
            sum(movement) / INITIAL_CAPITAL / years
        ),
        "allocator_path_months": int(len(active_path)),
    }


def _trace_record(
    context: dict,
    configuration: dict,
    mechanism: str,
    include_detail: bool = True,
) -> dict:
    data = context["data"]
    weights = _weight_path(data, configuration)
    trace = simulate_trace(
        data,
        weights,
        mechanism,
        capital=INITIAL_CAPITAL,
        pct=PCT_PER_PAIR,
        max_pairs=MAX_PAIRS,
    )
    dates = sorted(pd.Timestamp(date) for date in trace["series"].index)
    basis = context.get("exposure_basis")
    if basis is None:
        basis = _build_exposure_basis(
            data, context["metadata"], context["close_by_leg"], dates
        )
        context["exposure_basis"] = basis
    elif not basis["dates"].equals(pd.DatetimeIndex(dates)):
        raise ValueError("replay date universe changed within a selected-book context")
    eod_exposure, beginning_exposure = _cached_position_exposure(trace, basis)
    daily = _trace_daily_frame(context, trace, eod_exposure, beginning_exposure)
    metric = _metric_series(trace["series"])
    trade_lookup = _trade_map(data)
    accepted_keys = {
        key
        for key, allocation in trace["allocations"].items()
        if _num(allocation) > EPSILON
    }
    trade_rows = []
    for key in sorted(accepted_keys):
        trade = trade_lookup[key]
        pnl = float(sum(trace["trade_daily_pnl"].get(key, {}).values()))
        trade_rows.append(
            {
                "trade_key": key,
                "leg": trade["leg"],
                "fold_id": int(trade["fold_id"]),
                "pair": str(trade["pair"]),
                "entry_date": pd.Timestamp(trade["entry"]),
                "exit_date": pd.Timestamp(trade["exit"]),
                "exit_reason": str(trade["reason"]),
                "trade_return": float(trade["ret"]),
                "allocation": float(trace["allocations"][key]),
                "pnl": pnl,
                "win": bool(pnl > 0.0),
            }
        )
    trade_frame = pd.DataFrame(trade_rows)
    if trade_frame.empty:
        trade_frame = pd.DataFrame(
            columns=[
                "trade_key",
                "leg",
                "fold_id",
                "pair",
                "entry_date",
                "exit_date",
                "exit_reason",
                "trade_return",
                "allocation",
                "pnl",
                "win",
            ]
        )
    active_gross = daily.loc[daily["gross_exposure"] > EPSILON, "gross_exposure"]
    leverage = daily.loc[daily["gross_exposure"] > EPSILON, "gross_leverage"]
    efficiency = daily.loc[
        daily["beginning_gross_exposure"] > EPSILON, "return_on_gross"
    ].dropna()
    metric.update(
        {
            "final_equity": float(daily["total_capital"].iloc[-1])
            if len(daily)
            else INITIAL_CAPITAL,
            "total_pnl": float(daily["pnl"].sum()),
            "trade_count": int(len(trade_frame)),
            "win_rate": float(trade_frame["win"].mean())
            if len(trade_frame)
            else float("nan"),
            "mean_trade_pnl": float(trade_frame["pnl"].mean())
            if len(trade_frame)
            else float("nan"),
            "median_trade_pnl": float(trade_frame["pnl"].median())
            if len(trade_frame)
            else float("nan"),
            "mean_gross_exposure": float(active_gross.mean())
            if len(active_gross)
            else 0.0,
            "median_gross_exposure": float(active_gross.median())
            if len(active_gross)
            else 0.0,
            "peak_gross_exposure": float(daily["gross_exposure"].max())
            if len(daily)
            else 0.0,
            "mean_gross_leverage": float(leverage.mean()) if len(leverage) else 0.0,
            "median_gross_leverage": float(leverage.median())
            if len(leverage)
            else 0.0,
            "peak_gross_leverage": float(daily["gross_leverage"].max())
            if len(daily)
            else 0.0,
            "capital_utilization_mean": float(daily["capital_utilization"].mean())
            if len(daily)
            else 0.0,
            "capital_utilization_peak": float(daily["capital_utilization"].max())
            if len(daily)
            else 0.0,
            "return_on_gross": float(efficiency.mean()) if len(efficiency) else float("nan"),
            "median_return_on_gross": float(efficiency.median())
            if len(efficiency)
            else float("nan"),
            "active_gross_days": int(len(active_gross)),
            "efficiency_days": int(len(efficiency)),
        }
    )
    metric.update(_allocator_stats(trace, weights, configuration, daily))
    reconciliation = {
        "equity_pnl_difference": float(
            daily["total_capital"].iloc[-1]
            - INITIAL_CAPITAL
            - daily["pnl"].sum()
        )
        if len(daily)
        else 0.0,
        "leg_pnl_difference": float(
            daily["pnl"].sum()
            - daily["leg_A_pnl"].sum()
            - daily["leg_B_pnl"].sum()
        ),
    }
    return {
        "context": context,
        "configuration": configuration,
        "mechanism": mechanism,
        "weights": weights,
        "trace": trace,
        "daily": daily,
        "metric": metric,
        "trade_frame": trade_frame if include_detail else trade_frame,
        "accepted_keys": accepted_keys,
        "reconciliation": reconciliation,
    }


def _metric_output_row(record: dict) -> dict:
    context = record["context"]
    config = record["configuration"]
    row = {
        "row_type": "per_start",
        "configuration": config["name"],
        "configuration_kind": config["kind"],
        "lookback_days": config["lookback_days"],
        "step": config["step"],
        "weight_min": config["weight_min"],
        "weight_max": config["weight_max"],
        "bounds_label": config["bounds_label"],
        "lattice_aligned": config["lattice_aligned"],
        "selected_book_origin": "v2_selected",
        "leg_a": "/".join(context["book"]["leg_a"]),
        "leg_b": "/".join(context["book"]["leg_b"]),
        "window": context["window"],
        "start_index": context["start_index"],
        "start_A": context["start_A"],
        "start_B": context["start_B"],
        "mechanism": record["mechanism"],
    }
    row.update(record["metric"])
    row.update(record["reconciliation"])
    return row


def _period_rows(record: dict) -> list[dict]:
    daily = record["daily"]
    trades = record["trade_frame"]
    rows = []
    for period_type, period_values in (
        ("year", sorted(daily["year"].unique())),
        ("quarter", sorted(daily["quarter"].unique())),
    ):
        for period in period_values:
            mask = daily[period_type].eq(period)
            frame = daily.loc[mask]
            if frame.empty:
                continue
            first_date = frame.index.min()
            prior = daily.loc[daily.index < first_date, "total_capital"]
            starting_equity = float(prior.iloc[-1]) if len(prior) else INITIAL_CAPITAL
            period_equity = starting_equity * (1.0 + frame["daily_return"]).cumprod()
            drawdown = (period_equity / period_equity.cummax() - 1.0).min()
            entry_period = pd.Series(dtype=object)
            if len(trades):
                dates = pd.to_datetime(trades["entry_date"])
                entry_period = dates.dt.year if period_type == "year" else dates.dt.to_period("Q").astype(str)
            trade_count = int((entry_period == period).sum()) if len(entry_period) else 0
            row = {
                "period_type": period_type,
                "period": str(period),
                "selected_book_origin": "v2_selected",
                "window": record["context"]["window"],
                "start_index": record["context"]["start_index"],
                "mechanism": record["mechanism"],
                "start_date": _iso(frame.index.min()),
                "end_date": _iso(frame.index.max()),
                "pnl": float(frame["pnl"].sum()),
                "account_return": float((1.0 + frame["daily_return"]).prod() - 1.0),
                "contribution_to_total_return": float(frame["pnl"].sum() / INITIAL_CAPITAL),
                "share_of_total_pnl": float(
                    frame["pnl"].sum() / record["metric"]["total_pnl"]
                )
                if abs(record["metric"]["total_pnl"]) > EPSILON
                else float("nan"),
                "annualized_volatility": float(frame["daily_return"].std() * math.sqrt(252))
                if len(frame) > 1
                else float("nan"),
                "within_period_max_drawdown": float(drawdown),
                "trade_count": trade_count,
                "mean_gross_exposure": float(frame.loc[frame["gross_exposure"] > EPSILON, "gross_exposure"].mean())
                if (frame["gross_exposure"] > EPSILON).any()
                else 0.0,
                "mean_gross_leverage": float(frame.loc[frame["gross_exposure"] > EPSILON, "gross_leverage"].mean())
                if (frame["gross_exposure"] > EPSILON).any()
                else 0.0,
                "mean_weight_A": float(frame["weight_A"].mean()),
                "mean_weight_B": float(frame["weight_B"].mean()),
                "leg_A_pnl": float(frame["leg_A_pnl"].sum()),
                "leg_B_pnl": float(frame["leg_B_pnl"].sum()),
            }
            rows.append(row)
    return rows


def _fold_rows(record: dict) -> list[dict]:
    trades = record["trade_frame"]
    if trades.empty:
        return []
    rows = []
    folds = pd.concat(
        [record["context"]["data"][leg]["folds"] for leg in ("A", "B")],
        ignore_index=True,
    ).drop_duplicates("fold")
    for fold_id, frame in trades.groupby("fold_id", sort=True):
        fold_meta = folds[folds["fold"].eq(fold_id)]
        rows.append(
            {
                "selected_book_origin": "v2_selected",
                "window": record["context"]["window"],
                "start_index": record["context"]["start_index"],
                "mechanism": record["mechanism"],
                "fold_id": int(fold_id),
                "fold_start": _iso(fold_meta["start"].min()) if len(fold_meta) else None,
                "fold_end": _iso(fold_meta["end"].max()) if len(fold_meta) else None,
                "pnl": float(frame["pnl"].sum()),
                "share_of_total_pnl": float(
                    frame["pnl"].sum() / record["metric"]["total_pnl"]
                )
                if abs(record["metric"]["total_pnl"]) > EPSILON
                else float("nan"),
                "trade_count": int(len(frame)),
                "win_rate": float(frame["win"].mean()),
                "mean_trade_pnl": float(frame["pnl"].mean()),
                "leg_A_pnl": float(frame.loc[frame["leg"].eq("A"), "pnl"].sum()),
                "leg_B_pnl": float(frame.loc[frame["leg"].eq("B"), "pnl"].sum()),
            }
        )
    return rows


def _filtered_data(data: dict, excluded_keys: set, excluded_folds: set | None = None) -> dict:
    result = {}
    excluded_folds = excluded_folds or set()
    for leg in ("A", "B"):
        trades = [
            trade
            for trade in data[leg]["trades"]
            if trade["trade_key"] not in excluded_keys
            and int(trade["fold_id"]) not in excluded_folds
        ]
        folds = data[leg]["folds"]
        if excluded_folds:
            folds = folds[~folds["fold"].isin(excluded_folds)].copy()
        result[leg] = {
            "trades": trades,
            "folds": folds,
            "ret": data[leg]["ret"],
        }
    return result


def _replay_metrics_with_data(data: dict, weights: pd.Series, mechanism: str) -> dict:
    trace = simulate_trace(
        data,
        weights,
        mechanism,
        capital=INITIAL_CAPITAL,
        pct=PCT_PER_PAIR,
        max_pairs=MAX_PAIRS,
    )
    return _metric_series(trace["series"])


def _concentration_rows(record: dict) -> tuple[dict, list[dict], list[dict], list[dict]]:
    trades = record["trade_frame"].copy()
    context = record["context"]
    base = {
        "selected_book_origin": "v2_selected",
        "window": context["window"],
        "start_index": context["start_index"],
        "mechanism": record["mechanism"],
    }
    if trades.empty:
        return {**base, "trade_count": 0}, [], [], []
    ordered = trades.sort_values("pnl", ascending=False).reset_index(drop=True)
    abs_total = float(trades["pnl"].abs().sum())
    top = {}
    for count in (1, 3, 5, 10):
        subset = ordered.head(count)
        top[f"top_{count}_trade_pnl"] = float(subset["pnl"].sum())
        top[f"top_{count}_trade_abs_share"] = float(
            subset["pnl"].abs().sum() / abs_total
        ) if abs_total > EPSILON else float("nan")
        excluded = set(subset["trade_key"])
        filtered = _replay_metrics_with_data(
            _filtered_data(context["data"], excluded),
            record["weights"],
            record["mechanism"],
        )
        top[f"remove_best_{count}_trade_cumulative_return"] = filtered[
            "cumulative_return"
        ]
        top[f"remove_best_{count}_trade_sharpe"] = filtered["sharpe"]
        top[f"remove_best_{count}_trade_max_drawdown"] = filtered[
            "max_drawdown"
        ]
        top[f"pnl_after_remove_best_{count}_trades"] = float(
            record["metric"]["total_pnl"] - subset["pnl"].sum()
        )
    pair_frame = (
        trades.groupby("pair", as_index=False)
        .agg(pair_pnl=("pnl", "sum"), trade_count=("pnl", "size"), wins=("win", "sum"))
        .sort_values("pair_pnl", ascending=False)
    )
    pair_frame["win_rate"] = pair_frame["wins"] / pair_frame["trade_count"]
    pair_frame["abs_pnl_share"] = pair_frame["pair_pnl"].abs() / abs_total
    pair_frame["rank_desc"] = np.arange(1, len(pair_frame) + 1)
    pair_frame["rank_abs"] = pair_frame["abs_pnl_share"].rank(
        ascending=False, method="first"
    )
    pair_rows = []
    for _, row in pair_frame.iterrows():
        pair_rows.append(
            {
                **base,
                "pair": row["pair"],
                "pair_pnl": float(row["pair_pnl"]),
                "trade_count": int(row["trade_count"]),
                "win_rate": float(row["win_rate"]),
                "abs_pnl_share": float(row["abs_pnl_share"]),
                "rank_desc": int(row["rank_desc"]),
                "rank_abs": int(row["rank_abs"]),
            }
        )
    symbol_rows = []
    for _, row in trades.iterrows():
        parts = str(row["pair"]).split("-", 1)
        if len(parts) != 2:
            parts = [str(row["pair"]), str(row["pair"])]
        for symbol in parts:
            symbol_rows.append(
                {
                    **base,
                    "symbol": symbol,
                    "symbol_pnl": float(row["pnl"]) / 2.0,
                    "symbol_abs_pnl": abs(float(row["pnl"])) / 2.0,
                    "source_pair": row["pair"],
                }
            )
    symbol_frame = pd.DataFrame(symbol_rows)
    symbol_frame = (
        symbol_frame.groupby(
            ["selected_book_origin", "window", "start_index", "mechanism", "symbol"],
            as_index=False,
        )
        .agg(
            symbol_pnl=("symbol_pnl", "sum"),
            symbol_abs_pnl=("symbol_abs_pnl", "sum"),
            pair_mentions=("source_pair", "nunique"),
        )
        .sort_values("symbol_pnl", ascending=False)
    )
    symbol_rows = []
    for rank, (_, row) in enumerate(symbol_frame.iterrows(), 1):
        symbol_rows.append(
            {
                **base,
                "symbol": row["symbol"],
                "symbol_pnl": float(row["symbol_pnl"]),
                "symbol_abs_pnl": float(row["symbol_abs_pnl"]),
                "abs_pnl_share": float(row["symbol_abs_pnl"] / abs_total),
                "pair_mentions": int(row["pair_mentions"]),
                "rank_desc": rank,
            }
        )
    trade_detail = []
    abs_shares = trades["pnl"].abs() / abs_total if abs_total > EPSILON else trades["pnl"] * 0.0
    hhi = float((abs_shares**2).sum())
    ascending_ranks = ordered["pnl"].rank(ascending=True, method="first").to_numpy()
    for rank, (_, row) in enumerate(ordered.iterrows(), 1):
        trade_detail.append(
            {
                **base,
                "trade_rank_desc": rank,
                "trade_rank_asc": int(ascending_ranks[rank - 1]),
                "trade_key": row["trade_key"],
                "leg": row["leg"],
                "fold_id": int(row["fold_id"]),
                "pair": row["pair"],
                "entry_date": _iso(row["entry_date"]),
                "exit_date": _iso(row["exit_date"]),
                "pnl": float(row["pnl"]),
                "absolute_pnl_share": float(abs(float(row["pnl"])) / abs_total)
                if abs_total > EPSILON
                else 0.0,
                "exit_reason": row["exit_reason"],
            }
        )
    summary = {
        **base,
        "trade_count": int(len(trades)),
        "pair_count": int(trades["pair"].nunique()),
        "symbol_count": int(symbol_frame["symbol"].nunique()),
        "total_pnl": float(record["metric"]["total_pnl"]),
        "absolute_trade_pnl_hhi": hhi,
        "top_trade": ordered.iloc[0]["trade_key"],
        "top_trade_pnl": float(ordered.iloc[0]["pnl"]),
        "worst_trade": ordered.iloc[-1]["trade_key"],
        "worst_trade_pnl": float(ordered.iloc[-1]["pnl"]),
        "top_pair": pair_frame.iloc[0]["pair"],
        "top_pair_pnl": float(pair_frame.iloc[0]["pair_pnl"]),
        "worst_pair": pair_frame.iloc[-1]["pair"],
        "worst_pair_pnl": float(pair_frame.iloc[-1]["pair_pnl"]),
        **top,
    }
    return summary, trade_detail, pair_rows, symbol_rows


def _baseline_leg_rows(context: dict, dynamic: dict, static: dict) -> list[dict]:
    rows = []
    for leg in ("A", "B"):
        path = context["paths"][("v2", leg)]
        exposure = pd.read_csv(path / "daily_exposure.csv", parse_dates=["date"])
        exposure["gross_leverage"] = exposure["gross_exposure"] / exposure["equity"]
        active_exposure = exposure[exposure["gross_exposure"] > EPSILON]
        series = context["data"][leg]["ret"].dropna()
        metric = _metric_series(series)
        trades = context["data"][leg]["trades"]
        rows.append(
            {
                "source": "standalone_v2_leg",
                "leg": leg,
                "window": context["window"],
                "start_index": context["start_index"],
                "mechanism": "standalone",
                "trade_count": len(trades),
                "win_rate": float(np.mean([trade["ret"] > 0 for trade in trades]))
                if trades
                else float("nan"),
                "mean_gross_exposure": float(
                    active_exposure["gross_exposure"].mean()
                ),
                "median_gross_exposure": float(
                    active_exposure["gross_exposure"].median()
                ),
                "mean_gross_leverage": float(
                    active_exposure["gross_leverage"].mean()
                ),
                "peak_gross_leverage": float(exposure["gross_leverage"].max()),
                **metric,
            }
        )
    a = context["data"]["A"]["ret"].rename("A")
    b = context["data"]["B"]["ret"].rename("B")
    aligned = pd.concat([a, b], axis=1).fillna(0.0)
    rolling = aligned["A"].rolling(63).corr(aligned["B"]).dropna()
    rows.append(
        {
            "source": "leg_correlation",
            "leg": "A_B",
            "window": context["window"],
            "start_index": context["start_index"],
            "mechanism": "both",
            "daily_correlation": float(aligned["A"].corr(aligned["B"])),
            "rolling_63d_correlation_mean": float(rolling.mean()) if len(rolling) else float("nan"),
            "rolling_63d_correlation_min": float(rolling.min()) if len(rolling) else float("nan"),
            "rolling_63d_correlation_max": float(rolling.max()) if len(rolling) else float("nan"),
        }
    )
    for source, record in (("book_clean40_baseline", dynamic), ("book_static_50_50", static)):
        rows.append(
            {
                "source": source,
                "leg": "book",
                "window": context["window"],
                "start_index": context["start_index"],
                "mechanism": record["mechanism"],
                **record["metric"],
            }
        )
    return rows


def _aggregate_metric_rows(grid_rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    mechanism_rows = []
    for keys, frame in grid_rows.groupby(
        ["configuration", "configuration_kind", "lookback_days", "step", "weight_min", "weight_max", "bounds_label", "lattice_aligned", "mechanism"],
        dropna=False,
    ):
        config, kind, lookback, step, wmin, wmax, bounds_label, aligned, mechanism = keys
        recent = frame[frame["window"].eq("recent")]
        historical = frame[frame["window"].eq("historical")]
        row = {
            "configuration": config,
            "configuration_kind": kind,
            "lookback_days": lookback,
            "step": step,
            "weight_min": wmin,
            "weight_max": wmax,
            "bounds_label": bounds_label,
            "lattice_aligned": aligned,
            "mechanism": mechanism,
            "recent_start_count": int(len(recent)),
            "recent_mean_sharpe": float(recent["sharpe"].mean()),
            "recent_median_sharpe": float(recent["sharpe"].median()),
            "recent_p20_sharpe": float(recent["sharpe"].quantile(0.2)),
            "recent_min_sharpe": float(recent["sharpe"].min()),
            "recent_max_sharpe": float(recent["sharpe"].max()),
            "recent_sharpe_std": float(recent["sharpe"].std()),
            "recent_mean_cumulative_return": float(recent["cumulative_return"].mean()),
            "recent_mean_annualized_return": float(recent["annualized_return"].mean()),
            "recent_worst_max_drawdown": float(recent["max_drawdown"].min()),
            "recent_mean_trade_count": float(recent["trade_count"].mean()),
            "recent_mean_turnover_ratio": float(recent["allocator_annualized_turnover_ratio"].mean()),
            "historical_sharpe": float(historical["sharpe"].iloc[0]) if len(historical) else float("nan"),
            "historical_cumulative_return": float(historical["cumulative_return"].iloc[0]) if len(historical) else float("nan"),
            "historical_annualized_return": float(historical["annualized_return"].iloc[0]) if len(historical) else float("nan"),
            "historical_max_drawdown": float(historical["max_drawdown"].iloc[0]) if len(historical) else float("nan"),
            "historical_trade_count": float(historical["trade_count"].iloc[0]) if len(historical) else float("nan"),
            "historical_turnover_ratio": float(historical["allocator_annualized_turnover_ratio"].iloc[0]) if len(historical) else float("nan"),
        }
        mechanism_rows.append(row)
    mechanism_frame = pd.DataFrame(mechanism_rows)
    config_rows = []
    group_columns = [
        "configuration",
        "configuration_kind",
        "lookback_days",
        "step",
        "weight_min",
        "weight_max",
        "bounds_label",
        "lattice_aligned",
    ]
    for keys, frame in mechanism_frame.groupby(group_columns, dropna=False):
        row = dict(zip(group_columns, keys))
        recent_cells = frame["recent_p20_sharpe"].to_numpy(dtype=float)
        historical_cells = frame["historical_sharpe"].to_numpy(dtype=float)
        median_cells = frame["recent_median_sharpe"].to_numpy(dtype=float)
        row.update(
            {
                "mechanism_count": int(len(frame)),
                "robust_floor": float(np.nanmin(np.concatenate([recent_cells, historical_cells]))),
                "robust_median_floor": float(np.nanmin(np.concatenate([median_cells, historical_cells]))),
                "recent_mean_sharpe": float(frame["recent_mean_sharpe"].mean()),
                "recent_median_sharpe_floor": float(frame["recent_median_sharpe"].min()),
                "recent_p20_sharpe_floor": float(frame["recent_p20_sharpe"].min()),
                "historical_mean_sharpe": float(frame["historical_sharpe"].mean()),
                "historical_min_sharpe": float(frame["historical_sharpe"].min()),
                "recent_mean_cumulative_return": float(frame["recent_mean_cumulative_return"].mean()),
                "historical_mean_cumulative_return": float(frame["historical_cumulative_return"].mean()),
                "worst_max_drawdown": float(
                    min(frame["recent_worst_max_drawdown"].min(), frame["historical_max_drawdown"].min())
                ),
                "mean_trade_count": float(
                    np.mean([frame["recent_mean_trade_count"].mean(), frame["historical_trade_count"].mean()])
                ),
                "mean_annualized_turnover_ratio": float(
                    np.mean([frame["recent_mean_turnover_ratio"].mean(), frame["historical_turnover_ratio"].mean()])
                ),
                "mechanism_sharpe_gap": float(frame["recent_mean_sharpe"].max() - frame["recent_mean_sharpe"].min()),
            }
        )
        config_rows.append(row)
    return mechanism_frame, pd.DataFrame(config_rows)


def _selection_sort(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.sort_values(
        [
            "robust_median_floor",
            "robust_floor",
            "recent_mean_sharpe",
            "historical_mean_sharpe",
            "worst_max_drawdown",
            "mean_annualized_turnover_ratio",
            "configuration",
        ],
        ascending=[False, False, False, False, False, True, True],
    )


def _select_dynamic(frame: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    dynamic = frame[frame["configuration_kind"].eq("dynamic")].copy()
    if dynamic.empty:
        raise ValueError("no dynamic Clean40 configurations were evaluated")
    best_floor = float(dynamic["robust_floor"].max())
    plateau = dynamic[dynamic["robust_floor"] >= best_floor - PLATEAU_SHARPE_TOLERANCE]
    ranked_dynamic = _selection_sort(dynamic).reset_index(drop=True)
    selection_rank = {
        name: rank + 1
        for rank, name in enumerate(ranked_dynamic["configuration"])
    }
    plateau_names = set(plateau["configuration"])
    result = frame.copy()
    result["plateau_member"] = result["configuration"].isin(plateau_names)
    result["selection_rank"] = result["configuration"].map(selection_rank)
    result["best_robust_floor"] = best_floor
    result["plateau_count"] = int(len(plateau))
    selected = _selection_sort(plateau).iloc[0].to_dict()
    selected.update(
        {
            "plateau_member": True,
            "selection_rank": selection_rank[selected["configuration"]],
            "best_robust_floor": best_floor,
            "plateau_count": int(len(plateau)),
        }
    )
    return selected, result


def _neighbor_rows(aggregate: pd.DataFrame, selected: dict) -> pd.DataFrame:
    dynamic = aggregate[aggregate["configuration_kind"].eq("dynamic")].copy()
    target = selected
    rows = []
    for _, row in dynamic.iterrows():
        relation = None
        if row["configuration"] == target["configuration"]:
            relation = "selected"
        elif row["weight_min"] == target["weight_min"] and row["weight_max"] == target["weight_max"] and row["step"] == target["step"]:
            if abs(float(row["lookback_days"]) - float(target["lookback_days"])) in (21, 42):
                relation = "lookback_neighbor"
        elif row["lookback_days"] == target["lookback_days"] and row["weight_min"] == target["weight_min"] and row["weight_max"] == target["weight_max"]:
            if abs(float(row["step"]) - float(target["step"])) in (0.1, 0.2):
                relation = "step_neighbor"
        elif row["lookback_days"] == target["lookback_days"] and row["step"] == target["step"]:
            if abs(float(row["weight_min"]) - float(target["weight_min"])) in (0.1, 0.2):
                relation = "bounds_neighbor"
        if relation:
            item = row.to_dict()
            item["neighbor_relation"] = relation
            rows.append(item)
    return pd.DataFrame(rows)


def _leave_one_start_out(
    grid_rows: pd.DataFrame,
    historical_rows: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    dynamic_names = set(
        grid_rows.loc[grid_rows["configuration_kind"].eq("dynamic"), "configuration"]
    )
    for excluded in range(RECENT_START_COUNT):
        training = grid_rows[
            grid_rows["window"].eq("recent")
            & grid_rows["start_index"].ne(excluded)
            & grid_rows["configuration"].isin(dynamic_names)
        ]
        training = pd.concat(
            [training, historical_rows[historical_rows["configuration"].isin(dynamic_names)]],
            ignore_index=True,
        )
        _, aggregate = _aggregate_metric_rows(training)
        selected, _ = _select_dynamic(aggregate)
        held = grid_rows[
            grid_rows["window"].eq("recent")
            & grid_rows["start_index"].eq(excluded)
            & grid_rows["configuration"].eq(selected["configuration"])
        ]
        for _, row in held.iterrows():
            rows.append(
                {
                    "excluded_start_index": excluded,
                    "excluded_start_A": row["start_A"],
                    "excluded_start_B": row["start_B"],
                    "selected_configuration": selected["configuration"],
                    "selected_lookback_days": selected["lookback_days"],
                    "selected_step": selected["step"],
                    "selected_bounds_label": selected["bounds_label"],
                    "selection_training_start_count": RECENT_START_COUNT - 1,
                    "selection_training_includes_historical": True,
                    "mechanism": row["mechanism"],
                    "held_out_sharpe": row["sharpe"],
                    "held_out_cumulative_return": row["cumulative_return"],
                    "held_out_max_drawdown": row["max_drawdown"],
                    "held_out_trade_count": row["trade_count"],
                }
            )
    return pd.DataFrame(rows)


def _cost_rows(grid_rows: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in grid_rows.iterrows():
        years = max(float(row["n_days"]) / 252.0, 1.0 / 252.0)
        movement = float(row["allocator_one_way_capital_movement"])
        for bps in COST_BPS:
            annual_drag = movement / INITIAL_CAPITAL / years * bps / 10000.0
            item = row.to_dict()
            item.update(
                {
                    "cost_bps": bps,
                    "allocator_only_annual_cost_drag": annual_drag,
                    "annualized_return_after_allocator_only_cost": float(
                        row["annualized_return"] - annual_drag
                    ),
                    "cost_scope": "allocator-only one-way movement; entry/exit costs excluded",
                }
            )
            rows.append(item)
    return pd.DataFrame(rows)


def _fold_leave_one_out(record: dict, fold_rows: list[dict]) -> list[dict]:
    rows = []
    folds = sorted({int(row["fold_id"]) for row in fold_rows})
    for fold_id in folds:
        filtered = _filtered_data(record["context"]["data"], set(), {fold_id})
        metric = _replay_metrics_with_data(filtered, record["weights"], record["mechanism"])
        selected = next(row for row in fold_rows if int(row["fold_id"]) == fold_id)
        rows.append(
            {
                "selected_book_origin": "v2_selected",
                "window": record["context"]["window"],
                "start_index": record["context"]["start_index"],
                "mechanism": record["mechanism"],
                "removed_fold_id": fold_id,
                "removed_fold_pnl": selected["pnl"],
                "removed_fold_share_of_total_pnl": selected["share_of_total_pnl"],
                "full_sharpe": record["metric"]["sharpe"],
                "full_cumulative_return": record["metric"]["cumulative_return"],
                "leave_one_fold_out_sharpe": metric["sharpe"],
                "leave_one_fold_out_cumulative_return": metric["cumulative_return"],
                "leave_one_fold_out_max_drawdown": metric["max_drawdown"],
            }
        )
    return rows


def _hash_file(path: Path) -> str | None:
    import hashlib

    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer, np.floating)):
        value = value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _write_plots(
    baseline_records: dict,
    aggregate: pd.DataFrame,
    output_root: Path,
) -> list[str]:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return []
    written = []
    recent = [
        record
        for key, record in baseline_records.items()
        if key[0] == "recent" and key[2] == "A" and key[1] < RECENT_START_COUNT
    ]
    if recent:
        figure, axis = plt.subplots(figsize=(10, 5))
        for record in recent:
            equity = record["daily"]["total_capital"] / INITIAL_CAPITAL
            axis.plot(equity.index, equity, label=f"start {record['context']['start_index'] + 1}")
        axis.set_title("V2-selected book: frozen Clean40 recent equity paths")
        axis.set_ylabel("Equity multiple")
        axis.legend(ncol=3, fontsize=8)
        axis.grid(alpha=0.25)
        path = output_root / "baseline_equity_recent.png"
        figure.tight_layout()
        figure.savefig(path, dpi=140)
        plt.close(figure)
        written.append(path.name)

        figure, axis = plt.subplots(figsize=(10, 4))
        for record in recent:
            axis.step(
                record["daily"].index,
                record["daily"]["weight_A"],
                where="post",
                label=f"start {record['context']['start_index'] + 1}",
            )
        axis.set_title("V2-selected book: frozen Clean40 Leg A weights")
        axis.set_ylabel("Leg A weight")
        axis.set_ylim(0.05, 0.95)
        axis.legend(ncol=3, fontsize=8)
        axis.grid(alpha=0.25)
        path = output_root / "baseline_weight_recent.png"
        figure.tight_layout()
        figure.savefig(path, dpi=140)
        plt.close(figure)
        written.append(path.name)

    dynamic = aggregate[aggregate["configuration_kind"].eq("dynamic")]
    surface = dynamic[dynamic["bounds_label"].eq("10_90")]
    if not surface.empty:
        for metric, name, title in (
            ("recent_mean_sharpe", "clean40_surface_recent.png", "Recent mean Sharpe"),
            ("historical_mean_sharpe", "clean40_surface_historical.png", "Historical mean Sharpe"),
        ):
            pivot = surface.pivot_table(
                index="lookback_days", columns="step", values=metric, aggfunc="mean"
            ).sort_index()
            figure, axis = plt.subplots(figsize=(8, 5))
            image = axis.imshow(pivot.to_numpy(), aspect="auto", cmap="RdYlGn")
            axis.set_xticks(range(len(pivot.columns)), [f"{x:.2f}" for x in pivot.columns])
            axis.set_yticks(range(len(pivot.index)), [str(x) for x in pivot.index])
            axis.set_xlabel("Step")
            axis.set_ylabel("Lookback days")
            axis.set_title(f"V2-selected book: {title}, bounds 10/90")
            figure.colorbar(image, ax=axis)
            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    value = pivot.iloc[i, j]
                    if pd.notna(value):
                        axis.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=8)
            path = output_root / name
            figure.tight_layout()
            figure.savefig(path, dpi=140)
            plt.close(figure)
            written.append(path.name)
    return written


def _markdown_summary(summary: dict, baseline: pd.DataFrame, aggregate: pd.DataFrame, neighbors: pd.DataFrame, loo: pd.DataFrame) -> str:
    def f(value, digits=3):
        if value is None or pd.isna(value):
            return "n/a"
        return f"{float(value):.{digits}f}"

    def pct(value, digits=2):
        if value is None or pd.isna(value):
            return "n/a"
        return f"{float(value):.{digits}%}"

    lines = [
        "# V2 Book Clean40 Robustness Audit and Retune",
        "",
        "This experiment keeps the current V2-selected book and V2 gross-exposure",
        "sizing fixed. It audits the frozen Clean40 configuration before evaluating",
        "a predeclared lattice-aware parameter grid against a static 50/50 replay.",
        "",
        "## Research Boundary",
        "",
        f"- V2-selected Leg A: `{summary['book']['leg_a']}`",
        f"- V2-selected Leg B: `{summary['book']['leg_b']}`",
        f"- Ranking identity verified against current artifacts: **{summary['book']['matches_current_ranking']}**",
        f"- Sizing mode: **gross_exposure**; pair budget: `${PCT_PER_PAIR * INITIAL_CAPITAL:,.0f}`",
        f"- Frozen Clean40 baseline: `{BASELINE_NAME}`",
        f"- Full-matrix rerun: **False**; pair/book selection changes: **False**",
        "",
        "## Baseline Per-Start Results",
        "",
        "Metrics below are the current V2 book under V2 sizing and frozen Clean40.",
        "Recent rows are not averaged together in this table.",
        "",
        "| Window | Start | Mech | Sharpe | Ann return | Vol | MDD | Trades | Win rate | Mean gross leverage | Peak gross leverage | Allocator changes |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    base_rows = baseline[
        (baseline["configuration"].eq(BASELINE_NAME))
        & (baseline["row_type"].eq("per_start"))
    ].sort_values(["window", "start_index", "mechanism"])
    for _, row in base_rows.iterrows():
        lines.append(
            f"| {row['window']} | {int(row['start_index']) + 1} | {row['mechanism']} | "
            f"{f(row['sharpe'])} | {pct(row['annualized_return'])} | {pct(row['annualized_volatility'])} | "
            f"{pct(row['max_drawdown'])} | {int(row['trade_count'])} | {pct(row['win_rate'])} | "
            f"{f(row['mean_gross_leverage'])}x | {f(row['peak_gross_leverage'])}x | "
            f"{int(row['allocator_rebalance_count'])} |"
        )
    lines.extend(
        [
            "",
            "## Calendar and Fold Concentration",
            "",
            "Calendar PnL is attributed by the actual daily replay PnL. Period",
            "contribution is additive PnL divided by initial capital; it is not a",
            "claim that calendar periods are independent samples.",
            "",
            f"- Recent total PnL is distributed across `{summary['calendar']['recent_period_count']}` year/quarter rows; historical across `{summary['calendar']['historical_period_count']}`.",
            f"- Top recent calendar-quarter share of total PnL: `{pct(summary['calendar']['top_recent_quarter_share'])}`.",
            f"- Positive recent fold observations: `{summary['folds']['recent_positive_fold_observations']}` of `{summary['folds']['recent_fold_observations']}`; top-fold PnL share: `{pct(summary['folds']['top_recent_fold_share'])}`.",
            f"- Removing the best recent fold changes mean Sharpe from `{f(summary['folds']['full_recent_mean_sharpe'])}` to `{f(summary['folds']['leave_best_fold_mean_sharpe'])}`.",
            "",
            "The report does not assign unobserved regime labels. The observable",
            "contrast is calendar period: the current V2 book is tested on the",
            "recent 2024--2025 12-month-selection runs versus the 2015--2019",
            "historical control represented by the preserved 09b run.",
            "",
            "## Trade, Pair, and Symbol Concentration",
            "",
            f"- Recent top-trade absolute-PnL share: `{pct(summary['concentration']['top_trade_abs_share'])}`; trade HHI: `{f(summary['concentration']['trade_hhi'], 4)}`.",
            f"- Removing the best trade changes recent mean Sharpe from `{f(summary['concentration']['full_recent_mean_sharpe'])}` to `{f(summary['concentration']['remove_best_trade_recent_mean_sharpe'])}`.",
            f"- Removing the best five trades changes recent mean Sharpe to `{f(summary['concentration']['remove_best_five_recent_mean_sharpe'])}`.",
            f"- Recent top-pair absolute-PnL share: `{pct(summary['concentration']['top_pair_abs_share'])}`; worst pair: `{summary['concentration']['worst_pair']}`.",
            f"- Recent top-symbol absolute-PnL share uses an equal 50/50 attribution of each pair trade to its two symbols; it is a concentration diagnostic, not leg-level causal PnL: `{pct(summary['concentration']['top_symbol_abs_share'])}`.",
            "",
            "## Clean40 Dependence and Standalone Legs",
            "",
            f"- Frozen Clean40 mean recent Leg A weight: `{pct(summary['allocator']['recent_mean_weight_A'])}`; fraction at 50/50: `{pct(summary['allocator']['fraction_at_50_daily'])}`.",
            f"- Frozen Clean40 mean daily time at bounds: lower `{pct(summary['allocator']['fraction_at_min_daily'])}`, upper `{pct(summary['allocator']['fraction_at_max_daily'])}`; mean monthly changes: `{f(summary['allocator']['mean_monthly_changes'])}`.",
            f"- Standalone Leg A recent/historical Sharpe: `{f(summary['legs']['A']['recent_sharpe'])}` / `{f(summary['legs']['A']['historical_sharpe'])}`.",
            f"- Standalone Leg B recent/historical Sharpe: `{f(summary['legs']['B']['recent_sharpe'])}` / `{f(summary['legs']['B']['historical_sharpe'])}`.",
            f"- Daily A/B return correlation: `{f(summary['legs']['daily_correlation'])}`; rolling 63-day range: `{f(summary['legs']['rolling_corr_min'])}` to `{f(summary['legs']['rolling_corr_max'])}`.",
            f"- Static 50/50 recent/historical mean Sharpe: `{f(summary['static']['recent_mean_sharpe'])}` / `{f(summary['static']['historical_mean_sharpe'])}`.",
            "",
            "## Predeclared Search and Selection",
            "",
            f"- Lookbacks: `{', '.join(str(x) for x in LOOKBACK_CANDIDATES)}` days.",
            f"- Steps: `{', '.join(f'{x:.2f}' for x in STEP_CANDIDATES)}`.",
            "- Bounds presets: 50/50 static control, 40/60, 30/70, 20/80, 10/90.",
            f"- Lattice-aligned dynamic configurations evaluated: `{summary['search_space']['dynamic_configuration_count']}`; static control: `1`.",
            "- Primary robustness criterion: maximin floor of each mechanism's recent 20th-percentile Sharpe and historical Sharpe.",
            "- Selection tie-breaks: minimum recent median Sharpe floor, recent mean Sharpe, historical mean Sharpe, worst drawdown, then lower allocator turnover.",
            f"- Plateau definition: within `{PLATEAU_SHARPE_TOLERANCE:.2f}` Sharpe of the best robust floor.",
            "",
            "| Configuration | Robust floor | Recent mean Sharpe | Historical mean Sharpe | Worst MDD | Annualized allocator turnover | Plateau |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    top_configs = aggregate.sort_values(
        ["configuration_kind", "robust_median_floor", "robust_floor"],
        ascending=[True, False, False],
    ).head(10)
    for _, row in top_configs.iterrows():
        lines.append(
            f"| `{row['configuration']}` | {f(row['robust_floor'])} | {f(row['recent_mean_sharpe'])} | "
            f"{f(row['historical_mean_sharpe'])} | {pct(row['worst_max_drawdown'])} | "
            f"{pct(row['mean_annualized_turnover_ratio'])} | {bool(row.get('plateau_member', False))} |"
        )
    lines.extend(
        [
            "",
            "## Neighbor and Leave-One-Start-Out Checks",
            "",
            f"- Best dynamic configuration under the predeclared rule: `{summary['selection']['best_dynamic_configuration']}`.",
            f"- Dynamic plateau size: `{summary['selection']['dynamic_plateau_count']}` configurations.",
            f"- Neighbor rows inspected: `{len(neighbors)}`.",
            f"- Leave-one-start-out selected regions: `{summary['selection']['leave_one_start_out_regions']}`.",
            "",
            "| Neighbor | Relation | Robust floor | Recent mean Sharpe | Historical mean Sharpe |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for _, row in neighbors.sort_values("configuration").iterrows():
        lines.append(
            f"| `{row['configuration']}` | {row['neighbor_relation']} | {f(row['robust_floor'])} | "
            f"{f(row['recent_mean_sharpe'])} | {f(row['historical_mean_sharpe'])} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Final research decision: **{summary['decision']['outcome']}**.",
            f"- Candidate dynamic configuration: `{summary['selection']['best_dynamic_configuration']}`.",
            f"- Existing frozen Clean40 robust floor: `{f(summary['decision']['old_robust_floor'])}`.",
            f"- Candidate dynamic robust floor: `{f(summary['decision']['dynamic_robust_floor'])}`.",
            f"- Static 50/50 robust floor: `{f(summary['decision']['static_robust_floor'])}`.",
            "",
            "The decision is intentionally not based on the highest recent Sharpe.",
            "The V2 book and V2 sizing remain fixed. A dynamic candidate is only",
            "preferred when it clears the predeclared robustness margin and lives in",
            "a plateau; otherwise the existing allocator or static 50/50 remains the",
            "more defensible live-research control.",
            "",
            "## Turnover and Live Readiness",
            "",
            f"- Cost sensitivity uses allocator-only one-way capital movement at `{', '.join(str(x) for x in COST_BPS)}` bps; pair entry/exit costs are not modeled.",
            "- Already modeled: preserved trade events, walk-forward fold boundaries, integer-share V2 sizing, V2 gross budgets, entry/exit dates, and native marked exposure.",
            "- Simplified but acceptable for current research: shared-account bookkeeping, no forced rebalancing of open trades, and replay-level monthly allocator timing.",
            "- Must be addressed in paper trading: commissions, spread/slippage, borrow availability/cost, partial fills, simultaneous two-leg execution, symbol overlap, and deployable-capital policy.",
            "- Must be addressed before live capital: broker margin/maintenance rules, borrow and locate constraints, corporate-action/dividend treatment, stale/missing price handling, operational reconciliation, and hard gross/single-symbol/pair exposure limits.",
            "",
            "## What This Does Not Establish",
            "",
            "- It does not create an independent portfolio holdout; the displayed recent and historical windows already informed prior book selection.",
            "- It does not prove factor-neutral alpha or live profitability; prior diagnostics found short-term-reversal exposure and insignificant alpha.",
            "- It does not validate broker execution, borrow, costs, or capacity.",
            "- It does not justify changing pair selection, pair parameters, V2 sizing, or the locked canonical configuration.",
            "",
            "## Falsifiers",
            "",
            "- A future paper-trading period with materially negative or unstable returns after realistic costs.",
            "- Repeated concentration in one pair, symbol, fold, or allocator flip that fails to reproduce out of sample.",
            "- Native exposure or trade-identity reconciliation failure.",
            "- A live-capital policy that cannot support the observed gross, margin, borrow, or partial-fill requirements.",
            "",
            "## Artifacts",
            "",
        ]
    )
    for name in summary["artifacts"]:
        lines.append(f"- `{name}`")
    return "\n".join(lines) + "\n"


def run() -> dict:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    books, selection_evidence = _resolve_books()
    book = books["v2_selected"]
    if not selection_evidence["current_v2_book"]["matches_handoff"]:
        raise ValueError("current V2 book no longer matches the expected handoff")
    protected_before = {
        "public_score": _hash_file(ROOT / "results/final/rankings/clean40_pair_scores.csv"),
        "canonical_rankings": _hash_file(ROOT / "results/final/rankings/clean40_pair_rankings.csv"),
        "selected_config": _hash_file(ROOT / "research/selected_book_config.json"),
    }

    contexts = []
    for window in WINDOWS:
        count = RECENT_START_COUNT if window == "recent" else 1
        for start_index in range(count):
            contexts.append(_load_context(book, window, start_index))

    configurations_by_name = {config["name"]: config for config in CONFIGURATIONS}
    baseline_config = configurations_by_name[BASELINE_NAME]
    static_config = configurations_by_name["static_50_50"]
    baseline_records = {}
    static_records = {}
    baseline_rows = []
    period_rows = []
    fold_rows = []
    fold_leaveout_rows = []
    trade_concentration_rows = []
    trade_detail_rows = []
    pair_concentration_rows = []
    symbol_concentration_rows = []
    leg_rows = []
    grid_rows = []
    grid_reconciliation = []
    grid_trade_sets = {}
    validation_native = []
    snapshot_differences = []

    for context in contexts:
        validation_native.extend(context["native_checks"])
        snapshot_differences.extend(context["price_differences"])
        for mechanism in MECHANISMS:
            dynamic = _trace_record(context, baseline_config, mechanism)
            static = _trace_record(context, static_config, mechanism)
            key = (context["window"], context["start_index"], mechanism)
            baseline_records[key] = dynamic
            static_records[key] = static
            baseline_rows.append(_metric_output_row(dynamic))
            period_rows.extend(_period_rows(dynamic))
            current_fold_rows = _fold_rows(dynamic)
            fold_rows.extend(current_fold_rows)
            fold_leaveout_rows.extend(_fold_leave_one_out(dynamic, current_fold_rows))
            concentration, details, pairs, symbols = _concentration_rows(dynamic)
            trade_concentration_rows.append(concentration)
            trade_detail_rows.extend(details)
            pair_concentration_rows.extend(pairs)
            symbol_concentration_rows.extend(symbols)
            leg_rows.extend(_baseline_leg_rows(context, dynamic, static))
            for record in (dynamic, static):
                row = _metric_output_row(record)
                grid_rows.append(row)
                grid_reconciliation.append(record["reconciliation"])
                grid_trade_sets[
                    (record["configuration"]["name"], context["window"], context["start_index"], mechanism)
                ] = record["accepted_keys"]

    for configuration in CONFIGURATIONS:
        if configuration["name"] in {BASELINE_NAME, "static_50_50"}:
            continue
        for context in contexts:
            for mechanism in MECHANISMS:
                record = _trace_record(context, configuration, mechanism, include_detail=False)
                grid_rows.append(_metric_output_row(record))
                grid_reconciliation.append(record["reconciliation"])
                grid_trade_sets[
                    (configuration["name"], context["window"], context["start_index"], mechanism)
                ] = record["accepted_keys"]

    baseline_frame = pd.DataFrame(baseline_rows)
    grid_frame = pd.DataFrame(grid_rows)
    mechanism_aggregate, aggregate = _aggregate_metric_rows(grid_frame)
    selected_dynamic, aggregate_with_selection = _select_dynamic(aggregate)
    aggregate = aggregate_with_selection
    neighbors = _neighbor_rows(aggregate, selected_dynamic)
    historical_grid = grid_frame[grid_frame["window"].eq("historical")]
    loo = _leave_one_start_out(grid_frame, historical_grid)
    costs = _cost_rows(grid_frame)

    old_aggregate = aggregate[aggregate["configuration"].eq(BASELINE_NAME)].iloc[0]
    static_aggregate = aggregate[aggregate["configuration"].eq("static_50_50")].iloc[0]
    dynamic_floor = float(selected_dynamic["robust_floor"])
    old_floor = float(old_aggregate["robust_floor"])
    static_floor = float(static_aggregate["robust_floor"])
    if (
        dynamic_floor >= old_floor + MATERIAL_SHARPE_MARGIN
        and dynamic_floor >= static_floor + MATERIAL_SHARPE_MARGIN
        and int(selected_dynamic["plateau_count"]) >= 2
    ):
        outcome = "freeze_dynamic_candidate"
        final_config = selected_dynamic["configuration"]
    elif static_floor >= old_floor + MATERIAL_SHARPE_MARGIN:
        outcome = "freeze_static_50_50"
        final_config = "static_50_50"
    else:
        outcome = "keep_old_clean40"
        final_config = BASELINE_NAME

    recent_baseline = baseline_frame[
        (baseline_frame["configuration"].eq(BASELINE_NAME))
        & (baseline_frame["window"].eq("recent"))
    ]
    historical_baseline = baseline_frame[
        (baseline_frame["configuration"].eq(BASELINE_NAME))
        & (baseline_frame["window"].eq("historical"))
    ]
    recent_periods = pd.DataFrame(period_rows)
    recent_periods = recent_periods[recent_periods["window"].eq("recent")]
    recent_folds = pd.DataFrame(fold_rows)
    recent_folds = recent_folds[recent_folds["window"].eq("recent")]
    recent_concentration = pd.DataFrame(trade_concentration_rows)
    recent_concentration = recent_concentration[recent_concentration["window"].eq("recent")]
    recent_symbol = pd.DataFrame(symbol_concentration_rows)
    recent_symbol = recent_symbol[recent_symbol["window"].eq("recent")]
    recent_trade_details = pd.DataFrame(trade_detail_rows)
    recent_trade_details = recent_trade_details[recent_trade_details["window"].eq("recent")]

    total_recent_pnl = float(recent_baseline["total_pnl"].mean())
    top_quarter = (
        recent_periods[recent_periods["period_type"].eq("quarter")]
        .groupby("period", as_index=False)["pnl"].mean()
    )
    top_quarter_share = float(
        top_quarter["pnl"].abs().max() / recent_baseline["total_pnl"].abs().mean()
    ) if len(top_quarter) and abs(recent_baseline["total_pnl"].abs().mean()) > EPSILON else float("nan")
    positive_folds = int((recent_folds["pnl"] > 0).sum()) if len(recent_folds) else 0
    fold_group_keys = ["window", "start_index", "mechanism"]
    top_fold_share = float(
        recent_folds.groupby(fold_group_keys)["share_of_total_pnl"]
        .apply(lambda values: values.abs().max())
        .mean()
    ) if len(recent_folds) else float("nan")
    full_recent_mean_sharpe = float(recent_baseline["sharpe"].mean())
    leave_best = pd.DataFrame(fold_leaveout_rows)
    if len(leave_best):
        leave_best = leave_best[leave_best["window"].eq("recent")]
        best_indices = leave_best.groupby(fold_group_keys)["removed_fold_pnl"].idxmax()
        leave_best = leave_best.loc[best_indices]
    leave_best_mean_sharpe = float(leave_best["leave_one_fold_out_sharpe"].mean()) if len(leave_best) else float("nan")
    top_trade_abs_share = float(recent_concentration["top_1_trade_abs_share"].mean())
    top_pair_abs_share = float(
        recent_trade_details.groupby(["window", "start_index", "mechanism", "pair"], as_index=False)["pnl"].sum()
        .assign(abs_pnl=lambda frame: frame["pnl"].abs())
        .groupby(["window", "start_index", "mechanism"])["abs_pnl"].apply(lambda values: values.max() / values.sum()).mean()
    ) if len(recent_trade_details) else float("nan")
    top_symbol_abs_share = float(
        recent_symbol.groupby(["window", "start_index", "mechanism"])["abs_pnl_share"].max().mean()
    ) if len(recent_symbol) else float("nan")
    selected_loo_regions = int(loo["selected_configuration"].nunique()) if len(loo) else 0
    base_allocator = baseline_frame[baseline_frame["configuration"].eq(BASELINE_NAME)]
    base_recent = base_allocator[base_allocator["window"].eq("recent")]

    protected_after = {
        "public_score": _hash_file(ROOT / "results/final/rankings/clean40_pair_scores.csv"),
        "canonical_rankings": _hash_file(ROOT / "results/final/rankings/clean40_pair_rankings.csv"),
        "selected_config": _hash_file(ROOT / "research/selected_book_config.json"),
    }
    baseline_existing = pd.read_csv(
        ROOT / "results/v1_v2_selected_book_crosscheck/selected_book_crosscheck_per_run.csv"
    )
    reproduction_differences = []
    for _, row in baseline_frame[baseline_frame["configuration"].eq(BASELINE_NAME)].iterrows():
        expected = baseline_existing[
            baseline_existing["selected_book_origin"].eq("v2_selected")
            & baseline_existing["window"].eq(row["window"])
            & baseline_existing["start_index"].eq(row["start_index"])
            & baseline_existing["mechanism"].eq(row["mechanism"])
            & baseline_existing["sizing_mode"].eq("v2")
            & baseline_existing["exposure_mode"].eq("actual")
        ]
        if len(expected) != 1:
            raise ValueError(f"missing prior baseline row for {row['window']}/{row['start_index']}/{row['mechanism']}")
        expected = expected.iloc[0]
        for metric in (
            "cumulative_return",
            "annualized_return",
            "annualized_volatility",
            "sharpe",
            "max_drawdown",
            "final_equity",
        ):
            actual = row[metric]
            prior = expected[metric]
            reproduction_differences.append(abs(float(actual) - float(prior)))

    baseline_trade_sets = {
        (row["window"], int(row["start_index"]), row["mechanism"]): set(
            grid_trade_sets[(BASELINE_NAME, row["window"], int(row["start_index"]), row["mechanism"])]
        )
        for _, row in baseline_frame[baseline_frame["configuration"].eq(BASELINE_NAME)].iterrows()
    }
    trade_identity_differences = 0
    for key, baseline_keys in baseline_trade_sets.items():
        for configuration in CONFIGURATIONS:
            candidate_keys = grid_trade_sets[(configuration["name"], *key)]
            if candidate_keys != baseline_keys:
                trade_identity_differences += 1

    validation = {
        "v2_book_identity": bool(selection_evidence["current_v2_book"]["matches_handoff"]),
        "v2_native_exposure_status": "pass"
        if all(row["status"] == "pass" for row in validation_native)
        else "fail",
        "v2_gross_budget_status": "pass"
        if all(
            bool(trade["raw"].get("pair_gross_budget_enforced", False))
            and _num(trade["raw"].get("gross_entry_exposure"))
            <= _num(trade["raw"].get("pair_gross_budget"), 250000.0) + EXPOSURE_TOLERANCE
            for context in contexts
            for leg in ("A", "B")
            for trade in context["runs"][("v2", leg)]["trades"]
        )
        else "fail",
        "baseline_reproduction_status": "pass"
        if max(reproduction_differences, default=0.0) <= 1e-7
        else "fail",
        "baseline_max_metric_difference": max(reproduction_differences, default=0.0),
        "trade_identity_across_allocator_status": "pass"
        if trade_identity_differences == 0
        else "fail",
        "trade_identity_difference_count": trade_identity_differences,
        "pnl_equity_reconciliation_status": "pass"
        if max(
            [abs(_num(row.get("equity_pnl_difference"))) for row in grid_reconciliation]
            + [abs(_num(row.get("leg_pnl_difference"))) for row in grid_reconciliation]
            + [0.0]
        )
        <= 1e-6
        else "fail",
        "max_snapshot_difference": max(snapshot_differences, default=0.0),
        "protected_hashes_unchanged": protected_before == protected_after,
        "full_matrix_rerun": False,
        "canonical_outputs_written": False,
    }
    validation["overall_status"] = "pass" if all(
        value in ("pass", True)
        for key, value in validation.items()
        if key.endswith("_status") or key.endswith("_identity") or key == "protected_hashes_unchanged"
    ) else "fail"

    leg_frame = pd.DataFrame(leg_rows)
    standalone_a = leg_frame[leg_frame["source"].eq("standalone_v2_leg") & leg_frame["leg"].eq("A")]
    standalone_b = leg_frame[leg_frame["source"].eq("standalone_v2_leg") & leg_frame["leg"].eq("B")]
    correlation = leg_frame[leg_frame["source"].eq("leg_correlation")]
    static_agg = aggregate[aggregate["configuration"].eq("static_50_50")].iloc[0]
    summary = {
        "status": validation["overall_status"],
        "branch": "sizing-v2-gross-exposure",
        "book": {
            "leg_a": "/".join(book["leg_a"]),
            "leg_b": "/".join(book["leg_b"]),
            "matches_current_ranking": selection_evidence["current_v2_book"]["matches_handoff"],
            "selection_evidence": selection_evidence,
        },
        "baseline_parameters": {
            "lookback_days": CURRENT_LOOKBACK,
            "step": CURRENT_STEP,
            "weight_min": CURRENT_WMIN,
            "weight_max": CURRENT_WMAX,
            "initial_weight_leg_a": INITIAL_WEIGHT_A,
            "sizing_mode": "gross_exposure",
            "pct_per_pair": PCT_PER_PAIR,
            "initial_capital": INITIAL_CAPITAL,
        },
        "search_space": {
            "lookback_days": LOOKBACK_CANDIDATES,
            "steps": STEP_CANDIDATES,
            "bounds": [label for _, _, label in BOUND_CANDIDATES],
            "lattice_rule": "bounds must be reachable from 0.50 by integer step moves",
            "dynamic_configuration_count": int(sum(config["kind"] == "dynamic" for config in CONFIGURATIONS)),
            "static_configuration_count": 1,
        },
        "selection_rule": {
            "primary": "maximin of recent 20th-percentile Sharpe and historical Sharpe across mechanisms",
            "plateau_tolerance": PLATEAU_SHARPE_TOLERANCE,
            "material_sharpe_margin": MATERIAL_SHARPE_MARGIN,
            "tie_breaks": [
                "recent median Sharpe floor",
                "recent mean Sharpe",
                "historical mean Sharpe",
                "worst drawdown",
                "lower allocator turnover",
            ],
        },
        "selection": {
            "best_dynamic_configuration": selected_dynamic["configuration"],
            "dynamic_plateau_count": int(selected_dynamic["plateau_count"]),
            "leave_one_start_out_regions": selected_loo_regions,
        },
        "decision": {
            "outcome": outcome,
            "final_configuration": final_config,
            "old_robust_floor": old_floor,
            "dynamic_robust_floor": dynamic_floor,
            "static_robust_floor": static_floor,
            "reason": "predeclared robustness margin and plateau rule; not maximum recent Sharpe",
        },
        "baseline": {
            "recent_mean_sharpe": full_recent_mean_sharpe,
            "historical_mean_sharpe": float(historical_baseline["sharpe"].mean()),
            "recent_mean_cumulative_return": float(recent_baseline["cumulative_return"].mean()),
            "historical_mean_cumulative_return": float(historical_baseline["cumulative_return"].mean()),
        },
        "static": {
            "recent_mean_sharpe": float(static_agg["recent_mean_sharpe"]),
            "historical_mean_sharpe": float(static_agg["historical_mean_sharpe"]),
            "recent_mean_cumulative_return": float(static_agg["recent_mean_cumulative_return"]),
            "historical_mean_cumulative_return": float(static_agg["historical_mean_cumulative_return"]),
        },
        "calendar": {
            "recent_period_count": int(len(recent_periods)),
            "historical_period_count": int(len(pd.DataFrame(period_rows)[pd.DataFrame(period_rows)["window"].eq("historical")])) if period_rows else 0,
            "top_recent_quarter_share": top_quarter_share,
        },
        "folds": {
            "recent_positive_fold_observations": positive_folds,
            "recent_fold_observations": int(len(recent_folds)),
            "recent_fold_id_count": int(len(recent_folds["fold_id"].unique()))
            if len(recent_folds)
            else 0,
            "top_recent_fold_share": top_fold_share,
            "full_recent_mean_sharpe": full_recent_mean_sharpe,
            "leave_best_fold_mean_sharpe": leave_best_mean_sharpe,
        },
        "concentration": {
            "top_trade_abs_share": top_trade_abs_share,
            "trade_hhi": float(recent_concentration["absolute_trade_pnl_hhi"].mean()),
            "full_recent_mean_sharpe": full_recent_mean_sharpe,
            "remove_best_trade_recent_mean_sharpe": float(
                recent_concentration["remove_best_1_trade_sharpe"].mean()
            ),
            "remove_best_five_recent_mean_sharpe": float(
                recent_concentration["remove_best_5_trade_sharpe"].mean()
            ),
            "top_pair_abs_share": top_pair_abs_share,
            "top_symbol_abs_share": top_symbol_abs_share,
            "worst_pair": recent_concentration.sort_values("worst_pair_pnl").iloc[0]["worst_pair"]
            if len(recent_concentration)
            else None,
        },
        "allocator": {
            "recent_mean_weight_A": float(base_recent["mean_gross_leverage"].mean())
            if False
            else float(
                np.mean(
                    [
                        record["daily"]["weight_A"].mean()
                        for record in baseline_records.values()
                        if record["context"]["window"] == "recent"
                    ]
                )
            ),
            "fraction_at_50_daily": float(
                np.mean(
                    [
                        record["metric"]["allocator_fraction_at_50_daily"]
                        for record in baseline_records.values()
                        if record["context"]["window"] == "recent"
                    ]
                )
            ),
            "fraction_at_min_daily": float(
                np.mean(
                    [
                        record["metric"]["allocator_fraction_at_min_daily"]
                        for record in baseline_records.values()
                        if record["context"]["window"] == "recent"
                    ]
                )
            ),
            "fraction_at_max_daily": float(
                np.mean(
                    [
                        record["metric"]["allocator_fraction_at_max_daily"]
                        for record in baseline_records.values()
                        if record["context"]["window"] == "recent"
                    ]
                )
            ),
            "mean_monthly_changes": float(
                np.mean(
                    [
                        record["metric"]["allocator_rebalance_count"]
                        for record in baseline_records.values()
                        if record["context"]["window"] == "recent"
                    ]
                )
            ),
        },
        "legs": {
            "A": {
                "recent_sharpe": float(standalone_a[standalone_a["window"].eq("recent")]["sharpe"].mean()),
                "historical_sharpe": float(standalone_a[standalone_a["window"].eq("historical")]["sharpe"].mean()),
            },
            "B": {
                "recent_sharpe": float(standalone_b[standalone_b["window"].eq("recent")]["sharpe"].mean()),
                "historical_sharpe": float(standalone_b[standalone_b["window"].eq("historical")]["sharpe"].mean()),
            },
            "daily_correlation": float(correlation["daily_correlation"].mean()),
            "rolling_corr_min": float(correlation["rolling_63d_correlation_min"].min()),
            "rolling_corr_max": float(correlation["rolling_63d_correlation_max"].max()),
        },
        "execution_realism": {
            "already_modeled": [
                "preserved walk-forward trade events and fold boundaries",
                "integer-share V2 gross-exposure sizing and entry budget invariant",
                "entry/exit dates, stop/signal/max-holding trade events",
                "native marked exposure reconciliation",
            ],
            "simplified_current_research": [
                "no commissions, spread, slippage, borrow costs, or financing",
                "margin_behavior=off in the preserved runs",
                "shared-account replay is accounting, not broker cash/settlement simulation",
                "no partial-fill or leg-asynchrony model",
                "static-universe and corporate-action/survivorship limitations remain",
            ],
            "paper_trading_required": [
                "realistic cost and slippage ledger",
                "borrow/locate and short-sale availability",
                "partial-fill and two-leg execution reconciliation",
                "deployable-capital, margin, and gross/symbol/pair limits",
            ],
            "live_capital_required": [
                "broker-specific margin and maintenance policy",
                "corporate actions/dividends and stale-price controls",
                "operational monitoring, reconciliation, and liquidation policy",
            ],
        },
        "validation": validation,
        "counts": {
            "contexts": len(contexts),
            "baseline_rows": len(baseline_frame),
            "grid_rows": len(grid_frame),
            "aggregate_rows": len(aggregate),
            "period_rows": len(period_rows),
            "fold_rows": len(fold_rows),
            "trade_detail_rows": len(trade_detail_rows),
            "neighbor_rows": len(neighbors),
            "leave_one_start_out_rows": len(loo),
        },
        "artifacts": [
            "baseline_per_start.csv",
            "baseline_daily.csv",
            "baseline_period_attribution.csv",
            "baseline_fold_attribution.csv",
            "baseline_fold_leave_one_out.csv",
            "baseline_trade_concentration.csv",
            "baseline_trade_contributions.csv",
            "baseline_pair_concentration.csv",
            "baseline_symbol_concentration.csv",
            "baseline_leg_diagnostics.csv",
            "clean40_grid_results.csv",
            "clean40_mechanism_aggregate.csv",
            "clean40_aggregate_rankings.csv",
            "clean40_neighbor_sensitivity.csv",
            "clean40_leave_one_start_out.csv",
            "clean40_static_50_50_comparison.csv",
            "clean40_turnover_analysis.csv",
            "clean40_cost_sensitivity.csv",
            "clean40_summary.json",
            "clean40_summary.md",
        ],
    }

    baseline_daily_rows = []
    static_comparison_rows = []
    for key, record in baseline_records.items():
        for date, row in record["daily"].iterrows():
            item = {
                "configuration": BASELINE_NAME,
                "window": key[0],
                "start_index": key[1],
                "mechanism": key[2],
                "date": _iso(date),
            }
            item.update({column: _num(value, value) for column, value in row.to_dict().items()})
            baseline_daily_rows.append(item)
        static = static_records[key]
        static_comparison_rows.append(
            {
                "window": key[0],
                "start_index": key[1],
                "mechanism": key[2],
                "dynamic_configuration": BASELINE_NAME,
                "static_configuration": "static_50_50",
                "dynamic_sharpe": record["metric"]["sharpe"],
                "static_sharpe": static["metric"]["sharpe"],
                "dynamic_cumulative_return": record["metric"]["cumulative_return"],
                "static_cumulative_return": static["metric"]["cumulative_return"],
                "dynamic_max_drawdown": record["metric"]["max_drawdown"],
                "static_max_drawdown": static["metric"]["max_drawdown"],
                "dynamic_trade_count": record["metric"]["trade_count"],
                "static_trade_count": static["metric"]["trade_count"],
                "dynamic_annualized_turnover_ratio": record["metric"]["allocator_annualized_turnover_ratio"],
                "static_annualized_turnover_ratio": static["metric"]["allocator_annualized_turnover_ratio"],
            }
        )

    outputs = {
        "baseline_per_start.csv": baseline_frame,
        "baseline_daily.csv": pd.DataFrame(baseline_daily_rows),
        "baseline_period_attribution.csv": pd.DataFrame(period_rows),
        "baseline_fold_attribution.csv": pd.DataFrame(fold_rows),
        "baseline_fold_leave_one_out.csv": pd.DataFrame(fold_leaveout_rows),
        "baseline_trade_concentration.csv": pd.DataFrame(trade_concentration_rows),
        "baseline_trade_contributions.csv": pd.DataFrame(trade_detail_rows),
        "baseline_pair_concentration.csv": pd.DataFrame(pair_concentration_rows),
        "baseline_symbol_concentration.csv": pd.DataFrame(symbol_concentration_rows),
        "baseline_leg_diagnostics.csv": leg_frame,
        "clean40_grid_results.csv": grid_frame,
        "clean40_mechanism_aggregate.csv": mechanism_aggregate,
        "clean40_aggregate_rankings.csv": aggregate,
        "clean40_neighbor_sensitivity.csv": neighbors,
        "clean40_leave_one_start_out.csv": loo,
        "clean40_static_50_50_comparison.csv": pd.DataFrame(static_comparison_rows),
        "clean40_turnover_analysis.csv": grid_frame[
            [
                "configuration",
                "configuration_kind",
                "window",
                "start_index",
                "mechanism",
                "allocator_rebalance_count",
                "allocator_abs_weight_turnover",
                "allocator_mean_abs_weight_change",
                "allocator_max_abs_weight_change",
                "allocator_one_way_capital_movement",
                "allocator_annualized_capital_movement",
                "allocator_annualized_turnover_ratio",
                "allocator_fraction_at_min_daily",
                "allocator_fraction_at_max_daily",
                "allocator_fraction_at_50_daily",
            ]
        ],
        "clean40_cost_sensitivity.csv": costs,
    }
    for filename, frame in outputs.items():
        frame.to_csv(OUTPUT_ROOT / filename, index=False)
    (OUTPUT_ROOT / "clean40_summary.json").write_text(
        json.dumps(_json_safe(summary), indent=2, sort_keys=True), encoding="utf-8"
    )
    plots = _write_plots(baseline_records, aggregate, OUTPUT_ROOT)
    summary["artifacts"].extend(plots)
    (OUTPUT_ROOT / "clean40_summary.json").write_text(
        json.dumps(_json_safe(summary), indent=2, sort_keys=True), encoding="utf-8"
    )
    (OUTPUT_ROOT / "clean40_summary.md").write_text(
        _markdown_summary(summary, baseline_frame, aggregate, neighbors, loo),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    summary = run()
    print(f"Validation: {summary['status']}")
    print(f"Decision: {summary['decision']['outcome']}")
    print(f"Candidate: {summary['selection']['best_dynamic_configuration']}")
    print(f"Wrote {OUTPUT_ROOT}")
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
