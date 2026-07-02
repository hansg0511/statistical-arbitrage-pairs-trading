# Statistical Arbitrage Pairs Trading System

A statistical arbitrage pairs trading framework that exploits cointegrated equity spreads using z-score mean reversion signals. The system is validated using strict walk-forward out-of-sample testing with an emphasis on robustness, regime stability, and market neutrality rather than in-sample optimisation.

---

## Summary

- **Strategy:** Cointegration-based pairs trading (mean-reverting spreads)
- **Universe:** S&P 500 mega-cap equities (same-sector pairs)
- **Signal:** Z-score of OLS residuals (entry/exit thresholds)
- **Validation:** 8-fold walk-forward out-of-sample testing
- **Market Exposure:** Near-zero beta (~0.003) and correlation (~0.01)
- **Performance:** Sharpe 0.65, 63% win rate, low drawdowns (1–2% avg per fold)

---

## Key Out-of-Sample Results (2024–2026)

| Metric | Value |
|---|---|
| Sharpe Ratio | 0.65 |
| Win Rate | 63.2% |
| Annualized Returns | 2.84% |
| Avg Max Drawdown (per fold) | 1.7% |
| Total Trades | 38 |
| Avg Capital Utilization | 8.0% |
| Market Beta (SPY) | 0.003 |
| Correlation to SPY | 0.011 |

> Returns are generated through highly selective, low-capital deployment with near-zero market dependency.

---

## Strategy Overview

The system identifies statistically linked equity pairs and trades deviations from equilibrium.

### Core Process

1. **Pair Selection**
   - Engle-Granger cointegration test (log prices, p < 0.05)
   - Same-sector S&P 500 mega-cap universe

2. **Signal Generation**
   - Rolling OLS residual spread
   - Z-score computed on fixed entry distribution

3. **Execution Logic**
   - Entry/exit triggered by Z-score thresholds
   - Frozen entry distribution (prevents rolling distortion)
   - Hedge ratio monitoring for structural drift

---

## Risk & Trade Management

- **Hedge Ratio Guard:** Prevents trades when structural drift exceeds threshold
- **Fixed Trade Reference:** Entry distribution remains constant over trade lifetime
- **Exit Conditions:**
  - Mean reversion (Z-score exit)
  - Stop-loss threshold
  - Hedge ratio break
  - Max holding period (losses only)
  - Fold termination

---

## Validation Framework

### Walk-Forward Design
- 15 folds total
- 2-month training / selection
- 3-month testing
- Strict out-of-sample evaluation (2020–2024 IS, 2024–2026 OOS)

### Parameter Selection
- 1,824 parameter combinations tested
- Grid search across:
  - Entry/exit/stop thresholds
  - Hedge ratio constraints
  - Lookback parameters
- Sensitivity analysis used to identify stable regions of performance

### Selection Criteria
- Robustness across stress regimes
- Out-of-sample Sharpe stability
- Survival under worst historical folds (e.g., 2022–2023 regime shock)

---

## Regime Performance

### 2018–2020 Stress Period
- Weak performance across all parameter sets (structural limitation)
- Idiosyncratic shocks (e.g., earnings events) dominated spread behaviour
- No parameter regime fully stabilised performance

### 2024–2026 Period
- Stable mean reversion across all folds
- Consistent signal generation in low-volatility regime
- Strategy behaves as designed under expected conditions

---

## Known Limitations

- Exposure to **idiosyncratic single-name shocks** (e.g., earnings/news gaps)
- Concentration risk from multi-pair exposure to same equities
- Low capital utilization (~8%) limits absolute return scalability

---

## Quick Start

```bash
pip install -r requirements.txt
python run_backtest.py

# Specify a custom backtest date range
python run_backtest.py --start 2018-01-01 --end 2020-12-31
```

- `--start`: Backtest start date (format: `YYYY-MM-DD`)
- `--end`: Backtest end date (format: `YYYY-MM-DD`)

If omitted, defaults to 2020-01-01 to 2020-05-31.
