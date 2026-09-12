"""Small set of defaults shared by the research engine and CLI."""

import os


STRATEGY_PARAMS = {
    "entry_z": 2.20,
    "exit_z": 1.00,
    "resid_val": 90,
    "z_m": 0.5,
    "hr_thresh": 0.80,
    "stop_z": 4.5,
    "max_holding_days": 15,
    "pvalue_threshold": 0.05,
}

BACKTEST_SETTINGS = {
    "initial_cash": 1_000_000.0,
    "pct_per_pair": 0.18,
    "pair_sizing_mode": "reference_leg",
    "log_space": True,
    "dollar_neutral": False,
    "max_pairs_per_fold": 5,
}

MARGIN_SETTINGS = {
    "margin_long": 0.50,
    "margin_short": 0.50,
    "maintenance_long": 0.25,
    "maintenance_short": 0.30,
    "margin_behavior": "off",
}

FOLD_SETTINGS = {
    "sel_months": 2,
    "test_months": 3,
    "slide_months": 3,
}

OUTPUT_DIR = os.path.join("results", "runs")
TRADE_LOGS_DIR = os.path.join(OUTPUT_DIR, "trade_logs")
EQUITY_CURVES_DIR = os.path.join(OUTPUT_DIR, "oos_equity_curves")

POOL_DIR = os.path.join("data", "pools")
POOL_12M = os.path.join(POOL_DIR, "sp500_12m.pkl")
POOL_2M = os.path.join(POOL_DIR, "sp500_2m.pkl")
POOL_CORE = os.path.join(POOL_DIR, "core_2m.pkl")


def pool_path_for(sel_months: int, universe: str | None = None) -> str:
    """Resolve the deterministic pool file for a selection window."""
    if sel_months == 12:
        return POOL_12M
    if universe == "sp500":
        return POOL_2M
    return POOL_CORE
