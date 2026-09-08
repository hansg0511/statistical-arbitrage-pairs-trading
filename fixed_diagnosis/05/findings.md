# Section 05 — core 2m, mp=5, pct=0.18 (recent)

**Runs:** 40 | **Starts:** 5 | **Configs:** 8

## Trading windows (untrimmed, from daily_returns.csv)

| Start | First trade | Last trade | Days |
|---|---|---|---|
| 2023-11-01 | 2024-01-02 | 2025-12-31 | 502 |
| 2023-12-01 | 2024-02-01 | 2025-12-31 | 481 |
| 2024-01-01 | 2024-03-01 | 2025-12-31 | 461 |
| 2024-02-01 | 2024-04-01 | 2025-12-31 | 441 |
| 2024-03-01 | 2024-05-01 | 2025-12-31 | 419 |

## Sharpe Pivot (trimmed, per start date)

| Config | 2023-11-01 | 2023-12-01 | 2024-01-01 | 2024-02-01 | 2024-03-01 | Mean |
|---|---|---|---|---|---|---|
| same_sector_slide3m_noscreen | 0.67 | -0.23 | 1.48 | 0.52 | -0.14 | 0.46 |
| same_sector_slide3m_bd7 | -0.05 | -0.06 | 1.26 | 0.01 | 0.29 | 0.29 |
| same_sector_slide1m_noscreen | 1.24 | 1.37 | 1.41 | 1.51 | 1.47 | 1.40 |
| same_sector_slide1m_bd7 | 1.06 | 1.28 | 1.40 | 1.47 | 1.40 | 1.32 |
| cross_sector_slide3m_noscreen | 1.18 | -0.32 | 0.98 | 1.26 | 0.12 | 0.65 |
| cross_sector_slide3m_bd7 | 0.30 | -0.20 | -0.04 | 0.32 | 0.00 | 0.08 |
| cross_sector_slide1m_noscreen | 0.82 | 0.89 | 1.36 | 1.31 | 1.35 | 1.15 |
| cross_sector_slide1m_bd7 | -0.07 | 0.02 | -0.04 | -0.03 | -0.11 | -0.05 |

## Aggregate (trimmed mean per config)

| Config | Sharpe | Ret% | Trades | AT |
|---|---:|---:|---:|---:|
| same_sector_slide1m_noscreen | 1.40 | 4.79 | 123.0 | 1.65 |
| same_sector_slide1m_bd7 | 1.32 | 3.21 | 74.6 | 0.94 |
| cross_sector_slide1m_noscreen | 1.15 | 3.90 | 105.4 | 1.58 |
| cross_sector_slide3m_noscreen | 0.65 | 2.99 | 35.0 | 0.50 |
| same_sector_slide3m_noscreen | 0.46 | 2.62 | 43.6 | 0.55 |
| same_sector_slide3m_bd7 | 0.29 | 1.53 | 26.8 | 0.33 |
| cross_sector_slide3m_bd7 | 0.08 | 0.01 | 18.0 | 0.26 |
| cross_sector_slide1m_bd7 | -0.05 | -0.12 | 53.8 | 0.83 |

## Untrimmed full-window (mean per config)

| Config | Sharpe | Ret% |
|---|---:|---:|
| same_sector_slide1m_noscreen | 0.99 | 3.45 |
| same_sector_slide1m_bd7 | 0.76 | 1.88 |
| cross_sector_slide1m_noscreen | 1.10 | 3.73 |
| cross_sector_slide3m_noscreen | 0.65 | 2.99 |
| same_sector_slide3m_noscreen | 0.46 | 2.62 |
| same_sector_slide3m_bd7 | 0.29 | 1.53 |
| cross_sector_slide3m_bd7 | 0.08 | 0.01 |
| cross_sector_slide1m_bd7 | -0.03 | -0.09 |

**Best config (trimmed Sharpe):** `same_sector_slide1m_noscreen` = 1.40 / 4.79%

