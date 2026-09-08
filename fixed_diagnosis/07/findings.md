# Section 07 — sp500 2m, mp=20, pct=0.045 (recent)

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
| same_sector_slide3m_noscreen | 1.33 | 0.27 | -1.01 | 0.66 | 0.47 | 0.34 |
| same_sector_slide3m_bd7 | 1.28 | 0.31 | -1.55 | 0.94 | 0.45 | 0.29 |
| same_sector_slide1m_noscreen | 0.08 | 0.02 | -0.30 | -0.01 | -0.04 | -0.05 |
| same_sector_slide1m_bd7 | -0.22 | -0.30 | -0.57 | -0.46 | -0.51 | -0.41 |
| cross_sector_slide3m_noscreen | -0.05 | 0.49 | 0.83 | -0.00 | 0.58 | 0.37 |
| cross_sector_slide3m_bd7 | -0.36 | -0.76 | 0.22 | -0.38 | -0.78 | -0.41 |
| cross_sector_slide1m_noscreen | 0.36 | 0.39 | 0.56 | 0.49 | 0.30 | 0.42 |
| cross_sector_slide1m_bd7 | -0.31 | -0.41 | -0.41 | -0.46 | -0.61 | -0.44 |

## Aggregate (trimmed mean per config)

| Config | Sharpe | Ret% | Trades | AT |
|---|---:|---:|---:|---:|
| cross_sector_slide1m_noscreen | 0.42 | 0.85 | 479.6 | 6.52 |
| cross_sector_slide3m_noscreen | 0.37 | 0.86 | 167.0 | 2.10 |
| same_sector_slide3m_noscreen | 0.34 | 0.84 | 169.0 | 2.17 |
| same_sector_slide3m_bd7 | 0.29 | 0.37 | 96.0 | 1.18 |
| same_sector_slide1m_noscreen | -0.05 | -0.08 | 480.8 | 6.45 |
| same_sector_slide1m_bd7 | -0.41 | -0.40 | 273.6 | 3.53 |
| cross_sector_slide3m_bd7 | -0.41 | -0.66 | 86.2 | 1.03 |
| cross_sector_slide1m_bd7 | -0.44 | -0.64 | 244.4 | 3.26 |

## Untrimmed full-window (mean per config)

| Config | Sharpe | Ret% |
|---|---:|---:|
| cross_sector_slide1m_noscreen | 0.61 | 1.21 |
| cross_sector_slide3m_noscreen | 0.37 | 0.86 |
| same_sector_slide3m_noscreen | 0.34 | 0.84 |
| same_sector_slide3m_bd7 | 0.29 | 0.37 |
| same_sector_slide1m_noscreen | 0.37 | 0.55 |
| same_sector_slide1m_bd7 | 0.11 | 0.11 |
| cross_sector_slide3m_bd7 | -0.41 | -0.66 |
| cross_sector_slide1m_bd7 | -0.36 | -0.49 |

**Best config (trimmed Sharpe):** `cross_sector_slide1m_noscreen` = 0.42 / 0.85%

