from types import SimpleNamespace

import numpy as np
import pandas as pd

from research.run_experiment import execute_folds
from src.pair_cache import PoolCache


def _args(output):
    return SimpleNamespace(
        name="test",
        output=str(output),
        cross_sector=True,
        pvalue=0.05,
        log_space=True,
        return_divergence=None,
        max_pairs=1,
        resid_val=10,
        z_m=0.5,
        fixed_params=False,
        initial_cash=100_000.0,
        broker_leverage=1.0,
        dollar_neutral=False,
        pct_per_pair=0.10,
        entry_z=2.2,
        exit_z=1.0,
        stop_z=4.5,
        max_holding_days=15,
        hr_thresh=0.8,
        verbose=False,
        earnings_screen=False,
        earnings_block_days=0,
        margin_behavior="off",
        margin_long=0.5,
        margin_short=0.5,
        maintenance_long=0.25,
        maintenance_short=0.30,
        margin_rates_dict={},
    )


def _inputs(tmp_path):
    dates = pd.bdate_range("2020-01-01", "2020-05-29")
    x = np.linspace(0, 0.15, len(dates))
    prices = pd.DataFrame(
        {
            "AAA": 100 * np.exp(x),
            "BBB": 100 * np.exp(x + 0.02 * np.sin(np.arange(len(dates)) / 3)),
        },
        index=dates,
    )
    pool = PoolCache(tmp_path / "pool.pkl", {"return_divergence_applied": True})
    pool.set(
        "2020-01-01",
        pd.DataFrame(
            [
                {
                    "pair": "AAA-BBB",
                    "cointegration_pvalue_log": 0.01,
                    "half_life_log": 5.0,
                    "hedge_ratio_log": 1.0,
                    "intercept_log": 0.0,
                }
            ]
        ),
    )
    pool.save()
    fold = (
        pd.Timestamp("2020-01-01").date(),
        pd.Timestamp("2020-01-31").date(),
        pd.Timestamp("2020-02-01").date(),
        pd.Timestamp("2020-02-01").date(),
        pd.Timestamp("2020-02-03").date(),
        pd.Timestamp("2020-04-30").date(),
    )
    return prices, pool.path, fold


def _normalize(result):
    (summary, logs, daily_returns, active, rejected, marks, signal, margin,
     exposure, selected, _) = result
    return {
        "summary": summary,
        "logs": logs,
        "returns": [(str(row["date"]), float(row["pnl_pct"])) for row in daily_returns],
        "active": active,
        "rejected": rejected,
        "marks": marks,
        "signal": signal,
        "margin": margin,
        "exposure": exposure,
        "selected": selected,
    }


def test_serial_and_parallel_fold_execution_are_equivalent(tmp_path):
    prices, pool_path, fold = _inputs(tmp_path)
    sectors = {"Tech": ["AAA", "BBB"]}
    args = _args(tmp_path / "out")

    serial, serial_failed = execute_folds(
        prices, args, ["AAA", "BBB"], sectors, "test", pool_path, None, [fold], 1
    )
    parallel, parallel_failed = execute_folds(
        prices, args, ["AAA", "BBB"], sectors, "test", pool_path, None, [fold], 2
    )

    assert serial_failed == []
    assert parallel_failed == []
    assert _normalize(serial[0]) == _normalize(parallel[0])
