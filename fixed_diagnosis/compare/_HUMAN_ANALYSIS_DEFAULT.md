# Original default allocation - consolidated human analysis

Pair ranks and recent/historical pair metrics: `fixed_diagnosis/compare/rank_comparison_A.csv` and `rank_comparison_B.csv`. Mechanism-A joined returns come from `fixed_diagnosis/joint/joined_pairs.csv`; displayed mechanism-B joined returns are recomputed from the corrected sweep with the default event replay.  pct=0.25 and capital=$1,000,000. Momentum parameters: lookback=63 days, step=0.10, weight bounds=[0.25, 0.75], initial weight_A=0.50.

Universe: 32 corrected legs and 496 two-leg combinations. Recent metrics are means over five aligned starts; historical metrics use the single aligned 2015-2019 window. Joined metrics concatenate historical and each recent series, then average the five joined results. All Sharpe ratios and returns are annualized.

Mechanism A and mechanism B are the two shared-account event-replay implementations. The displayed pair order is the source CSV order and does not change the stored mechanism result.

## Human analysis

The three methods answer different questions. The separate score protects the weaker window, rank-average rewards a consistently high position in both windows, and joined Sharpe treats the historical and recent series as one sample. A method disagreement is therefore evidence of regime dependence, not a reason to select the largest recent Sharpe automatically.

- Mechanism A leaders: separate score: `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` (joined Sh 1.04, joined return +7.65%); rank-average: `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` (joined Sh 0.75, joined return +7.07%); joined Sharpe: `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` (joined Sh 1.04, joined return +7.65%).
  The top-20 all-method intersection for mechanism A is 6 pair(s).
- Mechanism B leaders: separate score: `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` (joined Sh 0.84, joined return +6.43%); rank-average: `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` (joined Sh 0.68, joined return +4.17%); joined Sharpe: `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` (joined Sh 1.01, joined return +7.39%).
  The top-20 all-method intersection for mechanism B is 6 pair(s).
- The strongest strict-consensus pair by the sum of its six method ranks is `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` (rank-sum 32.0). This is a mechanical shortlist, not an automatic trading decision.
- Pair ranks and leg ranks are different objects. Dynamic capital rotation and the shared-account event replay can make a pair attractive even when neither leg is the top standalone leg in every window.
- Return ranks should be read alongside Sharpe ranks: a high annualized return can come with materially higher volatility or drawdown, while a high Sharpe can reflect a smaller but steadier return.
- This report is the original default allocation baseline. The clean40 report should be read as the later parameterized comparison, not mixed into these values.
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
| A | 6 | 10 | 10 | 6 |
| B | 6 | 11 | 9 | 6 |

| Mechanism | Separate vs rank-average | Separate vs joined | Rank-average vs joined |
|---|---:|---:|---:|
| A | 0.743 | 0.874 | 0.877 |
| B | 0.720 | 0.863 | 0.868 |

The strict cross-mechanism shortlist contains **6** pair(s): top 20 in all three methods for both mechanisms.

- `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen`
- `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7`
- `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_noscreen`
- `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide1m_noscreen`
- `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen`
- `sp500-12m/same_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7`

## Strict consensus pair detail

| Pair | Mech | Separate # | Rank-average # | Joined # | Recent Sh / Ret% | Hist Sh / Ret% | Joined Sh / Ret% | Score |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | A | 10 | 1 | 6 | 1.14 / +14.60% | 0.56 / +4.52% | 0.75 / +7.07% | 0.56 |
| `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | B | 6 | 3 | 6 | 1.08 / +14.01% | 0.60 / +4.83% | 0.76 / +7.16% | 0.60 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | A | 1 | 17 | 1 | 0.83 / +6.54% | 1.14 / +8.08% | 1.04 / +7.65% | 0.83 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | B | 2 | 16 | 1 | 0.82 / +6.56% | 1.09 / +7.73% | 1.01 / +7.39% | 0.82 |
| `sp500-12m/same_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | A | 2 | 17 | 4 | 0.87 / +8.09% | 0.81 / +5.57% | 0.82 / +6.22% | 0.81 |
| `sp500-12m/same_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | B | 1 | 20 | 4 | 0.83 / +7.77% | 0.87 / +5.95% | 0.84 / +6.43% | 0.83 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | A | 7 | 6 | 8 | 1.06 / +11.34% | 0.58 / +4.29% | 0.73 / +6.09% | 0.58 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | B | 17 | 7 | 10 | 1.04 / +11.17% | 0.53 / +3.87% | 0.69 / +5.74% | 0.53 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_noscreen` | A | 4 | 19 | 9 | 0.91 / +8.57% | 0.67 / +5.57% | 0.73 / +6.31% | 0.67 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_noscreen` | B | 4 | 15 | 9 | 0.90 / +8.60% | 0.65 / +5.40% | 0.71 / +6.19% | 0.65 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide1m_noscreen` | A | 20 | 6 | 14 | 1.09 / +9.04% | 0.49 / +2.79% | 0.68 / +4.39% | 0.49 |
| `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/same_sector_slide1m_noscreen` | B | 15 | 19 | 17 | 0.92 / +7.90% | 0.54 / +3.10% | 0.65 / +4.32% | 0.54 |

## Pair rankings

Each table contains the top 20 rows for one method. `Rec #`, `Hist #`, and `Joined #` are the pair ranks for the corresponding Sharpe metric; `Score` is the minimum of recent and historical Sharpe.

## Mechanism A

### Top 20 by separate score

| # | Pair | Rec # | Rec Sh | Rec Ret% | Hist # | Hist Sh | Hist Ret% | Joined # | Joined Sh | Joined Ret% | Score | Rank Avg |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 150 | 0.83 | +6.54% | 1 | 1.14 | +8.08% | 1 | 1.04 | +7.65% | 0.83 | 75.5 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 140 | 0.87 | +8.09% | 11 | 0.81 | +5.57% | 4 | 0.82 | +6.22% | 0.81 | 75.5 |
| 3 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 191 | 0.73 | +9.03% | 22 | 0.70 | +7.23% | 10 | 0.72 | +7.69% | 0.70 | 106.5 |
| 4 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 126 | 0.91 | +8.57% | 26 | 0.67 | +5.57% | 9 | 0.73 | +6.31% | 0.67 | 76.0 |
| 5 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 221 | 0.68 | +7.71% | 30 | 0.60 | +5.07% | 21 | 0.63 | +5.78% | 0.60 | 125.5 |
| 6 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 251 | 0.60 | +6.88% | 28 | 0.61 | +3.83% | 35 | 0.60 | +4.61% | 0.60 | 139.5 |
| 7 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 81 | 1.06 | +11.34% | 35 | 0.58 | +4.29% | 8 | 0.73 | +6.09% | 0.58 | 58.0 |
| 8 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide3m_bd7` | 267 | 0.57 | +3.54% | 29 | 0.61 | +4.77% | 45 | 0.57 | +4.46% | 0.57 | 148.0 |
| 9 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 220 | 0.68 | +7.42% | 36 | 0.56 | +3.99% | 37 | 0.60 | +4.85% | 0.56 | 128.0 |
| 10 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 54 | 1.14 | +14.60% | 37 | 0.56 | +4.52% | 6 | 0.75 | +7.07% | 0.56 | 45.5 |
| 11 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 280 | 0.55 | +4.28% | 15 | 0.76 | +5.57% | 12 | 0.69 | +5.19% | 0.55 | 147.5 |
| 12 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 196 | 0.73 | +7.18% | 38 | 0.53 | +3.73% | 39 | 0.60 | +4.65% | 0.53 | 117.0 |
| 13 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 169 | 0.78 | +8.83% | 39 | 0.53 | +3.72% | 29 | 0.62 | +5.02% | 0.53 | 104.0 |
| 14 | `sp500-2m/cross_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 141 | 0.86 | +9.50% | 40 | 0.53 | +3.96% | 18 | 0.63 | +5.37% | 0.53 | 90.5 |
| 15 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide3m_noscreen` | 182 | 0.76 | +7.21% | 42 | 0.52 | +4.13% | 42 | 0.59 | +4.90% | 0.52 | 112.0 |
| 16 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 301 | 0.52 | +6.29% | 3 | 1.09 | +8.72% | 2 | 0.91 | +8.12% | 0.52 | 152.0 |
| 17 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 154 | 0.82 | +7.89% | 44 | 0.52 | +3.41% | 24 | 0.62 | +4.57% | 0.52 | 99.0 |
| 18 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 139 | 0.87 | +9.17% | 45 | 0.52 | +4.34% | 28 | 0.62 | +5.58% | 0.52 | 92.0 |
| 19 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 186 | 0.74 | +8.09% | 46 | 0.51 | +2.91% | 36 | 0.60 | +4.22% | 0.51 | 116.0 |
| 20 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 69 | 1.09 | +9.04% | 47 | 0.49 | +2.79% | 14 | 0.68 | +4.39% | 0.49 | 58.0 |

### Top 20 by rank-average

| # | Pair | Rec # | Rec Sh | Rec Ret% | Hist # | Hist Sh | Hist Ret% | Joined # | Joined Sh | Joined Ret% | Score | Rank Avg |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 54 | 1.14 | +14.60% | 37 | 0.56 | +4.52% | 6 | 0.75 | +7.07% | 0.56 | 45.5 |
| 2 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 14 | 1.38 | +13.44% | 82 | 0.35 | +2.14% | 11 | 0.69 | +5.00% | 0.35 | 48.0 |
| 3 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 33 | 1.22 | +8.63% | 65 | 0.41 | +2.11% | 16 | 0.66 | +3.78% | 0.41 | 49.0 |
| 4 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 16 | 1.36 | +11.21% | 90 | 0.33 | +1.76% | 15 | 0.66 | +4.16% | 0.33 | 53.0 |
| 5 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 41 | 1.19 | +8.32% | 73 | 0.37 | +2.04% | 31 | 0.61 | +3.66% | 0.37 | 57.0 |
| 6 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 69 | 1.09 | +9.04% | 47 | 0.49 | +2.79% | 14 | 0.68 | +4.39% | 0.49 | 58.0 |
| 6 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 24 | 1.28 | +9.12% | 92 | 0.32 | +1.44% | 19 | 0.63 | +3.39% | 0.32 | 58.0 |
| 6 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 81 | 1.06 | +11.34% | 35 | 0.58 | +4.29% | 8 | 0.73 | +6.09% | 0.58 | 58.0 |
| 9 | `sp500-2m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 48 | 1.16 | +10.24% | 75 | 0.37 | +2.15% | 26 | 0.62 | +4.20% | 0.37 | 61.5 |
| 10 | `sp500-12m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 22 | 1.28 | +11.52% | 103 | 0.29 | +2.04% | 55 | 0.55 | +4.38% | 0.29 | 62.5 |
| 11 | `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 59 | 1.12 | +10.10% | 70 | 0.40 | +2.29% | 23 | 0.63 | +4.24% | 0.40 | 64.5 |
| 12 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 80 | 1.07 | +10.44% | 54 | 0.46 | +3.63% | 27 | 0.62 | +5.33% | 0.46 | 67.0 |
| 13 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 75 | 1.08 | +10.16% | 63 | 0.42 | +2.73% | 22 | 0.63 | +4.62% | 0.42 | 69.0 |
| 14 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 46 | 1.16 | +9.10% | 93 | 0.32 | +1.66% | 41 | 0.59 | +3.55% | 0.32 | 69.5 |
| 15 | `sp500-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 44 | 1.17 | +9.29% | 96 | 0.32 | +1.72% | 43 | 0.58 | +3.64% | 0.32 | 70.0 |
| 16 | `core-12m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 29 | 1.24 | +8.50% | 121 | 0.24 | +1.22% | 58 | 0.54 | +3.05% | 0.24 | 75.0 |
| 17 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 140 | 0.87 | +8.09% | 11 | 0.81 | +5.57% | 4 | 0.82 | +6.22% | 0.81 | 75.5 |
| 17 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 150 | 0.83 | +6.54% | 1 | 1.14 | +8.08% | 1 | 1.04 | +7.65% | 0.83 | 75.5 |
| 19 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 126 | 0.91 | +8.57% | 26 | 0.67 | +5.57% | 9 | 0.73 | +6.31% | 0.67 | 76.0 |
| 20 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 89 | 1.04 | +10.48% | 64 | 0.42 | +2.85% | 25 | 0.62 | +4.83% | 0.42 | 76.5 |

### Top 20 by joined Sharpe

| # | Pair | Rec # | Rec Sh | Rec Ret% | Hist # | Hist Sh | Hist Ret% | Joined # | Joined Sh | Joined Ret% | Score | Rank Avg |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 150 | 0.83 | +6.54% | 1 | 1.14 | +8.08% | 1 | 1.04 | +7.65% | 0.83 | 75.5 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 301 | 0.52 | +6.29% | 3 | 1.09 | +8.72% | 2 | 0.91 | +8.12% | 0.52 | 152.0 |
| 3 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 395 | 0.32 | +2.04% | 2 | 1.13 | +7.00% | 3 | 0.90 | +5.70% | 0.32 | 198.5 |
| 4 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 140 | 0.87 | +8.09% | 11 | 0.81 | +5.57% | 4 | 0.82 | +6.22% | 0.81 | 75.5 |
| 5 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_bd7` | 443 | 0.19 | +1.24% | 5 | 1.01 | +6.75% | 5 | 0.78 | +5.25% | 0.19 | 224.0 |
| 6 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 54 | 1.14 | +14.60% | 37 | 0.56 | +4.52% | 6 | 0.75 | +7.07% | 0.56 | 45.5 |
| 7 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_bd7` | 471 | -0.00 | -0.25% | 4 | 1.03 | +7.26% | 7 | 0.74 | +5.34% | -0.00 | 237.5 |
| 8 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 81 | 1.06 | +11.34% | 35 | 0.58 | +4.29% | 8 | 0.73 | +6.09% | 0.58 | 58.0 |
| 9 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 126 | 0.91 | +8.57% | 26 | 0.67 | +5.57% | 9 | 0.73 | +6.31% | 0.67 | 76.0 |
| 10 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 191 | 0.73 | +9.03% | 22 | 0.70 | +7.23% | 10 | 0.72 | +7.69% | 0.70 | 106.5 |
| 11 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 14 | 1.38 | +13.44% | 82 | 0.35 | +2.14% | 11 | 0.69 | +5.00% | 0.35 | 48.0 |
| 12 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 280 | 0.55 | +4.28% | 15 | 0.76 | +5.57% | 12 | 0.69 | +5.19% | 0.55 | 147.5 |
| 13 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-2m/cross_sector_slide3m_bd7` | 454 | 0.13 | +0.60% | 6 | 0.90 | +6.78% | 13 | 0.68 | +5.12% | 0.13 | 230.0 |
| 14 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 69 | 1.09 | +9.04% | 47 | 0.49 | +2.79% | 14 | 0.68 | +4.39% | 0.49 | 58.0 |
| 15 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 16 | 1.36 | +11.21% | 90 | 0.33 | +1.76% | 15 | 0.66 | +4.16% | 0.33 | 53.0 |
| 16 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 33 | 1.22 | +8.63% | 65 | 0.41 | +2.11% | 16 | 0.66 | +3.78% | 0.41 | 49.0 |
| 17 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_bd7` | 332 | 0.47 | +4.39% | 19 | 0.72 | +6.15% | 17 | 0.65 | +5.70% | 0.47 | 175.5 |
| 18 | `sp500-2m/cross_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 141 | 0.86 | +9.50% | 40 | 0.53 | +3.96% | 18 | 0.63 | +5.37% | 0.53 | 90.5 |
| 19 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 24 | 1.28 | +9.12% | 92 | 0.32 | +1.44% | 19 | 0.63 | +3.39% | 0.32 | 58.0 |
| 20 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | 446 | 0.18 | +1.30% | 13 | 0.80 | +9.33% | 20 | 0.63 | +7.31% | 0.18 | 229.5 |

## Mechanism B

### Top 20 by separate score

| # | Pair | Rec # | Rec Sh | Rec Ret% | Hist # | Hist Sh | Hist Ret% | Joined # | Joined Sh | Joined Ret% | Score | Rank Avg |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 160 | 0.83 | +7.77% | 9 | 0.87 | +5.95% | 4 | 0.84 | +6.43% | 0.83 | 84.5 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 163 | 0.82 | +6.56% | 2 | 1.09 | +7.73% | 1 | 1.01 | +7.39% | 0.82 | 82.5 |
| 3 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 196 | 0.75 | +9.12% | 24 | 0.71 | +7.30% | 8 | 0.73 | +7.76% | 0.71 | 110.0 |
| 4 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 131 | 0.90 | +8.60% | 26 | 0.65 | +5.40% | 9 | 0.71 | +6.19% | 0.65 | 78.5 |
| 5 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 218 | 0.68 | +7.67% | 30 | 0.62 | +5.20% | 19 | 0.64 | +5.86% | 0.62 | 124.0 |
| 6 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 66 | 1.08 | +14.01% | 33 | 0.60 | +4.83% | 6 | 0.76 | +7.16% | 0.60 | 49.5 |
| 7 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 259 | 0.59 | +6.76% | 28 | 0.64 | +3.98% | 26 | 0.61 | +4.69% | 0.59 | 143.5 |
| 8 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide3m_bd7` | 271 | 0.57 | +3.56% | 36 | 0.59 | +4.63% | 46 | 0.56 | +4.36% | 0.57 | 153.5 |
| 9 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 272 | 0.57 | +6.20% | 32 | 0.60 | +4.29% | 37 | 0.59 | +4.77% | 0.57 | 152.0 |
| 10 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 195 | 0.75 | +8.05% | 37 | 0.55 | +3.11% | 24 | 0.63 | +4.37% | 0.55 | 116.0 |
| 11 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 183 | 0.78 | +8.84% | 38 | 0.55 | +3.81% | 23 | 0.63 | +5.10% | 0.55 | 110.5 |
| 12 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 147 | 0.87 | +9.19% | 39 | 0.55 | +4.63% | 20 | 0.64 | +5.81% | 0.55 | 93.0 |
| 13 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 287 | 0.54 | +4.23% | 16 | 0.77 | +5.63% | 11 | 0.69 | +5.21% | 0.54 | 151.5 |
| 14 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide3m_noscreen` | 193 | 0.76 | +7.20% | 40 | 0.54 | +4.32% | 33 | 0.60 | +5.04% | 0.54 | 116.5 |
| 15 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 124 | 0.92 | +7.90% | 43 | 0.54 | +3.10% | 17 | 0.65 | +4.32% | 0.54 | 83.5 |
| 16 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 205 | 0.72 | +7.05% | 44 | 0.53 | +3.73% | 35 | 0.59 | +4.61% | 0.53 | 124.5 |
| 17 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 76 | 1.04 | +11.17% | 45 | 0.53 | +3.87% | 10 | 0.69 | +5.74% | 0.53 | 60.5 |
| 18 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 299 | 0.52 | +6.28% | 3 | 1.09 | +8.68% | 2 | 0.91 | +8.09% | 0.52 | 151.0 |
| 19 | `sp500-2m/cross_sector_slide1m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 148 | 0.87 | +8.00% | 48 | 0.52 | +2.55% | 22 | 0.63 | +3.96% | 0.52 | 98.0 |
| 20 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 173 | 0.79 | +7.55% | 49 | 0.52 | +3.37% | 29 | 0.61 | +4.46% | 0.52 | 111.0 |

### Top 20 by rank-average

| # | Pair | Rec # | Rec Sh | Rec Ret% | Hist # | Hist Sh | Hist Ret% | Joined # | Joined Sh | Joined Ret% | Score | Rank Avg |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 8 | 1.34 | +9.82% | 68 | 0.40 | +2.22% | 14 | 0.68 | +4.17% | 0.40 | 38.0 |
| 2 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 38 | 1.16 | +8.40% | 58 | 0.45 | +2.12% | 12 | 0.69 | +3.75% | 0.45 | 48.0 |
| 3 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 66 | 1.08 | +14.01% | 33 | 0.60 | +4.83% | 6 | 0.76 | +7.16% | 0.60 | 49.5 |
| 4 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 25 | 1.19 | +8.77% | 81 | 0.35 | +1.81% | 27 | 0.61 | +3.57% | 0.35 | 53.0 |
| 5 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 2 | 1.43 | +12.39% | 105 | 0.29 | +1.56% | 16 | 0.66 | +4.29% | 0.29 | 53.5 |
| 6 | `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 12 | 1.29 | +12.98% | 99 | 0.31 | +1.88% | 21 | 0.64 | +4.70% | 0.31 | 55.5 |
| 7 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 76 | 1.04 | +11.17% | 45 | 0.53 | +3.87% | 10 | 0.69 | +5.74% | 0.53 | 60.5 |
| 8 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 70 | 1.06 | +10.32% | 62 | 0.44 | +3.46% | 31 | 0.60 | +5.17% | 0.44 | 66.0 |
| 9 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 73 | 1.05 | +9.96% | 67 | 0.41 | +2.64% | 28 | 0.61 | +4.49% | 0.41 | 70.0 |
| 10 | `core-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 21 | 1.21 | +8.85% | 121 | 0.24 | +1.07% | 44 | 0.56 | +3.04% | 0.24 | 71.0 |
| 11 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 43 | 1.14 | +9.11% | 104 | 0.29 | +1.50% | 45 | 0.56 | +3.42% | 0.29 | 73.5 |
| 12 | `sp500-12m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 24 | 1.19 | +11.13% | 126 | 0.23 | +1.58% | 69 | 0.49 | +3.94% | 0.23 | 75.0 |
| 13 | `core-2m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide3m_bd7` | 74 | 1.05 | +6.94% | 82 | 0.35 | +1.80% | 59 | 0.53 | +3.01% | 0.35 | 78.0 |
| 13 | `sp500-12m/same_sector_slide1m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 47 | 1.12 | +9.32% | 109 | 0.28 | +1.52% | 51 | 0.55 | +3.49% | 0.28 | 78.0 |
| 15 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 131 | 0.90 | +8.60% | 26 | 0.65 | +5.40% | 9 | 0.71 | +6.19% | 0.65 | 78.5 |
| 16 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 77 | 1.04 | +8.84% | 88 | 0.34 | +1.77% | 38 | 0.58 | +3.61% | 0.34 | 82.5 |
| 16 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 163 | 0.82 | +6.56% | 2 | 1.09 | +7.73% | 1 | 1.01 | +7.39% | 0.82 | 82.5 |
| 18 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 101 | 0.97 | +9.84% | 65 | 0.43 | +2.94% | 30 | 0.61 | +4.74% | 0.43 | 83.0 |
| 19 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 124 | 0.92 | +7.90% | 43 | 0.54 | +3.10% | 17 | 0.65 | +4.32% | 0.54 | 83.5 |
| 20 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 160 | 0.83 | +7.77% | 9 | 0.87 | +5.95% | 4 | 0.84 | +6.43% | 0.83 | 84.5 |

### Top 20 by joined Sharpe

| # | Pair | Rec # | Rec Sh | Rec Ret% | Hist # | Hist Sh | Hist Ret% | Joined # | Joined Sh | Joined Ret% | Score | Rank Avg |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 163 | 0.82 | +6.56% | 2 | 1.09 | +7.73% | 1 | 1.01 | +7.39% | 0.82 | 82.5 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_noscreen` | 299 | 0.52 | +6.28% | 3 | 1.09 | +8.68% | 2 | 0.91 | +8.09% | 0.52 | 151.0 |
| 3 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_bd7` | 388 | 0.31 | +1.92% | 1 | 1.14 | +7.00% | 3 | 0.89 | +5.67% | 0.31 | 194.5 |
| 4 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 160 | 0.83 | +7.77% | 9 | 0.87 | +5.95% | 4 | 0.84 | +6.43% | 0.83 | 84.5 |
| 5 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_bd7` | 419 | 0.24 | +1.59% | 4 | 1.03 | +6.89% | 5 | 0.81 | +5.45% | 0.24 | 211.5 |
| 6 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 66 | 1.08 | +14.01% | 33 | 0.60 | +4.83% | 6 | 0.76 | +7.16% | 0.60 | 49.5 |
| 7 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide3m_bd7` | 471 | -0.00 | -0.28% | 5 | 1.03 | +7.24% | 7 | 0.74 | +5.32% | -0.00 | 238.0 |
| 8 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 196 | 0.75 | +9.12% | 24 | 0.71 | +7.30% | 8 | 0.73 | +7.76% | 0.71 | 110.0 |
| 9 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 131 | 0.90 | +8.60% | 26 | 0.65 | +5.40% | 9 | 0.71 | +6.19% | 0.65 | 78.5 |
| 10 | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 76 | 1.04 | +11.17% | 45 | 0.53 | +3.87% | 10 | 0.69 | +5.74% | 0.53 | 60.5 |
| 11 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 287 | 0.54 | +4.23% | 16 | 0.77 | +5.63% | 11 | 0.69 | +5.21% | 0.54 | 151.5 |
| 12 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_bd7` | 38 | 1.16 | +8.40% | 58 | 0.45 | +2.12% | 12 | 0.69 | +3.75% | 0.45 | 48.0 |
| 13 | `sp500-2m/same_sector_slide3m_bd7` + `sp500-2m/cross_sector_slide3m_bd7` | 456 | 0.12 | +0.55% | 8 | 0.89 | +6.73% | 13 | 0.68 | +5.06% | 0.12 | 232.0 |
| 14 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide3m_bd7` | 8 | 1.34 | +9.82% | 68 | 0.40 | +2.22% | 14 | 0.68 | +4.17% | 0.40 | 38.0 |
| 15 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_bd7` | 321 | 0.48 | +4.48% | 22 | 0.74 | +6.26% | 15 | 0.66 | +5.80% | 0.48 | 171.5 |
| 16 | `core-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 2 | 1.43 | +12.39% | 105 | 0.29 | +1.56% | 16 | 0.66 | +4.29% | 0.29 | 53.5 |
| 17 | `sp500-2m/same_sector_slide1m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 124 | 0.92 | +7.90% | 43 | 0.54 | +3.10% | 17 | 0.65 | +4.32% | 0.54 | 83.5 |
| 18 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7` | 434 | 0.21 | +1.70% | 13 | 0.81 | +9.44% | 18 | 0.64 | +7.49% | 0.21 | 223.5 |
| 19 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 218 | 0.68 | +7.67% | 30 | 0.62 | +5.20% | 19 | 0.64 | +5.86% | 0.62 | 124.0 |
| 20 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_noscreen` | 147 | 0.87 | +9.19% | 39 | 0.55 | +4.63% | 20 | 0.64 | +5.81% | 0.55 | 93.0 |

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
| `sp500-2m/cross_sector_slide3m_noscreen` | 0.41 (19) | +4.53% (16) | 0.62 (2) | +9.34% (1) | 0.56 (3) | +8.00% (1) |
| `sp500-2m/cross_sector_slide3m_bd7` | -0.38 (30) | -3.66% (32) | 0.88 (1) | +7.69% (2) | 0.54 (4) | +4.64% (5) |
| `sp500-12m/same_sector_slide3m_noscreen` | 0.81 (10) | +12.32% (6) | 0.37 (8) | +3.44% (3) | 0.51 (5) | +5.65% (2) |
| `sp500-2m/same_sector_slide1m_noscreen` | -0.04 (29) | -0.63% (29) | 0.28 (11) | +1.70% (10) | 0.28 (10) | +1.91% (11) |

## Source files

- Corrected leg metrics: `fixed_diagnosis/_sweep_pct25/`
- Leg joined metrics: `fixed_diagnosis/joint/joined_legs.csv`
- Ranking method definitions: `research/compare_rankings.py`
- Default event replay: `research/run_combined_backtest.py`
- Corrected pipeline context: `RESEARCH_PIPELINE_FIXED.md`

