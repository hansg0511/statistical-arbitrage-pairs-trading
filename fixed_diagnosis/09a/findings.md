# Section 09a — sp500 2m, mp=20, pct=0.045 (historical)

**Runs:** 8 | **Starts:** 1 | **Configs:** 8

## Trading windows (untrimmed, from daily_returns.csv)

| Start | First trade | Last trade | Days |
|---|---|---|---|
| 2014-11-01 | 2015-01-02 | 2019-12-31 | 1258 |

## Sharpe Pivot (trimmed, per start date)

| Config | 2014-11-01 | Mean |
|---|---|---|
| same_sector_slide3m_noscreen | 0.17 | 0.17 |
| same_sector_slide3m_bd7 | 0.20 | 0.20 |
| same_sector_slide1m_noscreen | 0.29 | 0.29 |
| same_sector_slide1m_bd7 | -0.24 | -0.24 |
| cross_sector_slide3m_noscreen | 0.62 | 0.62 |
| cross_sector_slide3m_bd7 | 0.89 | 0.89 |
| cross_sector_slide1m_noscreen | 0.11 | 0.11 |
| cross_sector_slide1m_bd7 | 0.39 | 0.39 |

## Aggregate (trimmed mean per config)

| Config | Sharpe | Ret% | Trades | AT |
|---|---:|---:|---:|---:|
| cross_sector_slide3m_bd7 | 0.89 | 1.43 | 266.0 | 1.19 |
| cross_sector_slide3m_noscreen | 0.62 | 1.79 | 525.0 | 2.43 |
| cross_sector_slide1m_bd7 | 0.39 | 0.35 | 768.0 | 3.46 |
| same_sector_slide1m_noscreen | 0.29 | 0.35 | 1505.0 | 6.64 |
| same_sector_slide3m_bd7 | 0.20 | 0.24 | 260.0 | 1.05 |
| same_sector_slide3m_noscreen | 0.17 | 0.32 | 508.0 | 2.21 |
| cross_sector_slide1m_noscreen | 0.11 | 0.16 | 1483.0 | 6.86 |
| same_sector_slide1m_bd7 | -0.24 | -0.20 | 810.0 | 3.56 |

## Untrimmed full-window (mean per config)

| Config | Sharpe | Ret% |
|---|---:|---:|
| cross_sector_slide3m_bd7 | 0.89 | 1.43 |
| cross_sector_slide3m_noscreen | 0.62 | 1.79 |
| cross_sector_slide1m_bd7 | 0.34 | 0.30 |
| same_sector_slide1m_noscreen | 0.25 | 0.33 |
| same_sector_slide3m_bd7 | 0.20 | 0.24 |
| same_sector_slide3m_noscreen | 0.17 | 0.32 |
| cross_sector_slide1m_noscreen | 0.23 | 0.36 |
| same_sector_slide1m_bd7 | -0.11 | -0.10 |

**Best config (trimmed Sharpe):** `cross_sector_slide3m_bd7` = 0.89 / 1.43%

