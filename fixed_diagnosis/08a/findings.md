# Section 08a — core 2m, mp=20, pct=0.045 (historical)

**Runs:** 8 | **Starts:** 1 | **Configs:** 8

## Trading windows (untrimmed, from daily_returns.csv)

| Start | First trade | Last trade | Days |
|---|---|---|---|
| 2014-11-01 | 2015-01-02 | 2019-12-31 | 1258 |

## Sharpe Pivot (trimmed, per start date)

| Config | 2014-11-01 | Mean |
|---|---|---|
| same_sector_slide3m_noscreen | -0.53 | -0.53 |
| same_sector_slide3m_bd7 | -0.64 | -0.64 |
| same_sector_slide1m_noscreen | -0.08 | -0.08 |
| same_sector_slide1m_bd7 | -0.11 | -0.11 |
| cross_sector_slide3m_noscreen | -0.27 | -0.27 |
| cross_sector_slide3m_bd7 | -0.21 | -0.21 |
| cross_sector_slide1m_noscreen | -0.60 | -0.60 |
| cross_sector_slide1m_bd7 | -0.15 | -0.15 |

## Aggregate (trimmed mean per config)

| Config | Sharpe | Ret% | Trades | AT |
|---|---:|---:|---:|---:|
| same_sector_slide1m_noscreen | -0.08 | -0.11 | 1374.0 | 6.04 |
| same_sector_slide1m_bd7 | -0.11 | -0.09 | 760.0 | 3.16 |
| cross_sector_slide1m_bd7 | -0.15 | -0.26 | 772.0 | 3.09 |
| cross_sector_slide3m_bd7 | -0.21 | -1.00 | 251.0 | 0.95 |
| cross_sector_slide3m_noscreen | -0.27 | -1.33 | 461.0 | 1.88 |
| same_sector_slide3m_noscreen | -0.53 | -0.88 | 439.0 | 1.78 |
| cross_sector_slide1m_noscreen | -0.60 | -1.19 | 1414.0 | 6.02 |
| same_sector_slide3m_bd7 | -0.64 | -0.67 | 240.0 | 0.87 |

## Untrimmed full-window (mean per config)

| Config | Sharpe | Ret% |
|---|---:|---:|
| same_sector_slide1m_noscreen | -0.38 | -0.49 |
| same_sector_slide1m_bd7 | -0.39 | -0.35 |
| cross_sector_slide1m_bd7 | -0.07 | -0.14 |
| cross_sector_slide3m_bd7 | -0.21 | -1.00 |
| cross_sector_slide3m_noscreen | -0.27 | -1.33 |
| same_sector_slide3m_noscreen | -0.53 | -0.88 |
| cross_sector_slide1m_noscreen | -0.44 | -0.86 |
| same_sector_slide3m_bd7 | -0.64 | -0.67 |

**Best config (trimmed Sharpe):** `same_sector_slide1m_noscreen` = -0.08 / -0.11%

