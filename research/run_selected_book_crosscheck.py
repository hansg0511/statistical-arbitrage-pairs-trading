"""Cross-check V1/V2 sizing on the books selected by each convention.

This is a focused replay of two selected books, not a strategy or book-matrix
rerun. The raw V1/V2 runs, trade marks, sizing audits, and archived snapshots
are read from the preserved full-matrix output tree. The existing old-winner
replay and marked-exposure helpers are reused so the selection-interaction
comparison has the same account, allocator, and exposure semantics.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from collections import defaultdict, deque
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
)
from research.run_gross_exposure_autopsy import (  # noqa: E402
    _account_path,
    _audit_sides,
    _gross,
    _load_metrics,
    _load_snapshots,
    _native_metadata,
    _num,
    _position_exposure,
    _scale_pnl,
    _series_metrics,
    _timestamp,
    _trace_map,
    _validate_native_v2_exposure,
)
from research.run_old_winner_v1_v2_autopsy import (  # noqa: E402
    V1_ROOT,
    V2_ROOT,
    _match_trades,
    _read_sizing_audit,
    _read_trade_log,
    _trade_key,
    allocator_path,
    simulate_trace,
)
from research.run_sizing_v2_full_matrix import STRATEGIES  # noqa: E402


OUTPUT_ROOT = ROOT / "results" / "v1_v2_selected_book_crosscheck"
PER_RUN_PATH = OUTPUT_ROOT / "selected_book_crosscheck_per_run.csv"
DAILY_PATH = OUTPUT_ROOT / "selected_book_crosscheck_daily.csv"
SUMMARY_PATH = OUTPUT_ROOT / "selected_book_crosscheck_summary.csv"
SUMMARY_JSON_PATH = OUTPUT_ROOT / "selected_book_crosscheck_summary.json"
SUMMARY_MD_PATH = OUTPUT_ROOT / "selected_book_crosscheck_summary.md"
ATTRIBUTION_PATH = OUTPUT_ROOT / "allocator_path_attribution.csv"
FORCED_PATH = OUTPUT_ROOT / "allocator_path_counterfactuals.csv"

RANKING_ROOT = ROOT / "results" / "sizing_v2_full_summary"
V1_RANKING_PATH = RANKING_ROOT / "combined_v1_rankings.csv"
V2_RANKING_PATH = RANKING_ROOT / "combined_v2_rankings.csv"
V1_SCORE_PATH = RANKING_ROOT / "combined_v1_scores.csv"
V2_SCORE_PATH = RANKING_ROOT / "combined_v2_scores.csv"
SELECTED_CONFIG_PATH = ROOT / "research" / "selected_book_config.json"

OLD_AUTOPSY_ROOT = ROOT / "results" / "old_winner_v1_v2_autopsy"
OLD_DAILY_PATH = OLD_AUTOPSY_ROOT / "daily_contributions_recent.csv"
OLD_COMBINED_PATH = OLD_AUTOPSY_ROOT / "combined_return_series.csv"
OLD_ALLOCATOR_PATH = OLD_AUTOPSY_ROOT / "allocator_path.csv"
PUBLIC_SCORE_PATH = ROOT / "results" / "final" / "rankings" / "clean40_pair_scores.csv"
CANONICAL_RANKINGS_PATH = ROOT / "results" / "final" / "rankings" / "clean40_pair_rankings.csv"

INITIAL_CAPITAL = 1_000_000.0
PCT_PER_PAIR = 0.25
MAX_PAIRS = 20
EPSILON = 1e-9
EXPOSURE_TOLERANCE = 1e-6
METRIC_COLUMNS = (
    "cumulative_return",
    "annualized_return",
    "annualized_volatility",
    "sharpe",
    "max_drawdown",
    "final_equity",
)
START_WINDOWS = ("recent", "historical")
MECHANISMS = ("A", "B")

HANDOFF_V2_BOOK = frozenset(
    (
        "sp500-12m/same_sector_slide1m_noscreen",
        "sp500-12m/same_sector_slide3m_noscreen",
    )
)


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_hash(path: Path) -> dict[str, str]:
    if not path.is_dir():
        return {}
    return {
        str(file.relative_to(ROOT)): _sha256(file)
        for file in sorted(path.rglob("*"))
        if file.is_file()
    }


def _git_value(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _iso(value) -> str:
    return pd.Timestamp(value).date().isoformat()


def _path_name(strategy: str, config: str) -> str:
    return f"{strategy}/{config}"


def _split_path(value: str) -> tuple[str, str]:
    strategy, config = str(value).split("/", 1)
    return strategy, config


def _pair_key(left: str, right: str) -> frozenset[str]:
    return frozenset((str(left), str(right)))


def _run_path(root: Path, leg: tuple[str, str], window: str, start_index: int) -> Path:
    strategy, config = leg
    spec = STRATEGIES[strategy]
    if window == "recent":
        starts = spec["recent_starts"]
        start = starts[start_index]
        section = spec["recent_section"]
    elif window == "historical":
        if start_index != 0:
            raise ValueError("historical has only start_index=0")
        start = spec["historical_start"]
        section = spec["historical_section"]
    else:
        raise ValueError(f"unknown window: {window}")
    return root / section / f"{start}_{config}"


def _load_generic_run(path: Path) -> dict:
    """Load a preserved run with the same metadata shape as the old autopsy."""
    if not path.is_dir():
        raise FileNotFoundError(f"missing preserved run: {path}")
    trades, folds = build_trades(path)
    raw = _read_trade_log(path)
    by_key: dict[tuple, deque] = defaultdict(deque)
    for _, row in raw.iterrows():
        by_key[_trade_key(row)].append(row.to_dict())
    attached = []
    for trade in trades:
        key = _trade_key(trade)
        if not by_key[key]:
            raise RuntimeError(f"trade-log metadata missing for {key} in {path}")
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


def _resolve_books() -> tuple[dict, dict]:
    with SELECTED_CONFIG_PATH.open(encoding="utf-8") as handle:
        selected_config = json.load(handle)
    if selected_config.get("status") != "locked":
        raise ValueError("selected book configuration is not locked")

    old_a = selected_config["pair"]["leg_a"]["path"]
    old_b = selected_config["pair"]["leg_b"]["path"]
    v1_rankings = pd.read_csv(V1_RANKING_PATH)
    v2_rankings = pd.read_csv(V2_RANKING_PATH)
    old_evidence = {}
    for mechanism in MECHANISMS:
        rows = v1_rankings[
            v1_rankings["mechanism"].eq(mechanism)
            & v1_rankings["A"].eq(old_a)
            & v1_rankings["B"].eq(old_b)
        ]
        if len(rows) != 1:
            raise ValueError(f"locked V1 book missing from {mechanism} rankings")
        row = rows.iloc[0]
        if not all(int(row[column]) == 1 for column in ("score_rank", "rank_avg_rank", "joined_rank")):
            raise ValueError(f"locked V1 book is no longer consensus rank one for {mechanism}")
        old_evidence[mechanism] = {
            column: row[column]
            for column in ("score_rank", "rank_avg_rank", "joined_rank", "recent_sh", "hist_sh")
        }

    v2_evidence = {}
    v2_pair_keys = set()
    v2_rows = {}
    for mechanism in MECHANISMS:
        candidates = v2_rankings[
            v2_rankings["mechanism"].eq(mechanism)
            & v2_rankings["rank_avg_rank"].eq(1)
        ].sort_values(["joined_rank", "score_rank", "A", "B"])
        if candidates.empty:
            raise ValueError(f"no current V2 rank-average leader for {mechanism}")
        row = candidates.iloc[0]
        v2_pair_keys.add(_pair_key(row["A"], row["B"]))
        v2_rows[mechanism] = row
        v2_evidence[mechanism] = {
            column: row[column]
            for column in ("score_rank", "rank_avg_rank", "joined_rank", "recent_sh", "hist_sh")
        }
    if len(v2_pair_keys) != 1:
        raise ValueError("current V2 rank-average leader differs by mechanism")
    v2_row = v2_rows["A"]
    v2_a = str(v2_row["A"])
    v2_b = str(v2_row["B"])

    books = {
        "v1_selected": {
            "selected_book_origin": "v1_selected",
            "selected_book": "old_v1_winner",
            "leg_a": _split_path(old_a),
            "leg_b": _split_path(old_b),
            "selection_evidence": old_evidence,
        },
        "v2_selected": {
            "selected_book_origin": "v2_selected",
            "selected_book": "current_v2_rank_average_leader",
            "leg_a": _split_path(v2_a),
            "leg_b": _split_path(v2_b),
            "selection_evidence": v2_evidence,
        },
    }
    evidence = {
        "locked_v1_book": {
            "leg_a": old_a,
            "leg_b": old_b,
            "matches_locked_config": True,
        },
        "current_v2_book": {
            "leg_a": v2_a,
            "leg_b": v2_b,
            "matches_handoff": _pair_key(v2_a, v2_b) == HANDOFF_V2_BOOK,
            "selection_basis": "rank_avg_rank == 1, with joined_rank and score_rank recorded",
        },
        "ranking_files": {
            "v1": str(V1_RANKING_PATH.relative_to(ROOT)),
            "v2": str(V2_RANKING_PATH.relative_to(ROOT)),
        },
    }
    return books, evidence


def _load_case_runs(book: dict, window: str, start_index: int) -> tuple[dict, dict]:
    paths = {}
    for version, root in (("v1", V1_ROOT), ("v2", V2_ROOT)):
        for leg_name, leg in (("A", book["leg_a"]), ("B", book["leg_b"])):
            paths[(version, leg_name)] = _run_path(root, leg, window, start_index)
    runs = {
        (version, leg): _load_generic_run(path)
        for (version, leg), path in paths.items()
    }
    return paths, runs


def _build_metadata(
    paths: dict[tuple[str, str], Path],
    runs: dict[tuple[str, str], dict],
) -> tuple[dict, dict, list[dict], list[float]]:
    snapshots, provenance = _load_snapshots(paths)
    pairs_by_leg = {
        leg: _match_trades(runs[("v1", leg)], runs[("v2", leg)])
        for leg in ("A", "B")
    }
    sides_by_leg = {
        leg: _audit_sides(runs[("v2", leg)])
        for leg in ("A", "B")
    }
    close_by_source = {
        (version, leg): snapshots[
            str(Path(_load_metrics(paths[(version, leg)])[
                "price_snapshot"
            ]).resolve())
        ]
        for version in ("v1", "v2")
        for leg in ("A", "B")
    }
    metadata_by_version = {"v1": {}, "v2": {}}
    price_differences = []
    for version in ("v1", "v2"):
        for leg in ("A", "B"):
            close = close_by_source[(version, leg)]
            for pair in pairs_by_leg[leg]:
                key = (
                    int(pair["key"][0]),
                    str(pair["key"][1]),
                    _timestamp(pair["key"][2]),
                )
                if key not in sides_by_leg[leg]:
                    raise ValueError(f"missing V2 side metadata for {key}")
                metadata = _native_metadata(
                    pair,
                    version,
                    close,
                    sides_by_leg[leg][key],
                )
                metadata_by_version[version][metadata["key"]] = metadata
                price_differences.extend(
                    [
                        abs(metadata["entry_price1_snapshot_difference"]),
                        abs(metadata["entry_price2_snapshot_difference"]),
                    ]
                )
    return (
        {"pairs_by_leg": pairs_by_leg, "close_by_source": close_by_source},
        metadata_by_version,
        provenance,
        price_differences,
    )


def _data_for_version(runs: dict, version: str) -> dict:
    return {
        leg: {
            "trades": runs[(version, leg)]["trades"],
            "folds": runs[(version, leg)]["folds"],
            "ret": runs[(version, leg)]["ret"],
        }
        for leg in ("A", "B")
    }


def _series_from_rows(rows: list[dict], field: str = "daily_return") -> pd.Series:
    return pd.Series(
        [float(row[field]) for row in rows],
        index=pd.to_datetime([row["date"] for row in rows]),
    ).sort_index()


def _max_series_difference(left: pd.Series, right: pd.Series) -> float:
    merged = pd.concat(
        [left.rename("left"), right.rename("right")],
        axis=1,
        join="outer",
        sort=False,
    ).fillna(0.0)
    if merged.empty:
        return 0.0
    return float((merged["left"] - merged["right"]).abs().max())


def _path_stats(v1_weight: pd.Series, v2_weight: pd.Series) -> tuple[dict, pd.DataFrame]:
    joined = pd.concat(
        [v1_weight.rename("v1_a_weight"), v2_weight.rename("v2_a_weight")],
        axis=1,
        join="outer",
        sort=False,
    ).sort_index()
    joined["abs_a_weight_difference"] = (
        joined["v2_a_weight"] - joined["v1_a_weight"]
    ).abs()
    joined["weights_different"] = ~np.isclose(
        joined["v1_a_weight"], joined["v2_a_weight"], equal_nan=True
    )
    valid = joined.dropna(subset=["v1_a_weight", "v2_a_weight"])
    stats = {
        "allocator_months": int(len(valid)),
        "allocator_different_months": int(valid["weights_different"].sum()),
        "allocator_identical_months": int((~valid["weights_different"]).sum()),
        "allocator_different_month_fraction": float(valid["weights_different"].mean())
        if len(valid)
        else None,
        "allocator_mean_abs_a_weight_difference": float(
            valid["abs_a_weight_difference"].mean()
        )
        if len(valid)
        else None,
        "allocator_max_abs_a_weight_difference": float(
            valid["abs_a_weight_difference"].max()
        )
        if len(valid)
        else None,
        "allocator_largest_difference_month": (
            str(valid["abs_a_weight_difference"].idxmax().date())
            if len(valid)
            else None
        ),
        "allocator_largest_difference": float(valid["abs_a_weight_difference"].max())
        if len(valid)
        else None,
    }
    return stats, joined.reset_index(names="rebalance_month")


def _daily_weight_series(trace: dict, dates: list[pd.Timestamp]) -> pd.Series:
    return pd.Series(
        [float(trace["weight_by_day"].get(date, 0.5)) for date in dates],
        index=pd.DatetimeIndex(dates),
    )


def _scenario_stats(
    pnl: pd.Series,
    returns: pd.Series,
    equity: pd.Series,
    gross: pd.Series,
    support_gross: pd.Series,
) -> dict:
    active = gross > EPSILON
    leverage = gross[active] / equity[active]
    efficiency = pnl[support_gross > EPSILON] / support_gross[support_gross > EPSILON]
    metrics = _series_metrics(returns)
    return {
        **metrics,
        "final_equity": float(metrics["final_equity"] * INITIAL_CAPITAL),
        "final_equity_multiple": float(metrics["final_equity"]),
        "mean_gross": float(gross[active].mean()) if active.any() else None,
        "median_gross": float(gross[active].median()) if active.any() else None,
        "mean_gross_leverage": float(leverage.mean()) if len(leverage) else None,
        "median_gross_leverage": float(leverage.median()) if len(leverage) else None,
        "return_on_gross": float(efficiency.mean()) if len(efficiency) else None,
        "median_return_on_gross": float(efficiency.median()) if len(efficiency) else None,
        "active_days": int(active.sum()),
        "efficiency_days": int(len(efficiency)),
    }


def _exposure_columns(values: dict[str, float], prefix: str) -> dict:
    return {
        f"{prefix}_a_long_exposure": values["a_long"],
        f"{prefix}_a_short_exposure": values["a_short"],
        f"{prefix}_a_total_gross_exposure": _gross(values, "A"),
        f"{prefix}_b_long_exposure": values["b_long"],
        f"{prefix}_b_short_exposure": values["b_short"],
        f"{prefix}_b_total_gross_exposure": _gross(values, "B"),
        f"{prefix}_total_gross_exposure": _gross(values),
    }


def _scenario_attribution(
    group: dict,
    comparison: str,
    left_return: pd.Series,
    right_return: pd.Series,
    left_pnl: pd.Series,
    right_pnl: pd.Series,
    left_equity: pd.Series,
    right_equity: pd.Series,
    different_weights: pd.Series,
    path_stats: dict,
) -> dict:
    def _sum(values: pd.Series, mask: pd.Series) -> float:
        return float(values[mask].sum())

    return_gap = left_return - right_return
    pnl_gap = left_pnl - right_pnl
    log_gap = np.log1p(left_return) - np.log1p(right_return)
    different = different_weights.astype(bool)
    identical = ~different
    total_log = float(log_gap.sum())
    total_return = float(return_gap.sum())
    return {
        "selected_book_origin": group["selected_book_origin"],
        "selected_book": group["selected_book"],
        "window": group["window"],
        "start_index": group["start_index"],
        "start_A": group["start_A"],
        "start_B": group["start_B"],
        "mechanism": group["mechanism"],
        "comparison": comparison,
        "different_weight_days": int(different.sum()),
        "identical_weight_days": int(identical.sum()),
        "mean_abs_daily_weight_difference": float(
            path_stats["daily_mean_abs_weight_difference"]
        ),
        "arithmetic_return_gap_different_weight_days": _sum(return_gap, different),
        "arithmetic_return_gap_identical_weight_days": _sum(return_gap, identical),
        "arithmetic_return_gap_total": total_return,
        "pnl_gap_different_weight_days": _sum(pnl_gap, different),
        "pnl_gap_identical_weight_days": _sum(pnl_gap, identical),
        "pnl_gap_total": float(pnl_gap.sum()),
        "log_equity_gap_different_weight_days": _sum(log_gap, different),
        "log_equity_gap_identical_weight_days": _sum(log_gap, identical),
        "log_equity_gap_total": total_log,
        "final_equity_gap": float(left_equity.iloc[-1] - right_equity.iloc[-1]),
        "different_weight_share_of_arithmetic_gap": (
            float(_sum(return_gap, different) / total_return)
            if abs(total_return) > EPSILON
            else None
        ),
        "identical_weight_share_of_arithmetic_gap": (
            float(_sum(return_gap, identical) / total_return)
            if abs(total_return) > EPSILON
            else None
        ),
        "different_weight_share_of_log_gap": (
            float(_sum(log_gap, different) / total_log)
            if abs(total_log) > EPSILON
            else None
        ),
        "identical_weight_share_of_log_gap": (
            float(_sum(log_gap, identical) / total_log)
            if abs(total_log) > EPSILON
            else None
        ),
        **path_stats,
    }


def _scenario_row(group: dict, sizing_mode: str, exposure_mode: str, stats: dict) -> dict:
    row = {
        "selected_book_origin": group["selected_book_origin"],
        "selected_book": group["selected_book"],
        "leg_a": _path_name(*group["leg_a"]),
        "leg_b": _path_name(*group["leg_b"]),
        "window": group["window"],
        "start_index": group["start_index"],
        "start_A": group["start_A"],
        "start_B": group["start_B"],
        "mechanism": group["mechanism"],
        "sizing_mode": sizing_mode,
        "exposure_mode": exposure_mode,
        "full_matrix_replay_case": (
            "case_1_v1_sizing_v1_allocator"
            if sizing_mode == "v1" and exposure_mode == "actual"
            else "case_2_v2_sizing_v2_allocator"
            if sizing_mode == "v2" and exposure_mode == "actual"
            else None
        ),
    }
    row.update(stats)
    row["allocator_different_weight_days"] = group["path_stats"]["daily_different_weight_days"]
    row["allocator_identical_weight_days"] = group["path_stats"]["daily_identical_weight_days"]
    row["allocator_different_weight_fraction"] = group["path_stats"]["daily_different_weight_fraction"]
    row["allocator_mean_abs_daily_weight_difference"] = group["path_stats"]["daily_mean_abs_weight_difference"]
    row["allocator_max_abs_daily_weight_difference"] = group["path_stats"]["daily_max_abs_weight_difference"]
    row["v1_allocator_months"] = group["path_stats"]["allocator_months"]
    row["v1_v2_allocator_different_months"] = group["path_stats"]["allocator_different_months"]
    row["v1_v2_allocator_mean_abs_monthly_difference"] = group["path_stats"]["allocator_mean_abs_a_weight_difference"]
    row["v1_v2_allocator_max_abs_monthly_difference"] = group["path_stats"]["allocator_max_abs_a_weight_difference"]
    return row


def _forced_rows(group: dict, v1_data: dict, v2_data: dict, v1_weight: pd.Series, v2_weight: pd.Series) -> list[dict]:
    cases = (
        ("v1_sizing_v1_allocator", "v1", "v1", v1_data, v1_weight),
        ("v2_sizing_v2_allocator", "v2", "v2", v2_data, v2_weight),
        ("v1_sizing_v2_allocator", "v1", "v2", v1_data, v2_weight),
        ("v2_sizing_v1_allocator", "v2", "v1", v2_data, v1_weight),
    )
    rows = []
    for case, sizing_mode, allocator_source, data, weights in cases:
        trace = simulate_trace(data, weights, group["mechanism"])
        series = _series_from_rows(trace["rows"])
        stats = _series_metrics(series)
        rows.append(
            {
                "selected_book_origin": group["selected_book_origin"],
                "selected_book": group["selected_book"],
                "leg_a": _path_name(*group["leg_a"]),
                "leg_b": _path_name(*group["leg_b"]),
                "window": group["window"],
                "start_index": group["start_index"],
                "start_A": group["start_A"],
                "start_B": group["start_B"],
                "mechanism": group["mechanism"],
                "case": case,
                "sizing_mode": sizing_mode,
                "allocator_source": allocator_source,
                "cumulative_return": stats["cumulative_return"],
                "annualized_return": stats["annualized_return"],
                "annualized_volatility": stats["annualized_volatility"],
                "sharpe": stats["sharpe"],
                "max_drawdown": stats["max_drawdown"],
                "final_equity": stats["final_equity"] * INITIAL_CAPITAL,
                "rejected_entries": len(trace["rejected"]),
            }
        )
    return rows


def _old_output_checks(
    group: dict,
    v1_trace: dict,
    v2_trace: dict,
    dates: list[pd.Timestamp],
    old_daily: pd.DataFrame,
    old_combined: pd.DataFrame,
) -> dict:
    if group["selected_book_origin"] != "v1_selected" or group["window"] != "recent":
        return {"status": "not_applicable"}
    daily = old_daily[
        old_daily["start_index"].eq(group["start_index"])
        & old_daily["mechanism"].eq(group["mechanism"])
    ].copy()
    daily["date"] = pd.to_datetime(daily["date"]).dt.normalize()
    daily = daily.set_index("date").reindex(dates)
    combined = old_combined[
        old_combined["window"].eq("recent")
        & old_combined["start_index"].eq(group["start_index"])
        & old_combined["mechanism"].eq(group["mechanism"])
    ].copy()
    combined["date"] = pd.to_datetime(combined["date"]).dt.normalize()
    checks = {}
    for version, trace in (("v1", v1_trace), ("v2", v2_trace)):
        trace_pnl = pd.Series(
            [float(row["pnl"]) for row in trace["rows"]], index=dates
        )
        trace_return = _series_from_rows(trace["rows"])
        checks[f"{version}_pnl_difference"] = float(
            (trace_pnl - daily[f"{version}_total_pnl"].astype(float)).abs().max()
        )
        checks[f"{version}_return_difference"] = float(
            (trace_return - daily[f"{version}_total_return"].astype(float)).abs().max()
        )
        case = "case_1_v1_sizing_v1_allocator" if version == "v1" else "case_2_v2_sizing_v2_allocator"
        expected = combined[combined["case"].eq(case)].set_index("date")["daily_return"].astype(float).reindex(dates)
        checks[f"{version}_combined_return_difference"] = float(
            (trace_return - expected).abs().max()
        )
    checks["status"] = "pass" if max(checks.values()) <= EPSILON else "fail"
    return checks


def _native_budget_checks(runs: dict, start_index: int, leg: str) -> dict:
    checks = []
    for trade in runs[("v2", leg)]["trades"]:
        raw = trade["raw"]
        budget = _num(raw.get("pair_gross_budget"), 250_000.0)
        gross = _num(raw.get("gross_entry_exposure"))
        sizing_gross = _num(raw.get("sizing_gross_exposure"), gross)
        checks.append(
            {
                "start_index": start_index,
                "leg": leg,
                "pair": str(trade["pair"]),
                "budget_enforced": bool(raw.get("pair_gross_budget_enforced", True)),
                "budget_headroom": budget - gross,
                "gross_metadata_difference": abs(gross - sizing_gross),
            }
        )
    return {
        "start_index": start_index,
        "leg": leg,
        "trade_count": len(checks),
        "status": "pass"
        if all(
            row["budget_enforced"]
            and row["budget_headroom"] >= -EXPOSURE_TOLERANCE
            and row["gross_metadata_difference"] <= EXPOSURE_TOLERANCE
            for row in checks
        )
        else "fail",
        "min_budget_headroom": min((row["budget_headroom"] for row in checks), default=0.0),
        "max_gross_metadata_difference": max(
            (row["gross_metadata_difference"] for row in checks), default=0.0
        ),
    }


def _group_summary_row(frame: pd.DataFrame, keys: dict) -> dict:
    row = dict(keys)
    row["aggregation"] = "mean_across_start_iterations"
    row["start_count"] = int(frame["start_index"].nunique())
    for column in (
        "cumulative_return",
        "annualized_return",
        "annualized_volatility",
        "sharpe",
        "max_drawdown",
        "final_equity",
        "mean_gross",
        "median_gross",
        "mean_gross_leverage",
        "median_gross_leverage",
        "return_on_gross",
        "median_return_on_gross",
    ):
        row[column] = float(frame[column].mean())
    for column in (
        "active_days",
        "efficiency_days",
        "allocator_different_weight_days",
        "allocator_identical_weight_days",
    ):
        row[column] = float(frame[column].mean())
    return row


def _interaction_summary(per_run: pd.DataFrame) -> list[dict]:
    rows = []
    for keys, frame in per_run.groupby(
        ["selected_book_origin", "selected_book", "window", "mechanism"],
        dropna=False,
    ):
        origin, book, window, mechanism = keys
        v1 = frame[(frame["sizing_mode"] == "v1") & (frame["exposure_mode"] == "actual")]
        v2 = frame[(frame["sizing_mode"] == "v2") & (frame["exposure_mode"] == "actual")]
        matched = frame[(frame["sizing_mode"] == "v1") & (frame["exposure_mode"] == "matched_to_v2")]
        if len(v1) == 0 or len(v2) == 0 or len(matched) == 0:
            raise ValueError(f"scenario rows missing for interaction group {keys}")
        v1_pair = v1[["start_index", "sharpe", "final_equity"]].merge(
            v2[["start_index", "sharpe", "final_equity"]],
            on="start_index",
            how="inner",
            suffixes=("_v1", "_v2"),
            validate="one_to_one",
        )
        matched_pair = matched[["start_index", "sharpe", "final_equity"]].merge(
            v2[["start_index", "sharpe", "final_equity"]],
            on="start_index",
            how="inner",
            suffixes=("_matched", "_v2"),
            validate="one_to_one",
        )
        if len(v1_pair) != len(v1) or len(matched_pair) != len(matched):
            raise ValueError(f"scenario start indices do not align for interaction group {keys}")
        rows.append(
            {
                "selected_book_origin": origin,
                "selected_book": book,
                "window": window,
                "mechanism": mechanism,
                "start_count": int(len(v1_pair)),
                "v1_actual_sharpe": float(v1_pair["sharpe_v1"].mean()),
                "v2_actual_sharpe": float(v1_pair["sharpe_v2"].mean()),
                "v1_matched_to_v2_sharpe": float(matched_pair["sharpe_matched"].mean()),
                "v1_actual_final_equity": float(v1_pair["final_equity_v1"].mean()),
                "v2_actual_final_equity": float(v1_pair["final_equity_v2"].mean()),
                "v1_matched_to_v2_final_equity": float(matched_pair["final_equity_matched"].mean()),
                "actual_v1_minus_v2_final_equity_gap": float(
                    (v1_pair["final_equity_v1"] - v1_pair["final_equity_v2"]).mean()
                ),
                "matched_v1_to_v2_minus_v2_final_equity_gap": float(
                    (matched_pair["final_equity_matched"] - matched_pair["final_equity_v2"]).mean()
                ),
                "matched_v1_sharpe_minus_v2_sharpe": float(
                    (matched_pair["sharpe_matched"] - matched_pair["sharpe_v2"]).mean()
                ),
                "matched_v1_beats_v2_sharpe": int(
                    (matched_pair["sharpe_matched"] > matched_pair["sharpe_v2"]).sum()
                ),
                "matched_final_gap_positive": int(
                    (matched_pair["final_equity_matched"] > matched_pair["final_equity_v2"]).sum()
                ),
                "v1_actual_beats_v2_sharpe": int(
                    (v1_pair["sharpe_v1"] > v1_pair["sharpe_v2"]).sum()
                ),
            }
        )
    return rows


def _score_table_checks(per_run: pd.DataFrame) -> list[dict]:
    checks = []
    for book_origin in ("v1_selected", "v2_selected"):
        for sizing_mode, score_path in (("v1", V1_SCORE_PATH), ("v2", V2_SCORE_PATH)):
            book_rows = per_run[per_run["selected_book_origin"].eq(book_origin)]
            if book_rows.empty:
                continue
            leg_a = book_rows.iloc[0]["leg_a"]
            leg_b = book_rows.iloc[0]["leg_b"]
            expected = pd.read_csv(score_path)
            expected = expected[expected["A"].eq(leg_a) & expected["B"].eq(leg_b)]
            for window in START_WINDOWS:
                for mechanism in MECHANISMS:
                    row = expected[expected["mechanism"].eq(mechanism)]
                    actual = per_run[
                        per_run["selected_book_origin"].eq(book_origin)
                        & per_run["sizing_mode"].eq(sizing_mode)
                        & per_run["exposure_mode"].eq("actual")
                        & per_run["window"].eq(window)
                        & per_run["mechanism"].eq(mechanism)
                    ]
                    if len(row) != 1 or actual.empty:
                        raise ValueError(
                            f"score check inputs missing for {book_origin}/{sizing_mode}/{window}/{mechanism}"
                        )
                    expected_row = row.iloc[0]
                    columns = {
                        "annualized_return": "recent_ret" if window == "recent" else "hist_ret",
                        "annualized_volatility": "recent_vol" if window == "recent" else "hist_vol",
                        "sharpe": "recent_sh" if window == "recent" else "hist_sh",
                        "max_drawdown": "recent_mdd" if window == "recent" else "hist_mdd",
                    }
                    differences = {
                        metric: abs(float(actual[metric].mean()) - float(expected_row[column]))
                        for metric, column in columns.items()
                    }
                    checks.append(
                        {
                            "selected_book_origin": book_origin,
                            "sizing_mode": sizing_mode,
                            "window": window,
                            "mechanism": mechanism,
                            "max_abs_difference": max(differences.values()),
                            "differences": differences,
                            "status": "pass"
                            if max(differences.values()) <= 1e-9
                            else "fail",
                        }
                    )
    return checks


def _build_markdown(summary: dict, summary_frame: pd.DataFrame, interactions: pd.DataFrame, attribution: pd.DataFrame) -> str:
    lines = [
        "# Selected-Book V1/V2 Cross-Check",
        "",
        "This focused replay compares the books selected by the V1 and V2",
        "research conventions under both sizing modes. It uses preserved raw",
        "runs and does not rerun the 496-book matrix or modify canonical outputs.",
        "",
        "## Selection",
        "",
        f"- V1-selected book: `{summary['books']['v1_selected']['leg_a']}` + `{summary['books']['v1_selected']['leg_b']}`",
        f"- V2-selected book: `{summary['books']['v2_selected']['leg_a']}` + `{summary['books']['v2_selected']['leg_b']}`",
        f"- V2 handoff candidate matches current ranking: **{summary['selection_evidence']['current_v2_book']['matches_handoff']}**",
        f"- Allocator: 84-day causal lookback, 0.40 step, 0.10--0.90 bounds, 0.50 initial A weight",
        "- These allocator settings are held fixed and were inherited from the broader research; they are not neutral proof for either sizing convention.",
        "",
        "## Validation",
        "",
        f"- Overall status: **{summary['status']}**",
        f"- Focused groups: **{summary['focused_group_count']}**; full matrix rerun: **False**",
        f"- Trade identity matching: **{summary['validation']['trade_identity_status']}**",
        f"- Replay PnL equivalence: **{summary['validation']['replay_equivalence_status']}**",
        f"- Native V2 marked exposure reconciliation: **{summary['validation']['native_v2_exposure_status']}**",
        f"- V2 gross-budget invariants: **{summary['validation']['v2_budget_status']}**",
        f"- Existing old-winner outputs unchanged: **{summary['validation']['old_winner_outputs_unchanged']}**",
        f"- Protected public hashes unchanged: **{summary['validation']['protected_hashes_unchanged']}**",
        "",
        "## Recent Aggregate Comparison",
        "",
        "The table reports mean metrics across the five recent starts. Gross and",
        "leverage statistics are means of each run's active-day statistics.",
        "",
        "| Origin | Mechanism | Scenario | Mean Sharpe | Mean cumulative return | Mean final equity | Mean gross leverage | Mean return on gross |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    recent = summary_frame[summary_frame["window"].eq("recent")]
    for _, row in recent.sort_values(["selected_book_origin", "mechanism", "sizing_mode", "exposure_mode"]).iterrows():
        scenario = f"{row['sizing_mode']} / {row['exposure_mode']}"
        lines.append(
            f"| {row['selected_book_origin']} | {row['mechanism']} | {scenario} | "
            f"{row['sharpe']:.4f} | {row['cumulative_return']:.4%} | "
            f"${row['final_equity']:,.0f} | {row['mean_gross_leverage']:.3f}x | "
            f"{row['return_on_gross']:.8f} |"
        )
    lines.extend(
        [
            "",
            "## Exposure-Matched Selection Interaction",
            "",
            "The primary comparison is V1 matched to V2 gross versus V2 actual.",
            "Positive gap means the matched V1 final equity exceeded V2 actual;",
            "this is an attribution result, not a causal estimate.",
            "",
            "| Origin | Mechanism | Mean actual V1-V2 gap | Mean matched V1-V2 gap | Matched V1 Sharpe > V2 | Positive matched gap |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    recent_interactions = interactions[interactions["window"].eq("recent")]
    for (origin, mechanism), frame in recent_interactions.groupby(
        ["selected_book_origin", "mechanism"], dropna=False
    ):
        start_count = int(frame["start_count"].sum())
        lines.append(
            f"| {origin} | {mechanism} | ${frame['actual_v1_minus_v2_final_equity_gap'].mean():,.0f} | "
            f"${frame['matched_v1_to_v2_minus_v2_final_equity_gap'].mean():,.0f} | "
            f"{int(frame['matched_v1_beats_v2_sharpe'].sum())}/{start_count} | "
            f"{int(frame['matched_final_gap_positive'].sum())}/{start_count} |"
        )
    lines.extend(
        [
            "",
            "## Allocator-Path Attribution",
            "",
            "Shares describe where the arithmetic or log-equity gap accumulated",
            "under the fixed replay paths. They do not identify causality.",
            "",
            "| Origin | Mechanism | Start | Comparison | Different-weight return-gap share | Identical-weight return-gap share | Different-weight log-gap share |",
            "|---|---|---:|---|---:|---:|---:|",
        ]
    )
    recent_attr = attribution[
        attribution["window"].eq("recent")
        & attribution["comparison"].eq("v1_matched_to_v2_minus_v2")
    ]
    for _, row in recent_attr.sort_values(["selected_book_origin", "mechanism"]).iterrows():
        fmt = lambda value: "n/a" if pd.isna(value) else f"{value:.1%}"
        lines.append(
            f"| {row['selected_book_origin']} | {row['mechanism']} | {int(row['start_index'])} | {row['comparison']} | "
            f"{fmt(row['different_weight_share_of_arithmetic_gap'])} | "
            f"{fmt(row['identical_weight_share_of_arithmetic_gap'])} | "
            f"{fmt(row['different_weight_share_of_log_gap'])} |"
        )
    lines.extend(
        [
            "",
            "## What This Establishes",
            "",
            "- It directly tests the old V1-selected and current V2-selected books under both sizing conventions on the same preserved recent and historical trade identities.",
            "- It shows whether V1's equal-gross residual survives book selection, rather than treating the old V1-selected book as a universal sizing test.",
            "- It separates realized leverage, return-on-gross, allocator-path differences, and forced allocator-path counterfactuals.",
            "- V2 remains methodologically cleaner for cross-pair and cross-book comparison because its configured pair allocation is total pair gross exposure.",
            "",
            "## What This Does Not Establish",
            "",
            "- It does not prove that V1 or V2 is intrinsically superior from two selected books.",
            "- It does not make the inherited Clean40 parameters neutral; they were held fixed only to isolate this interaction.",
            "- It does not identify causal shares from differing-weight days; the attribution is conditional decomposition.",
            "- It does not replace a broader out-of-sample selection study or retune the allocator.",
            "",
            "## Artifacts",
            "",
            "- `selected_book_crosscheck_per_run.csv`",
            "- `selected_book_crosscheck_daily.csv`",
            "- `selected_book_crosscheck_summary.csv`",
            "- `selected_book_crosscheck_summary.json`",
            "- `selected_book_crosscheck_summary.md`",
            "- `allocator_path_attribution.csv`",
            "- `allocator_path_counterfactuals.csv`",
        ]
    )
    return "\n".join(lines) + "\n"


def run() -> dict:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    books, selection_evidence = _resolve_books()
    protected_before = {
        "public_score": _sha256(PUBLIC_SCORE_PATH),
        "canonical_rankings": _sha256(CANONICAL_RANKINGS_PATH),
        "selected_config": _sha256(SELECTED_CONFIG_PATH),
        "old_autopsy_tree": _tree_hash(OLD_AUTOPSY_ROOT),
    }
    old_daily = pd.read_csv(OLD_DAILY_PATH)
    old_combined = pd.read_csv(OLD_COMBINED_PATH)
    per_run_rows = []
    daily_rows = []
    attribution_rows = []
    forced_rows = []
    native_exposure_checks = []
    budget_checks = []
    trade_identity_checks = []
    replay_checks = []
    old_output_checks = []
    path_checks = []
    snapshot_provenance = []
    price_differences = []
    groups = []

    for book_origin, book in books.items():
        for window in START_WINDOWS:
            start_count = 5 if window == "recent" else 1
            for start_index in range(start_count):
                paths, runs = _load_case_runs(book, window, start_index)
                source, metadata_by_version, provenance, price_diffs = _build_metadata(paths, runs)
                snapshot_provenance.extend(provenance)
                price_differences.extend(price_diffs)
                pairs_by_leg = source["pairs_by_leg"]
                close_by_source = source["close_by_source"]
                for leg in ("A", "B"):
                    native_exposure_checks.append(
                        _validate_native_v2_exposure(
                            paths[("v2", leg)],
                            runs[("v2", leg)],
                            {
                                trade["trade_key"]: metadata_by_version["v2"][trade["trade_key"]]
                                for trade in runs[("v2", leg)]["trades"]
                            },
                            close_by_source[("v2", leg)],
                            start_index,
                            leg,
                        )
                    )
                    budget_checks.append(_native_budget_checks(runs, start_index, leg))
                    trade_identity_checks.append(
                        {
                            "selected_book_origin": book_origin,
                            "window": window,
                            "start_index": start_index,
                            "leg": leg,
                            "v1_trade_count": len(runs[("v1", leg)]["trades"]),
                            "v2_trade_count": len(runs[("v2", leg)]["trades"]),
                            "matched_trade_count": len(pairs_by_leg[leg]),
                            "status": "pass",
                        }
                    )

                v1_data = _data_for_version(runs, "v1")
                v2_data = _data_for_version(runs, "v2")
                v1_weight, v1_path_details = allocator_path(
                    v1_data["A"]["ret"], v1_data["B"]["ret"]
                )
                v2_weight, v2_path_details = allocator_path(
                    v2_data["A"]["ret"], v2_data["B"]["ret"]
                )
                monthly_path_stats, monthly_paths = _path_stats(v1_weight, v2_weight)
                if book_origin == "v1_selected" and window == "recent":
                    existing = pd.read_csv(OLD_ALLOCATOR_PATH)
                    existing = existing[
                        existing["window"].eq(window)
                        & existing["start_index"].eq(start_index)
                    ]
                    existing_v1 = pd.Series(
                        existing["v1_a_weight"].to_numpy(dtype=float),
                        index=pd.to_datetime(existing["rebalance_month"]),
                    )
                    existing_v2 = pd.Series(
                        existing["v2_a_weight"].to_numpy(dtype=float),
                        index=pd.to_datetime(existing["rebalance_month"]),
                    )
                    path_checks.append(
                        {
                            "selected_book_origin": book_origin,
                            "window": window,
                            "start_index": start_index,
                            "v1_path_max_difference": _max_series_difference(v1_weight, existing_v1),
                            "v2_path_max_difference": _max_series_difference(v2_weight, existing_v2),
                        }
                    )

                for mechanism in MECHANISMS:
                    v1_trace = simulate_trace(v1_data, v1_weight, mechanism)
                    v2_trace = simulate_trace(v2_data, v2_weight, mechanism)
                    v1_map = _trace_map(v1_trace)
                    v2_map = _trace_map(v2_trace)
                    if set(v1_map) != set(v2_map):
                        raise ValueError(
                            f"trace dates differ for {book_origin}/{window}/{start_index}/{mechanism}"
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
                    v1_pnl = pd.Series([float(v1_map[d]["pnl"]) for d in dates], index=dates)
                    v2_pnl = pd.Series([float(v2_map[d]["pnl"]) for d in dates], index=dates)
                    v1_return = pd.Series([float(v1_map[d]["daily_return"]) for d in dates], index=dates)
                    v2_return = pd.Series([float(v2_map[d]["daily_return"]) for d in dates], index=dates)
                    v1_equity = pd.Series([float(v1_map[d]["total_capital"]) for d in dates], index=dates)
                    v2_equity = pd.Series([float(v2_map[d]["total_capital"]) for d in dates], index=dates)
                    v1_support_gross = pd.Series([_gross(v1_support[d]) for d in dates], index=dates)
                    v2_support_gross = pd.Series([_gross(v2_support[d]) for d in dates], index=dates)
                    v1_gross = pd.Series([_gross(v1_exposure[d]) for d in dates], index=dates)
                    v2_gross = pd.Series([_gross(v2_exposure[d]) for d in dates], index=dates)
                    v1_matched_pnl = pd.Series(
                        [_scale_pnl(v1_pnl[d], v1_support_gross[d], v2_support_gross[d]) for d in dates],
                        index=dates,
                    )
                    v2_matched_pnl = pd.Series(
                        [_scale_pnl(v2_pnl[d], v2_support_gross[d], v1_support_gross[d]) for d in dates],
                        index=dates,
                    )
                    if v1_matched_pnl.isna().any() or v2_matched_pnl.isna().any():
                        raise ValueError(
                            f"nonzero PnL without support for {book_origin}/{window}/{start_index}/{mechanism}"
                        )
                    v1_matched_return, v1_matched_equity, _ = _account_path(
                        v1_matched_pnl, pd.DatetimeIndex(dates)
                    )
                    v2_matched_return, v2_matched_equity, _ = _account_path(
                        v2_matched_pnl, pd.DatetimeIndex(dates)
                    )
                    v1_efficiency = v1_pnl / v1_support_gross.where(v1_support_gross > EPSILON)
                    v2_efficiency = v2_pnl / v2_support_gross.where(v2_support_gross > EPSILON)
                    v1_matched_efficiency = v1_matched_pnl / v2_support_gross.where(v2_support_gross > EPSILON)
                    v2_matched_efficiency = v2_matched_pnl / v1_support_gross.where(v1_support_gross > EPSILON)
                    v1_daily_weight = _daily_weight_series(v1_trace, dates)
                    v2_daily_weight = _daily_weight_series(v2_trace, dates)
                    weight_different = pd.Series(
                        ~np.isclose(v1_daily_weight, v2_daily_weight),
                        index=pd.DatetimeIndex(dates),
                    )
                    path_stats = {
                        **monthly_path_stats,
                        "daily_different_weight_days": int(weight_different.sum()),
                        "daily_identical_weight_days": int((~weight_different).sum()),
                        "daily_different_weight_fraction": float(weight_different.mean()),
                        "daily_mean_abs_weight_difference": float(
                            (v1_daily_weight - v2_daily_weight).abs().mean()
                        ),
                        "daily_max_abs_weight_difference": float(
                            (v1_daily_weight - v2_daily_weight).abs().max()
                        ),
                    }
                    group = {
                        "selected_book_origin": book_origin,
                        "selected_book": book["selected_book"],
                        "leg_a": book["leg_a"],
                        "leg_b": book["leg_b"],
                        "window": window,
                        "start_index": start_index,
                        "start_A": STRATEGIES[book["leg_a"][0]][
                            "recent_starts" if window == "recent" else "historical_start"
                        ][start_index]
                        if window == "recent"
                        else STRATEGIES[book["leg_a"][0]]["historical_start"],
                        "start_B": STRATEGIES[book["leg_b"][0]][
                            "recent_starts" if window == "recent" else "historical_start"
                        ][start_index]
                        if window == "recent"
                        else STRATEGIES[book["leg_b"][0]]["historical_start"],
                        "mechanism": mechanism,
                        "path_stats": path_stats,
                    }
                    actual_v1_stats = _scenario_stats(
                        v1_pnl, v1_return, v1_equity, v1_gross, v1_support_gross
                    )
                    actual_v2_stats = _scenario_stats(
                        v2_pnl, v2_return, v2_equity, v2_gross, v2_support_gross
                    )
                    matched_v1_stats = _scenario_stats(
                        v1_matched_pnl,
                        v1_matched_return,
                        v1_matched_equity,
                        v2_gross,
                        v2_support_gross,
                    )
                    matched_v2_stats = _scenario_stats(
                        v2_matched_pnl,
                        v2_matched_return,
                        v2_matched_equity,
                        v1_gross,
                        v1_support_gross,
                    )
                    group["actual_metrics"] = {"v1": actual_v1_stats, "v2": actual_v2_stats}
                    group["path_details"] = monthly_paths
                    groups.append(group)
                    per_run_rows.extend(
                        [
                            _scenario_row(group, "v1", "actual", actual_v1_stats),
                            _scenario_row(group, "v2", "actual", actual_v2_stats),
                            _scenario_row(group, "v1", "matched_to_v2", matched_v1_stats),
                            _scenario_row(group, "v2", "matched_to_v1", matched_v2_stats),
                        ]
                    )
                    attribution_rows.extend(
                        [
                            _scenario_attribution(
                                group,
                                "actual_v1_minus_v2",
                                v1_return,
                                v2_return,
                                v1_pnl,
                                v2_pnl,
                                v1_equity,
                                v2_equity,
                                weight_different,
                                path_stats,
                            ),
                            _scenario_attribution(
                                group,
                                "v1_matched_to_v2_minus_v2",
                                v1_matched_return,
                                v2_return,
                                v1_matched_pnl,
                                v2_pnl,
                                v1_matched_equity,
                                v2_equity,
                                weight_different,
                                path_stats,
                            ),
                        ]
                    )
                    forced_rows.extend(
                        _forced_rows(group, v1_data, v2_data, v1_weight, v2_weight)
                    )
                    old_output_checks.append(
                        _old_output_checks(
                            group, v1_trace, v2_trace, dates, old_daily, old_combined
                        )
                    )

                    plain_v1_rows, _, plain_v1_rejected, _ = simulate(
                        v1_data, v1_weight, mechanism, capital=INITIAL_CAPITAL,
                        pct=PCT_PER_PAIR, max_pairs=MAX_PAIRS,
                    )
                    plain_v2_rows, _, plain_v2_rejected, _ = simulate(
                        v2_data, v2_weight, mechanism, capital=INITIAL_CAPITAL,
                        pct=PCT_PER_PAIR, max_pairs=MAX_PAIRS,
                    )
                    replay_checks.append(
                        {
                            "selected_book_origin": book_origin,
                            "window": window,
                            "start_index": start_index,
                            "mechanism": mechanism,
                            "v1_trace_vs_replay_max_return_difference": _max_series_difference(
                                v1_return, _series_from_rows(plain_v1_rows)
                            ),
                            "v2_trace_vs_replay_max_return_difference": _max_series_difference(
                                v2_return, _series_from_rows(plain_v2_rows)
                            ),
                            "v1_rejected_entries_trace": len(v1_trace["rejected"]),
                            "v1_rejected_entries_replay": len(plain_v1_rejected),
                            "v2_rejected_entries_trace": len(v2_trace["rejected"]),
                            "v2_rejected_entries_replay": len(plain_v2_rejected),
                            "status": "pass"
                            if _max_series_difference(v1_return, _series_from_rows(plain_v1_rows)) <= EPSILON
                            and _max_series_difference(v2_return, _series_from_rows(plain_v2_rows)) <= EPSILON
                            else "fail",
                        }
                    )
                    for date in dates:
                        v1_values = v1_exposure[date]
                        v2_values = v2_exposure[date]
                        row = {
                            "selected_book_origin": book_origin,
                            "selected_book": book["selected_book"],
                            "leg_a": _path_name(*book["leg_a"]),
                            "leg_b": _path_name(*book["leg_b"]),
                            "window": window,
                            "start_index": start_index,
                            "start_A": group["start_A"],
                            "start_B": group["start_B"],
                            "mechanism": mechanism,
                            "date": _iso(date),
                            "v1_daily_pnl": float(v1_pnl[date]),
                            "v2_daily_pnl": float(v2_pnl[date]),
                            "v1_account_return": float(v1_return[date]),
                            "v2_account_return": float(v2_return[date]),
                            "v1_account_equity": float(v1_equity[date]),
                            "v2_account_equity": float(v2_equity[date]),
                            "v1_gross_leverage": float(v1_gross[date] / v1_equity[date]) if v1_equity[date] > 0 else float("nan"),
                            "v2_gross_leverage": float(v2_gross[date] / v2_equity[date]) if v2_equity[date] > 0 else float("nan"),
                            "v1_return_on_gross": float(v1_efficiency[date]) if pd.notna(v1_efficiency[date]) else float("nan"),
                            "v2_return_on_gross": float(v2_efficiency[date]) if pd.notna(v2_efficiency[date]) else float("nan"),
                            "v1_matched_to_v2_daily_pnl": float(v1_matched_pnl[date]),
                            "v1_matched_to_v2_account_return": float(v1_matched_return[date]),
                            "v1_matched_to_v2_account_equity": float(v1_matched_equity[date]),
                            "v1_matched_to_v2_gross_leverage": float(v2_gross[date] / v1_matched_equity[date]) if v1_matched_equity[date] > 0 else float("nan"),
                            "v1_matched_to_v2_return_on_gross": float(v1_matched_efficiency[date]) if pd.notna(v1_matched_efficiency[date]) else float("nan"),
                            "v2_matched_to_v1_daily_pnl": float(v2_matched_pnl[date]),
                            "v2_matched_to_v1_account_return": float(v2_matched_return[date]),
                            "v2_matched_to_v1_account_equity": float(v2_matched_equity[date]),
                            "v2_matched_to_v1_gross_leverage": float(v1_gross[date] / v2_matched_equity[date]) if v2_matched_equity[date] > 0 else float("nan"),
                            "v2_matched_to_v1_return_on_gross": float(v2_matched_efficiency[date]) if pd.notna(v2_matched_efficiency[date]) else float("nan"),
                            "v1_pnl_supporting_total_gross_exposure": float(v1_support_gross[date]),
                            "v2_pnl_supporting_total_gross_exposure": float(v2_support_gross[date]),
                            "v1_a_weight": float(v1_daily_weight[date]),
                            "v2_a_weight": float(v2_daily_weight[date]),
                            "weights_different": bool(weight_different.loc[date]),
                        }
                        row.update(_exposure_columns(v1_values, "v1"))
                        row.update(_exposure_columns(v2_values, "v2"))
                        daily_rows.append(row)

    per_run = pd.DataFrame(per_run_rows)
    daily = pd.DataFrame(daily_rows)
    attribution = pd.DataFrame(attribution_rows)
    forced = pd.DataFrame(forced_rows)
    summary_rows = []
    group_columns = [
        "selected_book_origin",
        "selected_book",
        "window",
        "mechanism",
        "sizing_mode",
        "exposure_mode",
    ]
    for keys, frame in per_run.groupby(group_columns, dropna=False):
        summary_rows.append(
            _group_summary_row(frame, dict(zip(group_columns, keys)))
        )
    summary_frame = pd.DataFrame(summary_rows)
    interactions = pd.DataFrame(_interaction_summary(per_run))
    score_checks = _score_table_checks(per_run)

    protected_after = {
        "public_score": _sha256(PUBLIC_SCORE_PATH),
        "canonical_rankings": _sha256(CANONICAL_RANKINGS_PATH),
        "selected_config": _sha256(SELECTED_CONFIG_PATH),
        "old_autopsy_tree": _tree_hash(OLD_AUTOPSY_ROOT),
    }
    old_checks = [row for row in old_output_checks if row.get("status") != "not_applicable"]
    validation = {
        "trade_identity_status": "pass"
        if all(row["status"] == "pass" for row in trade_identity_checks)
        else "fail",
        "replay_equivalence_status": "pass"
        if all(row["status"] == "pass" for row in replay_checks)
        else "fail",
        "native_v2_exposure_status": "pass"
        if all(row["status"] == "pass" for row in native_exposure_checks)
        else "fail",
        "v2_budget_status": "pass"
        if all(row["status"] == "pass" for row in budget_checks)
        else "fail",
        "old_winner_output_checks_status": "pass"
        if all(row["status"] == "pass" for row in old_checks)
        else "fail",
        "allocator_path_status": "pass"
        if all(
            row["v1_path_max_difference"] <= EPSILON
            and row["v2_path_max_difference"] <= EPSILON
            for row in path_checks
        )
        else "fail",
        "score_table_status": "pass"
        if all(row["status"] == "pass" for row in score_checks)
        else "fail",
        "entry_snapshot_status": "pass"
        if max(price_differences, default=0.0) <= EPSILON
        and all(item["hash_match"] for item in snapshot_provenance)
        else "fail",
        "old_winner_outputs_unchanged": protected_before["old_autopsy_tree"] == protected_after["old_autopsy_tree"],
        "protected_hashes_unchanged": all(
            protected_before[key] == protected_after[key]
            for key in ("public_score", "canonical_rankings", "selected_config")
        ),
        "trade_identity_checks": trade_identity_checks,
        "replay_checks": replay_checks,
        "native_v2_exposure_checks": native_exposure_checks,
        "budget_checks": budget_checks,
        "old_output_checks": old_output_checks,
        "allocator_path_checks": path_checks,
        "score_table_checks": score_checks,
        "snapshot_provenance": snapshot_provenance,
        "max_entry_snapshot_difference": max(price_differences, default=0.0),
    }
    status = "pass"
    for key, value in validation.items():
        if key.endswith("_status") and value != "pass":
            status = "fail"
    if not validation["old_winner_outputs_unchanged"] or not validation["protected_hashes_unchanged"]:
        status = "fail"

    summary = {
        "status": status,
        "branch": _git_value("branch", "--show-current"),
        "focused_group_count": len(groups),
        "full_matrix_rerun": False,
        "canonical_outputs_written": False,
        "books": {
            key: {
                "selected_book_origin": value["selected_book_origin"],
                "selected_book": value["selected_book"],
                "leg_a": _path_name(*value["leg_a"]),
                "leg_b": _path_name(*value["leg_b"]),
                "selection_evidence": value["selection_evidence"],
            }
            for key, value in books.items()
        },
        "selection_evidence": selection_evidence,
        "parameters": {
            "lookback_days": 84,
            "step": 0.4,
            "weight_min": 0.1,
            "weight_max": 0.9,
            "initial_weight_leg_a": 0.5,
            "initial_capital": INITIAL_CAPITAL,
            "pct_per_pair": PCT_PER_PAIR,
            "windows": START_WINDOWS,
            "mechanisms": MECHANISMS,
        },
        "validation": validation,
        "interaction_summary": interactions.to_dict(orient="records"),
        "aggregate_summary": summary_frame.to_dict(orient="records"),
        "pooled_daily_rows": int(len(daily)),
        "per_run_rows": int(len(per_run)),
        "attribution_rows": int(len(attribution)),
        "forced_counterfactual_rows": int(len(forced)),
        "protected_hashes_before": {
            "public_score": protected_before["public_score"],
            "canonical_rankings": protected_before["canonical_rankings"],
            "selected_config": protected_before["selected_config"],
        },
        "protected_hashes_after": {
            "public_score": protected_after["public_score"],
            "canonical_rankings": protected_after["canonical_rankings"],
            "selected_config": protected_after["selected_config"],
        },
    }
    per_run.to_csv(PER_RUN_PATH, index=False)
    daily.to_csv(DAILY_PATH, index=False)
    summary_frame.to_csv(SUMMARY_PATH, index=False)
    attribution.to_csv(ATTRIBUTION_PATH, index=False)
    forced.to_csv(FORCED_PATH, index=False)
    SUMMARY_JSON_PATH.write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    SUMMARY_MD_PATH.write_text(
        _build_markdown(summary, summary_frame, interactions, attribution),
        encoding="utf-8",
    )
    return summary


def main() -> int:
    summary = run()
    print(f"Validation: {summary['status']}")
    print(f"Wrote {OUTPUT_ROOT}")
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
