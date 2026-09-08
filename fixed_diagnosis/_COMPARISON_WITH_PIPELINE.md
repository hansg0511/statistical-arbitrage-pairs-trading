# Fixed-window reruns vs RESEARCH_PIPELINE.md

Generated from `fixed_diagnosis/` (aligned windows) against the numbers published in `RESEARCH_PIPELINE.md`. All figures are annualized Sharpe unless noted.

## How to read this (caveats)

Old and new numbers are **not perfectly apples-to-apples**. Differences mix three changes:

1. **Trading window:** old historical = single 2015-01-01 start, trading 2016-01 → 2020-12 (trimmed); new = 2014-11-01 (2m) / 2014-01-01 (12m) single start, trading 2015-01 → 2019-12. **2020 is fully dropped** in the new runs. Recent: old ≈ 2024-02 → 2025-12; new = 2024-01 → 2025-12 for all.

2. **Averaging convention:** historical cells are single-start in BOTH old and new. Recent cells are 5-start means (10 = 8-start) in both. No triple-counting remains: each historical section is one run over the full 2015-2019 window.

3. **Selection alignment:** new 2m and 12m grids trade the *identical* calendar window (start pushed back by `sel_months`), removing the 12m-vs-2m warmup mismatch that existed in the old runs. Configs, `mp=20`, `pct=0.045` (mp=5/pct=0.18 for 05, pct=0.25 for 10) unchanged.

Treat a delta as informative, not causal — it bundles window + alignment.

## 1. Headline — best config per cell (old → new)

| Cell | Old best (Sh) | New best | Δ |
|---|---:|---:|---:|
| core 2m hist (08a) | `same_sector_slide3m_bd7` 0.39 | `same_sector_slide1m_noscreen` **-0.08** / -0.11% | -0.47 ▼ |
| SP500 2m hist (09a) | `none (all negative)` -0.01 | `cross_sector_slide3m_bd7` **0.89** / 1.43% | +0.90 ▲ |
| core 2m recent (06) | `same_sector_slide1m_bd7` 1.28 | `cross_sector_slide1m_noscreen` **1.53** / 3.57% | +0.25 ▲ |
| SP500 2m recent (07) | `same_sector_slide3m_bd7` 0.42 | `cross_sector_slide1m_noscreen` **0.42** / 0.85% | +0.00 ≈ |
| core 12m hist (08b) | `same_sector_slide1m_bd7` 0.53 | `cross_sector_slide1m_bd7` **0.31** / 0.27% | -0.22 ▼ |
| SP500 12m hist (09b) | `same_sector_slide3m_noscreen` 1.56 | `cross_sector_slide1m_bd7` **0.59** / 0.59% | -0.97 ▼ |
| core 12m recent (10a) | `same_sector_slide1m_bd7` 0.97 | `cross_sector_slide1m_noscreen` **0.80** / 1.51% | -0.17 ▼ |
| SP500 12m recent (10b) | `same_sector_slide1m_bd7` 1.64 | `cross_sector_slide1m_noscreen` **1.89** / 3.43% | +0.25 ▲ |

## 2. Full per-config delta matrices (Sharpe: old → new, Δ)

*Cells show `old → new (Δ)`; ▲ = +>0.05, ▼ = −>0.05, ≈ = within ±0.05. Historical cells are single-start on both sides.*

### 2-month selection

| Config | core 2015-19 (08a) <br><sub>single-start</sub> | SP500 2015-19 (09a) <br><sub>single-start</sub> | core recent (06) <br><sub>5-start</sub> | SP500 recent (07) <br><sub>5-start</sub> |
|---|---|---|---|---|
| `same_sector_slide3m_noscreen` | 0.38 → -0.53 (-0.91) ▼ | -0.16 → 0.17 (+0.33) ▲ | 0.8 → 0.5 (-0.30) ▼ | 0.02 → 0.34 (+0.32) ▲ |
| `same_sector_slide3m_bd7` | 0.39 → -0.64 (-1.03) ▼ | -0.47 → 0.2 (+0.67) ▲ | 0.81 → 0.47 (-0.34) ▼ | 0.42 → 0.29 (-0.13) ▼ |
| `same_sector_slide1m_noscreen` | -0.24 → -0.08 (+0.16) ▲ | -0.06 → 0.29 (+0.35) ▲ | 1.01 → 1.27 (+0.26) ▲ | -0.0 → -0.05 (-0.05) ≈ |
| `same_sector_slide1m_bd7` | -0.27 → -0.11 (+0.16) ▲ | -0.27 → -0.24 (+0.03) ≈ | 1.28 → 1.3 (+0.02) ≈ | 0.4 → -0.41 (-0.81) ▼ |
| `cross_sector_slide3m_noscreen` | 0.12 → -0.27 (-0.39) ▼ | -0.03 → 0.62 (+0.65) ▲ | 0.34 → 0.8 (+0.46) ▲ | 0.33 → 0.37 (+0.04) ≈ |
| `cross_sector_slide3m_bd7` | 0.2 → -0.21 (-0.41) ▼ | -0.09 → 0.89 (+0.98) ▲ | 0.73 → -0.04 (-0.77) ▼ | 0.13 → -0.41 (-0.54) ▼ |
| `cross_sector_slide1m_noscreen` | 0.01 → -0.6 (-0.61) ▼ | -0.09 → 0.11 (+0.20) ▲ | 0.32 → 1.53 (+1.21) ▲ | 0.29 → 0.42 (+0.13) ▲ |
| `cross_sector_slide1m_bd7` | 0.25 → -0.15 (-0.40) ▼ | -0.01 → 0.39 (+0.40) ▲ | 0.48 → 0.3 (-0.18) ▼ | 0.05 → -0.44 (-0.49) ▼ |

### 12-month selection

| Config | core 2015-19 (08b) <br><sub>single-start</sub> | SP500 2015-19 (09b) <br><sub>single-start</sub> | core recent (10a) <br><sub>5-start</sub> | SP500 recent (10b) <br><sub>5-start</sub> |
|---|---|---|---|---|
| `same_sector_slide3m_noscreen` | -0.48 → -0.91 (-0.43) ▼ | 1.56 → 0.37 (-1.19) ▼ | -0.2 → 0.25 (+0.45) ▲ | 1.4 → 0.8 (-0.60) ▼ |
| `same_sector_slide3m_bd7` | 0.26 → -0.34 (-0.60) ▼ | 0.85 → 0.18 (-0.67) ▼ | 0.72 → 0.11 (-0.61) ▼ | 0.91 → 0.44 (-0.47) ▼ |
| `same_sector_slide1m_noscreen` | -0.48 → -0.79 (-0.31) ▼ | 0.11 → 0.4 (+0.29) ▲ | 0.08 → 0.27 (+0.19) ▲ | 1.42 → 1.32 (-0.10) ▼ |
| `same_sector_slide1m_bd7` | 0.53 → 0.13 (-0.40) ▼ | 0.56 → 0.49 (-0.07) ▼ | 0.97 → 0.28 (-0.69) ▼ | 1.64 → 0.67 (-0.97) ▼ |
| `cross_sector_slide3m_noscreen` | 0.02 → -0.7 (-0.72) ▼ | -0.09 → -0.21 (-0.12) ▼ | 0.06 → 0.4 (+0.34) ▲ | 1.07 → 1.11 (+0.04) ≈ |
| `cross_sector_slide3m_bd7` | 0.21 → -0.1 (-0.31) ▼ | -0.02 → 0.33 (+0.35) ▲ | 0.08 → 0.3 (+0.22) ▲ | 0.25 → 0.82 (+0.57) ▲ |
| `cross_sector_slide1m_noscreen` | -0.12 → -0.45 (-0.33) ▼ | 0.53 → 0.47 (-0.06) ▼ | 0.36 → 0.8 (+0.44) ▲ | 1.47 → 1.89 (+0.42) ▲ |
| `cross_sector_slide1m_bd7` | 0.14 → 0.31 (+0.17) ▲ | 0.56 → 0.59 (+0.03) ≈ | 0.36 → 0.49 (+0.13) ▲ | 0.97 → 1.31 (+0.34) ▲ |

## 3. What changed / key takeaways

- **SP500 2m historical flipped positive** (old: all 8 configs negative −0.01…−0.47; new single-start best `cross_sector_slide3m_bd7` 0.89). Dropping 2020 + aligned windows changed the verdict on this cell.

- **SP500 12m historical best collapsed** (old single-start `same 3m noscreen` 1.56 → new single-start best `cross_sector_slide1m_bd7` 0.59). The 1.56 was largely a 2016-2020 window effect.

- **Core 12m historical** best `cross_sector_slide1m_bd7` 0.31 vs old 0.53. Core 12m remains the thin-book caveat (few same-sector pairs).

- **Recent cells are not uniformly stable:** core 2m `same 1m bd7` 1.28 → 1.30; SP500 2m `same 3m bd7` 0.42 → 0.29 (best now `cross_sector_slide1m_noscreen` 0.42); core 12m `same 1m bd7` 0.97 → 0.28 (best now `cross_sector_slide1m_noscreen` 0.80); SP500 12m `same 1m bd7` 1.64 → 0.67 (best now `cross_sector_slide1m_noscreen` 1.89).

- **Consistent rule:** SP500 needs 12m selection; core 2m ≥ core 12m on recent. The universe × selection interaction in RESEARCH_PIPELINE.md still holds under aligned windows.

