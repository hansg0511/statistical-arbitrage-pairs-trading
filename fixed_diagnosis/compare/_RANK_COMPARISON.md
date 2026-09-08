# Config-pair ranking comparison (all pairs)

Methods: separate (score = min(mean recent Sharpe, hist Sharpe)), rank-average (mean dense rank across the two windows, lower = better), joined (single Sharpe of hist ++ recent concatenated series). pct=0.25. Mechanism A joined read from joined_pairs.csv; B joined computed here.

### Mechanism A — Spearman correlation of pair ranks (496 pairs)

| | separate (min) | rank-avg | joined |
|---|---:|---:|---:|
| score_rank | 1.000 | 0.743 | 0.874 |
| rank_avg_rank | 0.743 | 1.000 | 0.877 |
| joined_rank | 0.874 | 0.877 | 1.000 |

### Mechanism A — top 20 by each method

| # | separate (min) | min | rank-avg | avg | joined | J Sh |
|---|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.83 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 45.5 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.04 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.81 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 48.0 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.91 |
| 3 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.70 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 49.0 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 0.90 |
| 4 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.67 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 53.0 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.82 |
| 5 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.60 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 57.0 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_bd7` | 0.78 |
| 6 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.60 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 58.0 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.75 |
| 7 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.58 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 58.0 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_bd7` | 0.74 |
| 8 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide3m_bd7` | 0.57 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 58.0 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.73 |
| 9 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.56 | `sp500-2m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 61.5 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.73 |
| 10 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.56 | `sp500-12m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 62.5 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.72 |
| 11 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.55 | `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 64.5 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.69 |
| 12 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.53 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 67.0 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.69 |
| 13 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 0.53 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 69.0 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-2m/cross_sector_slide3m_bd7` | 0.68 |
| 14 | `sp500-2m/cross_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.53 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 69.5 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.68 |
| 15 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide3m_noscreen` | 0.52 | `sp500-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 70.0 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.66 |
| 16 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.52 | `core-12m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 75.0 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.66 |
| 17 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.52 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 75.5 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_bd7` | 0.65 |
| 18 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.52 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 75.5 | `sp500-2m/cross_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.63 |
| 19 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.51 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 76.0 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.63 |
| 20 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.49 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 76.5 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | 0.63 |

#### Separate (min score)

| # | Pair | Recent | Hist | Joined Sh |
|---|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.83 | 1.14 | 1.04 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.87 | 0.81 | 0.82 |
| 3 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.73 | 0.70 | 0.72 |
| 4 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.91 | 0.67 | 0.73 |
| 5 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.68 | 0.60 | 0.63 |
| 6 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.60 | 0.61 | 0.60 |
| 7 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.06 | 0.58 | 0.73 |
| 8 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide3m_bd7` | 0.57 | 0.61 | 0.57 |
| 9 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.68 | 0.56 | 0.60 |
| 10 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 1.14 | 0.56 | 0.75 |
| 11 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.55 | 0.76 | 0.69 |
| 12 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.73 | 0.53 | 0.60 |
| 13 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 0.78 | 0.53 | 0.62 |
| 14 | `sp500-2m/cross_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.86 | 0.53 | 0.63 |
| 15 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide3m_noscreen` | 0.76 | 0.52 | 0.59 |
| 16 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.52 | 1.09 | 0.91 |
| 17 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.82 | 0.52 | 0.62 |
| 18 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.87 | 0.52 | 0.62 |
| 19 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.74 | 0.51 | 0.60 |
| 20 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.09 | 0.49 | 0.68 |

#### Rank-average

| # | Pair | Recent | Hist | Joined Sh |
|---|---:|---:|---:|---:|
| 1 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 1.14 | 0.56 | 0.75 |
| 2 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.38 | 0.35 | 0.69 |
| 3 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.22 | 0.41 | 0.66 |
| 4 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.36 | 0.33 | 0.66 |
| 5 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 1.19 | 0.37 | 0.61 |
| 6 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.09 | 0.49 | 0.68 |
| 7 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.28 | 0.32 | 0.63 |
| 8 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.06 | 0.58 | 0.73 |
| 9 | `sp500-2m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.16 | 0.37 | 0.62 |
| 10 | `sp500-12m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.28 | 0.29 | 0.55 |
| 11 | `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 1.12 | 0.40 | 0.63 |
| 12 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 1.07 | 0.46 | 0.62 |
| 13 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.08 | 0.42 | 0.63 |
| 14 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.16 | 0.32 | 0.59 |
| 15 | `sp500-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.17 | 0.32 | 0.58 |
| 16 | `core-12m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.24 | 0.24 | 0.54 |
| 17 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.87 | 0.81 | 0.82 |
| 18 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.83 | 1.14 | 1.04 |
| 19 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.91 | 0.67 | 0.73 |
| 20 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 1.04 | 0.42 | 0.62 |

#### Joined Sharpe

| # | Pair | Recent | Hist | Joined Sh |
|---|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.83 | 1.14 | 1.04 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.52 | 1.09 | 0.91 |
| 3 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 0.32 | 1.13 | 0.90 |
| 4 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.87 | 0.81 | 0.82 |
| 5 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_bd7` | 0.19 | 1.01 | 0.78 |
| 6 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 1.14 | 0.56 | 0.75 |
| 7 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_bd7` | -0.00 | 1.03 | 0.74 |
| 8 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.06 | 0.58 | 0.73 |
| 9 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.91 | 0.67 | 0.73 |
| 10 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.73 | 0.70 | 0.72 |
| 11 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.38 | 0.35 | 0.69 |
| 12 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.55 | 0.76 | 0.69 |
| 13 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-2m/cross_sector_slide3m_bd7` | 0.13 | 0.90 | 0.68 |
| 14 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.09 | 0.49 | 0.68 |
| 15 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.36 | 0.33 | 0.66 |
| 16 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.22 | 0.41 | 0.66 |
| 17 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_bd7` | 0.47 | 0.72 | 0.65 |
| 18 | `sp500-2m/cross_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.86 | 0.53 | 0.63 |
| 19 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.28 | 0.32 | 0.63 |
| 20 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | 0.18 | 0.80 | 0.63 |

### Mechanism A — top-20 overlap

| Pair sets | Count |
|---|---:|
| separate ∩ rank-avg | 6 |
| separate ∩ joined | 10 |
| rank-avg ∩ joined | 10 |
| all three | 6 |

Pairs in all three top-20s:
  - sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen
  - sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7
  - sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_noscreen
  - sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/same_sector_slide1m_noscreen
  - sp500-12m/same_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen
  - sp500-12m/same_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7


### Mechanism B — Spearman correlation of pair ranks (496 pairs)

| | separate (min) | rank-avg | joined |
|---|---:|---:|---:|
| score_rank | 1.000 | 0.720 | 0.863 |
| rank_avg_rank | 0.720 | 1.000 | 0.868 |
| joined_rank | 0.863 | 0.868 | 1.000 |

### Mechanism B — top 20 by each method

| # | separate (min) | min | rank-avg | avg | joined | J Sh |
|---|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.83 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 38.0 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.01 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.82 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 48.0 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.91 |
| 3 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.71 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 49.5 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 0.89 |
| 4 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.65 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 53.0 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.84 |
| 5 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.62 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 53.5 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_bd7` | 0.81 |
| 6 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.60 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 55.5 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.76 |
| 7 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.59 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 60.5 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_bd7` | 0.74 |
| 8 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide3m_bd7` | 0.57 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 66.0 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.73 |
| 9 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.57 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 70.0 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.71 |
| 10 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.55 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 71.0 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.69 |
| 11 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 0.55 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 73.5 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.69 |
| 12 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.55 | `sp500-12m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 75.0 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.69 |
| 13 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.54 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide3m_bd7` | 78.0 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-2m/cross_sector_slide3m_bd7` | 0.68 |
| 14 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide3m_noscreen` | 0.54 | `sp500-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 78.0 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 0.68 |
| 15 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.54 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 78.5 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_bd7` | 0.66 |
| 16 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.53 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 82.5 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.66 |
| 17 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.53 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 82.5 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.65 |
| 18 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.52 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 83.0 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | 0.64 |
| 19 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.52 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 83.5 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.64 |
| 20 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.52 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 84.5 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.64 |

#### Separate (min score)

| # | Pair | Recent | Hist | Joined Sh |
|---|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.83 | 0.87 | 0.84 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.82 | 1.09 | 1.01 |
| 3 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.75 | 0.71 | 0.73 |
| 4 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.90 | 0.65 | 0.71 |
| 5 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.68 | 0.62 | 0.64 |
| 6 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 1.08 | 0.60 | 0.76 |
| 7 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.59 | 0.64 | 0.61 |
| 8 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide3m_bd7` | 0.57 | 0.59 | 0.56 |
| 9 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.57 | 0.60 | 0.59 |
| 10 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.75 | 0.55 | 0.63 |
| 11 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 0.78 | 0.55 | 0.63 |
| 12 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.87 | 0.55 | 0.64 |
| 13 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.54 | 0.77 | 0.69 |
| 14 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide3m_noscreen` | 0.76 | 0.54 | 0.60 |
| 15 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.92 | 0.54 | 0.65 |
| 16 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.72 | 0.53 | 0.59 |
| 17 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.04 | 0.53 | 0.69 |
| 18 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.52 | 1.09 | 0.91 |
| 19 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.87 | 0.52 | 0.63 |
| 20 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.79 | 0.52 | 0.61 |

#### Rank-average

| # | Pair | Recent | Hist | Joined Sh |
|---|---:|---:|---:|---:|
| 1 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 1.34 | 0.40 | 0.68 |
| 2 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 1.16 | 0.45 | 0.69 |
| 3 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 1.08 | 0.60 | 0.76 |
| 4 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.19 | 0.35 | 0.61 |
| 5 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.43 | 0.29 | 0.66 |
| 6 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.29 | 0.31 | 0.64 |
| 7 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.04 | 0.53 | 0.69 |
| 8 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 1.06 | 0.44 | 0.60 |
| 9 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.05 | 0.41 | 0.61 |
| 10 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.21 | 0.24 | 0.56 |
| 11 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.14 | 0.29 | 0.56 |
| 12 | `sp500-12m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.19 | 0.23 | 0.49 |
| 13 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide3m_bd7` | 1.05 | 0.35 | 0.53 |
| 14 | `sp500-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.12 | 0.28 | 0.55 |
| 15 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.90 | 0.65 | 0.71 |
| 16 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 1.04 | 0.34 | 0.58 |
| 17 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.82 | 1.09 | 1.01 |
| 18 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.97 | 0.43 | 0.61 |
| 19 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.92 | 0.54 | 0.65 |
| 20 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.83 | 0.87 | 0.84 |

#### Joined Sharpe

| # | Pair | Recent | Hist | Joined Sh |
|---|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.82 | 1.09 | 1.01 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 0.52 | 1.09 | 0.91 |
| 3 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 0.31 | 1.14 | 0.89 |
| 4 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.83 | 0.87 | 0.84 |
| 5 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_bd7` | 0.24 | 1.03 | 0.81 |
| 6 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 1.08 | 0.60 | 0.76 |
| 7 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_bd7` | -0.00 | 1.03 | 0.74 |
| 8 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.75 | 0.71 | 0.73 |
| 9 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.90 | 0.65 | 0.71 |
| 10 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.04 | 0.53 | 0.69 |
| 11 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 0.54 | 0.77 | 0.69 |
| 12 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 1.16 | 0.45 | 0.69 |
| 13 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-2m/cross_sector_slide3m_bd7` | 0.12 | 0.89 | 0.68 |
| 14 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 1.34 | 0.40 | 0.68 |
| 15 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_bd7` | 0.48 | 0.74 | 0.66 |
| 16 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.43 | 0.29 | 0.66 |
| 17 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.92 | 0.54 | 0.65 |
| 18 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | 0.21 | 0.81 | 0.64 |
| 19 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.68 | 0.62 | 0.64 |
| 20 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.87 | 0.55 | 0.64 |

### Mechanism B — top-20 overlap

| Pair sets | Count |
|---|---:|
| separate ∩ rank-avg | 6 |
| separate ∩ joined | 11 |
| rank-avg ∩ joined | 9 |
| all three | 6 |

Pairs in all three top-20s:
  - sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen
  - sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7
  - sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_noscreen
  - sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/same_sector_slide1m_noscreen
  - sp500-12m/same_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen
  - sp500-12m/same_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7


