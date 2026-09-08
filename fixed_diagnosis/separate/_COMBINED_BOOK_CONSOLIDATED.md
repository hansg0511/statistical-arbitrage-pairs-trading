# Combined two-leg book: consolidated sweep (trade-event replay)

Mechanisms A (monthly re-base) and B (entry-flow), pct=0.250. Recent = mean Sharpe over the 5 aligned start-pairs; hist = single aligned window; score = min(recent, hist).

## Mechanism A — top 20 pairs

| Pair | Recent | Range | Hist | Score | R% | H% |
|---|---:|---:|---:|---:|---:|---:|
| sp500-2m/cross_sector_slide3m_bd7 + sp500-12m/cross_sector_slide1m_noscreen | 0.83 | 0.52–1.12 | 1.14 | 0.83 | +6.5% | +8.1% |
| sp500-2m/cross_sector_slide3m_bd7 + sp500-12m/same_sector_slide1m_noscreen | 0.87 | 0.75–1.02 | 0.81 | 0.81 | +8.1% | +5.6% |
| sp500-2m/cross_sector_slide3m_noscreen + sp500-12m/same_sector_slide3m_noscreen | 0.73 | 0.21–1.58 | 0.70 | 0.70 | +9.0% | +7.2% |
| sp500-2m/cross_sector_slide3m_noscreen + sp500-12m/cross_sector_slide1m_noscreen | 0.91 | 0.26–1.38 | 0.67 | 0.67 | +8.6% | +5.6% |
| sp500-2m/same_sector_slide3m_noscreen + sp500-12m/same_sector_slide3m_noscreen | 0.68 | -0.31–1.40 | 0.60 | 0.60 | +7.7% | +5.1% |
| sp500-2m/cross_sector_slide1m_bd7 + sp500-12m/same_sector_slide3m_noscreen | 0.60 | -0.24–1.43 | 0.61 | 0.60 | +6.9% | +3.8% |
| sp500-12m/same_sector_slide3m_noscreen + sp500-12m/cross_sector_slide1m_noscreen | 1.06 | 0.32–1.46 | 0.58 | 0.58 | +11.3% | +4.3% |
| sp500-2m/cross_sector_slide3m_bd7 + sp500-12m/cross_sector_slide3m_bd7 | 0.57 | -0.05–1.39 | 0.61 | 0.57 | +3.5% | +4.8% |
| sp500-2m/same_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen | 0.68 | -0.35–1.36 | 0.56 | 0.56 | +7.4% | +4.0% |
| sp500-12m/same_sector_slide3m_noscreen + sp500-12m/same_sector_slide1m_noscreen | 1.14 | 0.65–1.57 | 0.56 | 0.56 | +14.6% | +4.5% |
| sp500-2m/cross_sector_slide3m_noscreen + sp500-12m/cross_sector_slide1m_bd7 | 0.55 | -0.09–1.22 | 0.76 | 0.55 | +4.3% | +5.6% |
| sp500-2m/same_sector_slide3m_bd7 + sp500-12m/same_sector_slide3m_noscreen | 0.73 | -0.20–1.37 | 0.53 | 0.53 | +7.2% | +3.7% |
| sp500-12m/same_sector_slide3m_noscreen + sp500-12m/same_sector_slide1m_bd7 | 0.78 | -0.01–1.48 | 0.53 | 0.53 | +8.8% | +3.7% |
| sp500-2m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen | 0.86 | 0.26–1.40 | 0.53 | 0.53 | +9.5% | +4.0% |
| sp500-2m/cross_sector_slide3m_bd7 + sp500-12m/cross_sector_slide3m_noscreen | 0.76 | 0.60–0.92 | 0.52 | 0.52 | +7.2% | +4.1% |
| sp500-2m/cross_sector_slide3m_bd7 + sp500-12m/same_sector_slide3m_noscreen | 0.52 | -0.40–1.47 | 1.09 | 0.52 | +6.3% | +8.7% |
| sp500-12m/same_sector_slide3m_noscreen + sp500-12m/cross_sector_slide1m_bd7 | 0.82 | 0.10–1.44 | 0.52 | 0.52 | +7.9% | +3.4% |
| sp500-2m/cross_sector_slide3m_noscreen + sp500-12m/same_sector_slide1m_noscreen | 0.87 | 0.55–1.21 | 0.52 | 0.52 | +9.2% | +4.3% |
| core-12m/same_sector_slide1m_bd7 + sp500-12m/same_sector_slide3m_noscreen | 0.74 | -0.34–1.66 | 0.51 | 0.51 | +8.1% | +2.9% |
| sp500-2m/same_sector_slide1m_noscreen + sp500-12m/cross_sector_slide1m_noscreen | 1.09 | 0.59–1.78 | 0.49 | 0.49 | +9.0% | +2.8% |

## Mechanism A — top 20 pairs by rank-average

Ranked by the mean of each pair\'s recent-rank and hist-rank (lower = better). For each pair, rank against all 496 pairs by recent Sharpe and by hist Sharpe, then average the two ranks. **Leg A = recent-strong.**

| Pair | Rec Rank | Hist Rank | RankAvg | Recent | Hist | Score |
|---|---:|---:|---:|---:|---:|---:|
| sp500-12m/same_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen | 54 | 37 | 45.5 | 1.14 | 0.56 | 0.56 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide1m_noscreen | 14 | 82 | 48.0 | 1.38 | 0.35 | 0.35 |
| sp500-12m/cross_sector_slide1m_noscreen + core-2m/same_sector_slide1m_bd7 | 33 | 65 | 49.0 | 1.22 | 0.41 | 0.41 |
| sp500-12m/cross_sector_slide1m_noscreen + core-2m/same_sector_slide1m_noscreen | 16 | 90 | 53.0 | 1.36 | 0.33 | 0.33 |
| core-2m/same_sector_slide1m_noscreen + sp500-12m/cross_sector_slide3m_bd7 | 41 | 73 | 57.0 | 1.19 | 0.37 | 0.37 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen | 81 | 35 | 58.0 | 1.06 | 0.58 | 0.58 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/same_sector_slide1m_noscreen | 69 | 47 | 58.0 | 1.09 | 0.49 | 0.49 |
| sp500-12m/cross_sector_slide1m_noscreen + core-12m/same_sector_slide1m_bd7 | 24 | 92 | 58.0 | 1.28 | 0.32 | 0.32 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide1m_noscreen | 48 | 75 | 61.5 | 1.16 | 0.37 | 0.37 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/cross_sector_slide3m_bd7 | 22 | 103 | 62.5 | 1.28 | 0.29 | 0.29 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/cross_sector_slide1m_bd7 | 59 | 70 | 64.5 | 1.12 | 0.40 | 0.40 |
| sp500-12m/cross_sector_slide3m_bd7 + sp500-12m/same_sector_slide3m_noscreen | 80 | 54 | 67.0 | 1.07 | 0.46 | 0.46 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/same_sector_slide3m_noscreen | 75 | 63 | 69.0 | 1.08 | 0.42 | 0.42 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/same_sector_slide3m_bd7 | 46 | 93 | 69.5 | 1.16 | 0.32 | 0.32 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide1m_bd7 | 44 | 96 | 70.0 | 1.17 | 0.32 | 0.32 |
| sp500-12m/cross_sector_slide1m_noscreen + core-12m/same_sector_slide3m_bd7 | 29 | 121 | 75.0 | 1.24 | 0.24 | 0.24 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7 | 150 | 1 | 75.5 | 0.83 | 1.14 | 0.83 |
| sp500-12m/same_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7 | 140 | 11 | 75.5 | 0.87 | 0.81 | 0.81 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_noscreen | 126 | 26 | 76.0 | 0.91 | 0.67 | 0.67 |
| sp500-12m/same_sector_slide1m_noscreen + sp500-2m/same_sector_slide3m_noscreen | 89 | 64 | 76.5 | 1.04 | 0.42 | 0.42 |

## Mechanism A — winners (daily_returns.csv written)

- **1.** `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` → recent 0.83 (+6.5%/yr), hist 1.14 (+8.1%/yr) (label `pair_01`)
- **2.** `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` → recent 0.87 (+8.1%/yr), hist 0.81 (+5.6%/yr) (label `pair_02`)
- **3.** `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` → recent 0.73 (+9.0%/yr), hist 0.70 (+7.2%/yr) (label `pair_03`)
- **4.** `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` → recent 0.91 (+8.6%/yr), hist 0.67 (+5.6%/yr) (label `pair_04`)
- **5.** `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` → recent 0.68 (+7.7%/yr), hist 0.60 (+5.1%/yr) (label `pair_05`)

## Mechanism B — top 20 pairs

| Pair | Recent | Range | Hist | Score | R% | H% |
|---|---:|---:|---:|---:|---:|---:|
| sp500-2m/cross_sector_slide3m_bd7 + sp500-12m/same_sector_slide1m_noscreen | 0.83 | 0.63–1.04 | 0.87 | 0.83 | +7.8% | +6.0% |
| sp500-2m/cross_sector_slide3m_bd7 + sp500-12m/cross_sector_slide1m_noscreen | 0.82 | 0.56–1.25 | 1.09 | 0.82 | +6.6% | +7.7% |
| sp500-2m/cross_sector_slide3m_noscreen + sp500-12m/same_sector_slide3m_noscreen | 0.75 | 0.26–1.56 | 0.71 | 0.71 | +9.1% | +7.3% |
| sp500-2m/cross_sector_slide3m_noscreen + sp500-12m/cross_sector_slide1m_noscreen | 0.90 | 0.34–1.38 | 0.65 | 0.65 | +8.6% | +5.4% |
| sp500-2m/same_sector_slide3m_noscreen + sp500-12m/same_sector_slide3m_noscreen | 0.68 | -0.30–1.42 | 0.62 | 0.62 | +7.7% | +5.2% |
| sp500-12m/same_sector_slide3m_noscreen + sp500-12m/same_sector_slide1m_noscreen | 1.08 | 0.55–1.56 | 0.60 | 0.60 | +14.0% | +4.8% |
| sp500-2m/cross_sector_slide1m_bd7 + sp500-12m/same_sector_slide3m_noscreen | 0.59 | -0.21–1.43 | 0.64 | 0.59 | +6.8% | +4.0% |
| sp500-2m/cross_sector_slide3m_bd7 + sp500-12m/cross_sector_slide3m_bd7 | 0.57 | -0.04–1.39 | 0.59 | 0.57 | +3.6% | +4.6% |
| sp500-2m/same_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen | 0.57 | -0.37–1.25 | 0.60 | 0.57 | +6.2% | +4.3% |
| core-12m/same_sector_slide1m_bd7 + sp500-12m/same_sector_slide3m_noscreen | 0.75 | -0.31–1.64 | 0.55 | 0.55 | +8.0% | +3.1% |
| sp500-12m/same_sector_slide3m_noscreen + sp500-12m/same_sector_slide1m_bd7 | 0.78 | 0.03–1.45 | 0.55 | 0.55 | +8.8% | +3.8% |
| sp500-2m/cross_sector_slide3m_noscreen + sp500-12m/same_sector_slide1m_noscreen | 0.87 | 0.63–1.22 | 0.55 | 0.55 | +9.2% | +4.6% |
| sp500-2m/cross_sector_slide3m_noscreen + sp500-12m/cross_sector_slide1m_bd7 | 0.54 | -0.04–1.08 | 0.77 | 0.54 | +4.2% | +5.6% |
| sp500-2m/cross_sector_slide3m_bd7 + sp500-12m/cross_sector_slide3m_noscreen | 0.76 | 0.61–0.93 | 0.54 | 0.54 | +7.2% | +4.3% |
| sp500-2m/same_sector_slide1m_noscreen + sp500-12m/cross_sector_slide1m_noscreen | 0.92 | 0.31–1.65 | 0.54 | 0.54 | +7.9% | +3.1% |
| sp500-2m/same_sector_slide3m_bd7 + sp500-12m/same_sector_slide3m_noscreen | 0.72 | -0.19–1.34 | 0.53 | 0.53 | +7.0% | +3.7% |
| sp500-12m/same_sector_slide3m_noscreen + sp500-12m/cross_sector_slide1m_noscreen | 1.04 | 0.30–1.35 | 0.53 | 0.53 | +11.2% | +3.9% |
| sp500-2m/cross_sector_slide3m_bd7 + sp500-12m/same_sector_slide3m_noscreen | 0.52 | -0.37–1.45 | 1.09 | 0.52 | +6.3% | +8.7% |
| sp500-2m/cross_sector_slide1m_bd7 + sp500-12m/same_sector_slide1m_noscreen | 0.87 | 0.65–1.09 | 0.52 | 0.52 | +8.0% | +2.6% |
| sp500-12m/same_sector_slide3m_noscreen + sp500-12m/cross_sector_slide1m_bd7 | 0.79 | 0.12–1.21 | 0.52 | 0.52 | +7.6% | +3.4% |

## Mechanism B — top 20 pairs by rank-average

Ranked by the mean of each pair\'s recent-rank and hist-rank (lower = better). For each pair, rank against all 496 pairs by recent Sharpe and by hist Sharpe, then average the two ranks. **Leg A = recent-strong.**

| Pair | Rec Rank | Hist Rank | RankAvg | Recent | Hist | Score |
|---|---:|---:|---:|---:|---:|---:|
| core-2m/same_sector_slide1m_noscreen + sp500-12m/cross_sector_slide3m_bd7 | 8 | 68 | 38.0 | 1.34 | 0.40 | 0.40 |
| sp500-12m/cross_sector_slide1m_bd7 + core-2m/same_sector_slide1m_noscreen | 38 | 58 | 48.0 | 1.16 | 0.45 | 0.45 |
| sp500-12m/same_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen | 66 | 33 | 49.5 | 1.08 | 0.60 | 0.60 |
| sp500-12m/cross_sector_slide1m_noscreen + core-2m/same_sector_slide1m_bd7 | 25 | 81 | 53.0 | 1.19 | 0.35 | 0.35 |
| sp500-12m/cross_sector_slide1m_noscreen + core-2m/same_sector_slide1m_noscreen | 2 | 105 | 53.5 | 1.43 | 0.29 | 0.29 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide1m_noscreen | 12 | 99 | 55.5 | 1.29 | 0.31 | 0.31 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen | 76 | 45 | 60.5 | 1.04 | 0.53 | 0.53 |
| sp500-12m/cross_sector_slide3m_bd7 + sp500-12m/same_sector_slide3m_noscreen | 70 | 62 | 66.0 | 1.06 | 0.44 | 0.44 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/same_sector_slide3m_noscreen | 73 | 67 | 70.0 | 1.05 | 0.41 | 0.41 |
| sp500-12m/cross_sector_slide1m_noscreen + core-12m/same_sector_slide1m_bd7 | 21 | 121 | 71.0 | 1.21 | 0.24 | 0.24 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/same_sector_slide3m_bd7 | 43 | 104 | 73.5 | 1.14 | 0.29 | 0.29 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/cross_sector_slide3m_bd7 | 24 | 126 | 75.0 | 1.19 | 0.23 | 0.23 |
| core-2m/same_sector_slide1m_bd7 + sp500-12m/cross_sector_slide3m_bd7 | 74 | 82 | 78.0 | 1.05 | 0.35 | 0.35 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide1m_bd7 | 47 | 109 | 78.0 | 1.12 | 0.28 | 0.28 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_noscreen | 131 | 26 | 78.5 | 0.90 | 0.65 | 0.65 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7 | 163 | 2 | 82.5 | 0.82 | 1.09 | 0.82 |
| sp500-12m/same_sector_slide1m_noscreen + sp500-2m/same_sector_slide3m_bd7 | 77 | 88 | 82.5 | 1.04 | 0.34 | 0.34 |
| sp500-12m/same_sector_slide1m_noscreen + sp500-2m/same_sector_slide3m_noscreen | 101 | 65 | 83.0 | 0.97 | 0.43 | 0.43 |
| sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/same_sector_slide1m_noscreen | 124 | 43 | 83.5 | 0.92 | 0.54 | 0.54 |
| sp500-12m/same_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7 | 160 | 9 | 84.5 | 0.83 | 0.87 | 0.83 |

## Mechanism B — winners (daily_returns.csv written)

- **1.** `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` → recent 0.83 (+7.8%/yr), hist 0.87 (+6.0%/yr) (label `pair_01`)
- **2.** `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` → recent 0.82 (+6.6%/yr), hist 1.09 (+7.7%/yr) (label `pair_02`)
- **3.** `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` → recent 0.75 (+9.1%/yr), hist 0.71 (+7.3%/yr) (label `pair_03`)
- **4.** `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` → recent 0.90 (+8.6%/yr), hist 0.65 (+5.4%/yr) (label `pair_04`)
- **5.** `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` → recent 0.68 (+7.7%/yr), hist 0.62 (+5.2%/yr) (label `pair_05`)

