# Top 15 config pairs (mechanism A)

Pairs from the consolidated sweep (trade-event replay, pct=0.25), ranked by score = min(recent, hist) pair Sharpe. Convention: **leg A = recent-strong**, **leg B = historical-strong**. Salient ranks shown per leg. Pair returns (%) are the pair book's annualized return in each window.

## How to read

Pair rank is NOT leg rank. Pairs are combined in a shared-account momentum replay (mechanism A: monthly re-tilt of fold capital to causal 63d-trailing-Sharpe weights, clamped to [0.25, 0.75]) and ranked by score = min(pair recent, pair historical) Sharpe of the **pair** book. The single-leg and pair rankings are different objects; use the tables below for the current values rather than assuming the strongest individual leg forms the strongest pair.

Pair rec Ret% / Pair hist Ret% are the pair book's annualized return in each window.

| # | Leg A (recent-strong) | A Rec# | A Rec Sh | A Ret% | A Hist# | Leg B (hist-strong) | B Hist# | B Hist Sh | B Ret% | B Rec# | Pair rec Sh | Pair rec Ret% | Pair hist Sh | Pair hist Ret% | Score |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-12m/cross_sector_slide1m_noscreen` | 1 | 1.84 | +19.54% | 5 | `sp500-2m/cross_sector_slide3m_bd7` | 1 | 0.88 | +7.69% | 30 | 0.83 | +6.50% | 1.14 | +8.10% | 0.83 |
| 2 | `sp500-12m/same_sector_slide1m_noscreen` | 3 | 1.33 | +15.90% | 6 | `sp500-2m/cross_sector_slide3m_bd7` | 1 | 0.88 | +7.69% | 30 | 0.87 | +8.10% | 0.81 | +5.60% | 0.81 |
| 3 | `sp500-12m/same_sector_slide3m_noscreen` | 10 | 0.81 | +12.32% | 8 | `sp500-2m/cross_sector_slide3m_noscreen` | 2 | 0.62 | +9.34% | 19 | 0.73 | +9.00% | 0.70 | +7.20% | 0.70 |
| 4 | `sp500-12m/cross_sector_slide1m_noscreen` | 1 | 1.84 | +19.54% | 5 | `sp500-2m/cross_sector_slide3m_noscreen` | 2 | 0.62 | +9.34% | 19 | 0.91 | +8.60% | 0.67 | +5.60% | 0.67 |
| 5 | `sp500-12m/same_sector_slide3m_noscreen` | 10 | 0.81 | +12.32% | 8 | `sp500-2m/same_sector_slide3m_noscreen` | 14 | 0.19 | +1.50% | 20 | 0.68 | +7.70% | 0.60 | +5.10% | 0.60 |
| 6 | `sp500-12m/same_sector_slide3m_noscreen` | 10 | 0.81 | +12.32% | 8 | `sp500-2m/cross_sector_slide1m_bd7` | 7 | 0.39 | +1.86% | 31 | 0.60 | +6.90% | 0.61 | +3.80% | 0.60 |
| 7 | `sp500-12m/cross_sector_slide1m_noscreen` | 1 | 1.84 | +19.54% | 5 | `sp500-12m/same_sector_slide3m_noscreen` | 8 | 0.37 | +3.44% | 10 | 1.06 | +11.30% | 0.58 | +4.30% | 0.58 |
| 8 | `sp500-12m/cross_sector_slide3m_bd7` | 9 | 0.81 | +6.91% | 10 | `sp500-2m/cross_sector_slide3m_bd7` | 1 | 0.88 | +7.69% | 30 | 0.57 | +3.50% | 0.61 | +4.80% | 0.57 |
| 9 | `sp500-12m/same_sector_slide3m_noscreen` | 10 | 0.81 | +12.32% | 8 | `sp500-2m/same_sector_slide1m_noscreen` | 11 | 0.28 | +1.70% | 29 | 0.68 | +7.40% | 0.56 | +4.00% | 0.56 |
| 10 | `sp500-12m/same_sector_slide1m_noscreen` | 3 | 1.33 | +15.90% | 6 | `sp500-12m/same_sector_slide3m_noscreen` | 8 | 0.37 | +3.44% | 10 | 1.14 | +14.60% | 0.56 | +4.50% | 0.56 |
| 11 | `sp500-12m/cross_sector_slide1m_bd7` | 5 | 1.29 | +8.99% | 3 | `sp500-2m/cross_sector_slide3m_noscreen` | 2 | 0.62 | +9.34% | 19 | 0.55 | +4.30% | 0.76 | +5.60% | 0.55 |
| 12 | `sp500-12m/same_sector_slide3m_noscreen` | 10 | 0.81 | +12.32% | 8 | `sp500-2m/same_sector_slide3m_bd7` | 12 | 0.20 | +1.12% | 23 | 0.73 | +7.20% | 0.53 | +3.70% | 0.53 |
| 13 | `sp500-12m/same_sector_slide3m_noscreen` | 10 | 0.81 | +12.32% | 8 | `sp500-12m/same_sector_slide1m_bd7` | 4 | 0.50 | +2.67% | 12 | 0.78 | +8.80% | 0.53 | +3.70% | 0.53 |
| 14 | `sp500-12m/same_sector_slide3m_noscreen` | 10 | 0.81 | +12.32% | 8 | `sp500-2m/cross_sector_slide1m_noscreen` | 16 | 0.13 | +0.74% | 16 | 0.86 | +9.50% | 0.53 | +4.00% | 0.53 |
| 15 | `sp500-12m/cross_sector_slide3m_noscreen` | 7 | 1.10 | +14.85% | 23 | `sp500-2m/cross_sector_slide3m_bd7` | 1 | 0.88 | +7.69% | 30 | 0.76 | +7.20% | 0.52 | +4.10% | 0.52 |

