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
    'dollar_neutral': False,
    'max_pairs_per_fold': 5,
    'lock_hr_for_zscore': True, 
    'lock_std_for_zscore': True, 
}

# =================================================================
# MARGIN SETTINGS (opt-in; behavior='off' preserves existing runs)
# =================================================================
# Margin is checked per-position on current market value, so it is
# direction-agnostic and handles non-dollar-neutral (beta-hedged)
# pairs: s2 leg = notional, s1 leg = |hr| * notional (median |hr|
# ~0.5, ~12% of pairs have negative hr -> same-side book).
#   required = ml * long_value + ms * short_value
# Per-ticker overrides can be supplied via margin_rates
#   {TICKER: {'long': x, 'short': y}} (falls back to globals).
MARGIN_SETTINGS = {
    'margin_long': 0.50,          # initial margin on long positions (frac of market value)
    'margin_short': 0.50,         # initial margin on short positions
    'maintenance_long': 0.25,     # maintenance margin, long (FINRA minimums)
    'maintenance_short': 0.30,    # maintenance margin, short
    'margin_behavior': 'off',     # off | report | reject
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
OUTPUT_DIR = "diagnosis"
TRADE_LOGS_DIR = os.path.join(OUTPUT_DIR, "trade_logs")
EQUITY_CURVES_DIR = os.path.join(OUTPUT_DIR, "oos_equity_curves")

# =================================================================
# WINDOW-KEYED POOLS (universe-free superset caches)
# =================================================================
# Pools are keyed by bare sel_start (window method encoded by file split).
# Universe / sector / p-value / divergence filtering happens at load time.
# Routing is by selection window only: 2m -> the 2m pool, 12m -> the 12m
# pool. The 12m pool covers both historical (2015-2020) and recent
# (2023-2025) windows in one file.
POOL_DIR = os.path.join("research", "cache")
POOL_12M = os.path.join(POOL_DIR, "sp500_12m.pkl")
POOL_2M = os.path.join(POOL_DIR, "sp500_2m.pkl")
POOL_CORE = os.path.join(POOL_DIR, "core_2m.pkl")


def pool_path_for(sel_months: int, universe: str = None, cross_sector: bool = True, profile: str = None) -> str:
    """
    Resolve the pool file for a selection window and run context (coint mode).

    Routing is driven by the selection window:
    - 12m -> sp500_12m.pkl (covers 2015-2020 and 2023-2025).
    - 2m  -> sp500_2m.pkl for sp500/golden runs; core_2m.pkl for core-universe
      baseline runs (kept only to recreate the historical 08_CLEAN runs).
    """
    if sel_months == 12:
        return POOL_12M
    if profile == "golden":
        return POOL_2M
    if universe == "sp500":
        return POOL_2M
    return POOL_CORE

# =================================================================
# PROFILES — Named configurations for different strategy regimes
# =================================================================
# Use: python run_backtest.py --profile <name>
# Individual CLI flags override profile values.
PROFILES = {
    'golden': {
        'STRATEGY_PARAMS': STRATEGY_PARAMS,
        'BACKTEST_SETTINGS': BACKTEST_SETTINGS,
        'FOLD_SETTINGS': {
            **FOLD_SETTINGS,
            'slide_months': 1,
        },
        'universe': 'core',
        'cross_sector': True,
        'fixed_params': False,
        'return_divergence': 0.10,
        'earnings_screen': True,
        'earnings_block_days': 7,
        'cache_dir': 'research/cache_golden',
    },
    'baseline': {
        'STRATEGY_PARAMS': STRATEGY_PARAMS,
        'BACKTEST_SETTINGS': BACKTEST_SETTINGS,
        'FOLD_SETTINGS': FOLD_SETTINGS,
        'universe': 'core',
        'cross_sector': False,
        'fixed_params': False,
        'return_divergence': None,
        'earnings_screen': False,
        'earnings_block_days': 0,
        'cache_dir': None,
    },
    'huck2015': {
        'STRATEGY_PARAMS': {
            'entry_z': 2.0,
            'exit_z': 0.1,
            'resid_val': 90,
            'z_m': 0.5,
            'hr_thresh': 0.80,
            'stop_z': 10.0,
            'max_holding_days': 999,
            'pvalue_threshold': 0.05,
        },
        'BACKTEST_SETTINGS': {
            'initial_cash': 1000000.0,
            'pct_per_pair': 0.05,
            'log_space': False,
            'max_pairs_per_fold': 20,
            'lock_hr_for_zscore': True,
            'lock_std_for_zscore': True,
            'dollar_neutral': True,
        },
        'FOLD_SETTINGS': {
            'sel_months': 12,
            'opt_months': 0,
            'test_months': 6,
            'slide_months': 1,
        },
        'universe': 'sp500',
        'cross_sector': True,
        'fixed_params': True,
        'return_divergence': 0.10,
        'earnings_screen': False,
        'earnings_block_days': 0,
        'cache_dir': 'research/cache',
    },
}
