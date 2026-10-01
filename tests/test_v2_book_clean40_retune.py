import pandas as pd

from research.run_v2_book_clean40_retune import (
    BASELINE_NAME,
    CONFIGURATIONS,
    _lattice_aligned,
    _select_dynamic,
)


def test_clean40_grid_only_contains_lattice_aligned_dynamic_bounds():
    assert len(CONFIGURATIONS) == 41
    assert BASELINE_NAME in {config["name"] for config in CONFIGURATIONS}
    assert sum(config["kind"] == "dynamic" for config in CONFIGURATIONS) == 40
    assert all(
        config["lattice_aligned"]
        for config in CONFIGURATIONS
        if config["kind"] == "dynamic"
    )
    assert _lattice_aligned(0.2, 0.3, 0.7)
    assert not _lattice_aligned(0.2, 0.4, 0.6)


def test_dynamic_selection_keeps_static_control_in_aggregate():
    rows = []
    for name, kind, floor, median, recent, historical, drawdown, turnover in (
        ("dynamic_best", "dynamic", 0.80, 0.85, 1.10, 0.82, -0.10, 0.20),
        ("dynamic_neighbor", "dynamic", 0.77, 0.80, 1.05, 0.79, -0.09, 0.15),
        ("static_50_50", "static", 0.90, 0.90, 1.20, 0.95, -0.20, 0.00),
    ):
        rows.append(
            {
                "configuration": name,
                "configuration_kind": kind,
                "lookback_days": 84 if kind == "dynamic" else None,
                "step": 0.4 if kind == "dynamic" else 0.0,
                "weight_min": 0.1 if kind == "dynamic" else 0.5,
                "weight_max": 0.9 if kind == "dynamic" else 0.5,
                "bounds_label": "10_90" if kind == "dynamic" else "50_50",
                "lattice_aligned": True,
                "mechanism": "aggregate",
                "robust_floor": floor,
                "robust_median_floor": median,
                "recent_mean_sharpe": recent,
                "historical_mean_sharpe": historical,
                "worst_max_drawdown": drawdown,
                "mean_annualized_turnover_ratio": turnover,
            }
        )

    selected, aggregate = _select_dynamic(pd.DataFrame(rows))

    assert selected["configuration"] == "dynamic_best"
    assert selected["plateau_count"] == 2
    assert set(aggregate["configuration"]) == {
        "dynamic_best",
        "dynamic_neighbor",
        "static_50_50",
    }
    assert not bool(
        aggregate.loc[
            aggregate["configuration"].eq("static_50_50"), "plateau_member"
        ].iloc[0]
    )
