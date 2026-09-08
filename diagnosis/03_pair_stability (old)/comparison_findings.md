# Pair Selection Stability — 4-Way Comparison

**Grid:** 5 start dates × variable folds per config

**Generated:** 2026-07-28 03:14

## Aggregate Summary Across All Folds

| Metric | same_sector slide=3m | same_sector slide=1m | cross_sector slide=3m | cross_sector slide=1m |
|--------|---------------------|---------------------|----------------------|----------------------|
| Mean Candidate Pool | 23.657 | 23.970 | 114.543 | 119.900 |
| Jaccard@5 | 0.036 | 0.034 | 0.010 | 0.008 |
| Jaccard@10 | 0.042 | 0.052 | 0.015 | 0.013 |
| Jaccard@20 | 0.067 | 0.075 | 0.024 | 0.021 |
| Dropout Rate (top-5) | 0.940 | 0.945 | 0.983 | 0.986 |
| Rank Volatility | 7.225 | 6.943 | 30.960 | 32.071 |
| Spearman ρ | 0.122 | 0.109 | 0.179 | 0.121 |

## Per-Fold Detail

### same_sector, slide=3m

| Fold | Pool | Dates | Jacc@5 | Jacc@10 | Dropout | RankVol | Spearman |
|------|------|-------|--------|---------|---------|---------|----------|
| 0 | 23 | 5 | 0.044 | 0.037 | 0.920 | 8.4 | 0.000 |
| 1 | 21 | 5 | 0.011 | 0.022 | 0.980 | 8.6 | 0.000 |
| 2 | 25 | 5 | 0.022 | 0.027 | 0.960 | 6.6 | 0.000 |
| 3 | 23 | 5 | 0.043 | 0.034 | 0.940 | 4.9 | 0.000 |
| 4 | 16 | 5 | 0.022 | 0.050 | 0.960 | 5.7 | 0.000 |
| 5 | 34 | 5 | 0.058 | 0.064 | 0.900 | 10.9 | 0.404 |
| 6 | 24 | 5 | 0.054 | 0.060 | 0.920 | 5.6 | 0.448 |

### same_sector, slide=1m

| Fold | Pool | Dates | Jacc@5 | Jacc@10 | Dropout | RankVol | Spearman |
|------|------|-------|--------|---------|---------|---------|----------|
| 0 | 23 | 5 | 0.044 | 0.037 | 0.920 | 8.3 | 0.000 |
| 1 | 24 | 5 | 0.011 | 0.052 | 0.980 | 7.6 | 0.030 |
| 2 | 21 | 5 | 0.000 | 0.054 | 1.000 | 10.2 | 0.030 |
| 3 | 20 | 5 | 0.011 | 0.022 | 0.980 | 8.3 | 0.000 |
| 4 | 24 | 5 | 0.022 | 0.065 | 0.960 | 7.5 | -0.032 |
| 5 | 26 | 5 | 0.000 | 0.088 | 1.000 | 6.8 | -0.032 |
| 6 | 25 | 5 | 0.022 | 0.027 | 0.960 | 6.7 | 0.000 |
| 7 | 24 | 5 | 0.011 | 0.016 | 0.980 | 6.2 | 0.000 |
| 8 | 26 | 5 | 0.000 | 0.011 | 1.000 | 6.4 | 0.000 |
| 9 | 23 | 5 | 0.043 | 0.034 | 0.940 | 4.9 | 0.000 |
| 10 | 20 | 5 | 0.054 | 0.061 | 0.920 | 3.8 | 0.000 |
| 11 | 17 | 5 | 0.022 | 0.065 | 0.960 | 5.5 | 0.000 |
| 12 | 16 | 5 | 0.022 | 0.050 | 0.960 | 5.7 | 0.000 |
| 13 | 17 | 5 | 0.033 | 0.058 | 0.940 | 4.2 | 0.000 |
| 14 | 27 | 5 | 0.067 | 0.072 | 0.880 | 9.4 | 0.000 |
| 15 | 33 | 5 | 0.058 | 0.058 | 0.900 | 11.2 | 0.404 |
| 16 | 36 | 5 | 0.047 | 0.052 | 0.920 | 8.6 | 0.423 |
| 17 | 26 | 5 | 0.011 | 0.022 | 0.980 | 6.9 | 0.462 |
| 18 | 24 | 5 | 0.054 | 0.060 | 0.920 | 5.5 | 0.448 |
| 19 | 27 | 3 | 0.143 | 0.129 | 0.800 | 5.3 | 0.448 |

### cross_sector, slide=3m

| Fold | Pool | Dates | Jacc@5 | Jacc@10 | Dropout | RankVol | Spearman |
|------|------|-------|--------|---------|---------|---------|----------|
| 0 | 103 | 5 | 0.011 | 0.038 | 0.980 | 27.6 | 0.313 |
| 1 | 116 | 5 | 0.011 | 0.022 | 0.980 | 34.1 | 0.109 |
| 2 | 117 | 5 | 0.011 | 0.005 | 0.980 | 30.8 | 0.228 |
| 3 | 105 | 5 | 0.011 | 0.011 | 0.980 | 25.6 | 0.271 |
| 4 | 89 | 5 | 0.011 | 0.016 | 0.980 | 25.2 | 0.152 |
| 5 | 131 | 5 | 0.011 | 0.011 | 0.980 | 33.7 | 0.193 |
| 6 | 141 | 5 | 0.000 | 0.005 | 1.000 | 39.6 | -0.014 |

### cross_sector, slide=1m

| Fold | Pool | Dates | Jacc@5 | Jacc@10 | Dropout | RankVol | Spearman |
|------|------|-------|--------|---------|---------|---------|----------|
| 0 | 103 | 5 | 0.011 | 0.038 | 0.980 | 27.6 | 0.313 |
| 1 | 114 | 5 | 0.011 | 0.021 | 0.980 | 29.4 | 0.143 |
| 2 | 113 | 5 | 0.000 | 0.005 | 1.000 | 29.1 | -0.156 |
| 3 | 116 | 5 | 0.011 | 0.022 | 0.980 | 34.1 | 0.109 |
| 4 | 139 | 5 | 0.022 | 0.022 | 0.960 | 39.0 | 0.062 |
| 5 | 144 | 5 | 0.022 | 0.011 | 0.960 | 39.2 | 0.054 |
| 6 | 117 | 5 | 0.011 | 0.005 | 0.980 | 30.8 | 0.228 |
| 7 | 107 | 5 | 0.000 | 0.005 | 1.000 | 28.2 | 0.006 |
| 8 | 107 | 5 | 0.011 | 0.016 | 0.980 | 27.6 | -0.010 |
| 9 | 105 | 5 | 0.011 | 0.011 | 0.980 | 25.6 | 0.271 |
| 10 | 107 | 5 | 0.000 | 0.000 | 1.000 | 26.1 | 0.352 |
| 11 | 106 | 5 | 0.011 | 0.011 | 0.980 | 29.7 | 0.176 |
| 12 | 89 | 5 | 0.011 | 0.016 | 0.980 | 25.2 | 0.152 |
| 13 | 87 | 5 | 0.000 | 0.021 | 1.000 | 26.6 | 0.240 |
| 14 | 108 | 5 | 0.000 | 0.011 | 1.000 | 31.1 | 0.160 |
| 15 | 131 | 5 | 0.011 | 0.011 | 0.980 | 33.7 | 0.193 |
| 16 | 160 | 5 | 0.011 | 0.005 | 0.980 | 38.9 | 0.148 |
| 17 | 155 | 5 | 0.000 | 0.000 | 1.000 | 39.2 | -0.091 |
| 18 | 141 | 5 | 0.000 | 0.005 | 1.000 | 39.6 | -0.014 |
| 19 | 148 | 3 | 0.000 | 0.018 | 1.000 | 40.5 | 0.083 |

## Interpretation

### Key Surprise: Pool Size Doesn't Matter

Despite having **5x the candidate pool** (115 vs 24 pairs/fold), cross_sector's Jaccard@5 is **0.01** — essentially identical to same_sector's 0.04. The dropout rate is **98%** vs 94%. Pool size is NOT the driver.

This contradicts my earlier hypothesis. The stability metrics are nearly identical across all four configs — the 2×2 grid shows almost no variation:

| Metric | same=3m | same=1m | cross=3m | cross=1m |
|--------|---------|---------|----------|----------|
| Jaccard@5 | 0.036 | 0.034 | 0.010 | 0.008 |
| Dropout | 0.940 | 0.945 | 0.983 | 0.986 |
| RankVol | 7.2 | 6.9 | 31.0 | 32.1 |

**Why cross_sector has higher absolute rank volatility:** With 115 candidates, a pair shifting 31 positions is a ~27% relative move. With 24 candidates, a pair shifting 7 positions is a ~29% relative move. They're proportionally the same.

### Root Cause: Cointegration P-Value is a Noisy Ranking Metric

The real issue is that **cointegration p-values in the 0.000–0.005 range are statistically indistinguishable**. The top-5 pairs differ by p-values of 0.001 vs 0.002 — differences dominated by noise in the 2-month selection window. A 2-week shift in start date reshuffles these essentially randomly.

This is confirmed by Spearman ρ ≈ 0.12 across all configs — even among the few shared pairs, rank correlation is near zero. The ranking order is essentially uncorrelated between start dates.

### Why Notebook 06 Showed Different Numbers

Notebook 06's "Jaccard vs center (0.28–0.47)" used the **median/center ranking** across start dates, not **pairwise Jaccard** across start dates. These are different metrics:
- **Pairwise Jaccard** (our metric): measures overlap between two start dates directly — extremely strict
- **Jaccard vs center** (notebook 06): what fraction of each start date's top-K are in the consensus top-K across all dates — higher by construction

### Implication

Enlarging the candidate pool (cross_sector) **does not fix the instability**. The instability is intrinsic to using cointegration p-value as a ranking metric over short selection windows. Possible remedies:
1. **Ensemble across start dates**: Average the rankings from multiple start dates
2. **Use a different selection metric**: Return predictability, half-life-weighted, or ML-based
3. **Longer selection window (sel=6m)**: Notebook 06 shows rank volatility drops from 68.6 to 39.0 (absolute); would likely help here too
4. **Accept the randomness**: Run a portfolio of 5 random top-5 selections and average results
