# Research Pipeline — Robust Mean Reversion (chronological)

**The arc in one line:** Diagnosed severe start-date instability → ruled out earnings as the cause
→ found the true root cause (tiny pair pool / pair-selection volatility) → enlarged the pool &
tuned the grid → discovered a cache bug that contaminated the 2015–2020 results → cleaned &
revalidated everything → sized the best config up and swept it across periods → **combined the two
strongest legs into a momentum-rotated book** with Fama-French diagnostics (edge =
short-term-reversal factor, not alpha).

## TL;DR - one line per section

| # | Test (context) | Key result | Decision |
|---|---|---|---|
| [**01**](#01---baseline_instability) | Baseline: 5 start dates × 7 folds | Sharpe swings −0.28→+1.48 across 2-wk start shifts; losses are earnings-gap driven | Try earnings screen → **02** |
| [**02**](#02---earnings_screen_baseline) | Forward earnings screen ON/OFF, 5 dates | Inconsistent (14 better / 17 worse); blocks legit trades | Earnings isn't the driver → **02b** |
| [**02b**](#02b---earnings_sweep_full) | Sweep earnings block-days {0,3,5,7,9} × 5 dates | Mean Sharpe flat 0.24–0.49; bd7 best trade-off | Screen = variance-shrink, not fix → **03** |
| [**03**](#03---pair_stability--root-cause) | Quantify pair-selection stability (Jaccard, dropout) | Jaccard@5 ≈ 0.04, dropout 94%; same-sector pool only ~20 pairs | Enlarge pool / try combos → **03a-c** |
| [**03a-c**](#03a03b03c---cross_sector_slide1m-cross_sector_slide3m-same_sector_slide1m-checking-for-pair-selection-stability) | Per-fold rankings for 3 sector×slide combos | Fold-level data to compare pool size & rank vol | Feed into grid sweeps → **06/05** |
| [**04**](#04---max_pairs_sweep) | max_pairs {5,10,20,50}, same vs cross | mp=20 best (0.80, std low) | Use **mp=20** → **06,05** |
| [**05**](#05---grid_search_mp5-mp5-pct018) | 8-config grid at mp=5, core recent | Best same 1m **noscreen = 1.42** (std 0.07); bd7 1.32 | mp=20 retained on book thickness → **06** |
| [**06**](#06---grid_search-mp20-pct0045--recent-period-winner) | 8-config grid at mp=20 CORE, recent | **Winner same 1m bd7 = 1.30**, positive all 5 dates; ns 1.27 | Push winner to 2015–2019 → **08** |
| [**07**](#07---grid_search_sp500-sp500-mp20-pct0045) | 8-config grid on mp=20 SP500, recent | Nothing beats core; best same 3m bd7 = **0.74** but std 0.82 | Compare core vs SP500 on 2015–2019 → **08/09** |
| [**08a**](#08a_core_2015_2020--comparisonmd--true-20152019-baseline) | Core 2015–2019 2m-sel | **Cross-sector wins: cross 3m bd7 +0.51, cross 1m bd7 +0.50**; same 3m collapsed to −0.5 | 12m selection better → **08b** |
| [**08b**](#08b---core_12m_sel_2015_2020--12-month-selection-on-core-sector-masked-redo) | Core 2015-2019 12m-sel | **cross 1m bd7 = +0.34** single-start; thin book | Core 12m is marginal + thin → SP500 12m matters |
| [**09a**](#09a---sp500_2015_2020) | SP500 2015–2019 2m-sel | **cross 3m = +0.62**; SP500 2m is viable | SP500 2m viable → **10** |
| [**09b**](#09b---sp500_12m_sel_2015_2020--12-month-selection-on-sp500-sector-masked) | SP500 2015-2019 12m-sel | **same 1m ns = +0.43** single-start; 12m still rescues SP500 | SP500 needs 12m selection; 1m is the winner |
| [**10**](#10---sweep_same_sector_slide1m_bd7_pct025--same_sector_slide1m_bd7_pct025--start-date-fragility) | Winner same 1m bd7 at pct=0.25, recent + 2015–2019 | 1st-of-month +0.66…+1.18, **15th +0.50…+0.61 (no collapse)**; 2015–2019 negative | Start-date sensitivity reduced but persists |
| [**10a**](#10a---core_12m_sel_2023_2025--12-month-selection-on-core-recent-period) | Core 12m-selection, recent | **cross 1m ns = +0.82** (std 0.03) best; same 1m bd7 falls to 0.37 | Core-12m thin; cross-sector 1m is the reliable cell |
| [**10b**](#10b---sp500_12m_sel_2023_2025--12-month-selection-on-sp500-recent-period) | SP500 12m-selection, recent | **cross 1m ns = +1.80** best; same 1m ns +1.63 (std 0.04) | SP500 12m = strongest cell in the study |
| [**11a**](#11a---core-12m-same_sector_slide1m_bd7-at-pct025-2015-2020) | Core 12m, winner at pct=0.25, 2015–2020 | Sharpe ~unchanged at 0.52 single-start; returns ×5.3 | pct scaling = linear returns, no capacity relief |
| [**11b**](#11b---sp500-12m-same_sector_slide1m_bd7-at-pct025-2015-2020) | SP500 12m, winner at pct=0.25, 2015–2020 | Sharpe ~unchanged at 0.53 single-start; returns ×5.1 | pct scaling = linear returns, no capacity relief |
| [**13**](#13---combined-two-leg-book) | Sweep **all 496 pairs** of the 32 legs; score = min(recent, hist) Sharpe | Winner core-2m `cross 3m bd7` + sp500-12m `cross 1m noscreen`: recent **1.37**, hist **1.00** | Combined pct0.25 book: recent **1.44**, hist **1.03**; beats S&P on Sharpe, not return |
| [**14**](#14---fama-french-on-the-combined-pct025-book) | FF3 + Mom + ST_Rev daily regression on the combined pct0.25 book & legs | **Alpha insignificant** (t ≤ 1.42); **ST_Rev significant** (t ≈ 2.3–3.4); low R² | Edge = short-term-reversal factor exposure, not unexplained alpha → **14** |

*(Full details below; "What works where" cross-period table at the bottom.)*

---

## 01 - `baseline_instability`

**Context:** Discovered that returns and sharpe vary differently on different neighbouring start dates.

**Test:** 5 start dates (~2 wks apart) × 7 folds on the baseline config (same-sector, slide 3m,
pct 0.18).

**Result:** Sharpe swings −0.28 → +1.48 across just 2-week start shifts (std 0.66). Worst trades
(AVGO-NVDA, AAPL-NVDA, CRM-NVDA…) are **earnings-gap driven**, concentrated in Fold 3 (Nov
2024–Jan 2025).

**Decision:** Try the earnings screen to combat **earnings-gap** event. → **02**

## 02 - `earnings_screen_baseline`

**Context:** Implementation of earnings screen to combat earnings event gap.

**Test:** Baseline ON vs OFF forward only earnings screen (if earnings date within 15 days, don't trade), 5 start dates.

**Result:** Screen effect is **inconsistent** (14 improve / 17 degrade). Mean Sharpe drops 0.48 →
0.41; it blocks too many legit trades during peak earnings season.

**Decision:** Earnings isn't the driver — instability is about *which pairs get selected*, i.e. a
selection-window/slide issue. Sweep block-days & then slide. → **02b**

## 02b - `earnings_sweep_full`

**Context:** Some large losses happen **AFTER** earnings event, hence we implement a backward looking earnings block. Perform sweep to analyze block-days.

**Test:** 30 runs: 5 dates × {noscreen, bd0,3,5,7,9}. (bd3 == bd5 exactly — events cluster on
weekdays.)

**Result:** Mean Sharpe flat (0.24–0.49); screen acts as **variance-shrinkage**, not edge. bd7 =
best stability/return trade-off.

**Decision:** Earnings is a *secondary* filter, not the fix. → dive into pair-selection stability.
→ **03**

## 03 - `pair_stability` ★ root cause

**Context:** By varying start dates, our pair selection is highly volatile, and our performance is heavily affected by one pair because we only trade 5 pairs, maybe trading more pairs will diversify, less susceptible to single pair idiosyncratic event. 

**Test:** Quantified selection stability across start dates (Jaccard, dropout, rank-vol).

**Result:** Jaccard@5 ≈ **0.04**, dropout ≈ **94%**. Same-sector candidate pool is only **~20
pairs** vs **~180** for cross-sector; a rank shift of 7 completely replaces the top-5.

**Insight:** Instability is **inherent to same-sector** (tiny pool) — earnings & stop-loss were
symptoms, not cause.

**Decision:** Enlarge the pool / try cross-sector + other sector×slide combos. → **03a/03b/03c**

## 03a/03b/03c - `cross_sector_slide1m`, `cross_sector_slide3m`, `same_sector_slide1m` checking for pair selection stability

**Context:** Testing all sorts of combinations to see how pair selection stability varies.

  **Test:** Generated per-fold `pair_ranking_fold*.csv` for these three combos (the
  stability-across-start-date data for the alternative pool/configurations).

  **Result:** Fold-level rankings needed to compare pool size & rank volatility across sector×slide.

  **Decision:** Feed these into the grid sweeps. → **06/05**

## 04 - `max_pairs_sweep`

**Context:** Testing trading different amount of pairs to see which gives us best performance.

**Test:** same vs cross × mp ∈ {5,10,20,50}, 5 start dates.

**Result:** Same-sector mean Sharpe peaks at **mp=20 (0.80)**; std collapses at mp=50 (0.34).
Cross-sector most stable at mp=20 (std 0.11).

**Decision:** Use **mp=20**. → full config grid at mp=5 and mp=20. → **06, 05**

## 05 - `grid_search_mp5` (mp=5, pct=0.18)

**Context:** Setting a baseline grid search for our initial mp=5. Then comparing the results to mp20.

**Test:** 8 configs (sector × slide × screen) × 5 start dates = 40 runs at mp=5.

**Result:** Best = `same_sector_slide1m_noscreen` ≈ **1.42** mean Sharpe (std 0.07, range
[1.33, 1.51]) — remarkably stable across all 5 starts; `same_sector_slide1m_bd7` second at **1.32**
(std 0.14). mp=5 still deploys far fewer active trades than mp=20 (see the mp=5 vs mp=20 table) —
thinner books.

**Decision:** Push the mp=20 grid; mp=5 abandoned on variance & book thickness, not on mean. → **06**
### mp=5 Sharpe pivot (per start date)
| Start | same 3m ns | same 3m bd7 | same 1m ns | same 1m bd7 | cross 3m ns | cross 3m bd7 | cross 1m ns | cross 1m bd7 |
|---|---|---|---|---|---|---|---|---|
| 2023-11-01 | 0.69 | −0.13 | 1.33 | 1.06 | 0.44 | 0.13 | 0.42 | 0.23 |
| 2023-12-01 | −0.23 | −0.06 | 1.37 | 1.28 | 0.11 | 0.12 | 0.61 | 0.40 |
| 2024-01-01 | 1.48 | 1.26 | 1.41 | 1.40 | 0.54 | −0.10 | 0.70 | 0.28 |
| 2024-02-01 | 0.52 | 0.01 | 1.51 | 1.47 | 1.05 | 0.95 | 0.62 | 0.17 |
| 2024-03-01 | −0.14 | 0.29 | 1.47 | 1.40 | 0.32 | 0.05 | 0.74 | 0.32 |
| **Mean** | 0.46 | 0.27 | **1.42** | 1.32 | 0.49 | 0.23 | 0.62 | 0.28 |
| **Std** | 0.62 | 0.51 | **0.07** | 0.14 | 0.31 | 0.37 | 0.11 | 0.08 |
| **Mean Ret%** | 2.64 | 1.47 | 4.85 | 3.21 | 1.92 | 0.47 | 1.74 | 0.48 |

### mp=5 deltas
- **Slide 1m vs 3m:** same-sector helps massively (+0.96 noscreen, +1.05 bd7); cross-sector helps
    mildly (+0.13 noscreen, +0.05 bd7).
- **bd7 screen:** hurts same 1m (−0.10), same 3m (−0.19), cross 3m (−0.26); helps cross 1m (+0.02)
    — the screen is a *negative* lever at mp=5 on slide-1m.

### mp=5 vs mp=20 (winner, same_sector_slide1m)
| Start | mp=5 ns | mp=5 bd7 | mp=20 bd7 |
|---|---|---|---|
| 2023-11-01 | 1.33 | 1.06 | 1.06 |
| 2023-12-01 | 1.37 | 1.28 | 1.34 |
| 2024-01-01 | 1.41 | 1.40 | 1.37 |
| 2024-02-01 | 1.51 | 1.47 | 1.44 |
| 2024-03-01 | 1.47 | 1.40 | 1.30 |
| **Mean / Std** | **1.42 / 0.07** | 1.32 / 0.14 | **1.30 / 0.13** |

mp=5's winner actually matches mp=20 on mean Sharpe here (1.42 vs 1.30) with *lower* variance, but
it deploys a much thinner book (see section 06 trades table) — mp=20 is retained as the robust choice.

mp=20 both raises mean Sharpe and cuts variance on the winner → mp=5 dropped.

## 06 - `grid_search` (mp=20, pct=0.045) ★ recent-period winner

**Test:** 40 runs (5 start dates × 8 configs) on core, 2024-01 → 2025-12.

**Result:** **Winner: `same_sector_slide1m_bd7`** — mean Sharpe **1.30**, std **0.13**, positive on
**all 5 start dates** (range [1.06, 1.44]). `same_sector_slide1m_noscreen` is essentially tied at
**1.27** (std 0.06) — slide-1m same-sector is the only genuinely strong family. Slide 1m beats 3m;
the bd7 screen is a marginal +0.03 at 1m.

**Decision:** Push the winner to the long 2015–2019 horizon to check regime robustness. → **08**

### Sharpe pivot (per start date)
| Start | same 3m ns | same 3m bd7 | same 1m ns | same 1m bd7 | cross 3m ns | cross 3m bd7 | cross 1m ns | cross 1m bd7 |
|---|---|---|---|---|---|---|---|---|
| 2023-11-01 | 0.26 | 0.40 | 1.23 | 1.06 | 0.99 | 0.98 | 0.51 | 0.59 |
| 2023-12-01 | 0.25 | −0.20 | 1.36 | 1.34 | 0.32 | 0.38 | 0.56 | 0.70 |
| 2024-01-01 | 1.81 | 1.61 | 1.23 | 1.37 | 0.44 | 0.17 | 0.55 | 0.69 |
| 2024-02-01 | −0.19 | 0.45 | 1.33 | 1.44 | 0.59 | 0.99 | 0.60 | 0.55 |
| 2024-03-01 | 0.35 | 0.11 | 1.21 | 1.30 | 0.36 | 0.29 | 0.68 | 0.62 |
| **Mean Sharpe** | 0.50 | 0.47 | 1.27 | **1.30** | 0.54 | 0.56 | 0.58 | 0.63 |
| **Std** | 0.68 | 0.61 | 0.06 | **0.13** | 0.24 | 0.35 | 0.06 | 0.06 |
| **Range** | [−0.19,1.81] | [−0.20,1.61] | [1.21,1.36] | **[1.06,1.44]** | [0.32,0.99] | [0.17,0.99] | [0.51,0.68] | [0.55,0.70] |
| **Mean Ret%** | 1.31 | 0.83 | 2.13 | 1.46 | 1.22 | 0.75 | 1.04 | 0.71 |

### Trades & deployment
| Metric | same 3m ns | same 3m bd7 | same 1m ns | same 1m bd7 | cross 3m ns | cross 3m bd7 | cross 1m ns | cross 1m bd7 |
|---|---|---|---|---|---|---|---|---|
| Mean Trades | 158 | 85 | 437 | 237 | 157 | 84 | 461 | 247 |
| Mean Active Trades | ~1.9 | ~1.3 | ~5.8 | ~3.7 | ~2.1 | ~1.3 | ~6.1 | ~3.7 |
| Pairs/fold mean | ~18 | ~18 | ~18 | ~18 | 20 | 20 | 20 | 20 |
| Fill-rate (20 pairs) | ~69% | ~69% | ~70% | ~70% | 100% | 100% | 100% | 100% |

### Deltas (what each knob does on 2024-01→2025-12)
- **Slide 1m vs 3m:** same-sector **+0.77** (noscreen) / **+0.83** (bd7) — 1m wins decisively;
    cross-sector **+0.04** / **+0.07** — no difference.
- **bd7 screen:** same 1m **+0.03**, same 3m **−0.03**, cross 3m **+0.02**, cross 1m **+0.05** —
    screen is a wash at mp=20.
- **Cross vs same:** same-sector wins only on slide-1m (1.27–1.30 vs 0.58–0.63); cross-sector
    beats same on slide-3m (0.54–0.56 vs 0.47–0.50).

### Key caveats
- **Thin same-sector book:** same-sector selects only ~18 pairs/fold and fills all 20 only ~70% of
    folds; cross-sector always fills 20. The winner's 1.30 is earned on a thin book.
- **No 15th-of-month starts here:** the 2m grid uses 1st-of-month starts only (2023-11-01 →
    2024-03-01); mid-month fragility is quantified in **10**.

## 07 - `grid_search_sp500` (SP500, mp=20, pct=0.045)

**Context:** Previous test was only on core universe, for more diversification, try expanding to snp, inspired by research papers.

**Test:** Same 8-config grid on the full SP500 universe, 5 start dates, 2024-01 → 2025-12.

**Result:** SP500 is noisy/mixed — nothing matches core. Best mean Sharpe is
`same_sector_slide3m_bd7` = **0.74** but with std 0.82 (range [−0.81, 1.52]) — far too unstable.
`same_sector_slide1m_bd7` is weakly positive (0.43) but very stable (std 0.10), ~0.87 Sharpe below
the core winner.

**Decision:** To determine if core is just better than SP500, run core & SP500 over 2015–2019. → **08 (core), 09 (SP500)**

### Sharpe pivot (per start date)
| Start | same 3m ns | same 3m bd7 | same 1m ns | same 1m bd7 | cross 3m ns | cross 3m bd7 | cross 1m ns | cross 1m bd7 |
|---|---|---|---|---|---|---|---|---|
| 2023-11-01 | 1.33 | 1.52 | 0.16 | 0.55 | −0.18 | 0.29 | 0.19 | 0.13 |
| 2023-12-01 | 0.41 | 0.76 | 0.11 | 0.51 | 0.43 | −0.44 | 0.21 | 0.05 |
| 2024-01-01 | −1.02 | −0.81 | −0.21 | 0.27 | 0.71 | 0.54 | 0.37 | 0.06 |
| 2024-02-01 | 0.66 | 1.30 | 0.09 | 0.41 | −0.15 | 0.30 | 0.29 | 0.03 |
| 2024-03-01 | 0.64 | 0.90 | 0.06 | 0.40 | 0.52 | −0.44 | −0.51 | −0.01 |
| **Mean / Std** | 0.40/0.78 | 0.74/0.82 | 0.04/0.13 | 0.43/0.10 | 0.27/0.36 | 0.05/0.41 | 0.11/0.32 | 0.05/0.05 |
| **Mean Ret%** | 0.99 | 1.18 | 0.05 | 0.44 | 0.54 | 0.21 | 0.19 | 0.07 |

### SP500 vs Core (winner: same 1m bd7)
| Metric | SP500 | Core | Δ |
|---|---|---|---|
| Mean Sharpe | 0.43 | **1.30** | −0.87 |
| Mean Ret% | 0.44 | **1.46** | −1.02 |
| Mean Active Trades | ~3.9 | ~3.7 | ~0 |
| Mean Trades | 316 | 237 | ~0 |

### Key findings
- **SP500 never beats core** on any config (2024-01→2025-12); the full 500-ticker universe dilutes
    the curated mega-cap edge.
- SP500 slide1m configs are weakly positive but stable (std 0.10); slide3m is strong-but-unstable
    (std 0.82).

## 08a_core_2015_2020 (`+ COMPARISON.md`) ★ true 2015–2019 baseline

**Context:** Running core mp20 to see if core beats SP500. BUT halfway through we made a mistake and used 12m selection cache. This is 2m selection, which is supposedly our best result.

**Result:** Slide-1m is mildly *negative-to-flat* (same 1m bd7 −0.11, same 1m noscreen −0.08,
cross 1m bd7 **+0.50**), and **cross-sector is the winner: `cross_sector_slide3m_bd7` +0.51,
`cross_sector_slide1m_bd7` +0.50.** Same-sector 3m collapsed to −0.54/−0.65. On 2m selection over
2015–2019, cross-sector (especially 3m) is what survives on core.

**Decision:** These clean numbers are the true baseline. Moving forward with 12m selection.

### Single-start results (2014-11-01, trading 2015-01→2019-12)
| Config | Sharpe | Ret% | Trades |
|---|---|---|---|
| `cross_sector_slide3m_bd7` | **+0.51** | +0.60 | 281 |
| `cross_sector_slide1m_bd7` | **+0.50** | +0.40 | 843 |
| `cross_sector_slide3m_noscreen` | +0.24 | +0.41 | 504 |
| `cross_sector_slide1m_noscreen` | −0.04 | −0.06 | 1525 |
| `same_sector_slide1m_noscreen` | −0.08 | −0.11 | 1391 |
| `same_sector_slide1m_bd7` | −0.11 | −0.09 | 766 |
| `same_sector_slide3m_noscreen` | −0.54 | −0.88 | 440 |
| `same_sector_slide3m_bd7` | −0.65 | −0.67 | 240 |

### Clean vs contaminated-12m-selection (historical record)
*(The 12m-selection columns are the **contaminated** 08b archive preserved in `_preserved/` — a
cache-shadow bug, not real edge. They are retained here only as the record of the bug; the clean
sector-masked 12m REDO numbers are in section 08b below.)*
| Start | Config | Clean 2m Sharpe | Contam-12m Sharpe | ΔSharpe |
|---|---|---|---|---|
| 2015-01-01 | same_sector_slide1m_bd7 | −0.27 | 0.86 | −1.13 |
| 2015-01-01 | same_sector_slide1m_noscreen | −0.24 | 1.39 | −1.63 |
| 2015-01-01 | same_sector_slide3m_bd7 | +0.39 | 0.95 | −0.56 |
| 2015-01-01 | same_sector_slide3m_noscreen | +0.38 | 1.29 | −0.92 |
| 2015-01-01 | cross_sector_slide1m_bd7 | +0.25 | 0.92 | −0.67 |
| 2015-01-01 | cross_sector_slide1m_noscreen | +0.01 | 1.51 | −1.50 |
| 2015-01-01 | cross_sector_slide3m_bd7 | +0.20 | 0.80 | −0.60 |
| 2015-01-01 | cross_sector_slide3m_noscreen | +0.12 | 1.20 | −1.08 |
| 2017-01-01 | same_sector_slide1m_bd7 | −0.54 | 0.82 | −1.36 |
| 2017-01-01 | same_sector_slide1m_noscreen | −0.74 | 1.33 | −2.06 |
| 2017-01-01 | same_sector_slide3m_bd7 | +0.27 | 1.05 | −0.78 |
| 2017-01-01 | same_sector_slide3m_noscreen | +0.15 | 1.40 | −1.25 |
| 2017-01-01 | cross_sector_slide1m_bd7 | −0.15 | 0.90 | −1.05 |
| 2017-01-01 | cross_sector_slide1m_noscreen | −0.28 | 1.49 | −1.77 |
| 2017-01-01 | cross_sector_slide3m_bd7 | −0.31 | 0.85 | −1.16 |
| 2017-01-01 | cross_sector_slide3m_noscreen | −0.01 | 1.27 | −1.27 |
| 2019-01-01 | same_sector_slide1m_bd7 | −0.41 | 0.90 | −1.31 |
| 2019-01-01 | same_sector_slide1m_noscreen | −0.54 | 1.23 | −1.76 |
| 2019-01-01 | same_sector_slide3m_bd7 | +0.67 | 1.22 | −0.54 |
| 2019-01-01 | same_sector_slide3m_noscreen | +0.53 | 1.26 | −0.73 |
| 2019-01-01 | cross_sector_slide1m_bd7 | −0.14 | 1.02 | −1.16 |
| 2019-01-01 | cross_sector_slide1m_noscreen | +0.19 | 1.50 | −1.31 |
| 2019-01-01 | cross_sector_slide3m_bd7 | −0.27 | 0.90 | −1.18 |
| 2019-01-01 | cross_sector_slide3m_noscreen | +0.48 | 0.97 | −0.48 |

### Clean findings
- **Cross-sector survives; same-sector 3m collapses.** The 2m-selection core best over 2015–2019 is
    cross-sector (`cross 3m bd7` 0.51, `cross 1m bd7` 0.50); same-sector 3m is negative (−0.54/−0.65).
- **Slide 1m is weak on this window:** same-sector slide1m negative-to-flat (−0.08/−0.11);
    cross-sector slide1m bd7 is the one strong 1m cell (+0.50).
- **Regime reversal holds directionally:** slide 1m wins recent (06) but not 2015–2019.
- *(All 24 clean-vs-contaminated comparisons had ΔSharpe < 0 — the 12m-selection archive was a
    bug, as documented above.)*

## 08b - `core_12m_sel_2015_2020` ★ 12-month selection on core, sector-masked (REDO)

**Test:** 8 configs, single start **2014-01-01**, trading 2015-01 → 2019-12, on core,
`--sel_months 12` (pairs from `sp500_12m.pkl` masked to core tickers, p<0.05 log).
**The sector mask is applied for real this time** — the cache-shadow bug is fixed and these are
clean runs.

**Why redo:** The original 08b ran the *same* 12m-selection grid, but the huck-cache shadow bug
bypassed the sector mask and core ticker mask on cache-hit folds (see archive note below).
This redo overwrites `diagnosis/08b_core_12m_sel_2015_2020/` with sector-masked results;
the contaminated originals are preserved in `diagnosis/08b_core_12m_sel_2015_2020_preserved/`.

**Result (annualized Sharpe per config — single start, 2015–2019, trimmed):**
| Config | Sharpe | Ret% | Trades |
|---|---|---|---|
| `cross_sector_slide1m_bd7` | **+0.34** | +0.29 | 740 |
| `same_sector_slide1m_bd7` | +0.13 | +0.05 | 228 |
| `cross_sector_slide3m_bd7` | −0.00 | −0.01 | 254 |
| `same_sector_slide3m_bd7` | −0.34 | −0.20 | 96 |
| `cross_sector_slide1m_noscreen` | −0.43 | −0.56 | 1468 |
| `cross_sector_slide3m_noscreen` | −0.63 | −1.08 | 510 |
| `same_sector_slide1m_noscreen` | −0.80 | −0.44 | 434 |
| `same_sector_slide3m_noscreen` | −0.91 | −0.85 | 176 |

Cross-sector 1m bd7 tops the grid at 0.34 — with only ~5 qualifying pairs/fold, the book is
structurally thin (mean active trades <1).

**Key finding:** With the sector mask actually enforced, core-12m is **marginal (≤0.34)** and
thin-booked — best config is `cross_sector_slide1m_bd7`. Core-12m same-sector remains
structurally thin.

**Archive note (original contaminated runs, `_preserved/`):** the cache-shadow bug fed
12-month SP500 cross-sector pairs into the baseline 2-month core folds on cache-hit windows
(selection in [2015-01..2020-01]); the sector mask and core ticker mask were bypassed there,
so early cache-hit folds were cross==same. Those numbers (Sharpe 0.80–1.51, FF alpha +6.04%)
are **artifact, not edge.** The archive remains a faithful record of the bug.

**Script:** `run_12m_core_2015_2020.py` (runs 2 backtests at a time, `--workers 1` each).





## 09a - `sp500_2015_2020`

**Test:** Same 8-config grid on SP500, single start **2014-11-01**, trading 2015-01 → 2019-12.

**Result (annualized Sharpe per config — single start, 2015–2019, trimmed):**
| Config | Sharpe | Ret% | Trades |
|---|---|---|---|
| `cross_sector_slide3m_noscreen` | **+0.62** | +1.80 | 529 |
| `cross_sector_slide3m_bd7` | +0.62 | +1.80 | 529 |
| `same_sector_slide1m_noscreen` | +0.34 | +0.42 | 1517 |
| `same_sector_slide1m_bd7` | +0.34 | +0.42 | 1517 |
| `same_sector_slide3m_noscreen` | +0.24 | +0.46 | 509 |
| `same_sector_slide3m_bd7` | +0.24 | +0.46 | 509 |
| `cross_sector_slide1m_noscreen` | +0.19 | +0.28 | 1505 |
| `cross_sector_slide1m_bd7` | +0.19 | +0.28 | 1505 |

**Result:** **SP500 2m-selection is positive on 2015–2019** — best `cross 3m` **+0.62**
(bd7 ≈ noscreen; the screen had no measurable effect on SP500 2015–2019), and every config clears
zero. SP500 is viable with 2m selection on this window.

**Decision:** Curated core universe is essential **with 2m selection**; set SP500 aside — but note
SP500 becomes viable with 12m selection (09b). → **10**

### Key findings
- **Cross-sector 3m is clearly positive (+0.62)** and every config clears zero on 2015–2019.
- **bd7 screen has ~zero effect** on SP500 2015–2019 (bd7 ≈ noscreen to the 3rd decimal).
- **SP500 vs Core 2015–2019 (single-start):** core best 0.51 (08a `cross 3m bd7`) vs SP500
    best 0.62 (`cross 3m`) → SP500 slightly edges core on 2m selection.

## 09b - `sp500_12m_sel_2015_2020` ★ 12-month selection on SP500, sector-masked

**Test:** Same 8-config grid on SP500, single start **2014-01-01**, trading 2015-01 → 2019-12,
`--sel_months 12`, sector mask applied. Counterpart to 08b but on the full SP500 universe.

**Result (annualized Sharpe per config — single start, 2015–2019, trimmed):**
| Config | Sharpe | Ret% | Trades |
|---|---|---|---|
| `same_sector_slide1m_noscreen` | **+0.43** | +0.58 | 1618 |
| `same_sector_slide1m_bd7` | +0.38 | +0.52 | 1615 |
| `same_sector_slide3m_noscreen` | +0.35 | +0.65 | 560 |
| `same_sector_slide3m_bd7` | +0.35 | +0.65 | 560 |
| `cross_sector_slide1m_noscreen` | +0.31 | +0.44 | 1564 |
| `cross_sector_slide1m_bd7` | +0.31 | +0.44 | 1564 |
| `cross_sector_slide3m_noscreen` | −0.27 | −0.64 | 510 |
| `cross_sector_slide3m_bd7` | −0.27 | −0.64 | 510 |

**Key finding:** 12-month selection **rescues SP500 2015–2019** (the 2m-selection grid is much
weaker on this window), led by **`same_sector_slide1m_noscreen` +0.43** with full books (20
pairs/fold). 12m same-sector 1m wins; cross-sector 3m is negative. bd7 screen ~zero effect.

**Script:** `run_12m_sp500_2015_2020.py` (runs 2 backtests at a time, `--workers 1` each).

## 10 - `sweep_same_sector_slide1m_bd7_pct025` (+ `same_sector_slide1m_bd7_pct025`) ★ start-date fragility

**Test:** The winning config `same_sector_slide1m_bd7` re-run at **pct per-pair = 0.25** (higher
sizing across 20 pairs), swept over recent start-dates (2023-11-01 → 2024-02-15) **and** a
2015–2019 arm (2015/2017/2019).

**Result (recent, pct=0.25, trading 2024-01→2025-12):** 1st-of-month starts are
positive (+0.66…+1.18); **mid-month (15th) starts are weaker but do NOT collapse** (+0.50…+0.61):
| Start | Sharpe | Ret% ann | Trades |
|---|---|---|---|
| 2023-11-01 | +0.66 | 3.83 | 254 |
| 2023-11-15 | +0.50 | 3.09 | 258 |
| 2023-12-01 | **+1.11** | 6.83 | 247 |
| 2023-12-15 | +0.60 | 3.77 | 251 |
| 2024-01-01 | **+1.12** | 7.04 | 239 |
| 2024-01-15 | +0.61 | 3.94 | 238 |
| 2024-02-01 | **+1.18** | 7.56 | 227 |
| 2024-02-15 | +0.56 | 3.67 | 228 |

**Result (2015–2019 arm, pct=0.25):** **negative** — 2015-01-01 −0.06, 2017-01-01 −0.46,
2019-01-01 −0.13 (ret −0.48%/−2.83%/−1.20%).

**Interpretation:** Higher sizing (0.25) does **not** change the regime/start-date story: 1st-of-month
starts stay stronger than 15th (0.66–1.18 vs 0.50–0.61) — the 1st/15th spread is real but moderate
on the recent window — and 2015–2019 is negative regardless.

**Decision (moving forward):** Treat `same_sector_slide1m_bd7` as the preferred config **only**
under favorable (recent, 1st-of-month) conditions; the start-date sensitivity confirmed in steps
01–03 remains the central unsolved risk — likely a pool-size / selection-metric stability problem,
not a sizing (pct) problem.

## 10a - `core_12m_sel_2023_2025` ★ 12-month selection on core, recent period

**Test:** Same 8-config grid on core, `--sel_months 12`, 5 monthly start dates
(2023-01/02/03/04/05). Sector mask applied. Counterpart to 08b on the recent period.

**Result (annualized Sharpe per config, 5 starts — full grid):**
| Config | 2023-01 | 2023-02 | 2023-03 | 2023-04 | 2023-05 | Mean | Mean Ret% |
|---|---|---|---|---|---|---|---|
| `cross_sector_slide1m_noscreen` | 0.81 | 0.79 | 0.78 | 0.85 | 0.86 | **+0.82** | +1.55 |
| `cross_sector_slide1m_bd7` | 0.57 | 0.52 | 0.55 | 0.49 | 0.45 | +0.52 | +0.66 |
| `cross_sector_slide3m_noscreen` | 0.62 | −0.12 | 1.02 | 0.81 | −0.24 | +0.42 | +1.03 |
| `same_sector_slide1m_bd7` | 0.24 | 0.25 | 0.42 | 0.53 | 0.40 | +0.37 | +0.14 |
| `same_sector_slide1m_noscreen` | 0.31 | 0.31 | 0.28 | 0.42 | 0.39 | +0.34 | +0.26 |
| `cross_sector_slide3m_bd7` | 0.09 | 0.26 | 1.04 | −0.07 | 0.25 | +0.31 | +0.42 |
| `same_sector_slide3m_noscreen` | 0.43 | 0.18 | −0.00 | 0.57 | 0.19 | +0.28 | +0.23 |
| `same_sector_slide3m_bd7` | −0.61 | 0.80 | 0.17 | −0.62 | 0.96 | +0.14 | +0.03 |

**Key finding:** The best core-12m config on the recent window is **`cross_sector_slide1m_noscreen` (+0.82, std 0.03)** — remarkably stable across all 5 starts — not the same-sector 1m bd7 (+0.37). Cross-sector slide1m is the reliable cell here; same-sector stays thin-booked. Core-12m's edge is thin everywhere — it only clears positive on recent data, and the winner is a cross-sector config.

**10a vs 06 (12m-selection vs 2m-selection, core, recent):** the 12-month selection **does NOT beat the 2-month selection** on the recent period — 2m wins every config except cross 1m noscreen.
| Config | 06 (2m-sel) | 10a (12m-sel) | Δ | 06 Ret% | 10a Ret% |
|---|---|---|---|---|---|
| `same_sector_slide1m_bd7` | **1.30** | 0.37 | −0.93 | 1.46 | 0.14 |
| `same_sector_slide1m_noscreen` | **1.27** | 0.34 | −0.93 | 2.13 | 0.26 |
| `same_sector_slide3m_bd7` | **0.47** | 0.14 | −0.33 | 0.83 | 0.03 |
| `same_sector_slide3m_noscreen` | **0.50** | 0.28 | −0.22 | 1.31 | 0.23 |
| `cross_sector_slide3m_bd7` | **0.56** | 0.31 | −0.25 | 0.75 | 0.42 |
| `cross_sector_slide1m_bd7` | **0.63** | 0.52 | −0.11 | 0.71 | 0.66 |
| `cross_sector_slide3m_noscreen` | **0.54** | 0.42 | −0.12 | 1.22 | 1.03 |
| `cross_sector_slide1m_noscreen` | 0.58 | **0.82** | +0.24 | 1.04 | 1.55 |

*(Same 5 starts on both sides; Δ compares per-config means.)*

**Script:** `run_12m_core_2023_2025.py` (runs 2 backtests at a time, `--workers 1` each).

## 10b - `sp500_12m_sel_2023_2025` ★ 12-month selection on SP500, recent period

**Test:** Same 8-config grid on SP500, `--sel_months 12`, 5 monthly start dates
(2023-01/02/03/04/05). Sector mask applied. Counterpart to 09b on the recent
period — the missing cell in the 2×2 (core/SP500) × (2015–2020/recent) 12m grid.

**Result (annualized Sharpe per config, 5 starts — full grid):**
| Config | 2023-01 | 2023-02 | 2023-03 | 2023-04 | 2023-05 | Mean | Mean Ret% |
|---|---|---|---|---|---|---|---|
| `cross_sector_slide1m_noscreen` | 1.32 | 1.43 | 1.67 | 2.21 | 2.34 | **+1.80** | +3.32 |
| `same_sector_slide1m_noscreen` | 1.62 | 1.66 | 1.63 | 1.66 | 1.56 | +1.63 | +3.42 |
| `same_sector_slide1m_bd7` | 1.47 | 1.48 | 1.45 | 1.61 | 1.39 | +1.48 | +2.21 |
| `cross_sector_slide1m_bd7` | 0.90 | 0.95 | 1.10 | 1.89 | 2.03 | +1.37 | +1.85 |
| `cross_sector_slide3m_noscreen` | 0.88 | 1.13 | 0.61 | 1.14 | 1.52 | +1.06 | +2.58 |
| `same_sector_slide3m_bd7` | 1.62 | 0.46 | 0.94 | 1.55 | 0.56 | +1.03 | +1.92 |
| `same_sector_slide3m_noscreen` | 1.76 | −0.12 | 1.64 | 1.73 | 0.02 | +1.01 | +2.67 |
| `cross_sector_slide3m_bd7` | 0.09 | 1.39 | 0.46 | 0.47 | 1.48 | +0.78 | +1.32 |

**Key finding:** On the recent period, **SP500 12m-selection is the strongest cell in the whole
study** — `cross_sector_slide1m_noscreen` reaches **+1.80** (std 0.41), with same 1m noscreen
**+1.63** (std 0.04, the most stable) and same 1m bd7 +1.48. The winner is a cross-sector config,
mirroring 10a; the 1m family wins broadly, and same 1m noscreen is exceptionally stable.

**10b vs 10a (SP500 vs core, 12m-selection, same 5 starts):**
| Config | 10a core | 10b SP500 | Δ | 10a Ret% | 10b Ret% |
|---|---|---|---|---|---|
| `same_sector_slide1m_bd7` | 0.37 | **1.48** | +1.11 | 0.14 | 2.21 |
| `same_sector_slide1m_noscreen` | 0.34 | **1.63** | +1.29 | 0.26 | 3.42 |
| `same_sector_slide3m_noscreen` | 0.28 | **1.01** | +0.73 | 0.23 | 2.67 |
| `same_sector_slide3m_bd7` | 0.14 | **1.03** | +0.89 | 0.03 | 1.92 |
| `cross_sector_slide3m_noscreen` | 0.42 | **1.06** | +0.64 | 1.03 | 2.58 |
| `cross_sector_slide1m_bd7` | 0.52 | **1.37** | +0.85 | 0.66 | 1.85 |
| `cross_sector_slide3m_bd7` | 0.31 | **0.78** | +0.47 | 0.42 | 1.32 |
| `cross_sector_slide1m_noscreen` | 0.82 | **1.80** | +0.98 | 1.55 | 3.32 |

*(SP500 beats core on every config with 12m selection on the recent period — the wider
universe is a benefit when selection is good, the opposite of the 2015–2020 2m result.)*

**Script:** `run_12m_sp500_2023_2025.py` (runs 2 backtests at a time, `--workers 1` each).

## 11a - core 12m, `same_sector_slide1m_bd7` at pct=0.25, 2015-2020

**Test:** The best config (`same_sector_slide1m_bd7`, 12m selection, core) re-run at
**pct per-pair = 0.25** (vs 0.045 baseline) on 2015–2020. Tests whether higher sizing changes
Sharpe or returns linearly, and whether capacity is the binding limit.

**Result (core, same 1m bd7 — 2015-start single run, full 2016–20, trimmed):**
| Metric | pct=0.25 (11a) |
|---|---|
| Sharpe | **0.52** |
| Ret% ann | **1.21** |
| Mean Active Trades | 0.89 |

**Key finding:** pct scaling is **purely linear** — higher sizing scales returns but does **not**
improve the risk-adjusted result. **Capacity is the binding limit:** even at pct=0.25 the book
deploys <1 position on average (MeanAT ~0.9/20), so there's no crowding — but also no more edge
per unit risk.

**Script:** `run_12m_core_2015_2020_pct025.py` (runs 2 backtests at a time, `--workers 1` each).

## 11b - SP500 12m, `same_sector_slide1m_bd7` at pct=0.25, 2015-2020

**Test:** Same as 11a but on the SP500 universe (wider book than core).

**Result (SP500, same 1m bd7 — 2015-start single run, full 2016–20, trimmed):**
| Metric | pct=0.25 (11b) |
|---|---|
| Sharpe | **0.53** |
| Ret% ann | **2.86** |
| Mean Active Trades | 3.76 |

**Key finding:** Same story as 11a — higher sizing levers the same signal linearly without adding
edge. SP500 deploys ~3.5 positions vs core's ~0.9, but both are far under the 20-pair
(×~3-fold = 60-slot) limit.

**11a vs 11b (core vs SP500, same 1m bd7, pct=0.25, 2015–2020 single-start):**
| Metric | 11a core | 11b SP500 |
|---|---|---|
| Sharpe | 0.52 | **0.53** |
| Ret% | 1.21 | **2.86** |
| Mean Active Trades | 0.89 | **3.76** |

*(SP500 wins on return and book thickness; Sharpe is a near-tie at the single-start level.)*

**Script:** `run_12m_sp500_2015_2020_pct025.py` (runs 2 backtests at a time, `--workers 1` each).


## 13 - Combined two-leg book

**Context:** Instead of picking one config, deploy **two legs** simultaneously — each strong in its
own regime, not terrible in the other — with a **monthly momentum rotation** allocating more to the
recently-stronger leg. Full documentation: `fixed_diagnosis/_COMBINED_BOOK.md`.

**Sweep:** all **496 pairs** of the 32 single-leg configs (4 strategies × 8 configs), scored on both
windows. Recent = mean Sharpe over the 5 start-pairs (trading 2024-01-02..2025-12-31);
historical = single window (2015-01-02..2019-12-31). **Score = min(recent, hist)** — "strong in
its regime, not terrible in the other".

**Top 20 pairs (momentum scheme):**

| Pair | Recent | Range | Hist | Score |
|---|---:|---:|---:|---:|
| core-2m/`cross 3m bd7` + sp500-12m/`cross 1m bd7` | 1.18 | 0.73–1.62 | 1.00 | 1.00 |
| core-2m/`cross 3m bd7` + sp500-12m/`cross 1m noscreen` | 1.37 | 0.72–1.80 | 1.00 | **1.00** |
| core-2m/`cross 3m bd7` + sp500-12m/`same 3m bd7` | 1.26 | 0.56–2.15 | 0.94 | 0.94 |
| core-2m/`cross 3m bd7` + sp500-12m/`same 3m noscreen` | 1.24 | 0.19–2.17 | 0.94 | 0.94 |
| sp500-2m/`cross 3m noscreen` + sp500-12m/`same 3m noscreen` | 0.92 | 0.31–1.53 | 0.91 | 0.91 |
| core-2m/`cross 1m bd7` + sp500-12m/`same 3m bd7` | 1.19 | 0.76–1.61 | 0.88 | 0.88 |
| core-2m/`cross 1m bd7` + sp500-12m/`same 3m noscreen` | 1.15 | 0.36–1.74 | 0.88 | 0.88 |
| core-2m/`cross 3m noscreen` + sp500-12m/`same 3m bd7` | 1.18 | 0.57–1.96 | 0.86 | 0.86 |
| core-2m/`cross 3m noscreen` + sp500-12m/`same 3m noscreen` | 1.26 | 0.29–2.16 | 0.86 | 0.86 |
| core-2m/`cross 3m bd7` + sp500-2m/`same 1m bd7` | 0.91 | 0.52–1.40 | 0.86 | 0.86 |

*(Full top-20 + recent-only and historical-only top-5 tables in `_COMBINED_BOOK.md`.)*

**Winner (tied #1, selected for the combined book):**
`core-2m/cross_sector_slide3m_bd7` **(A)** + `sp500-12m/cross_sector_slide1m_noscreen` **(B)** —
recent **1.37**, hist **1.00**, score **1.00**. CSVs written to
`fixed_diagnosis/_combined/sweep_momentum_02/{recent,historical}/daily_returns.csv` (top-5 pairs → `sweep_momentum_01..05`).

**Why cross over same for the strong recent leg:** sp500-12m `same 1m noscreen` is stronger recent
(1.63 vs 1.37) but its pair-hist is far worse (0.67 vs 1.00) — the min-score rule favors the
cross-sector leg that survives both regimes.

### Rotation mechanics
Start 50/50, rebalance **monthly**: compare trailing **63-day Sharpe** of each leg, shift weight
±10% toward the winner, clamp at 25–75% on leg A. Weights held flat between rebalances.

### pct=0.25 runs (sizing, not a filter)
`pct_per_pair` scales position size linearly — it does **not** change the signal (identical trade
counts at 0.045 vs 0.25). Four single-leg runs in `fixed_diagnosis/_pct25/`, plus the combined
book in `_combined/sweep_pct25/`:

| Series | Recent (2024-01..2025-12) | Historical (2015-01..2019-12) |
|---|---|---|
| Leg A core-2m `cross 3m bd7` | Sharpe 0.98, +6.45% ann | Sharpe 0.47, +2.94% ann |
| Leg B sp500-12m `cross 1m noscreen` | Sharpe 1.26, +12.76% ann | Sharpe 0.37, +2.69% ann |
| **Combined momentum** | Sharpe **1.44**, +11.0% ann, vol 7.4%, MDD −4.9% | Sharpe **1.03**, +5.8% ann, vol 5.6%, MDD −6.6% |
| S&P 500 buy & hold | Sharpe 1.28, +48.1% ann, vol 16.5% | Sharpe 0.87, +72.7% ann, vol 13.7% |

**Takeaways:** the combined book **beats buy-and-hold on Sharpe in both windows** (1.44 vs 1.28
recent; 1.03 vs 0.87 hist) despite far lower absolute return — S&P runs 2–3× the volatility.
As a diversifier it's strong: **corr(combined, S&P) ≈ 0.36 recent / 0.08 hist**, and a 50/50 blend
reaches Sharpe **1.56 / 1.16**, above either alone. The rotation's value is better drawdown/Sharpe,
not unexplained return.

**Caveats:** pnl is bookkeeping-combined from existing leg backtests (1M start, weight arithmetic) —
no consolidated trade log; cross-sleeve slippage/cash drag not simulated. The winning pair and the
rotation rule were **selected on the same windows they're scored on** (in-sample).

## 14 - Fama-French on the combined pct0.25 book

**Model:** FF3 + Momentum + ST_Reversal, **daily** factors (cached `research/ff_factors/ff_daily.pkl`),
HAC standard errors, alpha annualized ×252. Y = strategy daily − RF. Full output:
`fixed_diagnosis/_FF_COMBINED_PCT25.md`.

| Window | Series | Ann. alpha | alpha t | Mkt-RF β (t) | ST_Rev β (t) | R² |
|---|---:|---:|---:|---:|---:|
| Recent | Combined | +2.16% | 0.47 | 0.16 (2.6) | 0.10 (2.3) | 0.16 |
| | Leg A core-2m `cross 3m bd7` | +5.38% | 0.65 | 0.16 (1.9) | 0.06 (1.2) | 0.12 |
| | Leg B sp500-12m `cross 1m noscreen` | +0.47% | 0.06 | 0.19 (2.8) | 0.10 (1.6) | 0.09 |
| Historical | Combined | +3.74% | 1.42 | 0.01 (0.7) | **0.10 (3.4)** | 0.04 |
| | Leg A core-2m `cross 3m bd7` | +2.39% | 0.40 | 0.00 (0.0) | **0.20 (2.9)** | 0.05 |
| | Leg B sp500-12m `cross 1m noscreen` | −0.25% | −0.07 | 0.03 (1.4) | **0.11 (2.9)** | 0.02 |

*(Only loadings with |t| ≥ 2 shown as bold; SMB/HML/Mom were insignificant in every cell.)*

**Interpretation:**
1. **Alpha is not statistically significant in any cell** (best t = 1.42, historical combined). After
   controlling for factors, the excess return is within noise — the "edge" is largely factor
   exposure, not unexplained alpha.
2. **The consistent, significant loading is `ST_Rev` (short-term reversal)** — significant in both
   windows for the combined book and both legs (t ≈ 2.3–3.4). That's the economically meaningful
   signature: these are short-term-reversal strategies harvesting the ST_Rev factor premium.
3. **Mkt-RF is significant only in the recent window** (β ≈ 0.16–0.19); market-neutrality holds
   historically (β ≈ 0.01–0.03). R² is low (2–16%) — most variance is idiosyncratic.

**Honest read:** the combined pct0.25 book is effectively a **short-term-reversal strategy with
modest (insignificant) alpha**, whose recent performance partly rides market beta. It is a
low-correlation, low-vol **risk reducer / diversifier** next to buy-and-hold — not an S&P
substitute — and its value is structural (low vol, low correlation), not proven alpha.

---

## Per-year breakdown (2015–2020 grids)

**The "3-start mean" used earlier in this doc triple-counted 2020** (2015-start tests 2016–20,
2017-start tests 2018–20, 2019-start tests 2020 only) and 2020 was a high-vol regime where mean
reversion thrived. The reference is the single-start view (2015-01-01 run, 2016–20, every year
counted once, **trimmed to fully-active windows**). Full per-year Sharpe / return / trade tables
for all 6 grids:

**[`diagnosis/per_year_breakdown.md`](diagnosis/per_year_breakdown.md)** (generated by
`diagnosis/per_year_breakdown.py` from existing `daily_returns.csv` + trade logs — no reruns).

Headline deltas (single-start trimmed 2016-20 vs the retired 3-start mean):
- 08b core 12m `same 1m bd7`: **1.50 → 0.53** (2016/17 negative; ~3× weaker)
- 09b SP500 12m `cross 1m bd7`: **1.32 → 0.56** (inflated by the 2019=2020 start)
- 09b SP500 12m `same 3m noscreen`: **0.74 → 1.56** (the reverse — understated by 3-start mean)
- 11a/11b pct0.25 `same 1m bd7`: **1.50/0.97 → 0.52/0.53** (returns stay meaningful at pct 0.25)

**Interpretation:** most 12m-selection Sharpe on 2015–2020 is earned in **2018–2020** (COVID vol /
recovery); 2016–17 is flat-to-negative for most 12m configs. So "12m beats 2m on 2015–2020" should
read "12m beats 2m on 2018–2020".

---

## What works where (cross-period & universe summary, mp=20)

**Best config per universe × selection × period (annualized Sharpe):**
*(2015–2019 = single start (2014-11-01 for 2m, 2014-01-01 for 12m), trading 2015-01 → 2019-12;
recent = 5-start means, trading 2024-01 → 2025-12.)*
| Universe | Selection | 2015–2019 (single-start) | 2024-01→2025-12 (5-start mean) |
|---|---|---|---|
| core | 2m | `cross_sector_slide3m_bd7` **+0.51** (cross 1m bd7 +0.50; same 3m negative) | `same_sector_slide1m_bd7` **1.30** ±0.13 |
| core | 12m | `cross_sector_slide1m_bd7` **+0.34** (thin book ~5 pairs) | `cross_sector_slide1m_noscreen` **+0.82** |
| SP500 | 2m | `cross_sector_slide3m_noscreen` **+0.62** | `same_sector_slide3m_bd7` **0.74** but std 0.82 |
| SP500 | 12m | `same_sector_slide1m_noscreen` **+0.43** | `cross_sector_slide1m_noscreen` **+1.80** |

### 2-month selection — full 4-cell matrix (Sharpe / Ret%)
| Config | core 2015–19 (08a) | SP500 2015–19 (09a) | core recent (06) | SP500 recent (07) |
|---|---|---|---|---|
| `same_sector_slide1m_bd7` | −0.11 / −0.09 | 0.34 / 0.42 | **1.30** / 1.46 | 0.43 / 0.44 |
| `cross_sector_slide1m_noscreen` | −0.04 / −0.06 | 0.19 / 0.28 | 0.58 / 1.04 | 0.11 / 0.19 |
| `same_sector_slide1m_noscreen` | −0.08 / −0.11 | 0.34 / 0.42 | 1.27 / 2.13 | 0.04 / 0.05 |
| `same_sector_slide3m_noscreen` | −0.54 / −0.88 | 0.24 / 0.46 | 0.50 / 1.31 | 0.40 / 0.99 |
| `cross_sector_slide3m_noscreen` | 0.24 / 0.41 | 0.62 / 1.80 | 0.54 / 1.22 | 0.27 / 0.54 |
| `same_sector_slide3m_bd7` | −0.65 / −0.67 | 0.24 / 0.46 | 0.47 / 0.83 | **0.74** / 1.18 |
| `cross_sector_slide1m_bd7` | **0.50** / 0.40 | 0.19 / 0.28 | 0.63 / 0.71 | 0.05 / 0.07 |
| `cross_sector_slide3m_bd7` | **0.51** / 0.60 | 0.62 / 1.80 | 0.56 / 0.75 | 0.05 / 0.21 |

### 12-month selection — full 4-cell matrix (Sharpe / Ret%)
| Config | core 2015–19 (08b) | SP500 2015–19 (09b) | core recent (10a) | SP500 recent (10b) |
|---|---|---|---|---|
| `same_sector_slide1m_bd7` | 0.13 / 0.05 | 0.38 / 0.52 | 0.37 / 0.14 | 1.48 / 2.21 |
| `cross_sector_slide1m_noscreen` | −0.43 / −0.56 | 0.31 / 0.44 | **0.82** / 1.55 | **1.80** / 3.32 |
| `same_sector_slide1m_noscreen` | −0.80 / −0.44 | **0.43** / 0.58 | 0.34 / 0.26 | 1.63 / 3.42 |
| `same_sector_slide3m_noscreen` | −0.91 / −0.85 | 0.35 / 0.65 | 0.28 / 0.23 | 1.01 / 2.67 |
| `cross_sector_slide3m_noscreen` | −0.63 / −1.08 | −0.27 / −0.64 | 0.42 / 1.03 | 1.06 / 2.58 |
| `same_sector_slide3m_bd7` | −0.34 / −0.20 | 0.35 / 0.65 | 0.14 / 0.03 | 1.03 / 1.92 |
| `cross_sector_slide1m_bd7` | **0.34** / 0.29 | 0.31 / 0.44 | 0.52 / 0.66 | 1.37 / 1.85 |
| `cross_sector_slide3m_bd7` | −0.00 / −0.01 | −0.27 / −0.64 | 0.31 / 0.42 | 0.78 / 1.32 |

*(08a/08b/09a/09b columns = single start, trimmed; 06/07/10a/10b columns = 5-start means.)*

### Rules that hold
1. **The lever is universe × selection together, not selection alone.** On core, 2m ≥ 12m (0.51 vs
    0.34 single-start; 1.30 vs 0.82 recent) — the long lookback adds little on the small core
    universe and 12m same-sector has a ~5-pair book. On SP500, 12m ≫ 2m on recent (1.80 vs 0.74)
    and 12m is the only way the wide universe stays consistently positive.
2. **SP500 2m historical is positive** on 2015–2019 (`cross 3m` **+0.62**) — SP500 2m is viable on
    this window.
3. **Cross-sector slide1m is the reliable recent-12m cell:** core 10a `cross 1m ns` **0.82**
    (std 0.03) and SP500 10b `cross 1m ns` **1.80**; same-sector 1m bd7 no longer tops either grid.
4. **Single-start levels are modest:** 0.43 (SP500 12m same 1m ns) and 0.51 (core 2m cross 3m bd7).
5. **Sector preference depends on universe & period:** core 2015–19 → cross-sector wins; SP500
    2015–19 → same-sector 1m wins on 12m; recent → same-sector 1m wins on 2m-core (06) but
    cross-sector 1m wins on 12m (10a/10b).
6. **Start-date fragility persists but softened:** the 1st-vs-15th gap in section 10 is moderate
    (15th does not collapse to ~0), and slide-3m configs still swing hard across starts
    (e.g. 10a/10b same 3m bd7 range ≈ −0.62…+0.96 / +0.46…+1.62). Never trust a single start date.
7. **Earnings screen (bd7) is a mild lever at best:** helps same 1m at mp=20 on recent core
    (+0.03); has ~zero effect on SP500 2015–2019. Never a big edge either way.

**Non-viable / artifact traps:**
- **Core with 12m same-sector** — structurally thin: only ~5 qualifying pairs/fold (12m
    cointegration on 67 core tickers), so books run <1 position on average. Not a viable book even
    though the Sharpe looks fine.
- **huck2015 12m profile (real params)** — negative on 2015–2020 (−0.21 SP500, −0.08 core). The
    "great" 12m-selection numbers only ever appeared inside the **08b** runs (12m SP500 cross-sector
    selection data + baseline fast exits, pct=0.045) — never validated clean.
- **Contaminated 08 numbers** (Sharpe 0.80–1.51, FF alpha +6.04%) are pure cache-bug artifact.
- **Any 3-start mean on 2015–2020** triple-counts 2020 and inflates the result (e.g. 08b `same
    1m bd7` 1.50 is really 0.13 single-start). Use the single-start / per-year numbers instead.

---

## Cache & pools (the new pair-selection cache)

**Old design:** a single two-tier dict (`pair_selection_cache.pkl` +
`pair_selection_filtered.pkl`) keyed by `(universe, sel_start, sel_end, same_sector)` — filters
baked at seed time.

**New design:** pools are dicts keyed by **bare `sel_start`** (window method encoded by the file
split). All universe/sector/pvalue/divergence filtering is deferred to load time via
`PoolCache.select()` (`src/pair_cache.py`). Routing is by **selection window only** in
`src/config.py:pool_path_for` — no `--pool_path` flag (removed). 2m runs read the 2m pool; 12m
runs read the 12m pool (one file covers both 2015–2020 and 2023–2025):

| Run context | Pool | Baked filters | Built from |
|---|---|---|---|
| baseline + core 2m (05/08/09 recreate grids) | `core_2m.pkl` (5 MB, 151 keys) | pvalue<0.05 (log), `sector` col | `pair_selection_cache.pkl` via `rekey_core_2m` |
| golden / any sp500 2m universe | `sp500_2m.pkl` (1 GB, 132 keys) | divergence≤0.10 only, unfiltered pvalue | golden `cache_golden/...` via `rekey_sp500_2m` |
| 12-month (huck2015 / `--sel_months 12`) | `sp500_12m.pkl` (482 MB, 84 keys: 2015–2020 + 2023–2025) | none (raw pool) | `huck2015_pvalues.pkl` verbatim + `sp500_12m_recent.pkl` merged in |

Key quirks:
- **`core_2m.pkl` is the only prefiltered pool** — `run_backtest_parallel.py:35` sets
    `prefiltered=True`, so `PoolCache.select()` skips the pvalue/half-life filter (already baked).
    This is why the baseline-core grid hits `[pool core_2m.pkl HIT …]` and skips filtering.
- **P-value is always filtered in LOG space** for non-huck paths (`cointegration_pvalue_log`). The
    **raw** `cointegration_pvalue < 0.05` filter exists **only** in the `huck2015` branch
    (`run_backtest_parallel.py:187`). During the contamination investigation the buggy path was
    *initially* hypothesized to use raw pvalue<0.05 — empirically proven to be **LOG** pvalue;
    `core_2m.pkl` (log-baked) matches the fixed path.
- **Cross-pool gap:** only ~80% of `core_2m` pairs exist in `sp500_2m` for the same window — the
    missing 20% are pairs with return divergence > 0.10 (sp500 seed pre-filters divergence, core
    doesn't). The two 2m pools are not subsets of each other.
- **`core_2m.pkl` did NOT recreate the 12m-selection (08b) runs** — that used the 12m pool
    `sp500_12m.pkl` (cross-sector semantics; the `--repro_contam` flag is removed). It *was* used for
    the `05_repro_check` verification (re-running an archived 05 grid config under current code →
    14/19 folds identical, 5 off by one pair from the pool rebuild).
- **Legacy files kept but unused by routing:** `huck2015_pvalues.pkl` (superseded by
    `sp500_12m.pkl`) and `sp500_12m_recent.pkl` (merged into `sp500_12m.pkl`).


## Honest bottom line
The investigation moved from *"noisiness"* → *"earnings?"* (rule out) → *"tiny same-sector pool =
selection volatility"* (the real cause) → *"enlarged pool + slide1m + bd7 is the practical best
(1.30 Sharpe, std 0.13 on recent core)"* → *"long-window results were a cache-bug artifact"* →
*"cleaned & rebuilt the cache as universe-free pools"* → *"12-month selection rescues SP500 but
not core"* → *"the 3-start means triple-counted 2020 and inflated the 2015–2020 numbers —
the single-start view is far weaker"* → *"two complementary legs combined with monthly momentum
rotation beat buy-and-hold on Sharpe in both windows but add no statistically significant alpha —
the edge is short-term-reversal factor exposure (ST_Rev t≈2.3–3.4), not unexplained return"*.

**Net state:** there is a real, stable short-term-reversal signal (ST_Rev p<0.001 in every run),
and the best configs are **SP500 12m on recent — `cross_sector_slide1m_noscreen` at 1.80** (same
1m noscreen 1.63, std 0.04) — and **SP500 12m same 1m noscreen at 0.43** on 2015–2019. On core,
2m selection ≥ 12m, and core-12m same-sector is a thin ~5-pair book that's structurally
capacity-limited. Every cell is still **start-date-dependent** (1st-of-month beats 15th, though the
gap is moderate), statistically insignificant at conventional alpha, and the historical numbers
are much weaker than the original 3-start means suggested. The combined book
(**[13](#13---combined-two-leg-book)**, **[14](#14---fama-french-on-the-combined-pct025-book)**)
deploys the two most complementary legs under momentum rotation: recent **1.44** / hist **1.03**
Sharpe at pct=0.25, low correlation with the market (0.36 / 0.08), beating buy-and-hold on
risk-adjusted terms — but with **insignificant Fama-French alpha** (max t = 1.42). It is a
candidate diversifier / risk reducer, not a proven edge.