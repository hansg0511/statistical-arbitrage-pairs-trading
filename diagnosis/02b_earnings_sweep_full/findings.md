# Earnings Block Days Sweep — Baseline (same_sector, slide=3m)

**Grid:** 5 start dates × 6 screen settings = 30 runs

**Generated:** 2026-09-04 05:26

## Sharpe Pivot

| Start Date | noscreen | bd0 | bd3 | bd5 | bd7 | bd9 |
|------------|---|---|---|---|---|---|
| 2023-12-01 | -0.23 | -0.29 | -0.46 | -0.46 | -0.06 | -0.13 |
| 2023-12-15 | 1.24 | 1.19 | 1.52 | 1.52 | 1.52 | 1.52 |
| 2024-01-01 | 1.48 | 0.75 | 1.18 | 1.18 | 1.26 | 1.74 |
| 2024-01-15 | -0.28 | 0.4 | 1.06 | 1.06 | 0.99 | 0.99 |
| 2024-02-01 | 0.52 | 0.11 | 0.01 | 0.01 | 0.01 | 0.01 |

## Trades Pivot

| Start Date | noscreen | bd0 | bd3 | bd5 | bd7 | bd9 |
|------------|---|---|---|---|---|---|
| 2023-12-01 | 55 | 44 | 37 | 37 | 36 | 34 |
| 2023-12-15 | 50 | 36 | 27 | 27 | 27 | 27 |
| 2024-01-01 | 43 | 32 | 24 | 24 | 23 | 23 |
| 2024-01-15 | 44 | 28 | 24 | 24 | 22 | 22 |
| 2024-02-01 | 32 | 25 | 20 | 20 | 20 | 20 |

## Return % Pivot

| Start Date | noscreen | bd0 | bd3 | bd5 | bd7 | bd9 |
|------------|---|---|---|---|---|---|
| 2023-12-01 | -1.63 | -1.8 | -2.05 | -2.05 | -0.33 | -0.59 |
| 2023-12-15 | 6.87 | 4.15 | 4.47 | 4.47 | 4.47 | 4.47 |
| 2024-01-01 | 10.68 | 4.44 | 6.64 | 6.64 | 7.12 | 9.21 |
| 2024-01-15 | -1.85 | 1.16 | 2.6 | 2.6 | 2.28 | 2.28 |
| 2024-02-01 | 2.27 | 0.36 | -0.02 | -0.02 | -0.02 | -0.02 |

## Aggregate Summary

| Metric | noscreen | bd0 | bd3 | bd5 | bd7 | bd9 |
|--------|---|---|---|---|---|---|
| Mean Sharpe | 0.55 | 0.43 | 0.66 | 0.66 | 0.74 | 0.83 |
| Mean Trades | 44.8 | 33.0 | 26.4 | 26.4 | 25.6 | 25.2 |
| Mean Return % | 3.27 | 1.66 | 2.33 | 2.33 | 2.70 | 3.07 |
| Mean Active Trades | 0.58 | 0.44 | 0.32 | 0.32 | 0.30 | 0.30 |

## Stability (Sharpe Std per Block Days)

| Metric | noscreen | bd0 | bd3 | bd5 | bd7 | bd9 |
|--------|---|---|---|---|---|---|
| Sharpe Std | 0.81 | 0.57 | 0.84 | 0.84 | 0.73 | 0.85 |
| Sharpe Range | [-0.28, 1.48] | [-0.29, 1.19] | [-0.46, 1.52] | [-0.46, 1.52] | [-0.06, 1.52] | [-0.13, 1.74] |

## Interpretation

bd3 and bd5 are identical across all displayed starts and metrics. bd7 and bd9 match on four of five starts; their only material difference is the 2024-01-01 start, where bd9 is higher. That one start accounts for most of bd9's higher mean Sharpe, so it is not sufficient evidence that bd9 is generally superior.

bd7 and bd9 retain nearly the same number of trades (25.6 versus 25.2 mean trades), while bd7 has lower Sharpe dispersion (0.73 versus 0.85). bd7 is therefore retained as the conservative minimum-sufficient secondary filter; earnings screening remains secondary to pair-selection stability.
