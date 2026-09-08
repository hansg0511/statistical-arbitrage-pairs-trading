# Section 08b — core 12m, mp=20, pct=0.045 (historical)

**Runs:** 8 | **Starts:** 1 | **Configs:** 8

## Trading windows (untrimmed, from daily_returns.csv)

| Start | First trade | Last trade | Days |
|---|---|---|---|
| 2014-01-01 | 2015-01-02 | 2019-12-31 | 1258 |

## Sharpe Pivot (trimmed, per start date)

| Config | 2014-01-01 | Mean |
|---|---|---|
| same_sector_slide3m_noscreen | -0.91 | -0.91 |
| same_sector_slide3m_bd7 | -0.34 | -0.34 |
| same_sector_slide1m_noscreen | -0.79 | -0.79 |
| same_sector_slide1m_bd7 | 0.13 | 0.13 |
| cross_sector_slide3m_noscreen | -0.70 | -0.70 |
| cross_sector_slide3m_bd7 | -0.10 | -0.10 |
| cross_sector_slide1m_noscreen | -0.45 | -0.45 |
| cross_sector_slide1m_bd7 | 0.31 | 0.31 |

## Aggregate (trimmed mean per config)

| Config | Sharpe | Ret% | Trades | AT |
|---|---:|---:|---:|---:|
| cross_sector_slide1m_bd7 | 0.31 | 0.27 | 731.0 | 3.33 |
| same_sector_slide1m_bd7 | 0.13 | 0.05 | 226.0 | 0.98 |
| cross_sector_slide3m_bd7 | -0.10 | -0.11 | 251.0 | 1.14 |
| same_sector_slide3m_bd7 | -0.34 | -0.20 | 95.0 | 0.43 |
| cross_sector_slide1m_noscreen | -0.45 | -0.60 | 1449.0 | 6.75 |
| cross_sector_slide3m_noscreen | -0.70 | -1.23 | 511.0 | 2.47 |
| same_sector_slide1m_noscreen | -0.79 | -0.44 | 430.0 | 1.97 |
| same_sector_slide3m_noscreen | -0.91 | -0.85 | 175.0 | 0.81 |

## Untrimmed full-window (mean per config)

| Config | Sharpe | Ret% |
|---|---:|---:|
| cross_sector_slide1m_bd7 | 0.18 | 0.15 |
| same_sector_slide1m_bd7 | -0.10 | -0.04 |
| cross_sector_slide3m_bd7 | -0.10 | -0.11 |
| same_sector_slide3m_bd7 | -0.34 | -0.20 |
| cross_sector_slide1m_noscreen | -0.50 | -0.66 |
| cross_sector_slide3m_noscreen | -0.70 | -1.23 |
| same_sector_slide1m_noscreen | -0.62 | -0.44 |
| same_sector_slide3m_noscreen | -0.91 | -0.85 |

**Best config (trimmed Sharpe):** `cross_sector_slide1m_bd7` = 0.31 / 0.27%

