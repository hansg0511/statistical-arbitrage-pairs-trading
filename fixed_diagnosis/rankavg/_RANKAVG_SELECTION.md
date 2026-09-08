# Rank-average-only survivor selection

Method: drop the separate (min-score) and joined-Sharpe rankings. Rank all 496 pairs by rank-average (mean of recent and historical dense ranks, lower = better). Survivors = top-20 in mechanism A AND top-20 in mechanism B.

## Mechanism A — top 20 by rank-average

| # | Pair | rank_avg | recent | hist | min | joined Sh |
|---|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 45.5 | 1.14 | 0.56 | 0.56 | 0.75 |
| 2 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 48.0 | 1.38 | 0.35 | 0.35 | 0.69 |
| 3 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 49.0 | 1.22 | 0.41 | 0.41 | 0.66 |
| 4 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 53.0 | 1.36 | 0.33 | 0.33 | 0.66 |
| 5 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 57.0 | 1.19 | 0.37 | 0.37 | 0.61 |
| 6 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 58.0 | 1.09 | 0.49 | 0.49 | 0.68 |
| 7 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 58.0 | 1.28 | 0.32 | 0.32 | 0.63 |
| 8 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 58.0 | 1.06 | 0.58 | 0.58 | 0.73 |
| 9 | `sp500-2m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 61.5 | 1.16 | 0.37 | 0.37 | 0.62 |
| 10 | `sp500-12m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 62.5 | 1.28 | 0.29 | 0.29 | 0.55 |
| 11 | `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 64.5 | 1.12 | 0.40 | 0.40 | 0.63 |
| 12 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 67.0 | 1.07 | 0.46 | 0.46 | 0.62 |
| 13 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 69.0 | 1.08 | 0.42 | 0.42 | 0.63 |
| 14 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 69.5 | 1.16 | 0.32 | 0.32 | 0.59 |
| 15 | `sp500-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 70.0 | 1.17 | 0.32 | 0.32 | 0.58 |
| 16 | `core-12m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 75.0 | 1.24 | 0.24 | 0.24 | 0.54 |
| 17 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 75.5 | 0.87 | 0.81 | 0.81 | 0.82 |
| 18 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 75.5 | 0.83 | 1.14 | 0.83 | 1.04 |
| 19 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 76.0 | 0.91 | 0.67 | 0.67 | 0.73 |
| 20 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 76.5 | 1.04 | 0.42 | 0.42 | 0.62 |

## Mechanism B — top 20 by rank-average

| # | Pair | rank_avg | recent | hist | min | joined Sh |
|---|---:|---:|---:|---:|---:|---:|
| 1 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 38.0 | 1.34 | 0.40 | 0.40 | 0.68 |
| 2 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 48.0 | 1.16 | 0.45 | 0.45 | 0.69 |
| 3 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 49.5 | 1.08 | 0.60 | 0.60 | 0.76 |
| 4 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 53.0 | 1.19 | 0.35 | 0.35 | 0.61 |
| 5 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 53.5 | 1.43 | 0.29 | 0.29 | 0.66 |
| 6 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 55.5 | 1.29 | 0.31 | 0.31 | 0.64 |
| 7 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 60.5 | 1.04 | 0.53 | 0.53 | 0.69 |
| 8 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 66.0 | 1.06 | 0.44 | 0.44 | 0.60 |
| 9 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 70.0 | 1.05 | 0.41 | 0.41 | 0.61 |
| 10 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 71.0 | 1.21 | 0.24 | 0.24 | 0.56 |
| 11 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 73.5 | 1.14 | 0.29 | 0.29 | 0.56 |
| 12 | `sp500-12m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 75.0 | 1.19 | 0.23 | 0.23 | 0.49 |
| 13 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide3m_bd7` | 78.0 | 1.05 | 0.35 | 0.35 | 0.53 |
| 14 | `sp500-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 78.0 | 1.12 | 0.28 | 0.28 | 0.55 |
| 15 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 78.5 | 0.90 | 0.65 | 0.65 | 0.71 |
| 16 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 82.5 | 1.04 | 0.34 | 0.34 | 0.58 |
| 17 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 82.5 | 0.82 | 1.09 | 0.82 | 1.01 |
| 18 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 83.0 | 0.97 | 0.43 | 0.43 | 0.61 |
| 19 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 83.5 | 0.92 | 0.54 | 0.54 | 0.65 |
| 20 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 84.5 | 0.83 | 0.87 | 0.83 | 0.84 |

## Intersection (survivors, 17)

  - `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen`
  - `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen`
  - `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen`
  - `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7`
  - `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7`
  - `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_bd7`
  - `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen`
  - `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen`
  - `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7`
  - `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_noscreen`
  - `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide1m_noscreen`
  - `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide3m_bd7`
  - `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide3m_noscreen`
  - `sp500-12m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen`
  - `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen`
  - `sp500-12m/same_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7`
  - `sp500-12m/same_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide3m_noscreen`

## Mechanism A only (3)

  - `core-12m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen`
  - `sp500-12m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen`
  - `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide1m_noscreen`

## Mechanism B only (3)

  - `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide3m_bd7`
  - `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7`
  - `sp500-12m/same_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide3m_bd7`

