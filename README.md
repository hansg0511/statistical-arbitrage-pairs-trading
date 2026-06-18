# Algorithmic Pairs Trading System

A statistical arbitrage strategy trading mean-reverting spreads on same-sector S&P 500 mega-cap equity pairs. Built and validated independently with a focus on methodological rigour and robustness over raw performance optimisation.

---

## Results (Out-of-Sample: 2024–2026)

| Metric | Value |
|---|---|
| Sharpe Ratio | 0.65 |
| Win Rate | 63.2% |
| Avg Max Drawdown (per fold) | 1.7% |
| Total Trades | 38 |
| Avg Capital Utilization | 8.0% |
| **Market Beta (SPY)** | **0.003** |
| **Correlation (SPY)** | **0.011** |

*Capital utilization reflects conservative pair selection criteria — pairs must pass cointegration testing each fold before capital is deployed.*

---

## Market Neutrality & Beta Analysis

A key design requirement of the system is structural market neutrality. Regression analysis against the S&P 500 (SPY) for the 2024–2026 period confirms that returns are driven by idiosyncratic pair alpha rather than market directionality.

| Metric | Full Period | Active Days Only* |
| :--- | :--- | :--- |
| **Market Beta** | 0.0030 | 0.0111 |
| **Correlation** | 0.0110 | 0.0205 |
| **Annualized Alpha** | +2.89% | +8.33% |
| **R-Squared** | 0.0001 | 0.0004 |

*\*Active Days Only includes only days where the strategy had open positions (non-zero PnL).*

The strategy maintains a Beta near zero across all 8 folds, with market movements explaining less than 0.05% of performance variance. This confirms that the statistical arbitrage engine successfully isolates intra-sector mean reversion.

---

## Strategy Overview


The strategy identifies cointegrated equity pairs within the same GICS sector, enters trades when the residual Z-score breaches a threshold, and exits when it reverts toward the mean.

**Universe:** S&P 500 mega-cap equities across 8 GICS sectors, selected for liquidity and execution symmetry.

**Pair Selection:** Engle-Granger cointegration test on log prices (p < 0.05) applied every fold. Top 5 pairs selected by cross-fold Sharpe stability — single-pair selection rejected after sensitivity analysis revealed prohibitive performance variance.

**Signal Generation:** Z-score on OLS residuals with adaptive lookback = max(z_multiplier × half-life, 10).

**Hedge Ratio Guard:** Blocks new entries and exits open positions if the rolling hedge ratio drifts beyond threshold of the selection-period value. Operates in log-price space to eliminate percentage-move asymmetry between high- and low-priced stocks.

**Frozen Entry Reference:** Hedge ratio, residual mean, and residual std locked at trade entry. All Z-scores computed against this fixed distribution for the full trade lifecycle, preventing rolling statistics from absorbing spread drift.

**Exit Conditions:**
- Residual Z-score hits exit threshold (signal)
- Residual Z-score hits stop threshold
- Hedge ratio guard breach
- Max 15-day holding period on losing positions only (winners run)
- Fold-end timeout

---

## Optimization & Validation Framework

**Walk-Forward Structure:** 15 folds, 2-month selection window, 3-month test window. Window lengths chosen empirically via pair survival rate analysis — measuring cointegration retention from selection to test period.

**Parameter Search:** Grid search over 1,824 valid parameter combinations across Z-entry, Z-exit, Z-stop, HR threshold, residual lookback, and locked vs unlocked reference. Validity constraint applied to exclude Z-entry ≤ Z-exit combinations.

**Sensitivity Analysis:** Marginal sensitivity analysis (score = mean Sharpe − 0.5 × std Sharpe) identified load-bearing vs non-binding parameters. Z-entry showed a clear mean Sharpe peak at 2.2; HR threshold flat from 0.4 onward; Z-multiplier non-binding due to active floor constraint. 72-combination shortlist derived for full walk-forward evaluation.

**Final Parameter Selection:** Robustness prioritized over total in-sample PnL:
1. Parameter survived the hardest fold (Dec 2022–Mar 2023: regime transition + SVB banking shock) with positive Sharpe.
2. Highest away mean Sharpe across remaining 14 folds
3. Best perfoming score among the 72-combination shortlist

The selected set independently ranked as the top-scoring combination in the full grid — confirming convergence of robustness and raw performance criteria.

**Final Parameters:**

| Parameter | Value |
|---|---|
| Z-entry | 2.2 |
| Z-exit | 1.0 |
| Z-stop | 4.5 |
| HR threshold | 0.8 |
| Residual lookback | 90 days |
| Max holding (loss) | 15 days |

**Stress Test Result:** Only 2 of 15 fold winners survived the difficult fold with positive Sharpe. Failing sets were dominated by stop-loss exits (6–9 per set vs 2 for the survivor), confirming the fold as a genuine discriminating stress test.

---

## Regime Analysis

**2018–2020 (OOS):** Mean Sharpe of −0.82 across all fold winning parameter combinations. Diagnosed as a strategy-class limitation — no parameter combination rescued the period. Primary failure mechanism: idiosyncratic stock repricing (NFLX earnings shock) amplified by concentration risk from same-stock multi-pair selection. Notably, 2018 Q4 (the macro shock period) was the best quarter with 75% win rate, while 2019 Q2 was the worst at 10% — suggesting the strategy is more sensitive to intra-sector dispersion and idiosyncratic events than broad macro regime.

**2024–2026 (OOS):** Soft landing, compressed volatility, stable sector relationships. Strategy performed as designed with consistent signal generation across all 8 folds.

**Known Limitations:**
- Vulnerable to gap risk on idiosyncratic stock events (AAPL-INTC, Feb 2025, single trade responsible for worst fold drawdown of 6.15%)
- Concentration risk from same-stock multi-pair selection — retained as a deliberate design decision after finding it material to IS profitability
- Low capital utilization (8% avg) limits absolute returns — future work would explore expanding the universe or relaxing pair selection criteria

---

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Default Backtest**:
   ```bash
   python run_backtest.py
   ```

---

## Usage

The `run_backtest.py` script provides a command-line interface to run the walk-forward backtest with custom parameters.

### Basic Examples

**Run for a specific date range:**
```bash
python run_backtest.py --start 2024-01-01 --end 2026-01-01
```

**Test a different entry threshold:**
```bash
python run_backtest.py --entry_z 2.5 --exit_z 0.5
```

**Increase the number of pairs per fold:**
```bash
python run_backtest.py --max_pairs 10
```

### Available Arguments

| Argument | Description | Default |
|---|---|---|
| `--start` | Backtest start date (YYYY-MM-DD) | `2020-01-01` |
| `--end` | Backtest end date (YYYY-MM-DD) | `2026-01-01` |
| `--entry_z` | Z-score entry threshold | `2.2` |
| `--exit_z` | Z-score exit threshold | `1.0` |
| `--stop_z` | Stop loss Z-score threshold | `4.5` |
| `--resid_val` | Residual lookback period (days) | `90` |
| `--max_pairs` | Max pairs traded per fold | `5` |
| `--initial_cash`| Starting capital ($) | `1,000,000` |
| `--output` | Directory for result CSVs | `results` |

Run `python run_backtest.py --help` for a full list of strategy and environment parameters.

---

## Repository Structure

```
├── README.md
├── src/
│   ├── pair_selection.py        # Cointegration testing, top-N selection
│   ├── signal.py                # Z-score, half-life, lookback computation
│   ├── hedge_ratio_guard.py     # HR guard logic, entry/exit conditions
│   ├── walk_forward.py          # Fold structure, train/test splitting
│   ├── backtest.py              # Trade execution, exit logic
│   └── optimization.py          # Grid search, sensitivity analysis
├── notebooks/
│   ├── 01_pair_selection_analysis.ipynb
│   ├── 02_parameter_optimization.ipynb
│   ├── 03_walk_forward_results.ipynb
│   ├── 04_oos_results.ipynb
│   └── 05_regime_analysis.ipynb
├── results/
│   ├── oos_equity_curves/       # Per-fold equity curves
│   ├── sensitivity_plots/       # Marginal sensitivity analysis charts
│   └── trade_logs/              # OOS and IS trade logs
└── requirements.txt
```

---

## Dependencies

```
pip install -r requirements.txt
```

Key libraries: pandas, numpy, statsmodels, scipy, backtrader, matplotlib, seaborn

---

## Notes

This project was built independently over 2025 as part of self-directed study in quantitative finance. Parameter selection was performed entirely on in-sample data (2020–2024). The 2018–2020 and 2024–2026 periods were held out as OOS throughout.
