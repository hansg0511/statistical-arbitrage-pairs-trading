# Momentum-param sensitivity & Fama-French — 6 survivor pairs

Pairs are the top-20 in all three ranking methods (min/rank-avg/joined), both mechanisms. pct=0.25, capital $1M.

## Task 1 — Momentum-param sensitivity (not re-optimization)

Combined daily-return series via the trade-event replay. `recent` = mean Sharpe over the 5 aligned start-pairs; `hist` = single aligned window. Schemes: default (step 10%, bounds 25-75%), step5, step15, bd20_80 (bounds 20-80%), bd35_65 (bounds 35-65%), static (no switching; w_A = Sh_A/(Sh_A+Sh_B)). lookback fixed at 63d.

### Mechanism A

| Pair | rec: default | rec: step5 | rec: step15 | rec: bd20_80 | rec: bd35_65 | rec: static | hist: default | hist: step5 | hist: step15 | hist: bd20_80 | hist: bd35_65 | hist: static |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen` | 1.06 | 1.13 | 1.09 | 1.02 | 1.19 | 1.59 | 0.58 | 0.45 | 0.70 | 0.56 | 0.64 | 0.46 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7` | 0.83 | 0.78 | 0.86 | 0.83 | 0.81 | 1.33 | 1.14 | 1.11 | 1.14 | 1.17 | 1.05 | 0.92 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_noscreen` | 0.91 | 0.84 | 0.90 | 0.87 | 0.93 | 1.33 | 0.67 | 0.72 | 0.62 | 0.69 | 0.66 | 0.68 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/same_sector_slide1m_noscreen` | 1.09 | 1.05 | 1.09 | 1.05 | 1.12 | 1.37 | 0.49 | 0.47 | 0.53 | 0.46 | 0.51 | 0.45 |
| `sp500-12m/same_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen` | 1.14 | 1.16 | 1.11 | 1.15 | 1.11 | 1.36 | 0.56 | 0.49 | 0.56 | 0.58 | 0.48 | 0.37 |
| `sp500-12m/same_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7` | 0.87 | 0.86 | 0.81 | 0.92 | 0.75 | 1.31 | 0.81 | 0.81 | 0.80 | 0.82 | 0.81 | 0.90 |

### Mechanism B

| Pair | rec: default | rec: step5 | rec: step15 | rec: bd20_80 | rec: bd35_65 | rec: static | hist: default | hist: step5 | hist: step15 | hist: bd20_80 | hist: bd35_65 | hist: static |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen` | 1.04 | 1.09 | 1.08 | 1.01 | 1.16 | 1.50 | 0.53 | 0.40 | 0.65 | 0.51 | 0.60 | 0.42 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7` | 0.82 | 0.75 | 0.87 | 0.82 | 0.78 | 1.12 | 1.09 | 1.06 | 1.10 | 1.13 | 1.01 | 0.90 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_noscreen` | 0.90 | 0.82 | 0.90 | 0.87 | 0.91 | 1.21 | 0.65 | 0.69 | 0.59 | 0.67 | 0.63 | 0.67 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/same_sector_slide1m_noscreen` | 0.92 | 0.86 | 0.92 | 0.89 | 0.91 | 1.17 | 0.54 | 0.50 | 0.59 | 0.50 | 0.56 | 0.45 |
| `sp500-12m/same_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen` | 1.08 | 1.10 | 1.05 | 1.09 | 1.05 | 1.27 | 0.60 | 0.53 | 0.60 | 0.62 | 0.51 | 0.39 |
| `sp500-12m/same_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7` | 0.83 | 0.83 | 0.77 | 0.88 | 0.71 | 1.22 | 0.87 | 0.87 | 0.86 | 0.88 | 0.86 | 0.91 |

## Task 2 — Fama-French (FF3 + Mom + ST_Rev, daily, HAC)

Combined daily-return series with the default momentum config (step 10%, bounds 25-75%), mechanisms A and B, start-pair 0. Alpha annualized x252; HAC standard errors. **Values in brackets are p-values** (the probability the true loading is zero; p < 0.05 conventionally indicates significance at the 5% level).

| Pair | Window | Mech | Alpha% | Mkt-RF | SMB | HML | Mom | ST_Rev | R2 | N |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen` | historical | A | +1.65% (0.646) | 0.08 (0.000) | -0.05 (0.121) | 0.01 (0.784) | 0.01 (0.673) | 0.12 (0.003) | 0.052 | 1256 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen` | historical | B | +1.25% (0.727) | 0.08 (0.000) | -0.05 (0.132) | 0.01 (0.769) | 0.01 (0.631) | 0.12 (0.002) | 0.053 | 1256 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen` | recent | A | +5.56% (0.370) | 0.11 (0.127) | -0.02 (0.776) | -0.06 (0.285) | -0.04 (0.513) | 0.15 (0.014) | 0.086 | 495 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen` | recent | B | +6.01% (0.331) | 0.12 (0.117) | -0.02 (0.755) | -0.06 (0.245) | -0.04 (0.463) | 0.15 (0.012) | 0.090 | 495 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7` | historical | A | +5.71% (0.074) | 0.04 (0.209) | -0.06 (0.185) | -0.04 (0.149) | 0.01 (0.570) | 0.08 (0.026) | 0.028 | 1255 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7` | historical | B | +5.37% (0.093) | 0.04 (0.215) | -0.06 (0.195) | -0.04 (0.151) | 0.02 (0.518) | 0.09 (0.023) | 0.029 | 1255 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7` | recent | A | -5.05% (0.290) | 0.19 (0.016) | -0.13 (0.064) | -0.04 (0.325) | -0.05 (0.357) | 0.12 (0.047) | 0.188 | 487 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7` | recent | B | -4.27% (0.372) | 0.19 (0.015) | -0.13 (0.061) | -0.05 (0.265) | -0.05 (0.334) | 0.12 (0.040) | 0.194 | 487 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_noscreen` | historical | A | +3.55% (0.352) | 0.06 (0.036) | -0.06 (0.130) | -0.02 (0.692) | 0.02 (0.515) | 0.06 (0.169) | 0.017 | 1256 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_noscreen` | historical | B | +3.37% (0.383) | 0.06 (0.038) | -0.06 (0.126) | -0.01 (0.709) | 0.02 (0.451) | 0.06 (0.146) | 0.018 | 1256 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_noscreen` | recent | A | -7.99% (0.214) | 0.24 (0.008) | -0.13 (0.072) | 0.02 (0.748) | -0.04 (0.547) | 0.16 (0.018) | 0.168 | 489 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_noscreen` | recent | B | -7.14% (0.268) | 0.24 (0.007) | -0.13 (0.070) | 0.01 (0.821) | -0.04 (0.527) | 0.16 (0.015) | 0.169 | 489 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/same_sector_slide1m_noscreen` | historical | A | +0.26% (0.923) | 0.08 (0.000) | -0.04 (0.093) | 0.01 (0.788) | 0.02 (0.309) | 0.11 (0.000) | 0.074 | 1257 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/same_sector_slide1m_noscreen` | historical | B | +0.56% (0.838) | 0.08 (0.000) | -0.04 (0.081) | 0.00 (0.865) | 0.01 (0.393) | 0.11 (0.000) | 0.073 | 1257 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/same_sector_slide1m_noscreen` | recent | A | +0.60% (0.901) | 0.16 (0.024) | -0.05 (0.397) | -0.02 (0.583) | -0.02 (0.701) | 0.12 (0.021) | 0.150 | 501 |
| `sp500-12m/cross_sector_slide1m_noscreen + sp500-2m/same_sector_slide1m_noscreen` | recent | B | +2.02% (0.695) | 0.16 (0.023) | -0.05 (0.431) | -0.03 (0.450) | -0.02 (0.690) | 0.13 (0.017) | 0.151 | 501 |
| `sp500-12m/same_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen` | historical | A | +1.42% (0.712) | 0.10 (0.000) | -0.06 (0.093) | -0.01 (0.854) | 0.02 (0.363) | 0.14 (0.000) | 0.063 | 1247 |
| `sp500-12m/same_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen` | historical | B | +1.71% (0.654) | 0.10 (0.000) | -0.06 (0.083) | -0.01 (0.839) | 0.02 (0.418) | 0.14 (0.000) | 0.066 | 1247 |
| `sp500-12m/same_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen` | recent | A | +5.88% (0.398) | 0.14 (0.167) | -0.08 (0.368) | -0.12 (0.047) | -0.04 (0.575) | 0.22 (0.002) | 0.134 | 494 |
| `sp500-12m/same_sector_slide1m_noscreen + sp500-12m/same_sector_slide3m_noscreen` | recent | B | +6.43% (0.369) | 0.15 (0.150) | -0.09 (0.321) | -0.11 (0.060) | -0.05 (0.494) | 0.22 (0.002) | 0.129 | 494 |
| `sp500-12m/same_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7` | historical | A | +2.95% (0.355) | 0.06 (0.054) | -0.06 (0.157) | -0.04 (0.108) | 0.02 (0.333) | 0.11 (0.002) | 0.049 | 1253 |
| `sp500-12m/same_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7` | historical | B | +3.29% (0.295) | 0.06 (0.047) | -0.06 (0.138) | -0.04 (0.103) | 0.02 (0.379) | 0.11 (0.002) | 0.051 | 1253 |
| `sp500-12m/same_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7` | recent | A | -3.26% (0.471) | 0.20 (0.070) | -0.16 (0.078) | -0.12 (0.009) | -0.07 (0.343) | 0.21 (0.004) | 0.268 | 494 |
| `sp500-12m/same_sector_slide1m_noscreen + sp500-2m/cross_sector_slide3m_bd7` | recent | B | -2.41% (0.600) | 0.20 (0.061) | -0.17 (0.066) | -0.12 (0.013) | -0.08 (0.287) | 0.21 (0.003) | 0.266 | 494 |

## Data-quality notes

1. **Earnings-screen cache bug (found & fixed 2026-08).** Every sp500 section (07/09a/09b/10b) was routed to `research/earnings_cache/earnings_dates_sp500.pkl`, which held only 2023-01..2025-06 dates, while `research/earnings_cache/earnings_dates.pkl` - same 503 tickers, full 2013-2026 coverage - sat alongside unused. Consequences: historical sp500 bd7 configs screened **nothing** (09b same3m: 560 bd7 trades == 560 noscreen), and recent sp500 sections went unscreened after Jun-2025. Core sections used the complete cache and screened correctly all along (08b: 176 -> 96 trades). Fix: truncated cache deleted, all sp500 sections repointed to the complete cache, sections 07/09a/09b/10b re-run. Post-fix 09b same3m screens ~46% of entries (bd7=311 vs noscreen=579). No yfinance fetching occurs: every ticker is already cached.

2. **Pairs 2 & 4 rendered identically pre-fix — explained by note 1.** Both pairs share the sp500-2m leg and differ only in the sp500-12m leg screen (bd7 vs noscreen); with the screen silent their historical legs had identical trade sets, so the combined books were near-duplicates (FF stats agreed to the 12th decimal; md rounding made rows byte-identical). Post-fix the two legs carry different trade sets and the pairs are genuinely distinct.

3. **Mechanism A and B are now exposure-comparable after the B sizing fix.** Both mechanisms compute daily returns identically as (C - C_prev)/C_prev on total book value. Mech A re-bases entry basis monthly to `w_L * C / n_active_L`; mech B locks an unweighted basis at fold start using `C / n_active_L` and applies the current weight only to new entry flow. The first-entry gross deployment therefore matches at equal weights and active-fold counts; remaining differences reflect monthly re-basing versus locked entry sizing. Compare alpha and risk with both exposure and timing in mind.

4. **Runtime return-divergence re-filter removed (2026-08).** The pool cache (sp500_2m.pkl) is seeded with return-divergence already applied (research/seed_2m3m.py, DIVERGENCE=0.10), but run_backtest_parallel.py ALSO re-applied the filter at runtime against freshly-fetched yfinance prices. On a rate-limited/partial fetch (~80 tickers missing, e.g. 2026-08-24), that re-filter silently dropped ~30% of already-valid pairs and reshuffled top-20 selection - producing a spurious 1.20 historical Sharpe (09a cross3m noscreen) that is not reproducible. Fix: pool-backed runs now skip the runtime re-filter (selection is deterministic and cache-driven); DataLoader now retries rate-limited fetches and aborts loudly if <95% of tickers return. After the fix that config re-runs to Sharpe 0.57 / 529 trades (its true value), and all sp500 sections were rebuilt on deterministic selection.

