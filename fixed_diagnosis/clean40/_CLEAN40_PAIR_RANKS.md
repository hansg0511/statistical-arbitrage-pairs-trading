# clean40 all-496 pair evaluation

Fixed leg inputs: `fixed_diagnosis/_sweep_pct25`; pct=0.25; capital=$1M. Momentum parameters: lookback=84, step=0.40, bounds=[0.10, 0.90]. Recent values are means over five aligned starts; historical is the single aligned 2015-2019 start; joined concatenates historical and each recent series.

## Mechanism A

### Top 20 by separate score

| # | Pair | Recent Sh | Recent Ret% | Hist Sh | Hist Ret% | Joined Sh | Score |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.09 | +9.45% | 1.12 | +9.10% | 1.11 | 1.09 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.89 | +8.93% | 0.78 | +6.24% | 0.81 | 0.78 |
| 3 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.06 | +9.62% | 0.72 | +4.72% | 0.82 | 0.72 |
| 4 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.82 | +10.26% | 0.71 | +6.29% | 0.76 | 0.71 |
| 5 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.97 | +10.12% | 0.68 | +5.62% | 0.76 | 0.68 |
| 6 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 1.16 | +12.00% | 0.66 | +6.11% | 0.78 | 0.66 |
| 7 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 1.01 | +13.20% | 0.64 | +5.43% | 0.76 | 0.64 |
| 8 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.63 | +8.06% | 0.68 | +7.85% | 0.67 | 0.63 |
| 9 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 0.61 | +4.09% | 1.05 | +7.93% | 0.93 | 0.61 |
| 10 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.60 | +7.81% | 0.61 | +4.64% | 0.61 | 0.60 |
| 11 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.67 | +7.06% | 0.60 | +4.44% | 0.63 | 0.60 |
| 12 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.75 | +8.08% | 0.58 | +5.81% | 0.63 | 0.58 |
| 13 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 0.56 | +6.97% | 0.65 | +4.92% | 0.63 | 0.56 |
| 14 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 1.06 | +10.90% | 0.55 | +3.37% | 0.71 | 0.55 |
| 15 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 0.57 | +3.45% | 0.53 | +2.56% | 0.54 | 0.53 |
| 16 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.95 | +7.19% | 0.53 | +3.04% | 0.66 | 0.53 |
| 17 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.34 | +11.41% | 0.53 | +3.14% | 0.78 | 0.53 |
| 18 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.13 | +12.94% | 0.53 | +4.29% | 0.72 | 0.53 |
| 19 | `sp500-12m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 1.00 | +10.44% | 0.53 | +3.49% | 0.68 | 0.53 |
| 20 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.92 | +8.99% | 0.52 | +4.43% | 0.63 | 0.52 |

### Top 20 by rank-average

| # | Pair | Recent Sh | Recent Ret% | Hist Sh | Hist Ret% | Joined Sh | Score |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.09 | +9.45% | 1.12 | +9.10% | 1.11 | 1.09 |
| 2 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.34 | +11.41% | 0.53 | +3.14% | 0.78 | 0.53 |
| 3 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 1.16 | +12.00% | 0.66 | +6.11% | 0.78 | 0.66 |
| 4 | `core-2m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 1.39 | +11.84% | 0.45 | +2.55% | 0.76 | 0.45 |
| 5 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.25 | +10.18% | 0.49 | +2.57% | 0.74 | 0.49 |
| 6 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.06 | +9.62% | 0.72 | +4.72% | 0.82 | 0.72 |
| 7 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.24 | +13.39% | 0.46 | +3.04% | 0.71 | 0.46 |
| 8 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.13 | +12.94% | 0.53 | +4.29% | 0.72 | 0.53 |
| 9 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 1.06 | +10.90% | 0.55 | +3.37% | 0.71 | 0.55 |
| 10 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 1.01 | +13.20% | 0.64 | +5.43% | 0.76 | 0.64 |
| 11 | `core-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.22 | +11.73% | 0.38 | +2.52% | 0.64 | 0.38 |
| 12 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.97 | +10.12% | 0.68 | +5.62% | 0.76 | 0.68 |
| 13 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.08 | +9.37% | 0.45 | +2.83% | 0.64 | 0.45 |
| 14 | `sp500-2m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.23 | +11.60% | 0.32 | +2.02% | 0.61 | 0.32 |
| 15 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 1.14 | +8.31% | 0.38 | +2.06% | 0.62 | 0.38 |
| 16 | `sp500-12m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 1.00 | +10.44% | 0.53 | +3.49% | 0.68 | 0.53 |
| 17 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 1.06 | +10.80% | 0.45 | +2.93% | 0.65 | 0.45 |
| 18 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.89 | +8.93% | 0.78 | +6.24% | 0.81 | 0.78 |
| 19 | `sp500-12m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.21 | +10.65% | 0.31 | +1.98% | 0.58 | 0.31 |
| 20 | `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 1.00 | +9.09% | 0.48 | +2.98% | 0.64 | 0.48 |

### Top 20 by joined Sharpe

| # | Pair | Recent Sh | Recent Ret% | Hist Sh | Hist Ret% | Joined Sh | Score |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.09 | +9.45% | 1.12 | +9.10% | 1.11 | 1.09 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 0.61 | +4.09% | 1.05 | +7.93% | 0.93 | 0.61 |
| 3 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.06 | +9.62% | 0.72 | +4.72% | 0.82 | 0.72 |
| 4 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.89 | +8.93% | 0.78 | +6.24% | 0.81 | 0.78 |
| 5 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 1.16 | +12.00% | 0.66 | +6.11% | 0.78 | 0.66 |
| 6 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.34 | +11.41% | 0.53 | +3.14% | 0.78 | 0.53 |
| 7 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_bd7` | 0.18 | +1.17% | 0.98 | +7.65% | 0.77 | 0.18 |
| 8 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.97 | +10.12% | 0.68 | +5.62% | 0.76 | 0.68 |
| 9 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.50 | +6.86% | 0.87 | +8.24% | 0.76 | 0.50 |
| 10 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 1.01 | +13.20% | 0.64 | +5.43% | 0.76 | 0.64 |
| 11 | `core-2m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 1.39 | +11.84% | 0.45 | +2.55% | 0.76 | 0.45 |
| 12 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.82 | +10.26% | 0.71 | +6.29% | 0.76 | 0.71 |
| 13 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.25 | +10.18% | 0.49 | +2.57% | 0.74 | 0.49 |
| 14 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | 0.21 | +1.68% | 0.91 | +12.04% | 0.73 | 0.21 |
| 15 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.13 | +12.94% | 0.53 | +4.29% | 0.72 | 0.53 |
| 16 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 1.06 | +10.90% | 0.55 | +3.37% | 0.71 | 0.55 |
| 17 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.24 | +13.39% | 0.46 | +3.04% | 0.71 | 0.46 |
| 18 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_bd7` | 0.00 | -0.33% | 0.98 | +7.60% | 0.71 | 0.00 |
| 19 | `sp500-12m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 1.00 | +10.44% | 0.53 | +3.49% | 0.68 | 0.53 |
| 20 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.63 | +8.06% | 0.68 | +7.85% | 0.67 | 0.63 |

Top-20 intersection across all three methods: **10** pairs.

## Mechanism B

### Top 20 by separate score

| # | Pair | Recent Sh | Recent Ret% | Hist Sh | Hist Ret% | Joined Sh | Score |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.14 | +9.81% | 1.10 | +8.83% | 1.11 | 1.10 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.83 | +8.30% | 0.80 | +6.37% | 0.81 | 0.80 |
| 3 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.93 | +8.85% | 0.77 | +5.18% | 0.81 | 0.77 |
| 4 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.80 | +9.99% | 0.70 | +6.23% | 0.75 | 0.70 |
| 5 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.92 | +12.25% | 0.67 | +5.68% | 0.75 | 0.67 |
| 6 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.00 | +10.32% | 0.65 | +5.32% | 0.75 | 0.65 |
| 7 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 1.15 | +11.82% | 0.65 | +5.99% | 0.77 | 0.65 |
| 8 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.63 | +8.05% | 0.68 | +7.79% | 0.67 | 0.63 |
| 9 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 0.62 | +4.10% | 1.04 | +7.87% | 0.93 | 0.62 |
| 10 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.75 | +8.11% | 0.60 | +6.01% | 0.64 | 0.60 |
| 11 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.63 | +6.62% | 0.59 | +4.35% | 0.61 | 0.59 |
| 12 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.59 | +7.52% | 0.64 | +4.86% | 0.62 | 0.59 |
| 13 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 0.98 | +10.22% | 0.56 | +3.52% | 0.70 | 0.56 |
| 14 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 0.56 | +6.93% | 0.69 | +5.15% | 0.65 | 0.56 |
| 15 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 0.54 | +3.18% | 0.60 | +2.89% | 0.56 | 0.54 |
| 16 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.82 | +8.02% | 0.52 | +2.96% | 0.61 | 0.52 |
| 17 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.36 | +11.64% | 0.51 | +3.03% | 0.78 | 0.51 |
| 18 | `core-2m/same_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide1m_noscreen` | 0.82 | +7.10% | 0.51 | +3.19% | 0.61 | 0.51 |
| 19 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide3m_bd7` | 0.75 | +5.59% | 0.51 | +4.49% | 0.54 | 0.51 |
| 20 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.50 | +6.76% | 0.86 | +8.16% | 0.76 | 0.50 |

### Top 20 by rank-average

| # | Pair | Recent Sh | Recent Ret% | Hist Sh | Hist Ret% | Joined Sh | Score |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.14 | +9.81% | 1.10 | +8.83% | 1.11 | 1.10 |
| 2 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.36 | +11.64% | 0.51 | +3.03% | 0.78 | 0.51 |
| 3 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 1.15 | +11.82% | 0.65 | +5.99% | 0.77 | 0.65 |
| 4 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.15 | +13.14% | 0.49 | +3.91% | 0.70 | 0.49 |
| 5 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.00 | +10.32% | 0.65 | +5.32% | 0.75 | 0.65 |
| 6 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.24 | +10.08% | 0.40 | +2.05% | 0.67 | 0.40 |
| 7 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 1.29 | +10.15% | 0.37 | +2.05% | 0.66 | 0.37 |
| 8 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.18 | +13.21% | 0.40 | +2.63% | 0.66 | 0.40 |
| 9 | `core-2m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 1.14 | +10.25% | 0.41 | +2.26% | 0.65 | 0.41 |
| 10 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.93 | +8.85% | 0.77 | +5.18% | 0.81 | 0.77 |
| 11 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 0.98 | +10.22% | 0.56 | +3.52% | 0.70 | 0.56 |
| 12 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.17 | +10.81% | 0.39 | +2.43% | 0.63 | 0.39 |
| 13 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.92 | +12.25% | 0.67 | +5.68% | 0.75 | 0.67 |
| 14 | `core-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.25 | +11.98% | 0.30 | +1.94% | 0.59 | 0.30 |
| 15 | `sp500-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.00 | +8.72% | 0.41 | +2.54% | 0.59 | 0.41 |
| 16 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.97 | +7.59% | 0.46 | +2.64% | 0.62 | 0.46 |
| 17 | `sp500-12m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.25 | +11.04% | 0.28 | +1.76% | 0.57 | 0.28 |
| 18 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.95 | +9.33% | 0.47 | +3.97% | 0.60 | 0.47 |
| 19 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.35 | +11.89% | 0.25 | +1.45% | 0.59 | 0.25 |
| 20 | `core-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 1.19 | +12.25% | 0.29 | +2.19% | 0.53 | 0.29 |

### Top 20 by joined Sharpe

| # | Pair | Recent Sh | Recent Ret% | Hist Sh | Hist Ret% | Joined Sh | Score |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.14 | +9.81% | 1.10 | +8.83% | 1.11 | 1.10 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 0.62 | +4.10% | 1.04 | +7.87% | 0.93 | 0.62 |
| 3 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.93 | +8.85% | 0.77 | +5.18% | 0.81 | 0.77 |
| 4 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.83 | +8.30% | 0.80 | +6.37% | 0.81 | 0.80 |
| 5 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_bd7` | 0.20 | +1.33% | 1.02 | +7.96% | 0.80 | 0.20 |
| 6 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.36 | +11.64% | 0.51 | +3.03% | 0.78 | 0.51 |
| 7 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 1.15 | +11.82% | 0.65 | +5.99% | 0.77 | 0.65 |
| 8 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.50 | +6.76% | 0.86 | +8.16% | 0.76 | 0.50 |
| 9 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.92 | +12.25% | 0.67 | +5.68% | 0.75 | 0.67 |
| 10 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.00 | +10.32% | 0.65 | +5.32% | 0.75 | 0.65 |
| 11 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.80 | +9.99% | 0.70 | +6.23% | 0.75 | 0.70 |
| 12 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | 0.24 | +2.15% | 0.92 | +12.12% | 0.74 | 0.24 |
| 13 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_bd7` | -0.01 | -0.46% | 0.97 | +7.55% | 0.70 | -0.01 |
| 14 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 0.98 | +10.22% | 0.56 | +3.52% | 0.70 | 0.56 |
| 15 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.15 | +13.14% | 0.49 | +3.91% | 0.70 | 0.49 |
| 16 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.24 | +10.08% | 0.40 | +2.05% | 0.67 | 0.40 |
| 17 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.63 | +8.05% | 0.68 | +7.79% | 0.67 | 0.63 |
| 18 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 1.29 | +10.15% | 0.37 | +2.05% | 0.66 | 0.37 |
| 19 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.18 | +13.21% | 0.40 | +2.63% | 0.66 | 0.40 |
| 20 | `core-2m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 1.14 | +10.25% | 0.41 | +2.26% | 0.65 | 0.41 |

Top-20 intersection across all three methods: **7** pairs.

## Cross-mechanism consensus

Pairs in the top 20 of all three methods for both mechanisms: **7**.

- `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide1m_bd7`

- `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7`

- `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide1m_noscreen`

- `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide3m_noscreen`

- `sp500-12m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen`

- `sp500-12m/same_sector_slide1m_bd7` + `sp500-12m/same_sector_slide1m_noscreen`

- `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen`

