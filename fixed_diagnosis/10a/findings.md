# Section 10a — core 12m, mp=20, pct=0.045 (recent)

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
| same_sector_slide3m_noscreen | 0.41 | 0.17 | -0.02 | 0.54 | 0.18 | 0.25 |
| same_sector_slide3m_bd7 | -0.65 | 0.80 | 0.11 | -0.66 | 0.96 | 0.11 |
| same_sector_slide1m_noscreen | 0.28 | 0.28 | 0.25 | 0.26 | 0.28 | 0.27 |
| same_sector_slide1m_bd7 | 0.18 | 0.18 | 0.35 | 0.36 | 0.32 | 0.28 |
| cross_sector_slide3m_noscreen | 0.60 | -0.13 | 1.00 | 0.79 | -0.25 | 0.40 |
| cross_sector_slide3m_bd7 | 0.08 | 0.24 | 1.02 | -0.08 | 0.24 | 0.30 |
| cross_sector_slide1m_noscreen | 0.79 | 0.77 | 0.76 | 0.83 | 0.84 | 0.80 |
| cross_sector_slide1m_bd7 | 0.55 | 0.49 | 0.53 | 0.47 | 0.43 | 0.49 |

## Aggregate (trimmed mean per config)

| Config | Sharpe | Ret% | Trades | AT |
|---|---:|---:|---:|---:|
| cross_sector_slide1m_noscreen | 0.80 | 1.51 | 425.0 | 5.42 |
| cross_sector_slide1m_bd7 | 0.49 | 0.63 | 225.2 | 2.81 |
| cross_sector_slide3m_noscreen | 0.40 | 0.99 | 143.6 | 1.63 |
| cross_sector_slide3m_bd7 | 0.30 | 0.39 | 76.8 | 0.86 |
| same_sector_slide1m_bd7 | 0.28 | 0.11 | 50.4 | 0.56 |
| same_sector_slide1m_noscreen | 0.27 | 0.20 | 95.0 | 1.11 |
| same_sector_slide3m_noscreen | 0.25 | 0.21 | 33.4 | 0.35 |
| same_sector_slide3m_bd7 | 0.11 | 0.01 | 17.8 | 0.17 |

## Untrimmed full-window (mean per config)

| Config | Sharpe | Ret% |
|---|---:|---:|
| cross_sector_slide1m_noscreen | 0.73 | 1.31 |
| cross_sector_slide1m_bd7 | 0.46 | 0.55 |
| cross_sector_slide3m_noscreen | 0.40 | 0.99 |
| cross_sector_slide3m_bd7 | 0.30 | 0.39 |
| same_sector_slide1m_bd7 | -0.10 | -0.04 |
| same_sector_slide1m_noscreen | 0.20 | 0.14 |
| same_sector_slide3m_noscreen | 0.25 | 0.21 |
| same_sector_slide3m_bd7 | 0.11 | 0.01 |

**Best config (trimmed Sharpe):** `cross_sector_slide1m_noscreen` = 0.80 / 1.51%

