# Section 09b — sp500 12m, mp=20, pct=0.045 (historical)

**Runs:** 8 | **Starts:** 1 | **Configs:** 8

## Trading windows (untrimmed, from daily_returns.csv)

| Start | First trade | Last trade | Days |
|---|---|---|---|
| 2014-01-01 | 2015-01-02 | 2019-12-31 | 1258 |

## Sharpe Pivot (trimmed, per start date)

| Config | 2014-01-01 | Mean |
|---|---|---|
| same_sector_slide3m_noscreen | 0.37 | 0.37 |
| same_sector_slide3m_bd7 | 0.18 | 0.18 |
| same_sector_slide1m_noscreen | 0.40 | 0.40 |
| same_sector_slide1m_bd7 | 0.49 | 0.49 |
| cross_sector_slide3m_noscreen | -0.21 | -0.21 |
| cross_sector_slide3m_bd7 | 0.33 | 0.33 |
| cross_sector_slide1m_noscreen | 0.47 | 0.47 |
| cross_sector_slide1m_bd7 | 0.59 | 0.59 |

## Aggregate (trimmed mean per config)

| Config | Sharpe | Ret% | Trades | AT |
|---|---:|---:|---:|---:|
| cross_sector_slide1m_bd7 | 0.59 | 0.59 | 768.0 | 3.40 |
| same_sector_slide1m_bd7 | 0.49 | 0.49 | 914.0 | 3.80 |
| cross_sector_slide1m_noscreen | 0.47 | 0.66 | 1400.0 | 6.09 |
| same_sector_slide1m_noscreen | 0.40 | 0.54 | 1586.0 | 7.10 |
| same_sector_slide3m_noscreen | 0.37 | 0.71 | 555.0 | 2.59 |
| cross_sector_slide3m_bd7 | 0.33 | 0.53 | 256.0 | 1.08 |
| same_sector_slide3m_bd7 | 0.18 | 0.22 | 310.0 | 1.28 |
| cross_sector_slide3m_noscreen | -0.21 | -0.51 | 487.0 | 2.12 |

## Untrimmed full-window (mean per config)

| Config | Sharpe | Ret% |
|---|---:|---:|
| cross_sector_slide1m_bd7 | 0.49 | 0.48 |
| same_sector_slide1m_bd7 | 0.33 | 0.33 |
| cross_sector_slide1m_noscreen | 0.40 | 0.56 |
| same_sector_slide1m_noscreen | 0.27 | 0.37 |
| same_sector_slide3m_noscreen | 0.37 | 0.71 |
| cross_sector_slide3m_bd7 | 0.33 | 0.53 |
| same_sector_slide3m_bd7 | 0.18 | 0.22 |
| cross_sector_slide3m_noscreen | -0.21 | -0.51 |

**Best config (trimmed Sharpe):** `cross_sector_slide1m_bd7` = 0.59 / 0.59%

