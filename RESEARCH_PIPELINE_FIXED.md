# Research Pipeline - Fixed and Reproducible

This document is the corrected companion to `RESEARCH_PIPELINE.md`. It records the
same investigation without rewriting the original user-curated note. The corrected
historical grid uses aligned 2015-01-02 through 2019-12-31 trading windows and the
correct pool, universe, sector, earnings, and return-divergence routing.

## Scope and Conventions

- `RESEARCH_PIPELINE.md` is preserved and is not a source for the corrected combined
  results below.
 - Sections 01, 02, 03, and 03a-c retain the original live-selection diagnosis as
  historical context. Sections 02b and 04 were regenerated with the corrected
  pool-backed runner and are current report sources.
- Canonical corrected single-leg grids are in `fixed_diagnosis/05` through
  `fixed_diagnosis/10b`.
- Canonical pct=0.25 leg inputs for all combined analyses are in
  `fixed_diagnosis/_sweep_pct25`. The older `fixed_diagnosis/_pct25 (old)` directory is
  not used.
- The original `diagnosis/05_grid_search_mp20 (old)`, `diagnosis/06_grid_search_mp5 (old)`,
  `diagnosis/07_grid_search_sp500 (old)`, and the original 2015-2020/12m-selection trees
  remain as legacy audit context. They are not canonical sources for sections 05
  through 10b; use the corresponding `fixed_diagnosis` trees instead. The explicitly
  superseded `diagnosis/00_summary (old).md` and preserved contaminated 08b tree are also
  not evidence for the corrected result.
- Sharpe and returns are annualized. Recent values are means across five aligned
  starts unless a table says `single start`; historical values are one aligned
  2015-2019 run.
- A `bd7` configuration uses the earnings block; `noscreen` does not.
- `AT` means mean active trades. `MDD` means maximum drawdown.
- Combined books replay logged trade events and daily marks into one shared account.
  They are not a synthetic arithmetic average of two final return series.

## Locked Selection

The quantitative book selection is now locked in the canonical machine-readable record
`research/selected_book_config.json`. Future tests should use this selection rather than
re-sweeping alternative pairs or momentum cells unless they are explicitly testing a new
selection decision.

- Leg A (recent-strong): `sp500-12m/cross_sector_slide1m_noscreen`.
- Leg B (historical-strong): `sp500-2m/cross_sector_slide3m_bd7`.
- Momentum: `lookback=84`, `step=0.40`, bounds `[0.10, 0.90]`, initial weight on leg A `0.50`.
- Book inputs: initial capital `$1,000,000`, `pct_per_pair=0.25`.
- Selection evidence: the pair ranked `#1` under separate score, rank-average, and joined
  Sharpe in both mechanisms across all 496 pairs in the clean40 evaluation.
- This lock does not choose broker leverage, margin behavior or rates, borrow costs, slippage,
  or transaction costs. Those remain open for realistic capacity validation.

## TL;DR - One Line Per Section

This table is the chronological argument, not just a list of winners. The middle
column records what the data actually showed; the last column records why the next
test was justified.

| # | Test and context | Observation and note | Why we moved to the next test |
|---|---|---|---|
| [01](#01---baseline-instability) | Baseline: five start dates x seven folds | Sharpe ranged `-0.28` to `1.48` (std `0.66`). Losses looked concentrated around earnings gaps. | Test an earnings screen before blaming pair selection. |
| [02](#02---earnings-screen-baseline) | Forward earnings screen ON/OFF | The screen improved 14 comparisons and degraded 17; mean Sharpe fell `0.48` to `0.41` and legitimate trades were blocked. | Since forward screening was inconsistent, test backward block durations because some losses happened after earnings. |
| [02b](#02b---earnings-block-days-sweep) | Earnings block-days `{0,3,5,7,9}` | bd3 and bd5 are identical; bd7 and bd9 also match on four of five starts. The bd9 mean advantage is concentrated in the `2024-01-01` start, while trade counts are nearly identical and bd7 is less dispersed. | Keep bd7 as the conservative, minimum-sufficient block rather than selecting bd9 on one potentially lucky event; treat earnings as secondary and inspect pair-selection stability. |
| [03](#03---pair-selection-stability) | Pair-selection stability | Jaccard@5 was `0.036`, top-five dropout `0.940`, and Spearman rho `0.122`. | Compare sector masks and slide lengths to see whether a larger or different candidate pool stabilizes rankings. |
| [03a-c](#03a-03c---sector-and-slide-stability-comparison) | Four sector/slide stability comparisons | Cross-sector had about five times the pool, but its proportional instability was similar. The deeper issue was noisy short-window cointegration p-value ranking; pool size amplified but did not explain it alone. | Stop treating cross-sector as a guaranteed stability fix, then choose a practical book breadth and run the full grid. |
| [04](#04---max-pairs-sweep) | `max_pairs` `{5,10,20,50}` | More pairs increased deployment breadth. `mp=20` was retained as the operating compromise, not as the universal raw-Sharpe winner. | Fix `max_pairs=20` so later configuration comparisons are about signal choices rather than book thickness. |
| [05](#05---core-2m-mp5-pct018) | Core 2m, mp=5, pct=.18 | Same-sector 1m noscreen reached Sharpe `1.40` and return `4.79%`, but the book was thin. | Compare against the thicker mp20 book before promoting the raw winner. |
| [06](#06---core-2m-mp20-pct0045) | Core 2m, mp=20, pct=.045 | Cross-sector 1m noscreen was the corrected recent winner at Sharpe `1.53`, return `3.57%`, positive at all five starts. | Test whether this recent result survives a wider universe and a different historical regime. |
| [6b](#6b---core-12m-recent) | Core 12m, recent | Cross-sector 1m noscreen led the core 12m cell at `0.80` and `1.51%`, but remained below the matching core 2m result. | Complete the same 12m comparison on SP500 rather than assuming the core result generalizes. |
| [07](#07---sp500-2m-mp20-pct0045) | SP500 2m, recent | The best cell was only `0.42` Sharpe and `0.85%`; the strongest alternative was start-date noisy. | Test 12m selection because a longer selection window might make the wider universe useful. |
| [7b](#7b---sp500-12m-recent) | SP500 12m, recent | Cross-sector 1m noscreen reached `1.89` and `3.43%`, the strongest single-leg recent cell; same 1m noscreen was more stable. | Check the apparently strong SP500 12m result against the historical window. |
| [08a](#08a---core-2m-historical) | Core 2m, historical | Every corrected configuration was negative; the best Sharpe was `-0.08`. The recent core winner did not transfer. | Test core 12m selection rather than concluding that all core methods fail historically. |
| [08b](#08b---core-12m-historical) | Core 12m, historical | Cross-sector 1m bd7 was only `0.31` Sharpe and `0.27%`; same-sector 12m remained thin. | Move to SP500 2m to determine whether the historical effect is universe-specific. |
| [09a](#09a---sp500-2m-historical) | SP500 2m, historical | Cross-sector 3m bd7 reached `0.89` and `1.43%`, showing a different historical regime from recent SP500 2m. | Complete the SP500 12m historical cell. |
| [09b](#09b---sp500-12m-historical) | SP500 12m, historical | Cross-sector 1m bd7 led at `0.59` and `0.59%`; 12m selection helped SP500 but did not produce a large universal edge. | Test sizing and start-date sensitivity separately from signal selection. |
| [10](#10---same-1m-bd7-at-pct025) | Same 1m bd7 at pct=.25 | Recent Sharpe ranged `0.50` to `1.04`; 15th-of-month starts were weaker but did not collapse, while the historical arm stayed negative. | Treat sizing as exposure control, not a solution to regime or start-date dependence. |
| [11](#11---pct-scaling-checks) | pct=.045 versus pct=.25 sizing checks | Trade counts and active trades were unchanged; returns scaled approximately linearly and Sharpe stayed nearly unchanged. | Since sizing did not add edge, combine legs that are strong in different periods instead of increasing one leg. |
| [12](#12---numbering-gap) | Numbering transition | There is no standalone section 12 artifact in the source chronology. | Continue to the explicitly documented two-leg combination rather than inventing an experiment. |
| [13](#13---combined-two-leg-book) | All 496 two-leg event-replay combinations | The mechanical screen favored SP500 12m cross 1m noscreen plus SP500 2m cross 3m bd7; it was strong in both separate and joined views. | Run factor diagnostics on the combined candidate before calling its return alpha. |
| [14](#14---fama-french-diagnostics) | FF3 + Mom + ST_Rev diagnostics | Alpha was insignificant; short-term reversal was the recurring exposure and recent market beta was material. | Tune rotation for robustness across all 496 pairs, not to manufacture a stronger alpha claim. |
| [15](#15---momentum-allocation-tuning-and-clean40) | Full-496 momentum tuning and clean40 | `lb84 / step0.40 / bounds0.10-0.90` ranked first across the clean40 candidate screen in both mechanisms, while avoiding the off-lattice trap. | Record clean40 as the locked quantitative configuration, with human selection criteria still explicit and separate. |

**Story in one line:** start-date instability -> earnings screening did not fix it ->
ranking instability and regime dependence became the central risks -> the four-cell
universe/selection grid exposed complementary recent and historical legs -> sizing did
not change the signal -> event replay and FF diagnostics tested whether combination
created robust, factor-adjusted edge -> clean40 was retained as the quantitative
rotation configuration.

**Human-selection boundary:** sections 13-15 contain a mechanical all-496 screen. They
do not encode or replace the original human-like criteria for choosing legs. The pair
named below is now the locked quantitative selection; human-like criteria remain an
explicit, separate consideration.

## 01 - Baseline Instability

**Configuration:** baseline same-sector, 2-month selection, 3-month slide, `pct=0.18`,
seven folds per run. Five starts were approximately two weeks apart.

| Start | Ann return | Sharpe | Trades | Folds | Mean AT |
|---|---:|---:|---:|---:|---:|
| 2023-12-01 | -1.63% | -0.23 | 55 | 7 | 0.7 |
| 2023-12-15 | +5.22% | 0.91 | 52 | 7 | 0.7 |
| 2024-01-01 | +10.68% | 1.48 | 44 | 7 | 0.6 |
| 2024-01-15 | -1.85% | -0.28 | 46 | 7 | 0.6 |
| 2024-02-01 | +2.27% | 0.52 | 32 | 7 | 0.4 |
| **Mean / std** | **+2.94% / 4.83%** | **0.48 / 0.66** | 45.8 / 8.4 | | 0.60 / 0.12 |

The baseline is highly sensitive to a two-week start shift. The largest losses cluster
around AVGO-NVDA, AAPL-NVDA, and other earnings-period trades, but the later tests show
that earnings timing is a symptom rather than the main source of instability.

Source: `diagnosis/01_baseline_instability (old)/findings.md`.

## 02 - Earnings Screen Baseline

The forward earnings screen was compared with no screen across the baseline starts.
It improved 14 comparisons and degraded 17. Mean Sharpe fell from `0.48` to `0.41`,
and the screen removed legitimate trades during active earnings periods.

**Decision:** earnings screening alone does not solve start-date instability. A
backward-looking block-duration sweep was run next.

## 02b - Earnings Block-Days Sweep

Thirty runs covered five starts and `{noscreen, bd0, bd3, bd5, bd7, bd9}`. `bd3` and
`bd5` were identical in this data because the relevant events clustered on weekdays.

| Metric | noscreen | bd0 | bd3 | bd5 | bd7 | bd9 |
|---|---:|---:|---:|---:|---:|---:|
| Mean Sharpe | 0.55 | 0.43 | 0.66 | 0.66 | 0.74 | 0.83 |
| Sharpe std | 0.81 | 0.57 | 0.84 | 0.84 | 0.73 | 0.85 |
| Sharpe range | [-0.28, 1.48] | [-0.29, 1.19] | [-0.46, 1.52] | [-0.46, 1.52] | [-0.06, 1.52] | [-0.13, 1.74] |
| Mean return | 3.27% | 1.66% | 2.33% | 2.33% | 2.70% | 3.07% |
| Mean trades | 44.8 | 33.0 | 26.4 | 26.4 | 25.6 | 25.2 |
| Mean AT | 0.58 | 0.44 | 0.32 | 0.32 | 0.30 | 0.30 |

The sweep shows two equivalence classes rather than a smooth optimization curve. `bd3` and
`bd5` are identical in every displayed metric and start date. `bd7` and `bd9` are also nearly
identical: their Sharpe and return values match on four of five starts, with the only material
difference at `2024-01-01` (`bd7` Sharpe `1.26` vs `bd9` `1.74`; return `7.12%` vs `9.21%`).
That single start drives most of bd9's higher mean (`0.83` vs `0.74`), so it is not enough
evidence that bd9 is generally superior; it may reflect one favorable event being blocked.

Trade retention is effectively the same for bd7 and bd9: mean trades are `25.6` vs `25.2`,
and the per-start counts differ only on `2023-12-01` (36 vs 34). Among those two near-equivalent
choices, bd7 has lower Sharpe dispersion (`0.73` vs `0.85`), a less aggressive block, and nearly
the same trade set. Therefore `bd7` is retained as the conservative minimum-sufficient secondary
filter, not because it maximizes mean Sharpe. Earnings remains secondary to pair-selection
stability.

Source: `diagnosis/02b_earnings_sweep_full/findings.md`.

## 03 - Pair Selection Stability

The baseline selected pairs were compared across start dates at each test fold.

| Metric | Mean | Min | Max |
|---|---:|---:|---:|
| Jaccard@5 | 0.036 | 0.011 | 0.058 |
| Jaccard@10 | 0.042 | 0.022 | 0.064 |
| Jaccard@20 | 0.067 | 0.029 | 0.099 |
| Jaccard@50 | 0.080 | 0.046 | 0.134 |
| Top-5 dropout | 0.940 | 0.900 | 0.980 |
| Rank volatility | 7.243 | 4.900 | 10.900 |
| Spearman rho | 0.122 | 0.000 | 0.448 |

Only about four percent of top-five pairs overlap between starts, and roughly 94% of
top-five pairs drop out. A small same-sector candidate pool amplifies the effect, but
the later four-way comparison shows that pool size alone is not the root cause.

Source: `diagnosis/03_pair_stability (old)/findings.md`.

## 03a-03c - Sector and Slide Stability Comparison

The four sector/slide combinations were compared using pairwise ranking statistics.

| Metric | Same 3m | Same 1m | Cross 3m | Cross 1m |
|---|---:|---:|---:|---:|
| Mean candidate pool | 23.657 | 23.970 | 114.543 | 119.900 |
| Jaccard@5 | 0.036 | 0.034 | 0.010 | 0.008 |
| Jaccard@10 | 0.042 | 0.052 | 0.015 | 0.013 |
| Jaccard@20 | 0.067 | 0.075 | 0.024 | 0.021 |
| Top-5 dropout | 0.940 | 0.945 | 0.983 | 0.986 |
| Rank volatility | 7.225 | 6.943 | 30.960 | 32.071 |
| Spearman rho | 0.122 | 0.109 | 0.179 | 0.121 |

Cross-sector has about five times the candidate pool, but its larger absolute rank
movement is proportionally similar. The corrected conclusion is that short-window
cointegration p-values are a noisy ranking metric. The small same-sector pool makes
the consequences more visible, but simply enlarging the pool does not fix the ranking
instability.

Possible remedies identified by the study were ranking ensembles, a less noisy
selection metric, longer selection windows, or averaging several independent top-pair
portfolios. The later combined-book work uses a cross-period ranking ensemble.

Source: `diagnosis/03_pair_stability (old)/comparison_findings.md`.

## 04 - Max-Pairs Sweep

The sweep covered same/cross sector and `max_pairs` in `{5, 10, 20, 50}` across five
recent starts.

| max_pairs | Same mean Sh | Same Sh std | Cross mean Sh | Cross Sh std | Same mean AT | Cross mean AT |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 0.55 | 0.81 | 0.71 | 0.67 | 0.58 | 0.56 |
| 10 | 0.72 | 0.99 | 0.99 | 0.93 | 1.05 | 1.10 |
| 20 | 0.82 | 0.80 | 0.81 | 0.79 | 1.92 | 2.13 |
| 50 | 0.62 | 0.34 | 0.99 | 0.35 | 2.50 | 4.91 |

`mp=20` is the retained standard because it materially thickens the book while
remaining comparable with the established 20-pair signal. It is a deployment-breadth
choice, not a claim that it maximizes raw Sharpe or minimizes every start-date
dispersion statistic.

Source: `diagnosis/04_max_pairs_sweep/findings.md`.

## 05 - Core 2m, mp=5, pct=0.18

This five-start, eight-configuration grid is the mp=5 comparison point.

### Sharpe by Start

| Config | 2023-11 | 2023-12 | 2024-01 | 2024-02 | 2024-03 | Mean |
|---|---:|---:|---:|---:|---:|---:|
| same 3m noscreen | 0.67 | -0.23 | 1.48 | 0.52 | -0.14 | 0.46 |
| same 3m bd7 | -0.05 | -0.06 | 1.26 | 0.01 | 0.29 | 0.29 |
| same 1m noscreen | 1.24 | 1.37 | 1.41 | 1.51 | 1.47 | **1.40** |
| same 1m bd7 | 1.06 | 1.28 | 1.40 | 1.47 | 1.40 | 1.32 |
| cross 3m noscreen | 1.18 | -0.32 | 0.98 | 1.26 | 0.12 | 0.65 |
| cross 3m bd7 | 0.30 | -0.20 | -0.04 | 0.32 | 0.00 | 0.08 |
| cross 1m noscreen | 0.82 | 0.89 | 1.36 | 1.31 | 1.35 | 1.15 |
| cross 1m bd7 | -0.07 | 0.02 | -0.04 | -0.03 | -0.11 | -0.05 |

| Config | Sharpe | Ann return | Trades | Mean AT |
|---|---:|---:|---:|---:|
| same 1m noscreen | **1.40** | **4.79%** | 123.0 | 1.65 |
| same 1m bd7 | 1.32 | 3.21% | 74.6 | 0.94 |
| cross 1m noscreen | 1.15 | 3.90% | 105.4 | 1.58 |
| cross 3m noscreen | 0.65 | 2.99% | 35.0 | 0.50 |
| same 3m noscreen | 0.46 | 2.62% | 43.6 | 0.55 |
| same 3m bd7 | 0.29 | 1.53% | 26.8 | 0.33 |
| cross 3m bd7 | 0.08 | 0.01% | 18.0 | 0.26 |
| cross 1m bd7 | -0.05 | -0.12% | 53.8 | 0.83 |

The mp=5 raw winner is stronger than the mp20 winner on this particular recent
sample, but it deploys fewer positions. The investigation retains mp20 to reduce
single-pair concentration and preserve book breadth.

Source: `fixed_diagnosis/05/findings.md`.

## 06 - Core 2m, mp=20, pct=0.045

The corrected recent grid uses five starts from 2023-11 through 2024-03 and trades
from the corresponding 2024 start through 2025-12.

| Config | 2023-11 | 2023-12 | 2024-01 | 2024-02 | 2024-03 | Mean Sh | Ann return | Trades | Mean AT |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| same 3m noscreen | 0.26 | 0.25 | 1.81 | -0.19 | 0.35 | 0.50 | 1.31% | 157.4 | 1.95 |
| same 3m bd7 | 0.40 | -0.20 | 1.61 | 0.45 | 0.11 | 0.47 | 0.83% | 84.8 | 1.03 |
| same 1m noscreen | 1.23 | 1.36 | 1.23 | 1.33 | 1.21 | 1.27 | 2.13% | 435.0 | 5.71 |
| same 1m bd7 | 1.06 | 1.35 | 1.37 | 1.44 | 1.29 | 1.30 | 1.46% | 235.8 | 3.06 |
| cross 3m noscreen | 1.27 | -0.20 | 1.48 | 1.39 | 0.06 | 0.80 | 2.84% | 154.8 | 2.02 |
| cross 3m bd7 | -0.39 | -0.35 | 0.81 | -0.19 | -0.09 | -0.04 | 0.03% | 78.2 | 0.97 |
| cross 1m noscreen | 1.33 | 1.44 | 1.61 | 1.57 | 1.69 | **1.53** | **3.57%** | 460.2 | 6.34 |
| cross 1m bd7 | 0.19 | 0.30 | 0.36 | 0.30 | 0.34 | 0.30 | 0.46% | 235.2 | 3.06 |

The cross-sector 1m noscreen configuration is positive at every start and is the
corrected core 2m recent winner. Same-sector 1m is also strong, but it fills only
about 70% of the 20-pair book; cross-sector fills all 20.

Source: `fixed_diagnosis/06/findings.md`.

## 6b - Core 12m, Recent

The corrected 12m core recent cell is represented by `fixed_diagnosis/10a`, which
uses five aligned 2023-01 through 2023-05 selection starts.

| Config | 2023-01 | 2023-02 | 2023-03 | 2023-04 | 2023-05 | Mean Sh | Ann return |
|---|---:|---:|---:|---:|---:|---:|---:|
| same 3m noscreen | 0.41 | 0.17 | -0.02 | 0.54 | 0.18 | 0.25 | 0.21% |
| same 3m bd7 | -0.65 | 0.80 | 0.11 | -0.66 | 0.96 | 0.11 | 0.01% |
| same 1m noscreen | 0.28 | 0.28 | 0.25 | 0.26 | 0.28 | 0.27 | 0.20% |
| same 1m bd7 | 0.18 | 0.18 | 0.35 | 0.36 | 0.32 | 0.28 | 0.11% |
| cross 3m noscreen | 0.60 | -0.13 | 1.00 | 0.79 | -0.25 | 0.40 | 0.99% |
| cross 3m bd7 | 0.08 | 0.24 | 1.02 | -0.08 | 0.24 | 0.30 | 0.39% |
| cross 1m noscreen | 0.79 | 0.77 | 0.76 | 0.83 | 0.84 | **0.80** | **1.51%** |
| cross 1m bd7 | 0.55 | 0.49 | 0.53 | 0.47 | 0.43 | 0.49 | 0.63% |

Core 12m is weaker than core 2m on every matching recent cell. Its best result is
cross-sector, not the thin same-sector family.

Source: `fixed_diagnosis/10a/findings.md`.

## 07 - SP500 2m, mp=20, pct=0.045

| Config | 2023-11 | 2023-12 | 2024-01 | 2024-02 | 2024-03 | Mean Sh | Ann return | Trades | Mean AT |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| same 3m noscreen | 1.33 | 0.27 | -1.01 | 0.66 | 0.47 | 0.34 | 0.84% | 169.0 | 2.17 |
| same 3m bd7 | 1.28 | 0.31 | -1.55 | 0.94 | 0.45 | 0.29 | 0.37% | 96.0 | 1.18 |
| same 1m noscreen | 0.08 | 0.02 | -0.30 | -0.01 | -0.04 | -0.05 | -0.08% | 480.8 | 6.45 |
| same 1m bd7 | -0.22 | -0.30 | -0.57 | -0.46 | -0.51 | -0.41 | -0.40% | 273.6 | 3.53 |
| cross 3m noscreen | -0.05 | 0.49 | 0.83 | -0.00 | 0.58 | 0.37 | 0.86% | 167.0 | 2.10 |
| cross 3m bd7 | -0.36 | -0.76 | 0.22 | -0.38 | -0.78 | -0.41 | -0.66% | 86.2 | 1.03 |
| cross 1m noscreen | 0.36 | 0.39 | 0.56 | 0.49 | 0.30 | **0.42** | **0.85%** | 479.6 | 6.52 |
| cross 1m bd7 | -0.31 | -0.41 | -0.41 | -0.46 | -0.61 | -0.44 | -0.64% | 244.4 | 3.26 |

SP500 2m is weaker than core 2m on every recent family that matters operationally.
The cross 1m noscreen cell is positive but modest; the strong-looking 3m same-sector
start is not stable.

Source: `fixed_diagnosis/07/findings.md`.

## 7b - SP500 12m, Recent

The corrected 12m SP500 recent cell is represented by `fixed_diagnosis/10b`.

| Config | 2023-01 | 2023-02 | 2023-03 | 2023-04 | 2023-05 | Mean Sh | Ann return |
|---|---:|---:|---:|---:|---:|---:|---:|
| same 3m noscreen | 1.26 | -0.19 | 1.67 | 1.16 | 0.09 | 0.80 | 2.18% |
| same 3m bd7 | 0.89 | 0.07 | 0.32 | 0.78 | 0.14 | 0.44 | 0.70% |
| same 1m noscreen | 1.33 | 1.37 | 1.32 | 1.33 | 1.23 | 1.32 | 2.75% |
| same 1m bd7 | 0.70 | 0.68 | 0.66 | 0.79 | 0.51 | 0.67 | 0.91% |
| cross 3m noscreen | 0.97 | 1.13 | 0.69 | 1.22 | 1.52 | 1.11 | 2.72% |
| cross 3m bd7 | 0.17 | 1.73 | -0.19 | 0.53 | 1.87 | 0.82 | 1.24% |
| cross 1m noscreen | 1.42 | 1.53 | 1.83 | 2.28 | 2.38 | **1.89** | **3.43%** |
| cross 1m bd7 | 0.85 | 0.90 | 1.06 | 1.81 | 1.92 | 1.31 | 1.60% |

SP500 12m cross 1m noscreen is the strongest single-leg recent cell. Same 1m
noscreen is almost as strong and has lower start-date dispersion.

Source: `fixed_diagnosis/10b/findings.md`.

## 08a - Core 2m, Historical

This is the clean, aligned 2m-selection historical baseline: selection start
`2014-11-01`, first trade `2015-01-02`, last trade `2019-12-31`.

| Config | Sharpe | Ann return | Trades | Mean AT |
|---|---:|---:|---:|---:|
| same 1m noscreen | -0.08 | -0.11% | 1374.0 | 6.04 |
| same 1m bd7 | -0.11 | -0.09% | 760.0 | 3.16 |
| cross 1m bd7 | -0.15 | -0.27% | 772.0 | 3.09 |
| cross 3m bd7 | -0.21 | -1.00% | 251.0 | 0.95 |
| cross 3m noscreen | -0.27 | -1.33% | 461.0 | 1.88 |
| same 3m noscreen | -0.53 | -0.88% | 439.0 | 1.78 |
| cross 1m noscreen | -0.60 | -1.19% | 1414.0 | 6.02 |
| same 3m bd7 | -0.64 | -0.67% | 240.0 | 0.87 |

The recent slide-1m result does not transfer to core historical data. Every corrected
configuration is negative on this single aligned historical start.

The previous contaminated 12m-selection archive is retained separately. It is not
used for this result.

Source: `fixed_diagnosis/08a/findings.md`.

## 08b - Core 12m, Historical

This is the sector-masked 12m redo: selection start `2014-01-01`, first trade
`2015-01-02`, last trade `2019-12-31`.

| Config | Sharpe | Ann return | Trades | Mean AT |
|---|---:|---:|---:|---:|
| cross 1m bd7 | **0.31** | **0.27%** | 731.0 | 3.33 |
| same 1m bd7 | 0.13 | 0.05% | 226.0 | 0.98 |
| cross 3m bd7 | -0.10 | -0.11% | 251.0 | 1.14 |
| same 3m bd7 | -0.34 | -0.20% | 95.0 | 0.43 |
| cross 1m noscreen | -0.45 | -0.60% | 1449.0 | 6.75 |
| cross 3m noscreen | -0.70 | -1.23% | 511.0 | 2.47 |
| same 1m noscreen | -0.79 | -0.44% | 430.0 | 1.97 |
| same 3m noscreen | -0.91 | -0.85% | 175.0 | 0.81 |

The core 12m result is marginal. Cross-sector fills the 20-pair book, while the
same-sector 12m configurations have the thin-book problem.

Source: `fixed_diagnosis/08b/findings.md`.

## 09a - SP500 2m, Historical

This is the clean aligned SP500 2m run: selection start `2014-11-01`, first trade
`2015-01-02`, last trade `2019-12-31`.

| Config | Sharpe | Ann return | Trades | Mean AT |
|---|---:|---:|---:|---:|
| cross 3m bd7 | **0.89** | **1.43%** | 266.0 | 1.19 |
| cross 3m noscreen | 0.62 | 1.79% | 525.0 | 2.43 |
| cross 1m bd7 | 0.39 | 0.35% | 768.0 | 3.46 |
| same 1m noscreen | 0.29 | 0.35% | 1505.0 | 6.64 |
| same 3m bd7 | 0.20 | 0.24% | 260.0 | 1.05 |
| same 3m noscreen | 0.17 | 0.32% | 508.0 | 2.21 |
| cross 1m noscreen | 0.11 | 0.16% | 1483.0 | 6.86 |
| same 1m bd7 | -0.24 | -0.20% | 810.0 | 3.56 |

SP500 2m can be positive historically, but it is a different regime from the weak
recent SP500 2m result. The screen changes the leading 3m result's risk/return and
trade count, so the positive historical cell is not a screen-invariant edge.

Source: `fixed_diagnosis/09a/findings.md`.

## 09b - SP500 12m, Historical

This is the sector-masked SP500 12m run: selection start `2014-01-01`, first trade
`2015-01-02`, last trade `2019-12-31`.

| Config | Sharpe | Ann return | Trades | Mean AT |
|---|---:|---:|---:|---:|
| cross 1m bd7 | **0.59** | **0.59%** | 768.0 | 3.40 |
| same 1m bd7 | 0.49 | 0.49% | 914.0 | 3.80 |
| cross 1m noscreen | 0.47 | 0.66% | 1400.0 | 6.09 |
| same 1m noscreen | 0.40 | 0.54% | 1586.0 | 7.10 |
| same 3m noscreen | 0.37 | 0.71% | 555.0 | 2.59 |
| cross 3m bd7 | 0.33 | 0.53% | 256.0 | 1.08 |
| same 3m bd7 | 0.18 | 0.22% | 310.0 | 1.28 |
| cross 3m noscreen | -0.21 | -0.51% | 487.0 | 2.12 |

The corrected 12m selection rescues SP500 relative to its 2m historical cell, but
the absolute Sharpe remains modest. The earnings screen changes trade count and
entry timing; it is not the primary selection edge.

Source: `fixed_diagnosis/09b/findings.md`.

## 10 - Same 1m bd7 at pct=0.25

The recent sizing sweep uses eight starts, alternating first-of-month and 15th-of-month
starts. It tests whether higher per-pair sizing changes the start-date result.

| Start | Sharpe | Ann return | Trades |
|---|---:|---:|---:|
| 2023-11-01 | 0.71 | 4.48% | 254 |
| 2023-11-15 | 0.50 | 3.09% | 258 |
| 2023-12-01 | 0.98 | 6.83% | 247 |
| 2023-12-15 | 0.60 | 3.77% | 251 |
| 2024-01-01 | 0.99 | 7.04% | 239 |
| 2024-01-15 | 0.61 | 3.94% | 238 |
| 2024-02-01 | 1.04 | 7.56% | 227 |
| 2024-02-15 | 0.56 | 3.67% | 228 |
| **Mean** | **0.75** | **4.70%** | 239.8 |

The first-of-month starts are stronger than the 15th starts, but the 15th starts do
not collapse. The historical arm remains negative. The corrected report is
`fixed_diagnosis/10/findings.md`; its exact trimmed aggregate is Sharpe `0.75`,
return `4.70%`, and mean AT `2.99`.

## 11 - pct Scaling Checks

The corrected comparison uses the identical aligned 12m historical runs at pct=.045
and pct=.25. Trade counts and active-trade counts are unchanged because pct changes
notional sizing, not signals.

| Universe / config | pct | Sharpe | Ann return | Trades | Mean AT |
|---|---:|---:|---:|---:|---:|
| Core 12m same 1m bd7 | 0.045 | 0.1330 | 0.0482% | 226 | 0.98 |
| Core 12m same 1m bd7 | 0.250 | 0.1335 | 0.2525% | 226 | 0.98 |
| SP500 12m same 1m bd7 | 0.045 | 0.4922 | 0.4877% | 914 | 3.80 |
| SP500 12m same 1m bd7 | 0.250 | 0.5030 | 2.6726% | 914 | 3.80 |

The pct=.25 return increases are approximately linear, while Sharpe is effectively
unchanged. The old three-start 2015-2020 sizing checks in `diagnosis/11a_*` and
`diagnosis/11b_*` use a different 2016-2020 trading window and are not substituted
for these aligned values.

## 12 - Numbering Gap

There is no standalone section 12 experiment in the source chronology. The research
record proceeds from 11a/11b sizing checks to the two-leg combined-book analysis in
section 13. This replacement document preserves that numbering rather than inventing
a result.

## 13 - Combined Two-Leg Book

### Inputs and Replay

The combined analysis sweeps all `32 choose 2 = 496` pairs of the four strategy groups
and eight configurations. It uses pct=.25 leg event logs and daily marks from
`fixed_diagnosis/_sweep_pct25`.

- Recent score: mean Sharpe over five aligned start-pairs.
- Historical score: one aligned 2015-2019 window.
- Separate score: `min(recent Sharpe, historical Sharpe)`.
- Joined score: one Sharpe after concatenating historical and recent daily returns.
- Mechanism A: monthly re-base of fold capital to the current leg weight.
- Mechanism B: fold-start basis `C / n_active_L` for each leg, with weight applied only to
  new entry flow; exposure drifts.
- Weight timing is causal for the replay: trailing Sharpe is measured strictly before
  each rebalance month.
- B sizing correction: the previous implementation divided its locked basis by active folds
  across both legs and then applied the leg weight, creating an unintended roughly 50%
  underdeployment. The corrected denominator is the active-fold count for the specific leg.
  All B-dependent results below were regenerated after this correction.

### Current Top Pairs

The corrected trade-event consolidated sweep has the following top five pairs under
the separate score.

| Rank | Pair | A recent | A hist | A score | B recent | B hist | B score |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.83 | 1.14 | 0.83 | 0.82 | 1.09 | 0.82 |
| 2 | `sp500-2m/cross_sector_slide3m_bd7` + `sp500-12m/same_sector_slide1m_noscreen` | 0.87 | 0.81 | 0.81 | 0.83 | 0.87 | 0.83 |
| 3 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.73 | 0.70 | 0.70 | 0.74 | 0.71 | 0.71 |
| 4 | `sp500-2m/cross_sector_slide3m_noscreen` + `sp500-12m/cross_sector_slide1m_noscreen` | 0.91 | 0.67 | 0.67 | 0.90 | 0.65 | 0.65 |
| 5 | `sp500-2m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.68 | 0.60 | 0.60 | 0.68 | 0.62 | 0.62 |

The selected pair is the top separate-score result in mechanism A and rank 2 in mechanism B.
Its corresponding default joined Sharpe is `1.04` in mechanism A and `1.01` in mechanism B. The full top-20
tables, including rank-average and joined rankings, are in
`fixed_diagnosis/separate/_COMBINED_BOOK_CONSOLIDATED.md` and
`fixed_diagnosis/compare/_RANK_COMPARISON.md`.

### Final-Pair Single-Start Validation

For the locked pair, with default rotation `lookback=63`, `step=.10`, and clamp
`[.25,.75]`, the direct shared-account replay is:

| Window | Mechanism | Sharpe | Ann return | Ann vol | MDD | Days |
|---|---|---:|---:|---:|---:|---:|
| Recent, single aligned start | A | 0.523 | 4.22% | 8.62% | -6.9% | 492 |
| Recent, single aligned start | B | 0.612 | 5.03% | 8.62% | -6.2% | 492 |
| Historical | A | 1.139 | 8.08% | 7.04% | -5.1% | 1258 |
| Historical | B | 1.094 | 7.73% | 7.03% | -5.1% | 1258 |

The ledger reconciles exactly: final equity minus initial equity equals summed daily
PnL in both mechanisms, and rejected entries are zero. The legacy CSV arithmetic book
was not regenerated and is marked unavailable; no comparison to that missing artifact
is claimed.

### Ranking Comparison

Across all 496 pairs, the fresh rank correlations are:

| Mechanism | Separate vs rank-average | Separate vs joined | Rank-average vs joined |
|---|---:|---:|---:|
| A | 0.743 | 0.874 | 0.877 |
| B | 0.720 | 0.863 | 0.868 |

Six pairs are in the top 20 of all three methods in each mechanism, and six are in
the cross-mechanism intersection. The locked pair is the common top pair in the
corrected clean40 evaluation.

The rank-average-only alternative is kept separate from that consensus rule. Its
top-20 intersection across mechanisms contains 17 pairs and is documented in
`fixed_diagnosis/rankavg/_RANKAVG_SELECTION.md` and
`fixed_diagnosis/rankavg/_MOMENTUM_FF_RANKAVG.md`.

## 14 - Fama-French Diagnostics

The model is daily FF3 plus momentum and short-term reversal, with HAC standard errors
and alpha annualized by multiplying the daily intercept by 252.

### Default Final-Pair Replay

| Window | Series | Alpha | Alpha t | Alpha p | Mkt-RF beta | ST_Rev beta | ST_Rev p | R2 | N |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Recent | Combined A | -5.05% | -1.057 | 0.2903 | 0.193 | 0.116 | 0.0474 | 0.188 | 487 |
| Historical | Combined A | +5.71% | 1.790 | 0.0735 | 0.040 | 0.084 | 0.0258 | 0.028 | 1255 |
| Recent | Leg A | +1.60% | 0.209 | 0.8342 | 0.202 | 0.104 | 0.1346 | 0.096 | 487 |
| Historical | Leg A | +0.32% | 0.089 | 0.9289 | 0.063 | 0.116 | 0.0032 | 0.038 | 1250 |

The historical combined alpha is not significant at five percent, and the recent
combined alpha is negative and insignificant. Market beta is significant recently;
the historical combined market beta is not. Short-term reversal is the recurring
factor exposure, not unexplained alpha. Full default output is in
`fixed_diagnosis/_FF_COMBINED_PCT25.md` and the all-survivor CSV is in
`fixed_diagnosis/compare/ff_regressions.csv`.

## 15 - Momentum Allocation Tuning and Clean40

### Selection Rule

Momentum parameters were evaluated across all 496 pairs, not only one preselected pair.
The selection methods were separate min-score, rank-average, and joined Sharpe. The
locked quantitative pair is:

- A, recent-strong: `sp500-12m/cross_sector_slide1m_noscreen`
- B, historical-strong: `sp500-2m/cross_sector_slide3m_bd7`

### Weight-Lattice Constraint

The weight update is `w <- w +/- step`, followed by clamping. Starting at `w=.50`,
the bounds should be on the same lattice as the step. For example, bounds `.15-.85`
with step `.30` can move the process onto a closed odd lattice that cannot return to
`.50`. This can create a permanent hidden leg bias. Clean bounds are
`0.50 +/- integer * step`.

### Clean40 Configuration

The locked quantitative rotation configuration is:

```text
lookback = 84 trading days
step = 0.40
bounds = [0.10, 0.90]
initial weight A = 0.50
pct per pair = 0.25
capital = $1,000,000
```

The clean40 evaluation replays every one of the 496 pairs in both mechanisms. The
locked pair is ranked first under separate score, rank-average, and joined Sharpe in
both mechanisms. This is not a substitute for applying human leg selection criteria.

### Clean40 Robustness

| Momentum cell | A recent | A hist | A joined | B recent | B hist | B joined |
|---|---:|---:|---:|---:|---:|---:|
| step .50, bounds 0.00-1.00 | 1.148 | 1.139 | 1.139 | 1.217 | 1.115 | 1.140 |
| **step .40, bounds 0.10-0.90** | **1.094** | **1.122** | **1.111** | **1.141** | **1.096** | **1.106** |
| step .30, bounds 0.20-0.80 | 1.019 | 1.091 | 1.066 | 1.041 | 1.062 | 1.052 |
| step .25, bounds 0.25-0.75 | 0.974 | 1.068 | 1.036 | 0.982 | 1.037 | 1.016 |

Clean40 is not selected because it maximizes every raw cell. It is selected because it
keeps the full-496 rank result while retaining a 10% diversification floor and avoids
the off-lattice trap.

### Clean40 Versus Default Rotation

| Window | Mechanism | Default Sharpe | Clean40 Sharpe | Change |
|---|---|---:|---:|---:|
| Historical | A | 1.139 | 1.122 | -0.017 |
| Historical | B | 1.094 | 1.096 | +0.003 |
| Recent mean of 5 | A | 0.826 | 1.094 | +0.268 |
| Recent mean of 5 | B | 0.817 | 1.141 | +0.324 |

The recent improvement is present at all five starts for A and B. Historical performance
is approximately unchanged for both mechanisms.

### Clean40 Fama-French Multi-Start

| Window | Start | Mech | Alpha | Alpha p | ST_Rev beta | ST_Rev p | Sharpe | R2 |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| Historical | 0 | A | +6.77% | 0.066 | 0.08 | 0.077 | 1.12 | 0.020 |
| Recent | 0 | A | -2.71% | 0.600 | 0.11 | 0.051 | 0.76 | 0.166 |
| Recent | 1 | A | -0.53% | 0.915 | 0.13 | 0.015 | 1.01 | 0.182 |
| Recent | 2 | A | +1.52% | 0.763 | 0.13 | 0.015 | 1.33 | 0.212 |
| Recent | 3 | A | +0.10% | 0.986 | 0.14 | 0.012 | 1.12 | 0.216 |
| Recent | 4 | A | +1.02% | 0.857 | 0.14 | 0.009 | 1.25 | 0.208 |
| Historical | 0 | B | +6.53% | 0.077 | 0.08 | 0.073 | 1.10 | 0.021 |
| Recent | 0 | B | -2.22% | 0.665 | 0.12 | 0.045 | 0.82 | 0.172 |
| Recent | 1 | B | -0.40% | 0.936 | 0.13 | 0.014 | 1.04 | 0.190 |
| Recent | 2 | B | +1.31% | 0.793 | 0.13 | 0.014 | 1.32 | 0.220 |
| Recent | 3 | B | +0.46% | 0.933 | 0.15 | 0.010 | 1.18 | 0.224 |
| Recent | 4 | B | +1.72% | 0.758 | 0.14 | 0.008 | 1.34 | 0.217 |

No alpha p-value is below .05. ST_Rev is significant in most recent cells, but not in
historical A or B at the five-percent threshold. Market beta is generally significant in
recent rows. The clean40 tuning therefore improves ranking and recent risk-adjusted
behavior without establishing factor-adjusted alpha.

Sources: `fixed_diagnosis/clean40/_CLEAN40_PAIR_RANKS.md`,
`fixed_diagnosis/compare/_CLEAN_ROBUSTNESS.csv`,
`fixed_diagnosis/clean40/_FF_COMPARE_clean40_vs_default.md`, and
`fixed_diagnosis/clean40/_FF_PAIR_MULTISTART_clean40.md`.

## Cache, Data, and Pool Corrections

### Earnings Cache

The SP500 sections were previously routed to a truncated cache containing only part
of the 2023-2025 earnings history. The complete cache has the same 503 tickers and
full 2013-2026 coverage. After correction, SP500 earnings-screened runs use the
complete cache, and historical SP500 bd7 runs no longer collapse into their noscreen
counterparts.

### Runtime Return-Divergence Filter

The SP500 2m pool was already seeded with the `divergence <= 0.10` filter, but the old
runtime path applied the filter again using fresh yfinance data. Partial rate-limited
fetches silently removed valid pairs and changed rankings. Pool-backed runs now use
the deterministic seeded pool, and incomplete price fetches fail loudly rather than
reshuffling selection.

### Correct Pool Routing

| Run context | Pool | Selection-time behavior |
|---|---|---|
| Core 2m | `core_2m.pkl` | Core ticker mask and log-space p-value filter are already represented |
| SP500 2m | `sp500_2m.pkl` | Seeded divergence filter; no duplicate runtime re-filter |
| Any 12m run | `sp500_12m.pkl` | Raw 12m pool, with universe and sector filters applied at load time |

The 12m core historical result is therefore a real sector-masked core result, not the
old cache-shadow result. Detailed evidence and snapshot hashes are in
`CACHE_BUG_FIX_REPORT.md` and `research/archive/pct25_comparison_audit/`.

## Reproduction Commands

The authoritative combined and final-analysis sequence is:

```text
python run_fixed_reports.py
python research/run_combined_backtest.py --window recent --mechanism both --lookback 63 --step 0.10 --clamp 0.25 0.75
python research/run_combined_backtest.py --window historical --mechanism both --lookback 63 --step 0.10 --clamp 0.25 0.75
python research/combined_backtest_synthetic_test.py
python research/pair_sweep_consolidated.py --mechanism both --pct 0.25 --top 20 --report
python research/write_joint_eval.py
python research/write_joint_vs_separate.py
python research/compare_rankings.py
python research/write_top7_period.py
python research/write_pairs_with_hist1.py
python research/write_pairs_with_recent1.py
python research/evaluate_clean40.py
python research/step_robustness.py step --force
python research/step_robustness.py lookback --force
python research/step_robustness.py joint --force
python research/step_robustness.py bounds --force
python research/step_robustness.py frontier --force
python research/step_robustness.py final --force
python research/step_robustness.py clean --force
python research/momentum_ff_pairs.py
python research/momentum_ff_rankavg.py
python research/run_ff_leg.py sp500-12m cross_sector_slide1m_noscreen
python research/run_ff_leg.py sp500-2m cross_sector_slide3m_bd7
python research/run_ff_pair_multistart.py
python research/run_ff_combined.py
python research/plot_ff_best84.py clean40 --reports-only
python research/plot_ff_best84.py clean40 --plots-only
python research/write_consolidated_comparison.py
python run_fixed_comparison.py
python research/write_pipeline_manifest.py
```

The generated manifest is `RESEARCH_PIPELINE_FIXED_MANIFEST.json`. It records the
fixed leg root, locked configuration and pair, commands, and SHA-256
hashes for the reports and generator scripts used here.

## Artifact Map

- Single-leg corrected findings: `fixed_diagnosis/05/` through `fixed_diagnosis/10b/`.
- Authoritative pct=.25 leg corpus: `fixed_diagnosis/_sweep_pct25/`.
- Consolidated event replay: `fixed_diagnosis/_combined/consolidated/`.
- All-496 consolidated sweep: `fixed_diagnosis/_combined/consolidated_sweep/`.
- Separate and joined reports: `fixed_diagnosis/separate/` and `fixed_diagnosis/joint/`.
- Ranking correlations and FF diagnostics: `fixed_diagnosis/compare/`.
- Rank-average-only diagnostics: `fixed_diagnosis/rankavg/`.
- Clean40 pair ranks and FF outputs: `fixed_diagnosis/clean40/`.
- Margin tests and chart outputs are archived under
  `archive/fixed_diagnosis_refresh_20260907_211241 (old)/` and are not part of the live
  report set.
- Cache diagnosis and sizing audit: `CACHE_BUG_FIX_REPORT.md` and
  `research/archive/pct25_comparison_audit/`.

## Honest Bottom Line

The research found real start-date and regime dependence. Earnings screening can
remove some event risk, but the main ranking problem is noisy short-window
cointegration p-values, amplified by thin same-sector books. The corrected historical
results are materially weaker than the contaminated cache-shadow results.

The strongest recent single leg is SP500 12m cross-sector 1m noscreen. The strongest
historical companion for the corrected all-496 event replay is SP500 2m cross-sector
3m bd7. Combining those legs and selecting clean40 rotation improves recent
risk-adjusted results, but the Fama-French alpha remains statistically insignificant.
The repeatable exposure is short-term reversal, so the final book is a low-volatility
candidate diversifier rather than a proven standalone alpha strategy.
