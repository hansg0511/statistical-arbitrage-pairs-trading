# Section 06 — core 2m, mp=20, pct=0.045 (recent)

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
| same_sector_slide3m_noscreen | 0.26 | 0.25 | 1.81 | -0.19 | 0.35 | 0.50 |
| same_sector_slide3m_bd7 | 0.40 | -0.20 | 1.61 | 0.45 | 0.11 | 0.47 |
| same_sector_slide1m_noscreen | 1.23 | 1.36 | 1.23 | 1.33 | 1.21 | 1.27 |
| same_sector_slide1m_bd7 | 1.06 | 1.35 | 1.37 | 1.44 | 1.29 | 1.30 |
| cross_sector_slide3m_noscreen | 1.27 | -0.20 | 1.48 | 1.39 | 0.06 | 0.80 |
| cross_sector_slide3m_bd7 | -0.39 | -0.35 | 0.81 | -0.19 | -0.09 | -0.04 |
| cross_sector_slide1m_noscreen | 1.33 | 1.44 | 1.61 | 1.57 | 1.69 | 1.53 |
| cross_sector_slide1m_bd7 | 0.19 | 0.30 | 0.36 | 0.30 | 0.34 | 0.30 |

## Aggregate (trimmed mean per config)

| Config | Sharpe | Ret% | Trades | AT |
|---|---:|---:|---:|---:|
| cross_sector_slide1m_noscreen | 1.53 | 3.57 | 460.2 | 6.34 |
| same_sector_slide1m_bd7 | 1.30 | 1.46 | 235.8 | 3.06 |
| same_sector_slide1m_noscreen | 1.27 | 2.13 | 435.0 | 5.71 |
| cross_sector_slide3m_noscreen | 0.80 | 2.84 | 154.8 | 2.02 |
| same_sector_slide3m_noscreen | 0.50 | 1.31 | 157.4 | 1.95 |
| same_sector_slide3m_bd7 | 0.47 | 0.83 | 84.8 | 1.03 |
| cross_sector_slide1m_bd7 | 0.30 | 0.46 | 235.2 | 3.06 |
| cross_sector_slide3m_bd7 | -0.04 | 0.03 | 78.2 | 0.97 |

## Untrimmed full-window (mean per config)

| Config | Sharpe | Ret% |
|---|---:|---:|
| cross_sector_slide1m_noscreen | 1.55 | 3.44 |
| same_sector_slide1m_bd7 | 0.91 | 1.00 |
| same_sector_slide1m_noscreen | 0.84 | 1.41 |
| cross_sector_slide3m_noscreen | 0.80 | 2.84 |
| same_sector_slide3m_noscreen | 0.50 | 1.31 |
| same_sector_slide3m_bd7 | 0.47 | 0.83 |
| cross_sector_slide1m_bd7 | 0.27 | 0.39 |
| cross_sector_slide3m_bd7 | -0.04 | 0.03 |

**Best config (trimmed Sharpe):** `cross_sector_slide1m_noscreen` = 1.53 / 3.57%

