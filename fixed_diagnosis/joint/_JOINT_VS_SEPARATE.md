# Joint vs separate evaluation

Separate: per-window metrics, pair score = min(recent, hist); legs ranked by per-window Sharpe. Joint: historical (2015–2019) ++ recent (2024–2025) daily returns as one series, one Sharpe/return (mean over the 5 recent start-pairs).

Spearman correlation across all 496 pairs:

| vs joined Sharpe | rho |
|---|---:|
| separate score = min(rec, hist) | 0.874 |
| recent Sharpe | 0.310 |
| historical Sharpe | 0.913 |

## Legs — top 15 by joined Sharpe

| # | Config | Joined Sh | Joined Ret% | J# | Rec Sh | Hist Sh | Score | S# |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-12m/cross_sector_slide1m_noscreen` | 0.66 | +5.53% | 1 | 1.84 | 0.44 | 0.44 | 3 |
| 2 | `sp500-12m/same_sector_slide1m_noscreen` | 0.63 | +5.32% | 2 | 1.33 | 0.40 | 0.40 | 5 |
| 3 | `sp500-2m/cross_sector_slide3m_noscreen` | 0.56 | +8.00% | 3 | 0.41 | 0.62 | 0.41 | 4 |
| 4 | `sp500-2m/cross_sector_slide3m_bd7` | 0.54 | +4.64% | 4 | -0.38 | 0.88 | -0.38 | 23 |
| 5 | `sp500-12m/same_sector_slide3m_noscreen` | 0.51 | +5.65% | 5 | 0.81 | 0.37 | 0.37 | 6 |
| 6 | `sp500-12m/cross_sector_slide1m_bd7` | 0.50 | +2.98% | 6 | 1.29 | 0.56 | 0.56 | 1 |
| 7 | `sp500-12m/cross_sector_slide3m_bd7` | 0.41 | +3.35% | 7 | 0.81 | 0.30 | 0.30 | 8 |
| 8 | `sp500-12m/same_sector_slide1m_bd7` | 0.37 | +2.11% | 8 | 0.68 | 0.50 | 0.50 | 2 |
| 9 | `sp500-2m/cross_sector_slide1m_noscreen` | 0.36 | +3.07% | 9 | 0.45 | 0.13 | 0.13 | 13 |
| 10 | `sp500-2m/same_sector_slide1m_noscreen` | 0.28 | +1.91% | 10 | -0.04 | 0.28 | -0.04 | 14 |
| 11 | `core-12m/cross_sector_slide1m_bd7` | 0.28 | +1.38% | 11 | 0.51 | 0.32 | 0.32 | 7 |
| 12 | `sp500-12m/same_sector_slide3m_bd7` | 0.27 | +1.75% | 12 | 0.44 | 0.19 | 0.19 | 10 |
| 13 | `sp500-2m/same_sector_slide3m_noscreen` | 0.24 | +2.14% | 13 | 0.33 | 0.19 | 0.19 | 11 |
| 14 | `sp500-2m/same_sector_slide3m_bd7` | 0.22 | +1.32% | 14 | 0.29 | 0.20 | 0.20 | 9 |
| 15 | `core-2m/cross_sector_slide1m_noscreen` | 0.15 | +1.09% | 15 | 1.51 | -0.57 | -0.57 | 28 |

## Legs — top 15 by separate score min(rec, hist)

| # | Config | Score | Rec Sh | Hist Sh | J# | Joined Sh | Joined Ret% |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-12m/cross_sector_slide1m_bd7` | 0.56 | 1.29 | 0.56 | 6 | 0.50 | +2.98% |
| 2 | `sp500-12m/same_sector_slide1m_bd7` | 0.50 | 0.68 | 0.50 | 8 | 0.37 | +2.11% |
| 3 | `sp500-12m/cross_sector_slide1m_noscreen` | 0.44 | 1.84 | 0.44 | 1 | 0.66 | +5.53% |
| 4 | `sp500-2m/cross_sector_slide3m_noscreen` | 0.41 | 0.41 | 0.62 | 3 | 0.56 | +8.00% |
| 5 | `sp500-12m/same_sector_slide1m_noscreen` | 0.40 | 1.33 | 0.40 | 2 | 0.63 | +5.32% |
| 6 | `sp500-12m/same_sector_slide3m_noscreen` | 0.37 | 0.81 | 0.37 | 5 | 0.51 | +5.65% |
| 7 | `core-12m/cross_sector_slide1m_bd7` | 0.32 | 0.51 | 0.32 | 11 | 0.28 | +1.38% |
| 8 | `sp500-12m/cross_sector_slide3m_bd7` | 0.30 | 0.81 | 0.30 | 7 | 0.41 | +3.35% |
| 9 | `sp500-2m/same_sector_slide3m_bd7` | 0.20 | 0.29 | 0.20 | 14 | 0.22 | +1.32% |
| 10 | `sp500-12m/same_sector_slide3m_bd7` | 0.19 | 0.44 | 0.19 | 12 | 0.27 | +1.75% |
| 11 | `sp500-2m/same_sector_slide3m_noscreen` | 0.19 | 0.33 | 0.19 | 13 | 0.24 | +2.14% |
| 12 | `core-12m/same_sector_slide1m_bd7` | 0.13 | 0.28 | 0.13 | 25 | -0.10 | -0.25% |
| 13 | `sp500-2m/cross_sector_slide1m_noscreen` | 0.13 | 0.45 | 0.13 | 9 | 0.36 | +3.07% |
| 14 | `sp500-2m/same_sector_slide1m_noscreen` | -0.04 | -0.04 | 0.28 | 10 | 0.28 | +1.91% |
| 15 | `core-12m/cross_sector_slide3m_bd7` | -0.10 | 0.31 | -0.10 | 19 | 0.04 | -0.01% |

## Pairs — top 20 by joined Sharpe

| # | Leg A | Leg B | Joined Sh | Joined Ret% | J# | S# | Score | Rec Sh | Hist Sh |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-2m/cross_sector_slide3m_bd7` | 1.04 | +7.65% | 1 | 1 | 0.83 | 0.83 | 1.14 |
| 2 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/cross_sector_slide3m_bd7` | 0.91 | +8.12% | 2 | 16 | 0.52 | 0.52 | 1.09 |
| 3 | `sp500-12m/cross_sector_slide1m_bd7` | `sp500-2m/cross_sector_slide3m_bd7` | 0.90 | +5.70% | 3 | 65 | 0.32 | 0.32 | 1.13 |
| 4 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-2m/cross_sector_slide3m_bd7` | 0.82 | +6.22% | 4 | 2 | 0.81 | 0.87 | 0.81 |
| 5 | `sp500-12m/same_sector_slide1m_bd7` | `sp500-2m/cross_sector_slide3m_bd7` | 0.78 | +5.25% | 5 | 118 | 0.19 | 0.19 | 1.01 |
| 6 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-12m/same_sector_slide3m_noscreen` | 0.75 | +7.07% | 6 | 10 | 0.56 | 1.14 | 0.56 |
| 7 | `sp500-12m/same_sector_slide3m_bd7` | `sp500-2m/cross_sector_slide3m_bd7` | 0.74 | +5.34% | 7 | 220 | -0.00 | -0.00 | 1.03 |
| 8 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-12m/same_sector_slide3m_noscreen` | 0.73 | +6.09% | 8 | 7 | 0.58 | 1.06 | 0.58 |
| 9 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-2m/cross_sector_slide3m_noscreen` | 0.73 | +6.31% | 9 | 4 | 0.67 | 0.91 | 0.67 |
| 10 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/cross_sector_slide3m_noscreen` | 0.72 | +7.69% | 10 | 3 | 0.70 | 0.73 | 0.70 |
| 11 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-12m/same_sector_slide1m_noscreen` | 0.69 | +5.00% | 11 | 53 | 0.35 | 1.38 | 0.35 |
| 12 | `sp500-12m/cross_sector_slide1m_bd7` | `sp500-2m/cross_sector_slide3m_noscreen` | 0.69 | +5.19% | 12 | 11 | 0.55 | 0.55 | 0.76 |
| 13 | `sp500-2m/same_sector_slide3m_bd7` | `sp500-2m/cross_sector_slide3m_bd7` | 0.68 | +5.12% | 13 | 150 | 0.13 | 0.13 | 0.90 |
| 14 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-2m/same_sector_slide1m_noscreen` | 0.68 | +4.39% | 14 | 20 | 0.49 | 1.09 | 0.49 |
| 15 | `sp500-12m/cross_sector_slide1m_noscreen` | `core-2m/same_sector_slide1m_noscreen` | 0.66 | +4.16% | 15 | 62 | 0.33 | 1.36 | 0.33 |
| 16 | `sp500-12m/cross_sector_slide1m_noscreen` | `core-2m/same_sector_slide1m_bd7` | 0.66 | +3.78% | 16 | 37 | 0.41 | 1.22 | 0.41 |
| 17 | `sp500-12m/same_sector_slide3m_bd7` | `sp500-2m/cross_sector_slide3m_noscreen` | 0.65 | +5.70% | 17 | 22 | 0.47 | 0.47 | 0.72 |
| 18 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/cross_sector_slide1m_noscreen` | 0.63 | +5.37% | 18 | 14 | 0.53 | 0.86 | 0.53 |
| 19 | `sp500-12m/cross_sector_slide1m_noscreen` | `core-12m/same_sector_slide1m_bd7` | 0.63 | +3.39% | 19 | 66 | 0.32 | 1.28 | 0.32 |
| 20 | `sp500-2m/cross_sector_slide3m_noscreen` | `sp500-2m/cross_sector_slide3m_bd7` | 0.63 | +7.31% | 20 | 128 | 0.18 | 0.18 | 0.80 |

## Pairs — top 20 by separate score

| # | Leg A | Leg B | Score | Rec Sh | Hist Sh | J# | Joined Sh | Joined Ret% |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-2m/cross_sector_slide3m_bd7` | 0.83 | 0.83 | 1.14 | 1 | 1.04 | +7.65% |
| 2 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-2m/cross_sector_slide3m_bd7` | 0.81 | 0.87 | 0.81 | 4 | 0.82 | +6.22% |
| 3 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/cross_sector_slide3m_noscreen` | 0.70 | 0.73 | 0.70 | 10 | 0.72 | +7.69% |
| 4 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-2m/cross_sector_slide3m_noscreen` | 0.67 | 0.91 | 0.67 | 9 | 0.73 | +6.31% |
| 5 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/same_sector_slide3m_noscreen` | 0.60 | 0.68 | 0.60 | 21 | 0.63 | +5.78% |
| 6 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/cross_sector_slide1m_bd7` | 0.60 | 0.60 | 0.61 | 35 | 0.60 | +4.61% |
| 7 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-12m/same_sector_slide3m_noscreen` | 0.58 | 1.06 | 0.58 | 8 | 0.73 | +6.09% |
| 8 | `sp500-12m/cross_sector_slide3m_bd7` | `sp500-2m/cross_sector_slide3m_bd7` | 0.57 | 0.57 | 0.61 | 45 | 0.57 | +4.46% |
| 9 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/same_sector_slide1m_noscreen` | 0.56 | 0.68 | 0.56 | 37 | 0.60 | +4.85% |
| 10 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-12m/same_sector_slide3m_noscreen` | 0.56 | 1.14 | 0.56 | 6 | 0.75 | +7.07% |
| 11 | `sp500-12m/cross_sector_slide1m_bd7` | `sp500-2m/cross_sector_slide3m_noscreen` | 0.55 | 0.55 | 0.76 | 12 | 0.69 | +5.19% |
| 12 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/same_sector_slide3m_bd7` | 0.53 | 0.73 | 0.53 | 39 | 0.60 | +4.65% |
| 13 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-12m/same_sector_slide1m_bd7` | 0.53 | 0.78 | 0.53 | 29 | 0.62 | +5.02% |
| 14 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/cross_sector_slide1m_noscreen` | 0.53 | 0.86 | 0.53 | 18 | 0.63 | +5.37% |
| 15 | `sp500-12m/cross_sector_slide3m_noscreen` | `sp500-2m/cross_sector_slide3m_bd7` | 0.52 | 0.76 | 0.52 | 42 | 0.59 | +4.90% |
| 16 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/cross_sector_slide3m_bd7` | 0.52 | 0.52 | 1.09 | 2 | 0.91 | +8.12% |
| 17 | `sp500-12m/cross_sector_slide1m_bd7` | `sp500-12m/same_sector_slide3m_noscreen` | 0.52 | 0.82 | 0.52 | 24 | 0.62 | +4.57% |
| 18 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-2m/cross_sector_slide3m_noscreen` | 0.52 | 0.87 | 0.52 | 28 | 0.62 | +5.58% |
| 19 | `sp500-12m/same_sector_slide3m_noscreen` | `core-12m/same_sector_slide1m_bd7` | 0.51 | 0.74 | 0.51 | 36 | 0.60 | +4.22% |
| 20 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-2m/same_sector_slide1m_noscreen` | 0.49 | 1.09 | 0.49 | 14 | 0.68 | +4.39% |

