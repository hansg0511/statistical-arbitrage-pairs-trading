import os

# =================================================================
# STRATEGY PARAMETERS (The "Golden Regime")
# =================================================================
# Derived from marginal sensitivity and Bayesian optimization
STRATEGY_PARAMS = {
    'entry_z': 2.20,
    'exit_z': 1.00,
    'resid_val': 90,
    'z_m': 0.5,
    'hr_thresh': 0.80,
    'stop_z': 4.5,
    'max_holding_days': 15,
    'pvalue_threshold': 0.05,
}

# =================================================================
# BACKTEST ENVIRONMENT SETTINGS
# =================================================================
BACKTEST_SETTINGS = {
    'initial_cash': 1000000.0,
    'pct_per_pair': 0.18, # 18% per pair (5 pairs total)
    'log_space': True,
    'max_pairs_per_fold': 5,
    'lock_hr_for_zscore': True, 
    'lock_std_for_zscore': True, 
}

# =================================================================
# WALK-FORWARD ARCHITECTURE
# =================================================================
FOLD_SETTINGS = {
    'sel_months': 2,
    'opt_months': 0, # Skip optimization in default run
    'test_months': 3,
    'slide_months': 3,
}

# =================================================================
# PATHS
# =================================================================
OUTPUT_DIR = "results"
TRADE_LOGS_DIR = os.path.join(OUTPUT_DIR, "trade_logs")
EQUITY_CURVES_DIR = os.path.join(OUTPUT_DIR, "oos_equity_curves")
