# Multi-start Fama-French (FF3 + Mom + ST_Rev, daily, HAC) — pair `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7`

Combined daily-return series via the trade-event replay, default momentum config (step 10%, bounds 25-75%). Historical = single window (2015-2019). Recent = each of the 5 aligned start-pairs (all trading strictly 2024-2025). Alpha annualized x252; HAC standard errors. **Values in brackets are p-values**.

| Window | Start | Mech | Alpha% | Mkt-RF | SMB | HML | Mom | ST_Rev | Sharpe | R2 | N |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| historical | 0 | A | +5.71% (0.074) | 0.04 (0.209) | -0.06 (0.185) | -0.04 (0.149) | 0.01 (0.570) | 0.08 (0.026) | 1.14 | 0.028 | 1255 |
| recent | 0 | A | -5.05% (0.290) | 0.19 (0.016) | -0.13 (0.064) | -0.04 (0.325) | -0.05 (0.357) | 0.12 (0.047) | 0.52 | 0.188 | 487 |
| recent | 1 | A | -4.44% (0.301) | 0.16 (0.017) | -0.10 (0.068) | -0.05 (0.132) | -0.03 (0.491) | 0.12 (0.009) | 0.61 | 0.220 | 469 |
| recent | 2 | A | -1.65% (0.723) | 0.20 (0.014) | -0.15 (0.029) | -0.00 (0.945) | -0.06 (0.293) | 0.14 (0.010) | 1.04 | 0.259 | 444 |
| recent | 3 | A | -2.76% (0.604) | 0.19 (0.021) | -0.16 (0.028) | -0.05 (0.262) | -0.03 (0.574) | 0.15 (0.009) | 0.83 | 0.244 | 425 |
| recent | 4 | A | -0.92% (0.853) | 0.18 (0.007) | -0.12 (0.041) | -0.03 (0.360) | -0.04 (0.439) | 0.13 (0.008) | 1.12 | 0.243 | 407 |
| historical | 0 | B | +5.37% (0.093) | 0.04 (0.215) | -0.06 (0.195) | -0.04 (0.151) | 0.02 (0.518) | 0.09 (0.023) | 1.09 | 0.029 | 1255 |
| recent | 0 | B | -4.27% (0.372) | 0.19 (0.015) | -0.13 (0.061) | -0.05 (0.265) | -0.05 (0.334) | 0.12 (0.040) | 0.61 | 0.194 | 487 |
| recent | 1 | B | -4.86% (0.268) | 0.17 (0.016) | -0.10 (0.069) | -0.05 (0.123) | -0.03 (0.531) | 0.13 (0.008) | 0.56 | 0.222 | 469 |
| recent | 2 | B | -3.14% (0.520) | 0.20 (0.012) | -0.15 (0.031) | 0.00 (0.966) | -0.06 (0.310) | 0.14 (0.009) | 0.85 | 0.254 | 444 |
| recent | 3 | B | -2.76% (0.619) | 0.19 (0.019) | -0.16 (0.026) | -0.04 (0.331) | -0.03 (0.616) | 0.16 (0.007) | 0.82 | 0.236 | 425 |
| recent | 4 | B | +0.04% (0.994) | 0.18 (0.007) | -0.11 (0.044) | -0.03 (0.302) | -0.04 (0.474) | 0.13 (0.008) | 1.25 | 0.246 | 407 |

## Recent alpha across the 5 starts (per mechanism)

| Mech | hist alpha | recent mean | recent min | recent max | # positive | # p<0.05 |
|---|---:|---:|---:|---:|---:|---:|
| A | +5.71% | -2.96% | -5.05% | -0.92% | 0 | 0 |
| B | +5.37% | -3.00% | -4.86% | +0.04% | 1 | 0 |

Caveat: alphas are annualized point estimates; with ~400-500 recent obs and HAC errors, p<0.05 is a high bar. The recent sign is informative only if it is consistent across starts.

