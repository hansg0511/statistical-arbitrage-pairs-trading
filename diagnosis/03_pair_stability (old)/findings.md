# Pair Selection Stability Analysis

**Profile:** baseline (same_sector, sel=2m, slide=3m, test=3m, log_space=True)

**Grid:** 5 start dates × 7 folds

**Generated:** 2026-07-28 02:13

## Per-Fold Metrics

| Fold | Pairs/fold | Dates | Jacc@5 | Jacc@10 | Jacc@20 | Jacc@50 | Dropout | RankVol | Spearman | SectorVol |
|------|-----------|-------|--------|---------|---------|---------|---------|---------|----------|-----------|
| 0 | 15 | 5 | 0.044 | 0.037 | 0.063 | 0.065 | 0.92 | 8.4 | 0.0 | 0.153 |
| 1 | 14 | 5 | 0.011 | 0.022 | 0.029 | 0.046 | 0.98 | 8.6 | 0.0 | 0.198 |
| 2 | 20 | 5 | 0.022 | 0.027 | 0.081 | 0.09 | 0.96 | 6.6 | 0.0 | 0.154 |
| 3 | 19 | 5 | 0.043 | 0.034 | 0.055 | 0.065 | 0.94 | 4.9 | 0.0 | 0.175 |
| 4 | 14 | 5 | 0.022 | 0.05 | 0.071 | 0.07 | 0.96 | 5.7 | 0.0 | 0.154 |
| 5 | 43 | 5 | 0.058 | 0.064 | 0.099 | 0.134 | 0.9 | 10.9 | 0.404 | 0.145 |
| 6 | 24 | 5 | 0.054 | 0.06 | 0.069 | 0.089 | 0.92 | 5.6 | 0.448 | 0.165 |

## Aggregate Summary

| Metric | Mean | Min | Max |
|--------|------|-----|-----|
| Jaccard@5 | 0.036 | 0.011 | 0.058 |
| Jaccard@10 | 0.042 | 0.022 | 0.064 |
| Jaccard@20 | 0.067 | 0.029 | 0.099 |
| Jaccard@50 | 0.080 | 0.046 | 0.134 |
| Dropout Rate | 0.940 | 0.900 | 0.980 |
| Rank Volatility | 7.243 | 4.900 | 10.900 |
| Spearman ρ | 0.122 | 0.000 | 0.448 |
| Sector Concentration Vol | 0.163 | 0.145 | 0.198 |

## Interpretation

- **Jaccard@5 ≈ 0.04**: On average, only ~0 of ~9 unique top-5 pairs are shared between two start dates. The rest are completely different.
- **Dropout rate ≈ 0.94**: ~94% of top-5 pairs in one start date vanish from top-5 in another.
- **Rank volatility ≈ 7**: Pairs shift ~7 rank positions on average between start dates.
- **Spearman ρ ≈ 0.12**: Weak rank correlation even among shared pairs.

## Root Cause: Small Pool Size

This is the core finding of the entire investigation. The instability is **not** driven by earnings timing or stop-loss mechanics — it's driven by the **tiny candidate pool under same_sector constraints**.

**Compare with notebook 06 (golden, cross_sector, sel=2m):**
| Metric | Baseline (same_sector) | Golden (cross_sector) |
|--------|----------------------|----------------------|
| Candidate pool | ~20 pairs/fold | ~180 pairs/fold |
| Rank volatility | 7.2 (36% of pool) | 68.6 (3% of pool) |
| Jaccard@5 | 0.04 | 0.28–0.47 |
| Dropout rate | 94% | ~50% |

The golden profile has **9x more candidates** (2,211 vs 251 total). With 180+ cointegrated pairs to choose from, rank movements of 68 positions barely scratch the top-5. Our 20-pair pool means a rank shift of 7 completely replaces the top-5.

This explains why the earnings screen failed to fix stability — it was treating symptoms, not the cause. The fundamental issue is that same_sector cointegration produces too few viable pairs, and any small price change in the 2-month selection window radically reshuffles the ranking.

**Implication:** To get stable pair selection, we need to either:
1. **Enlarge the pool** — use cross-sector (golden profile), which has 9x more candidates
2. **Lengthen the selection window** — sel=6m stabilizes rankings (notebook 06 shows rank volatility drops from 68.6 to 39.0, and relative improvement would be larger here)
3. **Use a different selection metric** — less sensitive to small price changes than cointegration p-value

The instability is an inherent property of the same_sector constraint, not a parameter that can be tuned away.

## Where These Results Live

```
diagnosis/03_pair_stability/
├── findings.md
├── stability_metrics_per_fold.csv
├── compute_stability.py
├── 2023-12-01/
│   ├── pair_ranking_fold0.csv  (15 pairs)
│   ├── pair_ranking_fold1.csv  (25 pairs)
│   └── ... fold2-6
├── 2023-12-15/
├── 2024-01-01/
├── 2024-01-15/
└── 2024-02-01/
```
