"""Run a small transaction-cost sensitivity overlay on the frozen V2 book.

This is a historical cost overlay, not an execution simulator. It replays the
existing V2-selected book and frozen Clean40 allocator, then subtracts simple
one-way costs from the daily gross PnL. The preserved native share quantities
and entry prices are used where available. Exit notional uses the preserved
exit-date close snapshot because exit execution prices are not recorded in the
compact trade log.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.run_gross_exposure_autopsy import _price  # noqa: E402
from research.run_selected_book_crosscheck import _resolve_books  # noqa: E402
from research.run_v2_book_clean40_retune import (  # noqa: E402
    BASELINE_NAME,
    CONFIGURATIONS,
    INITIAL_CAPITAL,
    MECHANISMS,
    _load_context,
    _trace_record,
)
from research.run_combined_backtest import metrics as replay_metrics  # noqa: E402


OUTPUT_ROOT = ROOT / "results" / "transaction_cost_analysis"
COST_BPS = (0, 5, 10, 20)
V2_LEG_A = "sp500-12m/same_sector_slide1m_noscreen"
V2_LEG_B = "sp500-12m/same_sector_slide3m_noscreen"
WINDOWS = ("recent", "historical")
RECENT_START_COUNT = 5
EPSILON = 1e-9


def _baseline_configuration() -> dict:
    matches = [config for config in CONFIGURATIONS if config["name"] == BASELINE_NAME]
    if len(matches) != 1:
        raise ValueError(f"expected one frozen baseline configuration, got {len(matches)}")
    configuration = dict(matches[0])
    expected = {
        "lookback_days": 84,
        "step": 0.4,
        "weight_min": 0.1,
        "weight_max": 0.9,
    }
    for key, value in expected.items():
        if configuration[key] != value:
            raise ValueError(f"frozen Clean40 mismatch for {key}: {configuration[key]}")
    return configuration


def _frozen_book() -> dict:
    books, _evidence = _resolve_books()
    book = books["v2_selected"]
    actual = {
        "/".join(book["leg_a"]),
        "/".join(book["leg_b"]),
    }
    expected = {V2_LEG_A, V2_LEG_B}
    if actual != expected:
        raise ValueError(f"unexpected V2 book: {sorted(actual)}")
    return book


def _align_date(value, dates: pd.DatetimeIndex) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp in dates:
        return timestamp
    normalized = timestamp.normalize()
    if normalized in dates:
        return normalized
    raise ValueError(f"trade date {timestamp} is missing from the replay date index")


def _trade_turnover(record: dict) -> tuple[pd.DataFrame, pd.Series]:
    """Return trade-level native turnover and a date-indexed notional series."""
    context = record["context"]
    trace = record["trace"]
    trades = record["trade_frame"]
    dates = pd.DatetimeIndex(record["daily"].index)
    turnover_rows = []
    entry_by_date: defaultdict[pd.Timestamp, float] = defaultdict(float)
    exit_by_date: defaultdict[pd.Timestamp, float] = defaultdict(float)

    for trade in trades.itertuples(index=False):
        key = trade.trade_key
        metadata = context["metadata"][key]
        allocation = float(trace["allocations"][key])
        target_notional = float(metadata["target_notional"])
        if not math.isfinite(allocation) or allocation <= 0:
            raise ValueError(f"invalid replay allocation for {key}: {allocation}")
        if not math.isfinite(target_notional) or target_notional <= 0:
            raise ValueError(f"invalid target notional for {key}: {target_notional}")
        scale = allocation / target_notional
        close = context["close_by_leg"][trade.leg]
        entry_date = _align_date(metadata["entry"], dates)
        exit_date = _align_date(metadata["exit"], dates)
        entry_notional = scale * (
            abs(float(metadata["size1"])) * float(metadata["entry_price1"])
            + abs(float(metadata["size2"])) * float(metadata["entry_price2"])
        )
        exit_price1 = _price(close, pd.Timestamp(metadata["exit"]), metadata["ticker1"])
        exit_price2 = _price(close, pd.Timestamp(metadata["exit"]), metadata["ticker2"])
        exit_notional = scale * (
            abs(float(metadata["size1"])) * exit_price1
            + abs(float(metadata["size2"])) * exit_price2
        )
        if not math.isfinite(entry_notional) or not math.isfinite(exit_notional):
            raise ValueError(f"non-finite traded notional for {key}")
        entry_by_date[entry_date] += entry_notional
        exit_by_date[exit_date] += exit_notional
        turnover_rows.append(
            {
                "trade_key": key,
                "leg": trade.leg,
                "pair": trade.pair,
                "entry_date": entry_date,
                "exit_date": exit_date,
                "allocation": allocation,
                "scale_to_native_v2_size": scale,
                "native_size1": float(metadata["size1"]),
                "native_size2": float(metadata["size2"]),
                "entry_traded_notional": entry_notional,
                "exit_traded_notional": exit_notional,
                "total_traded_notional": entry_notional + exit_notional,
            }
        )

    turnover = pd.DataFrame(turnover_rows)
    cost_basis = pd.Series(0.0, index=dates, dtype=float)
    for date, value in entry_by_date.items():
        cost_basis.loc[date] += value
    for date, value in exit_by_date.items():
        cost_basis.loc[date] += value
    return turnover, cost_basis


def _net_path(
    daily: pd.DataFrame,
    cost_basis: pd.Series,
    cost_bps: float,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return gross PnL, net PnL, and net equity for one cost scenario."""
    gross_pnl = daily["pnl"].astype(float)
    daily_cost = cost_basis.reindex(gross_pnl.index).fillna(0.0) * (cost_bps / 10_000.0)
    net_pnl = gross_pnl - daily_cost
    net_equity = INITIAL_CAPITAL + net_pnl.cumsum()
    if (net_equity <= 0).any():
        raise ValueError(f"non-positive net equity at {cost_bps} bps")
    return gross_pnl, net_pnl, net_equity


def _returns_from_equity(equity: pd.Series) -> pd.Series:
    previous = equity.shift(1).fillna(INITIAL_CAPITAL)
    return equity.div(previous).sub(1.0)


def _break_even_bps(gross_pnl: float, total_traded_notional: float) -> float:
    """Interpolate the one-way rate where final net PnL reaches zero."""
    if gross_pnl <= 0 or total_traded_notional <= 0:
        return float("nan")
    return float(gross_pnl / total_traded_notional * 10_000.0)


def _scenario_row(
    record: dict,
    turnover: pd.DataFrame,
    cost_basis: pd.Series,
    cost_bps: int,
) -> dict:
    daily = record["daily"]
    gross_pnl, net_pnl, net_equity = _net_path(daily, cost_basis, cost_bps)
    gross_returns = daily["daily_return"].astype(float)
    net_returns = _returns_from_equity(net_equity)
    gross_metrics = replay_metrics(gross_returns)
    net_metrics = replay_metrics(net_returns)
    total_cost = float(cost_basis.sum() * cost_bps / 10_000.0)
    gross_total_pnl = float(gross_pnl.sum())
    turnover_total = float(turnover["total_traded_notional"].sum())
    gross_equity = INITIAL_CAPITAL + gross_pnl.cumsum()
    zero_equity_difference = float(
        np.max(np.abs(gross_equity.to_numpy() - daily["total_capital"].to_numpy()))
    )
    zero_return_difference = float(
        np.max(np.abs(gross_returns.to_numpy() - _returns_from_equity(gross_equity).to_numpy()))
    )
    transaction_cost_pct = (
        float(total_cost / gross_total_pnl * 100.0)
        if abs(gross_total_pnl) > EPSILON
        else float("nan")
    )
    context = record["context"]
    return {
        "window": context["window"],
        "start_index": int(context["start_index"]),
        "start_A": context["start_A"],
        "start_B": context["start_B"],
        "mechanism": record["mechanism"],
        "cost_bps": int(cost_bps),
        "cost_rate": float(cost_bps / 10_000.0),
        "n_days": int(len(daily)),
        "trade_count": int(len(turnover)),
        "gross_annualized_return": float(gross_metrics["ann_ret"]),
        "gross_sharpe": float(gross_metrics["sharpe"]),
        "gross_max_drawdown": float(gross_metrics["mdd"]),
        "gross_cumulative_return": float(gross_equity.iloc[-1] / INITIAL_CAPITAL - 1.0),
        "gross_total_pnl": gross_total_pnl,
        "net_annualized_return": float(net_metrics["ann_ret"]),
        "net_sharpe": float(net_metrics["sharpe"]),
        "net_max_drawdown": float(net_metrics["mdd"]),
        "net_cumulative_return": float(net_equity.iloc[-1] / INITIAL_CAPITAL - 1.0),
        "net_total_pnl": float(net_pnl.sum()),
        "total_transaction_cost": total_cost,
        "transaction_cost_pct_of_gross_pnl": transaction_cost_pct,
        "entry_traded_notional": float(turnover["entry_traded_notional"].sum()),
        "exit_traded_notional": float(turnover["exit_traded_notional"].sum()),
        "total_traded_notional": turnover_total,
        "turnover_multiple_initial_capital": float(turnover_total / INITIAL_CAPITAL),
        "zero_bps_max_equity_difference": zero_equity_difference,
        "zero_bps_max_return_difference": zero_return_difference,
    }


def _aggregate(per_start: pd.DataFrame) -> pd.DataFrame:
    metric_columns = [
        "gross_annualized_return",
        "gross_sharpe",
        "gross_max_drawdown",
        "gross_cumulative_return",
        "gross_total_pnl",
        "net_annualized_return",
        "net_sharpe",
        "net_max_drawdown",
        "net_cumulative_return",
        "net_total_pnl",
        "total_transaction_cost",
        "transaction_cost_pct_of_gross_pnl",
        "entry_traded_notional",
        "exit_traded_notional",
        "total_traded_notional",
        "turnover_multiple_initial_capital",
    ]
    grouped = per_start.groupby(["window", "mechanism", "cost_bps"], sort=True)
    summary = grouped[metric_columns].mean().reset_index()
    summary.insert(3, "n_starts", grouped["start_index"].nunique().to_numpy())
    summary["positive_net_annualized_return_starts"] = grouped[
        "net_annualized_return"
    ].apply(lambda values: int((values > 0).sum())).to_numpy()
    summary["positive_net_sharpe_starts"] = grouped["net_sharpe"].apply(
        lambda values: int((values > 0).sum())
    ).to_numpy()
    summary["minimum_net_annualized_return"] = grouped[
        "net_annualized_return"
    ].min().to_numpy()
    summary["minimum_net_sharpe"] = grouped["net_sharpe"].min().to_numpy()
    return summary


def _break_even_table(per_start: pd.DataFrame) -> pd.DataFrame:
    base = per_start[per_start["cost_bps"].eq(0)].copy()
    rows = []
    for _, row in base.iterrows():
        rows.append(
            {
                "scope": "per_start",
                "window": row["window"],
                "mechanism": row["mechanism"],
                "start_index": int(row["start_index"]),
                "start_A": row["start_A"],
                "start_B": row["start_B"],
                "gross_annualized_return": row["gross_annualized_return"],
                "gross_total_pnl": row["gross_total_pnl"],
                "total_traded_notional": row["total_traded_notional"],
                "break_even_bps": _break_even_bps(
                    row["gross_total_pnl"], row["total_traded_notional"]
                ),
            }
        )
    recent = base[base["window"].eq("recent")]
    for mechanism in MECHANISMS:
        subset = recent[recent["mechanism"].eq(mechanism)]
        for aggregation, function in (("recent_mean", np.mean), ("recent_median", np.median)):
            rows.append(
                {
                    "scope": aggregation,
                    "window": "recent",
                    "mechanism": mechanism,
                    "start_index": "all",
                    "start_A": "all",
                    "start_B": "all",
                    "gross_annualized_return": float(function(subset["gross_annualized_return"])),
                    "gross_total_pnl": float(function(subset["gross_total_pnl"])),
                    "total_traded_notional": float(function(subset["total_traded_notional"])),
                    "break_even_bps": float(
                        function(
                            [
                                _break_even_bps(pnl, turnover)
                                for pnl, turnover in zip(
                                    subset["gross_total_pnl"],
                                    subset["total_traded_notional"],
                                )
                            ]
                        )
                    ),
                }
            )
    return pd.DataFrame(rows)


def _pct(value: float) -> str:
    return f"{float(value) * 100.0:.2f}%"


def _money(value: float) -> str:
    return f"${float(value):,.0f}"


def _write_figures(summary: pd.DataFrame, output_root: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    for metric, ylabel, filename in (
        ("net_sharpe", "Mean net Sharpe", "sharpe_vs_cost.png"),
        ("net_annualized_return", "Mean net annualized return", "annualized_return_vs_cost.png"),
    ):
        figure, axis = plt.subplots(figsize=(7.2, 4.2))
        for window, linestyle in (("recent", "-"), ("historical", "--")):
            for mechanism, marker in (("A", "o"), ("B", "s")):
                subset = summary[
                    summary["window"].eq(window) & summary["mechanism"].eq(mechanism)
                ].sort_values("cost_bps")
                axis.plot(
                    subset["cost_bps"],
                    subset[metric],
                    marker=marker,
                    linestyle=linestyle,
                    label=f"{window} {mechanism}",
                )
        axis.set_xlabel("One-way cost (bps of traded notional)")
        axis.set_ylabel(ylabel)
        axis.set_xticks(list(COST_BPS))
        axis.grid(True, alpha=0.25)
        axis.legend(frameon=False, ncol=2)
        figure.tight_layout()
        figure.savefig(output_root / filename, dpi=150)
        plt.close(figure)


def _write_summary_markdown(
    per_start: pd.DataFrame,
    summary: pd.DataFrame,
    break_even: pd.DataFrame,
    validation: dict,
    output_root: Path,
) -> None:
    lines = [
        "# Transaction-Cost Sensitivity",
        "",
        "This is a small historical sensitivity overlay on the frozen V2-selected",
        "book. It does not change pair selection, sizing, Clean40, signal rules, or",
        "the replay mechanisms.",
        "",
        "## Frozen Strategy",
        "",
        f"- Leg A: `{V2_LEG_A}`",
        f"- Leg B: `{V2_LEG_B}`",
        "- Sizing: V2 `gross_exposure`",
        "- Clean40: 84-day lookback, 0.40 step, 10%--90% bounds, 50/50 initial weight",
        "- Replay: Mechanisms A and B",
        "- Periods: five existing recent starts and one historical control",
        "",
        "## Cost Convention",
        "",
        "Costs are one-way all-in basis points of traded notional. Native V2 share",
        "quantities and recorded entry prices are scaled by the frozen replay",
        "allocation. Exit notional uses the preserved exit-date close snapshot",
        "because exact exit execution prices are not recorded. This is a historical",
        "sensitivity proxy, not a live execution or broker model.",
        "",
        "Scenarios are 0, 5, 10, and 20 bps. The 0 bps row is the gross baseline.",
        "",
        "## Zero-Bps Reconciliation",
        "",
        f"- Runs checked: `{validation['run_count']}`",
        f"- Maximum equity-path difference: `{validation['max_equity_difference']:.3e}`",
        f"- Maximum daily-return difference: `{validation['max_return_difference']:.3e}`",
        f"- Final equity difference: `{validation['max_final_equity_difference']:.3e}`",
        f"- Status: **{validation['status']}**",
        "",
        "## Turnover",
        "",
        "| Window | Mechanism | Mean trades | Mean traded notional | Mean turnover / initial capital |",
        "|---|---|---:|---:|---:|",
    ]
    turnover = (
        per_start[per_start["cost_bps"].eq(0)]
        .groupby(["window", "mechanism"], as_index=False)[
            ["trade_count", "total_traded_notional", "turnover_multiple_initial_capital"]
        ]
        .mean()
    )
    for row in turnover.itertuples(index=False):
        lines.append(
            f"| {row.window} | {row.mechanism} | {row.trade_count:.1f} | "
            f"{_money(row.total_traded_notional)} | {row.turnover_multiple_initial_capital:.2f}x |"
        )
    lines.extend(
        [
            "",
            "## Recent Aggregate",
            "",
            "Recent rows are means across the same five starts used by the public",
            "research. They are not a concatenated overlapping return series.",
            "",
            "| Cost | A net annualized return | A net Sharpe | B net annualized return | B net Sharpe | Positive A/B starts |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
    )
    recent = summary[summary["window"].eq("recent")]
    for cost_bps in COST_BPS:
        a = recent[(recent["mechanism"] == "A") & (recent["cost_bps"] == cost_bps)].iloc[0]
        b = recent[(recent["mechanism"] == "B") & (recent["cost_bps"] == cost_bps)].iloc[0]
        lines.append(
            f"| {cost_bps} | {_pct(a.net_annualized_return)} | {a.net_sharpe:.3f} | "
            f"{_pct(b.net_annualized_return)} | {b.net_sharpe:.3f} | "
            f"{int(a.positive_net_annualized_return_starts)}/"
            f"{int(b.positive_net_annualized_return_starts)} |"
        )
    lines.extend(
        [
            "",
            "## Historical Control",
            "",
            "| Cost | A net annualized return | A net Sharpe | B net annualized return | B net Sharpe |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    historical = summary[summary["window"].eq("historical")]
    for cost_bps in COST_BPS:
        a = historical[(historical["mechanism"] == "A") & (historical["cost_bps"] == cost_bps)].iloc[0]
        b = historical[(historical["mechanism"] == "B") & (historical["cost_bps"] == cost_bps)].iloc[0]
        lines.append(
            f"| {cost_bps} | {_pct(a.net_annualized_return)} | {a.net_sharpe:.3f} | "
            f"{_pct(b.net_annualized_return)} | {b.net_sharpe:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Cost Burden",
            "",
            "The cost percentage is total transaction cost divided by gross PnL for",
            "the same start and mechanism.",
            "",
            "| Window | Mechanism | 5 bps cost / gross PnL | 10 bps cost / gross PnL | 20 bps cost / gross PnL |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for window in WINDOWS:
        for mechanism in MECHANISMS:
            subset = per_start[
                per_start["window"].eq(window) & per_start["mechanism"].eq(mechanism)
            ]
            values = []
            for cost_bps in (5, 10, 20):
                values.append(
                    subset[subset["cost_bps"].eq(cost_bps)][
                        "transaction_cost_pct_of_gross_pnl"
                    ].mean()
                )
            lines.append(
                f"| {window} | {mechanism} | {values[0]:.2f}% | {values[1]:.2f}% | {values[2]:.2f}% |"
            )
    lines.extend(
        [
            "",
            "## Absolute Cost",
            "",
            "| Window | Mechanism | Mean cost at 5 bps | Mean cost at 10 bps | Mean cost at 20 bps |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for window in WINDOWS:
        for mechanism in MECHANISMS:
            subset = per_start[
                per_start["window"].eq(window) & per_start["mechanism"].eq(mechanism)
            ]
            values = [
                subset[subset["cost_bps"].eq(cost_bps)][
                    "total_transaction_cost"
                ].mean()
                for cost_bps in (5, 10, 20)
            ]
            lines.append(
                f"| {window} | {mechanism} | {_money(values[0])} | "
                f"{_money(values[1])} | {_money(values[2])} |"
            )
    lines.extend(
        [
            "",
            "## Approximate Break-Even Cost",
            "",
            "Break-even is the one-way rate at which final net PnL reaches zero,",
            "reported as an approximate interpolation from gross PnL and total",
            "traded notional.",
            "",
            "| Window | Mechanism | Per-start range | Recent mean | Recent median |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for window in WINDOWS:
        for mechanism in MECHANISMS:
            per = break_even[
                (break_even["scope"] == "per_start")
                & break_even["window"].eq(window)
                & break_even["mechanism"].eq(mechanism)
            ]
            recent_mean = break_even[
                (break_even["scope"] == "recent_mean")
                & break_even["mechanism"].eq(mechanism)
            ]
            recent_median = break_even[
                (break_even["scope"] == "recent_median")
                & break_even["mechanism"].eq(mechanism)
            ]
            if window == "recent":
                mean_text = (
                    f"{recent_mean['break_even_bps'].iloc[0]:.1f} bps"
                    if len(recent_mean)
                    else "n/a"
                )
                median_text = (
                    f"{recent_median['break_even_bps'].iloc[0]:.1f} bps"
                    if len(recent_median)
                    else "n/a"
                )
            else:
                mean_text = "n/a"
                median_text = "n/a"
            lines.append(
                f"| {window} | {mechanism} | "
                f"{per['break_even_bps'].min():.1f}--{per['break_even_bps'].max():.1f} bps | "
                f"{mean_text} | {median_text} |"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This overlay does not retune the candidate after observing costs. The",
            "gross result is the 0 bps row; the 5, 10, and 20 bps rows show the",
            "mechanical deterioration from the assumed traded-notional friction.",
            "",
        ]
    )
    for window in WINDOWS:
        subset = summary[summary["window"].eq(window) & summary["cost_bps"].eq(20)]
        positive = int(subset["positive_net_annualized_return_starts"].sum())
        total = int(subset["n_starts"].sum())
        lines.append(
            f"At 20 bps, {positive}/{total} {window} mechanism-start combinations "
            "have positive net annualized return."
        )
    lines.extend(
        [
            "",
            "The study therefore measures cost sensitivity, not live implementability.",
            "The next stage is forward paper testing with execution telemetry; no",
            "historical strategy optimization follows from this overlay.",
            "",
            "## Artifacts",
            "",
            "- `tca_per_start.csv`",
            "- `tca_summary.csv`",
            "- `tca_break_even.csv`",
            "- `sharpe_vs_cost.png`",
            "- `annualized_return_vs_cost.png`",
        ]
    )
    (output_root / "tca_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(output_root: Path = OUTPUT_ROOT, make_figures: bool = True) -> dict:
    output_root.mkdir(parents=True, exist_ok=True)
    book = _frozen_book()
    configuration = _baseline_configuration()
    per_start_rows = []
    validation_rows = []

    for window in WINDOWS:
        start_count = RECENT_START_COUNT if window == "recent" else 1
        for start_index in range(start_count):
            context = _load_context(book, window, start_index)
            records = {
                mechanism: _trace_record(context, configuration, mechanism)
                for mechanism in MECHANISMS
            }
            for mechanism, record in records.items():
                turnover, cost_basis = _trade_turnover(record)
                for cost_bps in COST_BPS:
                    per_start_rows.append(
                        _scenario_row(record, turnover, cost_basis, cost_bps)
                    )
                zero = per_start_rows[-len(COST_BPS)]
                validation_rows.append(
                    {
                        "window": window,
                        "start_index": start_index,
                        "mechanism": mechanism,
                        "max_equity_difference": zero["zero_bps_max_equity_difference"],
                        "max_return_difference": zero["zero_bps_max_return_difference"],
                        "final_equity_difference": abs(
                            zero["net_total_pnl"] - zero["gross_total_pnl"]
                        ),
                    }
                )

    per_start = pd.DataFrame(per_start_rows)
    summary = _aggregate(per_start)
    break_even = _break_even_table(per_start)
    validation_frame = pd.DataFrame(validation_rows)
    validation = {
        "status": "pass"
        if (
            validation_frame["max_equity_difference"].max() <= 1e-6
            and validation_frame["max_return_difference"].max() <= 1e-12
            and validation_frame["final_equity_difference"].max() <= 1e-6
        )
        else "fail",
        "run_count": int(len(validation_frame)),
        "max_equity_difference": float(validation_frame["max_equity_difference"].max()),
        "max_return_difference": float(validation_frame["max_return_difference"].max()),
        "max_final_equity_difference": float(
            validation_frame["final_equity_difference"].max()
        ),
    }
    if validation["status"] != "pass":
        raise AssertionError(f"0 bps gross replay reconciliation failed: {validation}")

    per_start.to_csv(output_root / "tca_per_start.csv", index=False)
    summary.to_csv(output_root / "tca_summary.csv", index=False)
    break_even.to_csv(output_root / "tca_break_even.csv", index=False)
    if make_figures:
        _write_figures(summary, output_root)
    _write_summary_markdown(per_start, summary, break_even, validation, output_root)
    print(f"TCA validation: {validation['status']}")
    print(f"Wrote {output_root}")
    return validation


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args(argv)
    run(args.output, make_figures=not args.no_figures)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
