"""Frozen portfolio factor diagnostics from committed daily return and factor files.

This is a descriptive report on the already-selected research portfolio. It must
not change portfolio selection, execution rules, historical runs, or allocator.

Run:
    python research/run_selected_portfolio_factors.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RETURNS = ROOT / "results/v2_book_clean40_retune/baseline_daily.csv"
DEFAULT_FACTORS = ROOT / "results/final/factors/ff_daily_2015_2025.csv"
DEFAULT_OUTPUT = ROOT / "results/factor_exposure/selected_portfolio_factor_regressions.csv"
SELECTED_CONFIG = "lb84_s0.40_b0.10_0.90"
FACTOR_COLS = ("Mkt-RF", "SMB", "HML", "Mom", "ST_Rev")
MODELS = {"market_only": ("Mkt-RF",), "ff3_mom_strev": FACTOR_COLS}


def load_inputs(returns_path: Path = DEFAULT_RETURNS, factors_path: Path = DEFAULT_FACTORS):
    daily = pd.read_csv(returns_path, parse_dates=["date"])
    expected_cols = {"configuration", "window", "start_index", "mechanism", "date", "daily_return"}
    if not expected_cols.issubset(daily.columns):
        raise ValueError(f"Missing return columns: {sorted(expected_cols - set(daily.columns))}")
    if daily.empty or set(daily["configuration"]) != {SELECTED_CONFIG}:
        raise ValueError("Expected only the frozen selected allocator configuration")
    daily["daily_return"] = pd.to_numeric(daily["daily_return"], errors="raise")
    if not np.isfinite(daily["daily_return"].to_numpy()).all():
        raise ValueError("Nonfinite portfolio returns")
    identity = ["window", "start_index", "mechanism", "date"]
    if daily.duplicated(identity).any():
        raise ValueError("Duplicate portfolio observation for context/date")
    contexts = set(
        (str(window), int(idx), str(mech))
        for window, idx, mech in daily[["window", "start_index", "mechanism"]].itertuples(index=False, name=None)
    )
    expected = {
        ("historical", 0, mech) for mech in ("A", "B")
    } | {
        ("recent", idx, mech) for idx in range(5) for mech in ("A", "B")
    }
    if contexts != expected:
        raise ValueError(f"Unexpected portfolio contexts: missing={expected - contexts}, extra={contexts - expected}")

    factors = pd.read_csv(factors_path, parse_dates=["date"])
    required_factors = {"date", "RF", *FACTOR_COLS}
    if not required_factors.issubset(factors.columns):
        raise ValueError(f"Missing factor columns: {sorted(required_factors - set(factors.columns))}")
    if factors["date"].duplicated().any():
        raise ValueError("Duplicate factor date")
    for col in ("RF", *FACTOR_COLS):
        factors[col] = pd.to_numeric(factors[col], errors="raise")
    if not np.isfinite(factors[["RF", *FACTOR_COLS]].to_numpy()).all():
        raise ValueError("Nonfinite factor values")
    return daily, factors


def fit_context(frame: pd.DataFrame, factors: pd.DataFrame, model_name: str) -> dict:
    """Fit on all dated account returns, including flat/zero-return days."""
    columns = list(MODELS[model_name])
    aligned = frame.merge(
        factors[["date", "RF", *columns]], on="date", how="left",
        validate="one_to_one", sort=True,
    )
    if aligned[["RF", *columns]].isna().any().any():
        raise ValueError("Factor snapshot does not cover every selected portfolio date")
    if len(aligned) < 30:
        raise ValueError("Too few daily observations for factor regression")
    y = (aligned["daily_return"] - aligned["RF"]).astype(float)
    X = sm.add_constant(aligned[columns].astype(float), has_constant="add")
    # Identical HAC lag convention to the earlier pinned regression, but do not
    # discard zero daily account returns as the earlier helper did.
    lag = int(len(aligned) ** 0.25)
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": lag})
    ci = fit.conf_int(alpha=0.05).loc["const"]
    row = {
        "model": model_name,
        "window": str(frame["window"].iloc[0]),
        "start_index": int(frame["start_index"].iloc[0]),
        "mechanism": str(frame["mechanism"].iloc[0]),
        "first_date": aligned["date"].min().date().isoformat(),
        "last_date": aligned["date"].max().date().isoformat(),
        "n_obs": int(len(aligned)),
        "zero_return_days": int((aligned["daily_return"] == 0).sum()),
        "hac_maxlags": lag,
        "alpha_ann": float(fit.params["const"] * 252.0),
        "alpha_ann_se": float(fit.bse["const"] * 252.0),
        "alpha_pval": float(fit.pvalues["const"]),
        "alpha_ci_low": float(ci.iloc[0] * 252.0),
        "alpha_ci_high": float(ci.iloc[1] * 252.0),
        "r_squared": float(fit.rsquared),
    }
    for factor in FACTOR_COLS:
        row[f"{factor}_beta"] = float(fit.params[factor]) if factor in columns else np.nan
        row[f"{factor}_pval"] = float(fit.pvalues[factor]) if factor in columns else np.nan
    return row


def calculate(returns_path: Path = DEFAULT_RETURNS, factors_path: Path = DEFAULT_FACTORS) -> pd.DataFrame:
    daily, factors = load_inputs(returns_path, factors_path)
    rows = []
    for (window, start_index, mechanism), group in daily.groupby(
        ["window", "start_index", "mechanism"], sort=True
    ):
        group = group.sort_values("date")
        for model in MODELS:
            rows.append(fit_context(group, factors, model))
    result = pd.DataFrame(rows)
    result = result.sort_values(
        ["window", "start_index", "mechanism", "model"]
    ).reset_index(drop=True)
    if len(result) != 24 or result["n_obs"].sum() != 2 * len(daily):
        raise AssertionError("Incomplete model results")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--returns", type=Path, default=DEFAULT_RETURNS)
    parser.add_argument("--factors", type=Path, default=DEFAULT_FACTORS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    results = calculate(args.returns, args.factors)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(args.output, index=False, float_format="%.12g")
    print(f"Wrote {len(results)} regression rows to {args.output}")
    print("Expanded-model alpha p < 0.05:", int(
        ((results["model"] == "ff3_mom_strev") & (results["alpha_pval"] < 0.05)).sum()
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
