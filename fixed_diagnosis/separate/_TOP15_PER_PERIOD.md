# Top 15 configs per period

Universe: 32 legs = 4 strategies (core-2m, sp500-2m, core-12m, sp500-12m) x 8 configs (same/cross-sector x slide 1m/3m x bd7/noscreen), pct=0.25.

Recent = mean annualized Sharpe/return over the 5 aligned start-pairs (2m: 2023-11..2024-03; 12m: 2023-01..2023-05). Historical = single aligned start (08a/09a: 2014-11-01; 08b/09b: 2014-01-01). Ranks across the full 32-leg set.

## Recent — top 15

| Rank(rec) | Config | Recent Sh | Recent Ret% | Rank(hist) | Hist Sh | Hist Ret% |
|---|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-12m/cross_sector_slide1m_noscreen` | 1.84 | +19.54% | 5 | 0.44 | +3.25% |
| 2 | `core-2m/cross_sector_slide1m_noscreen` | 1.51 | +20.16% | 28 | -0.57 | -6.64% |
| 3 | `sp500-12m/same_sector_slide1m_noscreen` | 1.33 | +15.90% | 6 | 0.40 | +2.86% |
| 4 | `core-2m/same_sector_slide1m_bd7` | 1.30 | +8.19% | 19 | -0.10 | -0.60% |
| 5 | `sp500-12m/cross_sector_slide1m_bd7` | 1.29 | +8.99% | 3 | 0.56 | +3.02% |
| 6 | `core-2m/same_sector_slide1m_noscreen` | 1.28 | +12.05% | 18 | -0.10 | -0.90% |
| 7 | `sp500-12m/cross_sector_slide3m_noscreen` | 1.10 | +14.85% | 23 | -0.22 | -3.72% |
| 8 | `core-12m/cross_sector_slide1m_noscreen` | 0.81 | +8.54% | 26 | -0.44 | -3.44% |
| 9 | `sp500-12m/cross_sector_slide3m_bd7` | 0.81 | +6.91% | 10 | 0.30 | +2.30% |
| 10 | `sp500-12m/same_sector_slide3m_noscreen` | 0.81 | +12.32% | 8 | 0.37 | +3.44% |
| 11 | `core-2m/cross_sector_slide3m_noscreen` | 0.79 | +15.65% | 22 | -0.18 | -8.92% |
| 12 | `sp500-12m/same_sector_slide1m_bd7` | 0.68 | +5.02% | 4 | 0.50 | +2.67% |
| 13 | `core-12m/cross_sector_slide1m_bd7` | 0.51 | +3.51% | 9 | 0.32 | +1.45% |
| 14 | `core-2m/same_sector_slide3m_noscreen` | 0.50 | +7.01% | 27 | -0.56 | -5.39% |
| 15 | `core-2m/same_sector_slide3m_bd7` | 0.47 | +4.47% | 29 | -0.64 | -3.85% |

## Historical — top 15

| Rank(hist) | Config | Hist Sh | Hist Ret% | Rank(rec) | Recent Sh | Recent Ret% |
|---|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` | 0.88 | +7.69% | 30 | -0.38 | -3.66% |
| 2 | `sp500-2m/cross_sector_slide3m_noscreen` | 0.62 | +9.34% | 19 | 0.41 | +4.53% |
| 3 | `sp500-12m/cross_sector_slide1m_bd7` | 0.56 | +3.02% | 5 | 1.29 | +8.99% |
| 4 | `sp500-12m/same_sector_slide1m_bd7` | 0.50 | +2.67% | 12 | 0.68 | +5.02% |
| 5 | `sp500-12m/cross_sector_slide1m_noscreen` | 0.44 | +3.25% | 1 | 1.84 | +19.54% |
| 6 | `sp500-12m/same_sector_slide1m_noscreen` | 0.40 | +2.86% | 3 | 1.33 | +15.90% |
| 7 | `sp500-2m/cross_sector_slide1m_bd7` | 0.39 | +1.86% | 31 | -0.39 | -3.36% |
| 8 | `sp500-12m/same_sector_slide3m_noscreen` | 0.37 | +3.44% | 10 | 0.81 | +12.32% |
| 9 | `core-12m/cross_sector_slide1m_bd7` | 0.32 | +1.45% | 13 | 0.51 | +3.51% |
| 10 | `sp500-12m/cross_sector_slide3m_bd7` | 0.30 | +2.30% | 9 | 0.81 | +6.91% |
| 11 | `sp500-2m/same_sector_slide1m_noscreen` | 0.28 | +1.70% | 29 | -0.04 | -0.63% |
| 12 | `sp500-2m/same_sector_slide3m_bd7` | 0.20 | +1.12% | 23 | 0.29 | +1.96% |
| 13 | `sp500-12m/same_sector_slide3m_bd7` | 0.19 | +1.08% | 17 | 0.44 | +3.58% |
| 14 | `sp500-2m/same_sector_slide3m_noscreen` | 0.19 | +1.50% | 20 | 0.33 | +4.09% |
| 15 | `core-12m/same_sector_slide1m_bd7` | 0.13 | +0.25% | 25 | 0.28 | +0.58% |

