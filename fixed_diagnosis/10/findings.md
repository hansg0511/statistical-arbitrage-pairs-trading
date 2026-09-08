# Section 10 — core 2m, mp=20, pct=0.25 (recent)

**Runs:** 8 | **Starts:** 8 | **Configs:** 1

## Trading windows (untrimmed, from daily_returns.csv)

| Start | First trade | Last trade | Days |
|---|---|---|---|
| 2023-11-01 | 2024-01-02 | 2025-12-31 | 502 |
| 2023-11-15 | 2024-01-16 | 2025-12-12 | 481 |
| 2023-12-01 | 2024-02-01 | 2025-12-31 | 481 |
| 2023-12-15 | 2024-02-15 | 2025-12-12 | 459 |
| 2024-01-01 | 2024-03-01 | 2025-12-31 | 461 |
| 2024-01-15 | 2024-03-15 | 2025-12-12 | 439 |
| 2024-02-01 | 2024-04-01 | 2025-12-31 | 441 |
| 2024-02-15 | 2024-04-15 | 2025-12-12 | 419 |

## Sharpe Pivot (trimmed, per start date)

| Config | 2023-11-01 | 2023-11-15 | 2023-12-01 | 2023-12-15 | 2024-01-01 | 2024-01-15 | 2024-02-01 | 2024-02-15 | Mean |
|---|---|---|---|---|---|---|---|---|---|
| same_sector_slide1m_bd7 | 0.71 | 0.50 | 0.98 | 0.60 | 0.99 | 0.61 | 1.04 | 0.56 | 0.75 |

## Aggregate (trimmed mean per config)

| Config | Sharpe | Ret% | Trades | AT |
|---|---:|---:|---:|---:|
| same_sector_slide1m_bd7 | 0.75 | 4.70 | 239.8 | 2.99 |

## Untrimmed full-window (mean per config)

| Config | Sharpe | Ret% |
|---|---:|---:|
| same_sector_slide1m_bd7 | 0.53 | 3.16 |

**Best config (trimmed Sharpe):** `same_sector_slide1m_bd7` = 0.75 / 4.70%

