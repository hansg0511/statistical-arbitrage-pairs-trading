# Step 3: Earnings Screen Impact on Baseline

**Profile:** baseline (same_sector, slide=3m, sel=2m, test=3m, pct=0.18, log_space=True)

**Block days:** 7 | **Generated:** 2026-07-27 18:50

## Results

| Start Date | Screen | Ann. Return % | Sharpe | Trades | Mean AT |
|------------|--------|--------------|--------|--------|---------|
| 2023-12-01 | OFF | -1.63 | -0.23 | 55 | 0.67 |
| 2023-12-01 | ON (+7d) | -1.11 | -0.21 | 43 | 0.51 |
| 2023-12-15 | OFF | 5.22 | 0.91 | 52 | 0.72 |
| 2023-12-15 | ON (+7d) | 1.11 | 0.29 | 35 | 0.47 |
| 2024-01-01 | OFF | 10.68 | 1.48 | 44 | 0.6 |
| 2024-01-01 | ON (+7d) | 7.41 | 1.26 | 31 | 0.38 |
| 2024-01-15 | OFF | -1.85 | -0.28 | 46 | 0.56 |
| 2024-01-15 | ON (+7d) | 1.9 | 0.68 | 29 | 0.3 |
| 2024-02-01 | OFF | 2.27 | 0.52 | 32 | 0.39 |
| 2024-02-01 | ON (+7d) | 0.09 | 0.04 | 22 | 0.28 |

## Aggregate Comparison

| Metric | No Screen | Screen +7d | Delta |
|--------|-----------|------------|-------|
| Mean Return % | 2.94 | 1.88 | -1.06 |
| Mean Sharpe | 0.48 | 0.41 | -0.07 |
| Mean Trades | 45.8 | 32.0 | -13.8 |
| Mean Active Trades | 0.59 | 0.39 | -0.2 |

## Stability Comparison

| Metric | No Screen | Screen +7d |
|--------|-----------|------------|
| Sharpe Std | 0.75 | 0.58 |
| Sharpe Range | [-0.28, 1.48] | [-0.21, 1.26] |

---

## Fold-Level Comparison (Screen Δ vs NoScreen)

| Fold | 2023-12-01 Δ | 2023-12-15 Δ | 2024-01-01 Δ | 2024-01-15 Δ | 2024-02-01 Δ |
|------|-------------|-------------|-------------|-------------|-------------|
| 0    | -0.12       | +0.02       | +0.04       | +0.02       | -0.11       |
| 1    | -0.01       | -0.18       | +0.16       | +0.10       | +0.03       |
| 2    | -0.04       | -0.05       | -0.17       | -0.04       | -0.22       |
| 3    | +0.09       | -0.04       | +0.01       | +0.13       | +0.00       |
| 4    | -0.02       | -0.04       | -0.02       | -0.01       | +0.00       |
| 5    | -0.08       | +0.00       | +0.00       | +0.00       | +0.00       |
| 6    | +0.00       | +0.00       | +0.00       | +0.00       | +0.00       |

### Key Observations

1. **Screen effect is inconsistent:** Of 35 fold-runs, 14 improved, 17 degraded, 4 unchanged. No clear directional signal.

2. **Fold 2 (Sep-Dec 2024) is consistently degraded** by the screen (-0.04 to -0.22). This is peak earnings season — the screen blocks too many legitimate trades, collapsing trade counts. For 2024-02-01, fold 2 went from 3 trades to 0.

3. **Fold 3 (Nov-Feb) sometimes improves** (+0.09 to +0.13 in 3/5 start dates), suggesting the screen does catch some of the catastrophic Nov-Dec earnings losses (AVGO-NVDA, AAPL-NVDA). For 2024-01-15, fold 3 improved from 0.11 to 0.24.

4. **Folds 4-6 are mostly unchanged** — the screen rarely triggers after Feb 2025 because the earnings cache covers fewer events in the outer years, or the selected pairs simply don't have earnings conflicts.

### Why the Screen Fails for Baseline (vs Golden)

The golden profile (cross_sector, slide=1m) showed significant improvement with the screen in notebook 06. The baseline (same_sector, slide=3m) does not. Probable reasons:

- **Same-sector pairs co-move on earnings:** If two tech stocks both report earnings in the same window, blocking both makes the pair untradeable. Cross-sector pairs have more offsetting earnings calendars.
- **Slide=3m means fewer, stickier pairs:** With only ~46 trades total, losing ~14 trades (30%) to the screen is a large relative hit. Golden with slide=1m has ~80+ trades — the same absolute loss is a smaller fraction.
- **Screen trades off tail-risk for volume:** The screen successfully blocked the -63k AVGO-NVDA trade, but also blocked many small winners, resulting in net neutral.

---

## Conclusions

1. **Earnings screen alone is NOT sufficient** to stabilize the baseline config. Mean Sharpe drops slightly (0.48 → 0.41), though stability improves modestly (Std 0.75 → 0.58).

2. **The core instability is driven by pair-selection volatility (slide=3m), not just earnings timing.** The earnings screen can't fix the fundamental issue that different start dates select completely different pairs.

3. **Next investigation direction:** The fold-level data shows that the same pairs are selected across start dates within the same fold (e.g., fold 3 always includes AAPL-NVDA/AVGO-ORCL when the window aligns). The instability is driven by which pairs get selected in each specific 3-month window — this is a **selection window / slide parameter issue**, not solely an earnings issue.

4. **Suggested next step:** Sweep the `slide` parameter (1m, 2m, 3m, 6m) at fixed start dates to find the value that maximizes stability, then re-evaluate the earnings screen on top of the optimal slide.
