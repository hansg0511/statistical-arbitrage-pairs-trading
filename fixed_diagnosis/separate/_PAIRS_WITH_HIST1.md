# Pairs with the historical-window #1 legs

All pairs use the trade-event replay (mechanism A, pct=0.25, shared-account momentum allocation). Recent = mean over the 5 aligned start-pairs; hist = single aligned window. Score = min(recent, hist). Partner leg ranks are across the full 32-leg set. R% = pair book recent annualized return; H% = pair book historical annualized return.

## Target leg: `sp500-2m/cross_sector_slide3m_bd7` (leg B, historical-strong)

Single leg: hist Sh 0.88, hist Ret +7.69%/yr (hist rank #1); recent Sh -0.38, recent Ret -3.66%/yr (recent rank #30).

Rows sorted by score = min(recent, hist). The partner (leg A) is the recent-strong leg; the target is the historical-strong leg.

| # | Partner (leg A) | Partner Rec# | Partner Hist# | Pair rec | Range | Pair hist | Score | R% | H% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-12m/cross_sector_slide1m_noscreen` | 1 | 5 | 0.83 | 0.52–1.12 | 1.14 | 0.83 | +6.5% | +8.1% |
| 2 | `sp500-12m/same_sector_slide1m_noscreen` | 3 | 6 | 0.87 | 0.75–1.02 | 0.81 | 0.81 | +8.1% | +5.6% |
| 3 | `sp500-12m/cross_sector_slide3m_bd7` | 9 | 10 | 0.57 | -0.05–1.39 | 0.61 | 0.57 | +3.5% | +4.8% |
| 4 | `sp500-12m/cross_sector_slide3m_noscreen` | 7 | 23 | 0.76 | 0.60–0.92 | 0.52 | 0.52 | +7.2% | +4.1% |
| 5 | `sp500-12m/same_sector_slide3m_noscreen` | 10 | 8 | 0.52 | -0.40–1.47 | 1.09 | 0.52 | +6.3% | +8.7% |
| 6 | `core-2m/same_sector_slide1m_noscreen` | 6 | 18 | 0.42 | 0.16–0.83 | 0.47 | 0.42 | +3.0% | +3.0% |
| 7 | `core-2m/cross_sector_slide3m_noscreen` | 11 | 22 | 0.57 | -0.57–1.56 | 0.35 | 0.35 | +8.3% | +2.9% |
| 8 | `core-12m/cross_sector_slide1m_noscreen` | 8 | 26 | 0.32 | 0.04–0.42 | 0.52 | 0.32 | +2.6% | +3.5% |
| 9 | `sp500-12m/cross_sector_slide1m_bd7` | 5 | 3 | 0.32 | 0.01–0.69 | 1.13 | 0.32 | +2.0% | +7.0% |
| 10 | `core-12m/cross_sector_slide3m_noscreen` | 18 | 30 | 0.24 | -0.38–0.94 | 0.26 | 0.24 | +2.6% | +1.7% |
| 11 | `sp500-2m/cross_sector_slide1m_noscreen` | 16 | 16 | 0.24 | 0.11–0.47 | 0.76 | 0.24 | +1.9% | +6.1% |
| 12 | `core-2m/cross_sector_slide1m_noscreen` | 2 | 28 | 1.22 | 0.97–1.54 | 0.23 | 0.23 | +12.1% | +1.5% |
| 13 | `sp500-12m/same_sector_slide1m_bd7` | 12 | 4 | 0.19 | -0.11–0.47 | 1.01 | 0.19 | +1.2% | +6.8% |
| 14 | `core-2m/same_sector_slide1m_bd7` | 4 | 19 | 0.18 | -0.40–0.85 | 0.59 | 0.18 | +1.1% | +3.7% |
| 15 | `sp500-2m/cross_sector_slide3m_noscreen` | 19 | 2 | 0.18 | -0.11–0.65 | 0.80 | 0.18 | +1.3% | +9.3% |
| 16 | `sp500-2m/same_sector_slide3m_noscreen` | 20 | 14 | 0.13 | -0.25–0.90 | 0.77 | 0.13 | +1.2% | +6.2% |
| 17 | `sp500-2m/same_sector_slide3m_bd7` | 23 | 12 | 0.13 | -0.25–0.75 | 0.90 | 0.13 | +0.6% | +6.8% |
| 18 | `core-2m/same_sector_slide3m_noscreen` | 14 | 27 | 0.11 | -0.61–1.72 | 0.36 | 0.11 | +1.2% | +2.3% |
| 19 | `core-12m/cross_sector_slide1m_bd7` | 13 | 9 | 0.11 | -0.04–0.34 | 0.72 | 0.11 | +0.6% | +4.5% |
| 20 | `core-12m/cross_sector_slide3m_bd7` | 22 | 17 | 0.02 | -0.37–1.07 | 0.81 | 0.02 | -0.6% | +5.7% |
| 21 | `sp500-2m/same_sector_slide1m_noscreen` | 29 | 11 | 0.01 | -0.45–0.55 | 0.73 | 0.01 | +0.0% | +5.0% |
| 22 | `sp500-12m/same_sector_slide3m_bd7` | 17 | 13 | -0.00 | -0.57–0.54 | 1.03 | -0.00 | -0.3% | +7.3% |
| 23 | `core-2m/same_sector_slide3m_bd7` | 15 | 29 | -0.00 | -1.04–1.60 | 0.64 | -0.00 | +0.7% | +4.6% |
| 24 | `core-2m/cross_sector_slide1m_bd7` | 21 | 20 | -0.10 | -0.37–0.25 | 0.60 | -0.10 | -1.0% | +4.1% |
| 25 | `core-12m/same_sector_slide3m_noscreen` | 26 | 32 | -0.32 | -0.59–0.09 | 0.70 | -0.32 | -2.2% | +5.1% |
| 26 | `core-12m/same_sector_slide1m_noscreen` | 24 | 31 | -0.38 | -0.66–0.22 | 0.75 | -0.38 | -2.2% | +5.0% |
| 27 | `core-2m/cross_sector_slide3m_bd7` | 28 | 21 | -0.42 | -0.98–0.76 | 0.11 | -0.42 | -3.7% | +0.2% |
| 28 | `sp500-2m/same_sector_slide1m_bd7` | 32 | 24 | -0.42 | -0.96–0.06 | 0.80 | -0.42 | -2.9% | +5.5% |
| 29 | `sp500-2m/cross_sector_slide1m_bd7` | 31 | 7 | -0.48 | -0.74–0.08 | 0.82 | -0.48 | -4.3% | +6.0% |
| 30 | `core-12m/same_sector_slide3m_bd7` | 27 | 25 | -0.53 | -0.93–0.25 | 0.90 | -0.53 | -4.4% | +6.6% |
| 31 | `core-12m/same_sector_slide1m_bd7` | 25 | 15 | -0.67 | -1.00–0.17 | 0.86 | -0.67 | -4.6% | +6.0% |

