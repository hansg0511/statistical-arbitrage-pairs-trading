# clean40 human analysis - consolidated pair and leg rankings

Pair metrics and ranks: `fixed_diagnosis/clean40/_CLEAN40_PAIR_RANKS_A.csv` and `_CLEAN40_PAIR_RANKS_B.csv`.  pct=0.25 and capital=$1,000,000. Momentum parameters: lookback=84 days, step=0.40, weight bounds=[0.10, 0.90], initial weight_A=0.50.

Universe: 32 corrected legs and 496 two-leg combinations. Recent metrics are means over five aligned starts; historical metrics use the single aligned 2015-2019 window. Joined metrics concatenate historical and each recent series, then average the five joined results. All Sharpe ratios and returns are annualized.

Mechanism A and mechanism B are the two shared-account event-replay implementations. The displayed pair order is the source CSV order and does not change the stored mechanism result.

## Human analysis

The three methods answer different questions. The separate score protects the weaker window, rank-average rewards a consistently high position in both windows, and joined Sharpe treats the historical and recent series as one sample. A method disagreement is therefore evidence of regime dependence, not a reason to select the largest recent Sharpe automatically.

- Mechanism A leaders: separate score: `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` (joined Sh 1.11, joined return +9.17%); rank-average: `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` (joined Sh 1.11, joined return +9.17%); joined Sharpe: `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` (joined Sh 1.11, joined return +9.17%).
  The top-20 all-method intersection for mechanism A is 10 pair(s).
- Mechanism B leaders: separate score: `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` (joined Sh 1.11, joined return +9.07%); rank-average: `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` (joined Sh 1.11, joined return +9.07%); joined Sharpe: `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` (joined Sh 1.11, joined return +9.07%).
  The top-20 all-method intersection for mechanism B is 7 pair(s).
- The strongest strict-consensus pair by the sum of its six method ranks is `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` (rank-sum 6.0). This is a mechanical shortlist, not an automatic trading decision.
- Pair ranks and leg ranks are different objects. Dynamic capital rotation and the shared-account event replay can make a pair attractive even when neither leg is the top standalone leg in every window.
- Return ranks should be read alongside Sharpe ranks: a high annualized return can come with materially higher volatility or drawdown, while a high Sharpe can reflect a smaller but steadier return.
- `clean40` is evaluated here as an explicitly selected parameter set across all 496 pairs. This report is not a new momentum-parameter optimization.
- These diagnostics do not establish out-of-sample alpha. The existing factor diagnostics remain the appropriate place to assess exposure and statistical alpha.

## Default versus clean40 leaders

| Mechanism | Method | Default leader | Default Joined Sh | Default Joined Ret% | clean40 leader | clean40 Joined Sh | clean40 Joined Ret% |
|---|---|---|---:|---:|---|---:|---:|
| A | separate score | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.04 | +7.65% | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.11 | +9.17% |
| A | rank-average | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 0.75 | +7.07% | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.11 | +9.17% |
| A | joined Sharpe | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.04 | +7.65% | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.11 | +9.17% |
| B | separate score | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.84 | +6.43% | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.11 | +9.07% |
| B | rank-average | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 0.68 | +4.17% | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.11 | +9.07% |
| B | joined Sharpe | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.01 | +7.39% | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 1.11 | +9.07% |

## Consensus and rank agreement

| Mechanism | Separate / rank-average | Separate / joined | Rank-average / joined | All three |
|---|---:|---:|---:|---:|
| A | 10 | 13 | 13 | 10 |
| B | 7 | 12 | 12 | 7 |

| Mechanism | Separate vs rank-average | Separate vs joined | Rank-average vs joined |
|---|---:|---:|---:|
| A | 0.803 | 0.886 | 0.907 |
| B | 0.788 | 0.881 | 0.899 |

The strict cross-mechanism shortlist contains **7** pair(s): top 20 in all three methods for both mechanisms.

- `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide1m_bd7`
- `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7`
- `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide1m_noscreen`
- `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide3m_noscreen`
- `sp500-12m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen`
- `sp500-12m/same_sector_slide1m_bd7` + `sp500-12m/same_sector_slide1m_noscreen`
- `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen`

## Strict consensus pair detail

| Pair | Mech | Separate # | Rank-average # | Joined # | Recent Sh / Ret% | Hist Sh / Ret% | Joined Sh / Ret% | Score |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | A | 1 | 1 | 1 | 1.09 / +9.45% | 1.12 / +9.10% | 1.11 / +9.17% | 1.09 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | B | 1 | 1 | 1 | 1.14 / +9.81% | 1.10 / +8.83% | 1.11 / +9.07% | 1.10 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide1m_noscreen` | A | 3 | 6 | 3 | 1.06 / +9.62% | 0.72 / +4.72% | 0.82 / +5.95% | 0.72 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide1m_noscreen` | B | 3 | 10 | 3 | 0.93 / +8.85% | 0.77 / +5.18% | 0.81 / +6.08% | 0.77 |
| `sp500-12m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | A | 6 | 3 | 5 | 1.16 / +12.00% | 0.66 / +6.11% | 0.78 / +7.61% | 0.66 |
| `sp500-12m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | B | 7 | 3 | 7 | 1.15 / +11.82% | 0.65 / +5.99% | 0.77 / +7.47% | 0.65 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide3m_noscreen` | A | 5 | 12 | 8 | 0.97 / +10.12% | 0.68 / +5.62% | 0.76 / +6.74% | 0.68 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide3m_noscreen` | B | 6 | 5 | 10 | 1.00 / +10.32% | 0.65 / +5.32% | 0.75 / +6.55% | 0.65 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide1m_bd7` | A | 17 | 2 | 6 | 1.34 / +11.41% | 0.53 / +3.14% | 0.78 / +5.25% | 0.53 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide1m_bd7` | B | 17 | 2 | 6 | 1.36 / +11.64% | 0.51 / +3.03% | 0.78 / +5.22% | 0.51 |
| `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | A | 7 | 10 | 10 | 1.01 / +13.20% | 0.64 / +5.43% | 0.76 / +7.41% | 0.64 |
| `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | B | 5 | 13 | 9 | 0.92 / +12.25% | 0.67 / +5.68% | 0.75 / +7.36% | 0.67 |
| `sp500-12m/same_sector_slide1m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | A | 14 | 9 | 16 | 1.06 / +10.90% | 0.55 / +3.37% | 0.71 / +5.30% | 0.55 |
| `sp500-12m/same_sector_slide1m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | B | 13 | 11 | 14 | 0.98 / +10.22% | 0.56 / +3.52% | 0.70 / +5.24% | 0.56 |

## Pair rankings

Each table contains the top 20 rows for one method. `Rec #`, `Hist #`, and `Joined #` are the pair ranks for the corresponding Sharpe metric; `Score` is the minimum of recent and historical Sharpe.

## Mechanism A

### Top 20 by separate score

| # | Pair | Rec # | Rec Sh | Rec Ret% | Hist # | Hist Sh | Hist Ret% | Joined # | Joined Sh | Joined Ret% | Score | Rank Avg |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 55 | 1.09 | +9.45% | 1 | 1.12 | +9.10% | 1 | 1.11 | +9.17% | 1.09 | 28.0 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 117 | 0.89 | +8.93% | 12 | 0.78 | +6.24% | 4 | 0.81 | +6.94% | 0.78 | 64.5 |
| 3 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 64 | 1.06 | +9.62% | 16 | 0.72 | +4.72% | 3 | 0.82 | +5.95% | 0.72 | 40.0 |
| 4 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 143 | 0.82 | +10.26% | 17 | 0.71 | +6.29% | 12 | 0.76 | +7.32% | 0.71 | 80.0 |
| 5 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 88 | 0.97 | +10.12% | 21 | 0.68 | +5.62% | 8 | 0.76 | +6.74% | 0.68 | 54.5 |
| 6 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 44 | 1.16 | +12.00% | 24 | 0.66 | +6.11% | 5 | 0.78 | +7.61% | 0.66 | 34.0 |
| 7 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 80 | 1.01 | +13.20% | 27 | 0.64 | +5.43% | 10 | 0.76 | +7.41% | 0.64 | 53.5 |
| 8 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 219 | 0.63 | +8.06% | 22 | 0.68 | +7.85% | 20 | 0.67 | +7.91% | 0.63 | 120.5 |
| 9 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 228 | 0.61 | +4.09% | 2 | 1.05 | +7.93% | 2 | 0.93 | +6.93% | 0.61 | 115.0 |
| 10 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 230 | 0.60 | +7.81% | 31 | 0.61 | +4.64% | 37 | 0.61 | +5.43% | 0.60 | 130.5 |
| 11 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 202 | 0.67 | +7.06% | 33 | 0.60 | +4.44% | 27 | 0.63 | +5.12% | 0.60 | 117.5 |
| 12 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 166 | 0.75 | +8.08% | 35 | 0.58 | +5.81% | 30 | 0.63 | +6.40% | 0.58 | 100.5 |
| 13 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 252 | 0.56 | +6.97% | 25 | 0.65 | +4.92% | 29 | 0.63 | +5.41% | 0.56 | 138.5 |
| 14 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 63 | 1.06 | +10.90% | 38 | 0.55 | +3.37% | 16 | 0.71 | +5.30% | 0.55 | 50.5 |
| 15 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 247 | 0.57 | +3.45% | 39 | 0.53 | +2.56% | 48 | 0.54 | +2.78% | 0.53 | 143.0 |
| 16 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 94 | 0.95 | +7.19% | 40 | 0.53 | +3.04% | 21 | 0.66 | +4.10% | 0.53 | 67.0 |
| 17 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 17 | 1.34 | +11.41% | 41 | 0.53 | +3.14% | 6 | 0.78 | +5.25% | 0.53 | 29.0 |
| 18 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 50 | 1.13 | +12.94% | 42 | 0.53 | +4.29% | 15 | 0.72 | +6.50% | 0.53 | 46.0 |
| 19 | `sp500-12m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 82 | 1.00 | +10.44% | 43 | 0.53 | +3.49% | 19 | 0.68 | +5.28% | 0.53 | 62.5 |
| 20 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 108 | 0.92 | +8.99% | 44 | 0.52 | +4.43% | 31 | 0.63 | +5.56% | 0.52 | 76.0 |

### Top 20 by rank-average

| # | Pair | Rec # | Rec Sh | Rec Ret% | Hist # | Hist Sh | Hist Ret% | Joined # | Joined Sh | Joined Ret% | Score | Rank Avg |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 55 | 1.09 | +9.45% | 1 | 1.12 | +9.10% | 1 | 1.11 | +9.17% | 1.09 | 28.0 |
| 2 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 17 | 1.34 | +11.41% | 41 | 0.53 | +3.14% | 6 | 0.78 | +5.25% | 0.53 | 29.0 |
| 3 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 44 | 1.16 | +12.00% | 24 | 0.66 | +6.11% | 5 | 0.78 | +7.61% | 0.66 | 34.0 |
| 4 | `core-2m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 11 | 1.39 | +11.84% | 60 | 0.45 | +2.55% | 11 | 0.76 | +4.92% | 0.45 | 35.5 |
| 5 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 22 | 1.25 | +10.18% | 50 | 0.49 | +2.57% | 13 | 0.74 | +4.49% | 0.49 | 36.0 |
| 6 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 64 | 1.06 | +9.62% | 16 | 0.72 | +4.72% | 3 | 0.82 | +5.95% | 0.72 | 40.0 |
| 7 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 25 | 1.24 | +13.39% | 59 | 0.46 | +3.04% | 17 | 0.71 | +5.67% | 0.46 | 42.0 |
| 8 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 50 | 1.13 | +12.94% | 42 | 0.53 | +4.29% | 15 | 0.72 | +6.50% | 0.53 | 46.0 |
| 9 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 63 | 1.06 | +10.90% | 38 | 0.55 | +3.37% | 16 | 0.71 | +5.30% | 0.55 | 50.5 |
| 10 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 80 | 1.01 | +13.20% | 27 | 0.64 | +5.43% | 10 | 0.76 | +7.41% | 0.64 | 53.5 |
| 11 | `core-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 30 | 1.22 | +11.73% | 78 | 0.38 | +2.52% | 24 | 0.64 | +4.86% | 0.38 | 54.0 |
| 12 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 88 | 0.97 | +10.12% | 21 | 0.68 | +5.62% | 8 | 0.76 | +6.74% | 0.68 | 54.5 |
| 13 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 58 | 1.08 | +9.37% | 61 | 0.45 | +2.83% | 23 | 0.64 | +4.50% | 0.45 | 59.5 |
| 14 | `sp500-2m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 28 | 1.23 | +11.60% | 93 | 0.32 | +2.02% | 36 | 0.61 | +4.44% | 0.32 | 60.5 |
| 15 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 47 | 1.14 | +8.31% | 76 | 0.38 | +2.06% | 34 | 0.62 | +3.69% | 0.38 | 61.5 |
| 16 | `sp500-12m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 82 | 1.00 | +10.44% | 43 | 0.53 | +3.49% | 19 | 0.68 | +5.28% | 0.53 | 62.5 |
| 17 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 65 | 1.06 | +10.80% | 62 | 0.45 | +2.93% | 22 | 0.65 | +4.96% | 0.45 | 63.5 |
| 18 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 117 | 0.89 | +8.93% | 12 | 0.78 | +6.24% | 4 | 0.81 | +6.94% | 0.78 | 64.5 |
| 19 | `sp500-12m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 32 | 1.21 | +10.65% | 98 | 0.31 | +1.98% | 41 | 0.58 | +4.15% | 0.31 | 65.0 |
| 20 | `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 81 | 1.00 | +9.09% | 52 | 0.48 | +2.98% | 25 | 0.64 | +4.49% | 0.48 | 66.5 |

### Top 20 by joined Sharpe

| # | Pair | Rec # | Rec Sh | Rec Ret% | Hist # | Hist Sh | Hist Ret% | Joined # | Joined Sh | Joined Ret% | Score | Rank Avg |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 55 | 1.09 | +9.45% | 1 | 1.12 | +9.10% | 1 | 1.11 | +9.17% | 1.09 | 28.0 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 228 | 0.61 | +4.09% | 2 | 1.05 | +7.93% | 2 | 0.93 | +6.93% | 0.61 | 115.0 |
| 3 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 64 | 1.06 | +9.62% | 16 | 0.72 | +4.72% | 3 | 0.82 | +5.95% | 0.72 | 40.0 |
| 4 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 117 | 0.89 | +8.93% | 12 | 0.78 | +6.24% | 4 | 0.81 | +6.94% | 0.78 | 64.5 |
| 5 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 44 | 1.16 | +12.00% | 24 | 0.66 | +6.11% | 5 | 0.78 | +7.61% | 0.66 | 34.0 |
| 6 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 17 | 1.34 | +11.41% | 41 | 0.53 | +3.14% | 6 | 0.78 | +5.25% | 0.53 | 29.0 |
| 7 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_bd7` | 418 | 0.18 | +1.17% | 4 | 0.98 | +7.65% | 7 | 0.77 | +5.88% | 0.18 | 211.0 |
| 8 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 88 | 0.97 | +10.12% | 21 | 0.68 | +5.62% | 8 | 0.76 | +6.74% | 0.68 | 54.5 |
| 9 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 283 | 0.50 | +6.86% | 6 | 0.87 | +8.24% | 9 | 0.76 | +7.88% | 0.50 | 144.5 |
| 10 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 80 | 1.01 | +13.20% | 27 | 0.64 | +5.43% | 10 | 0.76 | +7.41% | 0.64 | 53.5 |
| 11 | `core-2m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 11 | 1.39 | +11.84% | 60 | 0.45 | +2.55% | 11 | 0.76 | +4.92% | 0.45 | 35.5 |
| 12 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 143 | 0.82 | +10.26% | 17 | 0.71 | +6.29% | 12 | 0.76 | +7.32% | 0.71 | 80.0 |
| 13 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 22 | 1.25 | +10.18% | 50 | 0.49 | +2.57% | 13 | 0.74 | +4.49% | 0.49 | 36.0 |
| 14 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | 406 | 0.21 | +1.68% | 5 | 0.91 | +12.04% | 14 | 0.73 | +9.43% | 0.21 | 205.5 |
| 15 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 50 | 1.13 | +12.94% | 42 | 0.53 | +4.29% | 15 | 0.72 | +6.50% | 0.53 | 46.0 |
| 16 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 63 | 1.06 | +10.90% | 38 | 0.55 | +3.37% | 16 | 0.71 | +5.30% | 0.55 | 50.5 |
| 17 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 25 | 1.24 | +13.39% | 59 | 0.46 | +3.04% | 17 | 0.71 | +5.67% | 0.46 | 42.0 |
| 18 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_bd7` | 455 | 0.00 | -0.33% | 3 | 0.98 | +7.60% | 18 | 0.71 | +5.57% | 0.00 | 229.0 |
| 19 | `sp500-12m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 82 | 1.00 | +10.44% | 43 | 0.53 | +3.49% | 19 | 0.68 | +5.28% | 0.53 | 62.5 |
| 20 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 219 | 0.63 | +8.06% | 22 | 0.68 | +7.85% | 20 | 0.67 | +7.91% | 0.63 | 120.5 |

## Mechanism B

### Top 20 by separate score

| # | Pair | Rec # | Rec Sh | Rec Ret% | Hist # | Hist Sh | Hist Ret% | Joined # | Joined Sh | Joined Ret% | Score | Rank Avg |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 39 | 1.14 | +9.81% | 1 | 1.10 | +8.83% | 1 | 1.11 | +9.07% | 1.10 | 20.0 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 134 | 0.83 | +8.30% | 10 | 0.80 | +6.37% | 4 | 0.81 | +6.88% | 0.80 | 72.0 |
| 3 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 93 | 0.93 | +8.85% | 13 | 0.77 | +5.18% | 3 | 0.81 | +6.08% | 0.77 | 53.0 |
| 4 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 145 | 0.80 | +9.99% | 21 | 0.70 | +6.23% | 11 | 0.75 | +7.20% | 0.70 | 83.0 |
| 5 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 99 | 0.92 | +12.25% | 25 | 0.67 | +5.68% | 9 | 0.75 | +7.36% | 0.67 | 62.0 |
| 6 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 63 | 1.00 | +10.32% | 26 | 0.65 | +5.32% | 10 | 0.75 | +6.55% | 0.65 | 44.5 |
| 7 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 37 | 1.15 | +11.82% | 27 | 0.65 | +5.99% | 7 | 0.77 | +7.47% | 0.65 | 32.0 |
| 8 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 219 | 0.63 | +8.05% | 24 | 0.68 | +7.79% | 17 | 0.67 | +7.87% | 0.63 | 121.5 |
| 9 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 225 | 0.62 | +4.10% | 2 | 1.04 | +7.87% | 2 | 0.93 | +6.89% | 0.62 | 113.5 |
| 10 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 168 | 0.75 | +8.11% | 33 | 0.60 | +6.01% | 22 | 0.64 | +6.56% | 0.60 | 100.5 |
| 11 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 218 | 0.63 | +6.62% | 36 | 0.59 | +4.35% | 27 | 0.61 | +4.94% | 0.59 | 127.0 |
| 12 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 239 | 0.59 | +7.52% | 28 | 0.64 | +4.86% | 25 | 0.62 | +5.52% | 0.59 | 133.5 |
| 13 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 71 | 0.98 | +10.22% | 39 | 0.56 | +3.52% | 14 | 0.70 | +5.24% | 0.56 | 55.0 |
| 14 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 249 | 0.56 | +6.93% | 23 | 0.69 | +5.15% | 21 | 0.65 | +5.58% | 0.56 | 136.0 |
| 15 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 261 | 0.54 | +3.18% | 34 | 0.60 | +2.89% | 42 | 0.56 | +2.97% | 0.54 | 147.5 |
| 16 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 140 | 0.82 | +8.02% | 43 | 0.52 | +2.96% | 28 | 0.61 | +4.27% | 0.52 | 91.5 |
| 17 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 8 | 1.36 | +11.64% | 45 | 0.51 | +3.03% | 6 | 0.78 | +5.22% | 0.51 | 26.5 |
| 18 | `core-2m/same_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide1m_noscreen` | 139 | 0.82 | +7.10% | 46 | 0.51 | +3.19% | 30 | 0.61 | +4.23% | 0.51 | 92.5 |
| 19 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide3m_bd7` | 167 | 0.75 | +5.59% | 48 | 0.51 | +4.49% | 47 | 0.54 | +4.76% | 0.51 | 107.5 |
| 20 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 282 | 0.50 | +6.76% | 7 | 0.86 | +8.16% | 8 | 0.76 | +7.80% | 0.50 | 144.5 |

### Top 20 by rank-average

| # | Pair | Rec # | Rec Sh | Rec Ret% | Hist # | Hist Sh | Hist Ret% | Joined # | Joined Sh | Joined Ret% | Score | Rank Avg |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 39 | 1.14 | +9.81% | 1 | 1.10 | +8.83% | 1 | 1.11 | +9.07% | 1.10 | 20.0 |
| 2 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 8 | 1.36 | +11.64% | 45 | 0.51 | +3.03% | 6 | 0.78 | +5.22% | 0.51 | 26.5 |
| 3 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 37 | 1.15 | +11.82% | 27 | 0.65 | +5.99% | 7 | 0.77 | +7.47% | 0.65 | 32.0 |
| 4 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 36 | 1.15 | +13.14% | 51 | 0.49 | +3.91% | 15 | 0.70 | +6.26% | 0.49 | 43.5 |
| 5 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 63 | 1.00 | +10.32% | 26 | 0.65 | +5.32% | 10 | 0.75 | +6.55% | 0.65 | 44.5 |
| 6 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 23 | 1.24 | +10.08% | 70 | 0.40 | +2.05% | 16 | 0.67 | +4.07% | 0.40 | 46.5 |
| 7 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 17 | 1.29 | +10.15% | 82 | 0.37 | +2.05% | 18 | 0.66 | +4.14% | 0.37 | 49.5 |
| 8 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 32 | 1.18 | +13.21% | 72 | 0.40 | +2.63% | 19 | 0.66 | +5.33% | 0.40 | 52.0 |
| 9 | `core-2m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 38 | 1.14 | +10.25% | 67 | 0.41 | +2.26% | 20 | 0.65 | +4.32% | 0.41 | 52.5 |
| 10 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 93 | 0.93 | +8.85% | 13 | 0.77 | +5.18% | 3 | 0.81 | +6.08% | 0.77 | 53.0 |
| 11 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 71 | 0.98 | +10.22% | 39 | 0.56 | +3.52% | 14 | 0.70 | +5.24% | 0.56 | 55.0 |
| 12 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 33 | 1.17 | +10.81% | 78 | 0.39 | +2.43% | 24 | 0.63 | +4.55% | 0.39 | 55.5 |
| 13 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 99 | 0.92 | +12.25% | 25 | 0.67 | +5.68% | 9 | 0.75 | +7.36% | 0.67 | 62.0 |
| 14 | `core-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 21 | 1.25 | +11.98% | 105 | 0.30 | +1.94% | 33 | 0.59 | +4.47% | 0.30 | 63.0 |
| 15 | `sp500-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 64 | 1.00 | +8.72% | 64 | 0.41 | +2.54% | 34 | 0.59 | +4.07% | 0.41 | 64.0 |
| 16 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 75 | 0.97 | +7.59% | 54 | 0.46 | +2.64% | 26 | 0.62 | +3.90% | 0.46 | 64.5 |
| 17 | `sp500-12m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 20 | 1.25 | +11.04% | 111 | 0.28 | +1.76% | 39 | 0.57 | +4.07% | 0.28 | 65.5 |
| 18 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 80 | 0.95 | +9.33% | 52 | 0.47 | +3.97% | 31 | 0.60 | +5.30% | 0.47 | 66.0 |
| 19 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 10 | 1.35 | +11.89% | 125 | 0.25 | +1.45% | 32 | 0.59 | +4.07% | 0.25 | 67.5 |
| 20 | `core-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 31 | 1.19 | +12.25% | 110 | 0.29 | +2.19% | 56 | 0.53 | +4.64% | 0.29 | 70.5 |

### Top 20 by joined Sharpe

| # | Pair | Rec # | Rec Sh | Rec Ret% | Hist # | Hist Sh | Hist Ret% | Joined # | Joined Sh | Joined Ret% | Score | Rank Avg |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 39 | 1.14 | +9.81% | 1 | 1.10 | +8.83% | 1 | 1.11 | +9.07% | 1.10 | 20.0 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 225 | 0.62 | +4.10% | 2 | 1.04 | +7.87% | 2 | 0.93 | +6.89% | 0.62 | 113.5 |
| 3 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 93 | 0.93 | +8.85% | 13 | 0.77 | +5.18% | 3 | 0.81 | +6.08% | 0.77 | 53.0 |
| 4 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 134 | 0.83 | +8.30% | 10 | 0.80 | +6.37% | 4 | 0.81 | +6.88% | 0.80 | 72.0 |
| 5 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_bd7` | 407 | 0.20 | +1.33% | 3 | 1.02 | +7.96% | 5 | 0.80 | +6.15% | 0.20 | 205.0 |
| 6 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 8 | 1.36 | +11.64% | 45 | 0.51 | +3.03% | 6 | 0.78 | +5.22% | 0.51 | 26.5 |
| 7 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 37 | 1.15 | +11.82% | 27 | 0.65 | +5.99% | 7 | 0.77 | +7.47% | 0.65 | 32.0 |
| 8 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 282 | 0.50 | +6.76% | 7 | 0.86 | +8.16% | 8 | 0.76 | +7.80% | 0.50 | 144.5 |
| 9 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 99 | 0.92 | +12.25% | 25 | 0.67 | +5.68% | 9 | 0.75 | +7.36% | 0.67 | 62.0 |
| 10 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 63 | 1.00 | +10.32% | 26 | 0.65 | +5.32% | 10 | 0.75 | +6.55% | 0.65 | 44.5 |
| 11 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 145 | 0.80 | +9.99% | 21 | 0.70 | +6.23% | 11 | 0.75 | +7.20% | 0.70 | 83.0 |
| 12 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | 390 | 0.24 | +2.15% | 5 | 0.92 | +12.12% | 12 | 0.74 | +9.61% | 0.24 | 197.5 |
| 13 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_bd7` | 453 | -0.01 | -0.46% | 4 | 0.97 | +7.55% | 13 | 0.70 | +5.51% | -0.01 | 228.5 |
| 14 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 71 | 0.98 | +10.22% | 39 | 0.56 | +3.52% | 14 | 0.70 | +5.24% | 0.56 | 55.0 |
| 15 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 36 | 1.15 | +13.14% | 51 | 0.49 | +3.91% | 15 | 0.70 | +6.26% | 0.49 | 43.5 |
| 16 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 23 | 1.24 | +10.08% | 70 | 0.40 | +2.05% | 16 | 0.67 | +4.07% | 0.40 | 46.5 |
| 17 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 219 | 0.63 | +8.05% | 24 | 0.68 | +7.79% | 17 | 0.67 | +7.87% | 0.63 | 121.5 |
| 18 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 17 | 1.29 | +10.15% | 82 | 0.37 | +2.05% | 18 | 0.66 | +4.14% | 0.37 | 49.5 |
| 19 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 32 | 1.18 | +13.21% | 72 | 0.40 | +2.63% | 19 | 0.66 | +5.33% | 0.40 | 52.0 |
| 20 | `core-2m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 38 | 1.14 | +10.25% | 67 | 0.41 | +2.26% | 20 | 0.65 | +4.32% | 0.41 | 52.5 |

## Leg rankings - All 32 legs

Ranks are dense ranks across all 32 legs; rank 1 is the highest value. Return ranks are separate from Sharpe ranks.

| Leg | Rec Sh | Sh# | Rec Ret% | Ret# | Hist Sh | Sh# | Hist Ret% | Ret# | Joined Sh | Sh# | Joined Ret% | Ret# |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `sp500-12m/cross_sector_slide1m_noscreen` | 1.84 | 1 | +19.54% | 2 | 0.44 | 5 | +3.25% | 4 | 0.66 | 1 | +5.53% | 3 |
| `sp500-12m/same_sector_slide1m_noscreen` | 1.33 | 3 | +15.90% | 3 | 0.40 | 6 | +2.86% | 6 | 0.63 | 2 | +5.32% | 4 |
| `sp500-2m/cross_sector_slide3m_noscreen` | 0.41 | 19 | +4.53% | 16 | 0.62 | 2 | +9.34% | 1 | 0.56 | 3 | +8.00% | 1 |
| `sp500-2m/cross_sector_slide3m_bd7` | -0.38 | 30 | -3.66% | 32 | 0.88 | 1 | +7.69% | 2 | 0.54 | 4 | +4.64% | 5 |
| `sp500-12m/same_sector_slide3m_noscreen` | 0.81 | 10 | +12.32% | 6 | 0.37 | 8 | +3.44% | 3 | 0.51 | 5 | +5.65% | 2 |
| `sp500-12m/cross_sector_slide1m_bd7` | 1.29 | 5 | +8.99% | 8 | 0.56 | 3 | +3.02% | 5 | 0.50 | 6 | +2.98% | 8 |
| `sp500-12m/cross_sector_slide3m_bd7` | 0.81 | 9 | +6.91% | 12 | 0.30 | 10 | +2.30% | 8 | 0.41 | 7 | +3.35% | 6 |
| `sp500-12m/same_sector_slide1m_bd7` | 0.68 | 12 | +5.02% | 14 | 0.50 | 4 | +2.67% | 7 | 0.37 | 8 | +2.11% | 10 |
| `sp500-2m/cross_sector_slide1m_noscreen` | 0.45 | 16 | +4.71% | 15 | 0.13 | 16 | +0.74% | 15 | 0.36 | 9 | +3.07% | 7 |
| `sp500-2m/same_sector_slide1m_noscreen` | -0.04 | 29 | -0.63% | 29 | 0.28 | 11 | +1.70% | 10 | 0.28 | 10 | +1.91% | 11 |
| `core-12m/cross_sector_slide1m_bd7` | 0.51 | 13 | +3.51% | 20 | 0.32 | 9 | +1.45% | 12 | 0.28 | 11 | +1.38% | 13 |
| `sp500-12m/same_sector_slide3m_bd7` | 0.44 | 17 | +3.58% | 19 | 0.19 | 13 | +1.08% | 14 | 0.27 | 12 | +1.75% | 12 |
| `sp500-2m/same_sector_slide3m_noscreen` | 0.33 | 20 | +4.09% | 18 | 0.19 | 14 | +1.50% | 11 | 0.24 | 13 | +2.14% | 9 |
| `sp500-2m/same_sector_slide3m_bd7` | 0.29 | 23 | +1.96% | 23 | 0.20 | 12 | +1.12% | 13 | 0.22 | 14 | +1.32% | 14 |
| `core-2m/cross_sector_slide1m_noscreen` | 1.51 | 2 | +20.16% | 1 | -0.57 | 28 | -6.64% | 29 | 0.15 | 15 | +1.09% | 15 |
| `sp500-12m/cross_sector_slide3m_noscreen` | 1.10 | 7 | +14.85% | 5 | -0.22 | 23 | -3.72% | 25 | 0.12 | 16 | +0.74% | 16 |
| `sp500-2m/cross_sector_slide1m_bd7` | -0.39 | 31 | -3.36% | 31 | 0.39 | 7 | +1.86% | 9 | 0.11 | 17 | +0.46% | 17 |
| `core-2m/cross_sector_slide1m_bd7` | 0.33 | 21 | +2.55% | 21 | -0.12 | 20 | -1.60% | 22 | 0.04 | 18 | -0.09% | 20 |
| `core-12m/cross_sector_slide3m_bd7` | 0.31 | 22 | +2.06% | 22 | -0.10 | 17 | -0.71% | 18 | 0.04 | 19 | -0.01% | 18 |
| `core-2m/cross_sector_slide3m_noscreen` | 0.79 | 11 | +15.65% | 4 | -0.18 | 22 | -8.92% | 32 | 0.03 | 20 | -3.16% | 29 |
| `core-2m/same_sector_slide1m_bd7` | 1.30 | 4 | +8.19% | 10 | -0.10 | 19 | -0.60% | 17 | 0.01 | 21 | -0.06% | 19 |
| `core-2m/same_sector_slide1m_noscreen` | 1.28 | 6 | +12.05% | 7 | -0.10 | 18 | -0.90% | 19 | -0.00 | 22 | -0.29% | 23 |
| `sp500-2m/same_sector_slide1m_bd7` | -0.39 | 32 | -2.18% | 30 | -0.23 | 24 | -1.19% | 21 | -0.03 | 23 | -0.27% | 22 |
| `core-12m/cross_sector_slide1m_noscreen` | 0.81 | 8 | +8.54% | 9 | -0.44 | 26 | -3.44% | 24 | -0.07 | 24 | -0.93% | 25 |
| `core-12m/same_sector_slide1m_bd7` | 0.28 | 25 | +0.58% | 26 | 0.13 | 15 | +0.25% | 16 | -0.10 | 25 | -0.25% | 21 |
| `core-2m/cross_sector_slide3m_bd7` | -0.01 | 28 | +0.13% | 27 | -0.14 | 21 | -7.53% | 31 | -0.11 | 26 | -5.65% | 32 |
| `core-2m/same_sector_slide3m_noscreen` | 0.50 | 14 | +7.01% | 11 | -0.56 | 27 | -5.39% | 28 | -0.18 | 27 | -2.43% | 28 |
| `core-2m/same_sector_slide3m_bd7` | 0.47 | 15 | +4.47% | 17 | -0.64 | 29 | -3.85% | 26 | -0.23 | 28 | -1.78% | 27 |
| `core-12m/same_sector_slide3m_bd7` | 0.12 | 27 | +0.04% | 28 | -0.34 | 25 | -1.16% | 20 | -0.26 | 29 | -0.88% | 24 |
| `core-12m/cross_sector_slide3m_noscreen` | 0.41 | 18 | +5.36% | 13 | -0.70 | 30 | -7.08% | 30 | -0.34 | 30 | -3.99% | 31 |
| `core-12m/same_sector_slide1m_noscreen` | 0.29 | 24 | +1.14% | 24 | -0.79 | 31 | -2.45% | 23 | -0.39 | 31 | -1.59% | 26 |
| `core-12m/same_sector_slide3m_noscreen` | 0.27 | 26 | +1.12% | 25 | -0.90 | 32 | -4.69% | 27 | -0.60 | 32 | -3.21% | 30 |

## Legs used by the strict consensus shortlist

This compact view connects the pair shortlist to the individual-leg rankings. The full 32-leg table is above.

| Leg | Rec Sh (#) | Rec Ret% (#) | Hist Sh (#) | Hist Ret% (#) | Joined Sh (#) | Joined Ret% (#) |
|---|---:|---:|---:|---:|---:|---:|
| `sp500-12m/cross_sector_slide1m_noscreen` | 1.84 (1) | +19.54% (2) | 0.44 (5) | +3.25% (4) | 0.66 (1) | +5.53% (3) |
| `sp500-12m/same_sector_slide1m_noscreen` | 1.33 (3) | +15.90% (3) | 0.40 (6) | +2.86% (6) | 0.63 (2) | +5.32% (4) |
| `sp500-2m/cross_sector_slide3m_bd7` | -0.38 (30) | -3.66% (32) | 0.88 (1) | +7.69% (2) | 0.54 (4) | +4.64% (5) |
| `sp500-12m/same_sector_slide3m_noscreen` | 0.81 (10) | +12.32% (6) | 0.37 (8) | +3.44% (3) | 0.51 (5) | +5.65% (2) |
| `sp500-12m/cross_sector_slide3m_bd7` | 0.81 (9) | +6.91% (12) | 0.30 (10) | +2.30% (8) | 0.41 (7) | +3.35% (6) |
| `sp500-12m/same_sector_slide1m_bd7` | 0.68 (12) | +5.02% (14) | 0.50 (4) | +2.67% (7) | 0.37 (8) | +2.11% (10) |
| `sp500-2m/same_sector_slide1m_noscreen` | -0.04 (29) | -0.63% (29) | 0.28 (11) | +1.70% (10) | 0.28 (10) | +1.91% (11) |
| `sp500-2m/same_sector_slide3m_noscreen` | 0.33 (20) | +4.09% (18) | 0.19 (14) | +1.50% (11) | 0.24 (13) | +2.14% (9) |
| `sp500-2m/cross_sector_slide1m_bd7` | -0.39 (31) | -3.36% (31) | 0.39 (7) | +1.86% (9) | 0.11 (17) | +0.46% (17) |

## Source files

- Corrected leg metrics: `fixed_diagnosis/_sweep_pct25/`
- Leg joined metrics: `fixed_diagnosis/joint/joined_legs.csv`
- Ranking method definitions: `research/compare_rankings.py`
- Default event replay: `research/run_combined_backtest.py`
- Corrected pipeline context: `RESEARCH_PIPELINE_FIXED.md`

