# Section 10b — sp500 12m, mp=20, pct=0.045 (recent)

**Runs:** 40 | **Starts:** 5 | **Configs:** 8

## Trading windows (untrimmed, from daily_returns.csv)

| Start | First trade | Last trade | Days |
|---|---|---|---|
| 2023-01-01 | 2024-01-02 | 2025-12-31 | 502 |
| 2023-02-01 | 2024-02-01 | 2025-12-31 | 481 |
| 2023-03-01 | 2024-03-01 | 2025-12-31 | 461 |
| 2023-04-01 | 2024-04-01 | 2025-12-31 | 441 |
| 2023-05-01 | 2024-05-01 | 2025-12-31 | 419 |

## Sharpe Pivot (trimmed, per start date)

| Config | 2023-01-01 | 2023-02-01 | 2023-03-01 | 2023-04-01 | 2023-05-01 | Mean |
|---|---|---|---|---|---|---|
| same_sector_slide3m_noscreen | 1.26 | -0.19 | 1.67 | 1.16 | 0.09 | 0.80 |
| same_sector_slide3m_bd7 | 0.89 | 0.07 | 0.32 | 0.78 | 0.14 | 0.44 |
| same_sector_slide1m_noscreen | 1.33 | 1.37 | 1.32 | 1.33 | 1.23 | 1.32 |
| same_sector_slide1m_bd7 | 0.70 | 0.68 | 0.66 | 0.79 | 0.51 | 0.67 |
| cross_sector_slide3m_noscreen | 0.97 | 1.13 | 0.69 | 1.22 | 1.52 | 1.11 |
| cross_sector_slide3m_bd7 | 0.17 | 1.73 | -0.19 | 0.53 | 1.87 | 0.82 |
| cross_sector_slide1m_noscreen | 1.42 | 1.53 | 1.83 | 2.28 | 2.38 | 1.89 |
| cross_sector_slide1m_bd7 | 0.85 | 0.90 | 1.06 | 1.81 | 1.92 | 1.31 |

## Aggregate (trimmed mean per config)

| Config | Sharpe | Ret% | Trades | AT |
|---|---:|---:|---:|---:|
| cross_sector_slide1m_noscreen | 1.89 | 3.43 | 499.2 | 6.88 |
| same_sector_slide1m_noscreen | 1.32 | 2.75 | 553.8 | 7.21 |
| cross_sector_slide1m_bd7 | 1.31 | 1.60 | 263.2 | 3.21 |
| cross_sector_slide3m_noscreen | 1.11 | 2.72 | 172.8 | 2.25 |
| cross_sector_slide3m_bd7 | 0.82 | 1.24 | 90.4 | 1.05 |
| same_sector_slide3m_noscreen | 0.80 | 2.18 | 193.0 | 2.41 |
| same_sector_slide1m_bd7 | 0.67 | 0.91 | 308.8 | 3.71 |
| same_sector_slide3m_bd7 | 0.44 | 0.70 | 106.4 | 1.21 |

## Untrimmed full-window (mean per config)

| Config | Sharpe | Ret% |
|---|---:|---:|
| cross_sector_slide1m_noscreen | 1.32 | 2.53 |
| same_sector_slide1m_noscreen | 1.29 | 2.65 |
| cross_sector_slide1m_bd7 | 0.63 | 0.84 |
| cross_sector_slide3m_noscreen | 1.11 | 2.72 |
| cross_sector_slide3m_bd7 | 0.82 | 1.24 |
| same_sector_slide3m_noscreen | 0.80 | 2.18 |
| same_sector_slide1m_bd7 | 0.44 | 0.57 |
| same_sector_slide3m_bd7 | 0.44 | 0.70 |

**Best config (trimmed Sharpe):** `cross_sector_slide1m_noscreen` = 1.89 / 3.43%

