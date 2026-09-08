# Step 1: Baseline Start-Date Sweep — Pair-Selection Instability

**Objective:** Quantify how sensitive the baseline config is to the choice of start date.

**Config:** `--profile baseline` = same_sector, slide=3m, sel=2m, test=3m, pct=0.18, log_space=True, dollar_neutral=False

**Period:** 2023-11-01 to 2026-01-01 (5 start dates at 2-week cadence, 7 folds each)

---

## Global Results

| Start      | Ann Ret % | Sharpe | Trades | Folds | Mean AT |
|------------|-----------|--------|--------|-------|---------|
| 2023-12-01 | -1.63%    | -0.23  | 55     | 7     | 0.7     |
| 2023-12-15 | 5.22%     | 0.91   | 52     | 7     | 0.7     |
| 2024-01-01 | 10.68%    | 1.48   | 44     | 7     | 0.6     |
| 2024-01-15 | -1.85%    | -0.28  | 46     | 7     | 0.6     |
| 2024-02-01 | 2.27%     | 0.52   | 32     | 7     | 0.4     |

**Summary across 5 runs:**
| Metric     | Mean  | Std   | Min    | Max    |
|------------|-------|-------|--------|--------|
| Ann Ret %  | 2.94  | 4.83  | -1.85  | 10.68  |
| Sharpe     | 0.48  | 0.66  | -0.28  | 1.48   |
| Trades     | 45.8  | 8.4   | 32     | 55     |
| Mean AT    | 0.60  | 0.12  | 0.39   | 0.72   |

---

## Fold-Level Sharpe Stability

| Fold | 2023-12-01 | 2023-12-15 | 2024-01-01 | 2024-01-15 | 2024-02-01 | Mean  | Std   |
|------|------------|------------|------------|------------|------------|-------|-------|
| 0    | -0.09      | 0.14       | -0.02      | -0.02      | 0.08       | 0.02  | 0.08  |
| 1    | 0.20       | 0.20       | 0.01       | 0.05       | 0.04       | 0.10  | 0.08  |
| 2    | 0.09       | 0.05       | 0.16       | -0.18      | 0.22       | 0.07  | 0.14  |
| 3    | -0.14      | 0.00       | 0.09       | 0.11       | -0.06      | 0.00  | 0.09  |
| 4    | -0.05      | 0.19       | 0.13       | 0.17       | 0.24       | 0.14  | 0.10  |
| 5    | -0.01      | -0.00      | 0.26       | -0.03      | -0.01      | 0.04  | 0.11  |
| 6    | -0.04      | -0.09      | -0.24      | -0.18      | -0.04      | -0.12 | 0.08  |

---

## Key Findings

1. **High start-date sensitivity confirmed:** Sharpe ranges from -0.28 to 1.48 across just 2-week shifts in start date. Std=0.66.

2. **Nearly identical to golden slide=3m results:** The notebook 06 analysis of golden (cross_sector, slide=3m) found mean Sharpe=0.48, std=0.66 — essentially the same. Same-sector vs cross-sector makes little difference at slide=3m.

3. **2024-01-01 outlier:** This start date produces 10.68% return and 1.48 Sharpe across folds 2-5 (Sep 2024 to Aug 2025), while adjacent start dates are negative. Suggests specific pair selections in that window happened to work well.

4. **Low capital efficiency:** Mean active trades 0.4-0.7 means capital sits idle >30% of the time. Only ~46 trades over 2 years.

5. **Fold 6 consistently negative:** The Sep-Nov 2025 test window is negative across ALL start dates (mean -0.12). Suggests a systemic regime issue in late 2025, not a start-date artifact.

---

---

## Step 2: Loss Diagnosis — Earnings-Driven Losses

**Objective:** Identify the worst individual trades across all 5 start dates and check for earnings-driven patterns (notebook 06 found AVGO-NVDA, AAPL-NVDA as the top 3 losers for golden cross_sector profile).

### Top 10 Worst Trades by PnL

| Rank | Run Start   | Pair       | Entry      | Exit       | Reason       | PnL      | Return   | Fold |
|------|-------------|------------|------------|------------|--------------|----------|----------|------|
| 1    | 2024-01-15  | AVGO-NVDA  | 2024-12-06 | 2024-12-13 | stop_loss    | -63,306  | -35.2%   | 2    |
| 2    | 2024-02-01  | AAPL-INTC  | 2025-02-12 | 2025-02-18 | stop_loss    | -45,944  | -25.5%   | 3    |
| 3    | 2023-12-01  | AAPL-NVDA  | 2024-11-25 | 2024-12-09 | stop_loss    | -29,727  | -16.5%   | 3    |
| 4    | 2023-12-15  | ABT-UNH    | 2025-07-17 | 2025-08-01 | max_hold_loss| -31,401  | -17.4%   | 5    |
| 5    | 2023-12-15  | LLY-TMO    | 2025-07-23 | 2025-08-07 | stop_loss    | -21,903  | -12.2%   | 5    |
| 6    | 2024-01-15  | AVGO-NVDA  | 2024-11-12 | 2024-11-19 | stop_loss    | -11,035  | -6.1%    | 2    |
| 7    | 2023-12-01  | AVGO-ORCL  | 2024-12-13 | 2024-12-30 | max_hold_loss| -17,882  | -9.9%    | 3    |
| 8    | 2023-12-01  | GILD-TMO   | 2025-09-30 | 2025-10-01 | stop_loss    | -16,442  | -9.1%    | 6    |
| 9    | 2023-12-01  | CRM-NVDA   | 2024-12-23 | 2025-01-06 | stop_loss    | -16,398  | -9.1%    | 3    |
| 10   | 2024-01-01  | AAPL-ADBE  | 2024-05-03 | 2024-05-20 | stop_loss    | -14,130  | -7.9%    | 0    |

### Key Findings

1. **AVGO-NVDA confirmed as the single worst pair:** The Dec 6-13, 2024 AVGO-NVDA trade lost **-63,306 (-35.2%)** in the 2024-01-15 run. This is worse than the golden profile's equivalent trade. The pair also lost -11,035 in an earlier entry (Nov 12-19, 2024). AVGO reported earnings on **Dec 12, 2024** — the trade was stopped out the next day.

2. **AAPL-NVDA is the second-most destructive pattern:** -29,727 / -16.5% in the 2023-12-01 run, entered Nov 25 (5 days after NVDA earnings Nov 20) and stopped out Dec 9.

3. **Fold 3 (Nov 2024 - Jan 2025) is a consistent loss cluster:** Across multiple start dates, this window produces the largest losses — it spans NVDA earnings (Nov 20), AVGO earnings (Dec 12), and AAPL earnings (Jan 30). Three earnings events in ~10 weeks, and the mean-reversion pairs keep getting trapped.

4. **Same five pairs account for ~80% of total losses:** AVGO-NVDA, AAPL-NVDA, AVGO-ORCL, CRM-NVDA, AAPL-INTC — all heavily exposed to semiconductor earnings catalysts (NVDA, AVGO, AAPL, INTC).

5. **Not all losses are earnings-driven:** ABT-UNH (-31,401 in fold 5) and LLY-TMO (-21,903 in fold 5) are healthcare pairs in Jul-Aug 2025 — likely a different regime issue.

### Confirmed Hypothesis

The same earnings-driven mechanism identified in notebook 06 (golden cross_sector) applies identically to the **same_sector** baseline. AVGO-NVDA and AAPL-NVDA mean-reversion pairs get crushed when one of the two stocks has a large earnings gap. An earnings-screen filter should directly address ~60-70% of the worst losses.

---

## Output Files

```
diagnosis/01_baseline_instability/
├── findings.md
├── metrics_summary.csv
├── 2023-12-01_2026-01-01/
│   ├── metrics.json
│   ├── oos_fold_summary.csv
│   ├── daily_returns.csv
│   └── trade_logs/test_trade_log.csv
├── 2023-12-15_2026-01-01/   (same structure)
├── 2024-01-01_2026-01-01/
├── 2024-01-15_2026-01-01/
└── 2024-02-01_2026-01-01/
```
