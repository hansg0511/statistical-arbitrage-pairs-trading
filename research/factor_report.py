"""Fama-French diagnostics for the locked selected book.

The published path uses the tracked factor snapshot. Use ``--live-factors`` only
for exploratory comparisons against the current external data release.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

if __package__ in {None, ""}:  # Support both `python research/...` and `python -m ...`.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.run_combined_backtest import (
    DEFAULT_CONFIG,
    configured_series,
    load_selected_book_config,
    metrics,
)
from src.fama_french import FamaFrenchFetcher


DEFAULT_FACTOR_SNAPSHOT = (
    Path(__file__).resolve().parents[1]
    / "results"
    / "final"
    / "factors"
    / "ff_daily_2015_2025.csv"
)


def _run_parameters(config):
    bounds = config["momentum"]["weight_bounds"]
    return {
        "capital": config["book"]["initial_capital"],
        "pct": config["book"]["pct_per_pair"],
        "lookback": config["momentum"]["lookback_days"],
        "step": config["momentum"]["step"],
        "clamp": [bounds["min"], bounds["max"]],
    }


def build_factor_rows(
    config_path=DEFAULT_CONFIG,
    fetcher=None,
    factor_snapshot=DEFAULT_FACTOR_SNAPSHOT,
):
    """Run daily FF3 + Momentum + ST_Reversal regressions for both mechanisms."""
    config = load_selected_book_config(config_path)
    params = _run_parameters(config)
    fetcher = fetcher or FamaFrenchFetcher(
        frequency="daily", snapshot_path=str(factor_snapshot)
    )
    rows = []
    for window in ("historical", "recent"):
        starts = config["event_replay"]["windows"][window]["starts"]
        for start_idx in range(len(starts)):
            for mechanism in ("A", "B"):
                series, *_ = configured_series(
                    config, window, mechanism, start_idx, **params
                )
                result = fetcher.regress(
                    series, include_momentum=True, include_st_rev=True
                )
                row = {
                    "window": window,
                    "start_index": start_idx,
                    "mechanism": mechanism,
                    "sharpe": float(metrics(series)["sharpe"]),
                    "alpha_ann": float(result.alpha_ann),
                    "alpha_tstat": float(result.alpha_tstat),
                    "alpha_pval": float(result.alpha_pval),
                    "rsquared": float(result.rsquared),
                    "adj_rsquared": float(result.adj_rsquared),
                    "n_obs": int(result.n_obs),
                }
                for _, loading in result.loadings.iterrows():
                    factor = loading["factor"]
                    row[f"{factor}_beta"] = float(loading["beta"])
                    row[f"{factor}_pval"] = float(loading["pval"])
                rows.append(row)
    return pd.DataFrame(rows)


def write_report(rows, output_path):
    """Write a concise, auditable factor-regression table."""
    lines = [
        "# Selected Book Factor Diagnostics",
        "",
        "Daily FF3 + Momentum + ST_Reversal regressions with HAC standard errors.",
        "Alpha is annualized by multiplying the daily intercept by 252. Recent",
        "values cover the five configured start pairs; historical has one start.",
        "A significant factor loading is not evidence of strategy alpha.",
        "",
        "| Window | Start | Mech | Alpha | p-value | Sharpe | R2 | N |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in rows.iterrows():
        lines.append(
            "| %s | %d | %s | %+.2f%% | %.3f | %.2f | %.3f | %d |"
            % (
                row["window"],
                row["start_index"] + 1,
                row["mechanism"],
                row["alpha_ann"] * 100,
                row["alpha_pval"],
                row["sharpe"],
                row["rsquared"],
                row["n_obs"],
            )
        )
    lines.append("")
    lines.append("## Factor Loadings")
    lines.append("")
    lines.append("Betas are followed by HAC p-values in parentheses.")
    lines.append("")
    lines.append("| Window | Start | Mech | Mkt-RF | SMB | HML | Mom | ST_Rev |")
    lines.append("|---|---:|---|---:|---:|---:|---:|---:|")
    for _, row in rows.iterrows():
        cells = []
        for factor in ("Mkt-RF", "SMB", "HML", "Mom", "ST_Rev"):
            cells.append(
                "%.3f (%.3f)"
                % (row.get(f"{factor}_beta", float("nan")), row.get(f"{factor}_pval", float("nan")))
            )
        lines.append(
            "| %s | %d | %s | %s |"
            % (row["window"], row["start_index"] + 1, row["mechanism"], " | ".join(cells))
        )
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output", default="results/final/factors/selected_book.md")
    parser.add_argument("--csv", default="results/final/factors/selected_book.csv")
    parser.add_argument("--factor-snapshot", default=str(DEFAULT_FACTOR_SNAPSHOT))
    parser.add_argument(
        "--live-factors",
        action="store_true",
        help="fetch current Fama-French data instead of using the pinned snapshot",
    )
    args = parser.parse_args(argv)
    fetcher = FamaFrenchFetcher(frequency="daily") if args.live_factors else None
    rows = build_factor_rows(
        args.config,
        fetcher=fetcher,
        factor_snapshot=args.factor_snapshot,
    )
    Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
    rows.to_csv(args.csv, index=False)
    write_report(rows, args.output)
    print(f"Wrote {args.output}")
    print(f"Wrote {args.csv}")


if __name__ == "__main__":
    main()
