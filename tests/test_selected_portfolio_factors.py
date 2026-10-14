from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from research.run_selected_portfolio_factors import calculate, fit_context, load_inputs

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_factor_regression_integrity():
    daily, factors = load_inputs()
    assert len(daily) == 7026
    assert int((daily["daily_return"] == 0).sum()) == 36
    assert factors["date"].min() <= daily["date"].min()
    assert factors["date"].max() >= daily["date"].max()
    result = calculate()
    assert len(result) == 24
    assert sorted(result["model"].unique()) == ["ff3_mom_strev", "market_only"]
    expanded = result[result["model"] == "ff3_mom_strev"]
    assert len(expanded) == 12
    assert (expanded["alpha_ci_low"] < 0).all()
    assert (expanded["alpha_ci_high"] > 0).all()
    assert (expanded["ST_Rev_beta"] > 0).all()
    assert (expanded["ST_Rev_pval"] < 0.05).all()
    assert np.isclose(
        expanded[(expanded["window"] == "historical") &
                 (expanded["mechanism"] == "A")]["alpha_ann"].iloc[0],
        0.014393205799, atol=1e-9,
    )


def test_zero_return_days_remain_in_regression():
    daily, factors = load_inputs()
    group = daily[(daily["window"] == "recent") &
                  (daily["start_index"] == 0) &
                  (daily["mechanism"] == "A")]
    result = fit_context(group, factors, "ff3_mom_strev")
    assert result["n_obs"] == 496
    assert result["zero_return_days"] == 2


def test_missing_factor_date_is_rejected():
    daily, factors = load_inputs()
    group = daily[(daily["window"] == "historical") &
                  (daily["start_index"] == 0) &
                  (daily["mechanism"] == "A")]
    missing_date = group["date"].min()
    incomplete = factors[factors["date"] != missing_date]
    with pytest.raises(ValueError, match="does not cover"):
        fit_context(group, incomplete, "ff3_mom_strev")
