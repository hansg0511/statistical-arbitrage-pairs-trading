# Old Winner V1/V2 Sizing Autopsy

This focused diagnostic replays only the locked old winner:
`sp500-12m/cross_sector_slide1m_noscreen` plus
`sp500-2m/cross_sector_slide3m_bd7`. It reads the preserved raw V1
reference-leg and V2 gross-exposure runs and does not modify canonical
research outputs.

Allocator parameters: 84-day causal lookback, step 0.40, bounds
0.10--0.90, initial A weight 0.50. Recent metrics are means across the
five preserved recent starts; historical has one start.

## Headline Reproduction

Metrics are annualized return / volatility / Sharpe / max drawdown.

| Window | Mechanism | V1 Case 1 | V2 Case 2 | V2 minus V1 Sharpe |
|---|---|---|---|---:|
| recent | A | 9.45% / 8.60% / 1.094 / -5.54% | 1.92% / 5.38% / 0.372 / -4.95% | -0.721 |
| recent | B | 9.81% / 8.53% / 1.141 / -5.55% | 2.14% / 5.36% / 0.415 / -4.94% | -0.726 |
| historical | A | 9.10% / 8.05% / 1.122 / -8.95% | 4.04% / 3.95% / 1.023 / -4.99% | -0.100 |
| historical | B | 8.83% / 8.01% / 1.096 / -8.87% | 3.91% / 3.94% / 0.993 / -4.97% | -0.103 |

The V1 and V2 Case 1/2 rows match the existing old-winner summary
with validation status **pass**.

## Allocator Path

| Window | Rebalance months | Same direction | Flips | Mean abs A-weight difference | Max difference | Different weights |
|---|---:|---:|---:|---:|---:|---:|
| recent | 110 | 95 | 15 | 0.065 | 0.800 | 13.6% |
| historical | 60 | 56 | 4 | 0.027 | 0.400 | 6.7% |

The complete monthly path, including both trailing Sharpe inputs and
weights, is in `results/old_winner_v1_v2_autopsy/allocator_path.csv`.

## Hedge-Ratio Diagnostics

The `pair_level` rows classify trades by normalized trade-PnL sign and
use raw standalone dollar PnL for the pair-sizing view. Mechanism A/B
rows use their actual replay allocation for combined-book contribution.
V1 actual gross exposure is reconstructed from the preserved V1
reference-leg sizing formula using the matched V2 entry prices; the
pre-rescaling dollar PnL fields are the raw standalone trade PnL.

| Window | Mechanism | Outcome | Trades | Avg abs HR | Avg V1/V2 gross ratio | V1 contribution | V2 contribution | Difference |
|---|---|---|---:|---:|---:|---:|---:|---:|
| recent | pair_level | winning trade | 1593 | 0.855 | 1.856 | $15,943,624 | $8,677,219 | $7,266,405 |
| recent | pair_level | losing trade | 1335 | 0.780 | 1.781 | $-12,064,080 | $-6,829,038 | $-5,235,042 |
| recent | A | winning trade | 1593 | 0.855 | 1.856 | $4,066,721 | $1,971,181 | $2,095,540 |
| recent | A | losing trade | 1335 | 0.780 | 1.781 | $-3,200,810 | $-1,798,292 | $-1,402,518 |
| recent | B | winning trade | 1593 | 0.855 | 1.856 | $4,041,803 | $1,970,737 | $2,071,066 |
| recent | B | losing trade | 1335 | 0.780 | 1.781 | $-3,141,649 | $-1,777,706 | $-1,363,943 |
| historical | pair_level | winning trade | 918 | 0.885 | 1.885 | $7,136,348 | $3,831,967 | $3,304,381 |
| historical | pair_level | losing trade | 750 | 0.882 | 1.882 | $-6,256,593 | $-3,386,164 | $-2,870,428 |
| historical | A | winning trade | 918 | 0.885 | 1.885 | $2,192,822 | $1,005,947 | $1,186,875 |
| historical | A | losing trade | 750 | 0.882 | 1.882 | $-1,648,333 | $-787,139 | $-861,195 |
| historical | B | winning trade | 918 | 0.885 | 1.885 | $2,166,987 | $995,665 | $1,171,322 |
| historical | B | losing trade | 750 | 0.882 | 1.882 | $-1,641,238 | $-784,580 | $-856,658 |

Recent HR correlations:

| Mechanism | HR vs PnL sign | HR vs V1 contribution | HR vs V1-minus-V2 contribution |
|---|---:|---:|---:|
| A | 0.081 | 0.100 | 0.108 |
| B | 0.081 | 0.100 | 0.108 |
| pair_level | 0.081 | 0.114 | 0.170 |

Recent HR buckets are in `hr_bucket_analysis.csv`; winner/loser
aggregates are in `hr_winner_loser.csv`.

## Counterfactual Decomposition

| Window | Mechanism | Case 1 V1/V1 | Case 2 V2/V2 | Case 3 V2/V1 | Case 4 V1/V2 |
|---|---|---|---|---|---|
| recent | A | 9.45% / 8.60% / 1.094 / -5.54% | 1.92% / 5.38% / 0.372 / -4.95% | 4.50% / 5.16% / 0.879 / -3.48% | 5.32% / 8.99% / 0.614 / -7.56% |
| recent | B | 9.81% / 8.53% / 1.141 / -5.55% | 2.14% / 5.36% / 0.415 / -4.94% | 4.73% / 5.12% / 0.926 / -3.46% | 5.72% / 8.94% / 0.661 / -7.50% |
| historical | A | 9.10% / 8.05% / 1.122 / -8.95% | 4.04% / 3.95% / 1.023 / -4.99% | 3.85% / 4.04% / 0.956 / -4.99% | 9.33% / 7.88% / 1.171 / -8.95% |
| historical | B | 8.83% / 8.01% / 1.096 / -8.87% | 3.91% / 3.94% / 0.993 / -4.97% | 3.73% / 4.02% / 0.930 / -4.97% | 9.02% / 7.86% / 1.138 / -8.87% |

Sharpe is nonlinear, so the following is a counterfactual bridge
with an explicit interaction residual, not a claim that Sharpe has
a unique additive causal attribution.

| Window | Mechanism | Metric | Total V2 minus V1 | Sizing effect | Allocator effect | Interaction |
|---|---|---|---:|---:|---:|---:|
| historical | A | sharpe | -0.09967 | -0.16627 | 0.04902 | 0.01759 |
| historical | A | annualized_return | -0.05055 | -0.05248 | 0.00230 | -0.00037 |
| historical | A | annualized_volatility | -0.04093 | -0.04009 | -0.00168 | 0.00084 |
| historical | B | sharpe | -0.10316 | -0.16670 | 0.04175 | 0.02179 |
| historical | B | annualized_return | -0.04921 | -0.05105 | 0.00191 | -0.00007 |
| historical | B | annualized_volatility | -0.04069 | -0.03988 | -0.00150 | 0.00069 |
| recent | A | sharpe | -0.72130 | -0.21455 | -0.47921 | -0.02754 |
| recent | A | annualized_return | -0.07528 | -0.04941 | -0.04130 | 0.01544 |
| recent | A | annualized_volatility | -0.03221 | -0.03446 | 0.00389 | -0.00163 |
| recent | B | sharpe | -0.72582 | -0.21544 | -0.48045 | -0.02993 |
| recent | B | annualized_return | -0.07670 | -0.05086 | -0.04088 | 0.01505 |
| recent | B | annualized_volatility | -0.03167 | -0.03405 | 0.00417 | -0.00179 |

Case 3 versus Case 2 is the performance recovered by putting V1
weights back on V2-sized trades. Case 4 versus Case 1 is the cost of
putting the V2 path on V1-sized trades.

## Concentration

| Mechanism | Unit | Top 1 | Top 5 | Top 10 | Top 20 |
|---|---|---:|---:|---:|---:|
| A | trade contribution difference | 3.6% | 11.0% | 19.3% | 33.5% |
| A | daily return difference | 4.8% | 19.3% | 30.2% | 44.9% |
| B | trade contribution difference | 3.5% | 10.7% | 18.7% | 32.6% |
| B | daily return difference | 4.8% | 19.1% | 29.9% | 44.3% |

The top-day trade attribution file identifies the five largest
directional trade-level contributors for each of the top ten average
recent V1-outperformance days and V2-outperformance days per
mechanism. The leading trade on each day is summarized below.

| Mechanism | Direction | Rank | Date | Mean return difference | Leading trade | Leading trade difference |
|---|---|---:|---|---:|---|---:|
| A | v1 outperformed | 1 | 2025-04-09 | 2.322% | A:CME-MA | $5,647 |
| A | v1 outperformed | 2 | 2024-01-05 | 1.592% | A:ELV-KEY | $4,754 |
| A | v1 outperformed | 3 | 2025-05-02 | 1.145% | A:LII-MSI | $6,166 |
| A | v1 outperformed | 4 | 2024-01-12 | 1.014% | A:ELV-KEY | $2,929 |
| A | v1 outperformed | 5 | 2025-02-26 | 0.917% | A:INTU-VTRS | $7,614 |
| A | v1 outperformed | 6 | 2024-01-25 | 0.857% | B:TYL-UHS | $4,141 |
| A | v1 outperformed | 7 | 2025-06-23 | 0.820% | A:CF-FIX | $4,734 |
| A | v1 outperformed | 8 | 2025-04-04 | 0.800% | B:ERIE-OKE | $24,976 |
| A | v1 outperformed | 9 | 2025-07-31 | 0.694% | A:GLW-META | $5,213 |
| A | v1 outperformed | 10 | 2025-06-13 | 0.671% | A:CF-PYPL | $6,815 |
| A | v2 outperformed | 1 | 2024-01-03 | -2.138% | A:ELV-WAT | $-5,502 |
| A | v2 outperformed | 2 | 2024-01-09 | -1.043% | A:ELV-USB | $-2,542 |
| A | v2 outperformed | 3 | 2024-01-17 | -1.038% | A:ELV-USB | $-2,493 |
| A | v2 outperformed | 4 | 2024-10-31 | -0.987% | A:ETR-FE | $-4,774 |
| A | v2 outperformed | 5 | 2024-01-11 | -0.752% | A:ELV-USB | $-2,172 |
| A | v2 outperformed | 6 | 2024-10-30 | -0.748% | A:AVY-SW | $-6,478 |
| A | v2 outperformed | 7 | 2025-06-10 | -0.631% | A:CSGP-NTAP | $-2,015 |
| A | v2 outperformed | 8 | 2025-01-21 | -0.547% | A:SYK-USB | $-1,231 |
| A | v2 outperformed | 9 | 2025-10-21 | -0.527% | A:KO-WST | $-8,091 |
| A | v2 outperformed | 10 | 2024-02-15 | -0.498% | A:EQIX-MCO | $-4,593 |
| B | v1 outperformed | 1 | 2025-04-09 | 2.336% | A:CME-MA | $5,645 |
| B | v1 outperformed | 2 | 2024-01-05 | 1.592% | A:ELV-KEY | $4,754 |
| B | v1 outperformed | 3 | 2025-05-02 | 1.150% | A:LII-MSI | $6,277 |
| B | v1 outperformed | 4 | 2024-01-12 | 1.014% | A:ELV-KEY | $2,929 |
| B | v1 outperformed | 5 | 2025-02-26 | 0.896% | A:INTU-VTRS | $7,317 |
| B | v1 outperformed | 6 | 2024-01-25 | 0.857% | B:TYL-UHS | $4,141 |
| B | v1 outperformed | 7 | 2025-04-04 | 0.802% | B:ERIE-OKE | $24,960 |
| B | v1 outperformed | 8 | 2025-06-23 | 0.776% | A:CF-FIX | $4,532 |
| B | v1 outperformed | 9 | 2025-07-31 | 0.680% | A:GLW-META | $5,140 |
| B | v1 outperformed | 10 | 2025-04-28 | 0.653% | A:EBAY-IBM | $3,558 |
| B | v2 outperformed | 1 | 2024-01-03 | -2.138% | A:ELV-WAT | $-5,502 |
| B | v2 outperformed | 2 | 2024-01-09 | -1.043% | A:ELV-USB | $-2,542 |
| B | v2 outperformed | 3 | 2024-01-17 | -1.038% | A:ELV-USB | $-2,493 |
| B | v2 outperformed | 4 | 2024-10-31 | -0.915% | A:ETR-FE | $-4,540 |
| B | v2 outperformed | 5 | 2024-01-11 | -0.752% | A:ELV-USB | $-2,172 |
| B | v2 outperformed | 6 | 2024-10-30 | -0.708% | A:AVY-SW | $-6,285 |
| B | v2 outperformed | 7 | 2025-06-10 | -0.617% | A:CSGP-NTAP | $-2,014 |
| B | v2 outperformed | 8 | 2025-01-21 | -0.545% | A:SYK-USB | $-1,218 |
| B | v2 outperformed | 9 | 2025-10-21 | -0.528% | A:KO-WST | $-7,987 |
| B | v2 outperformed | 10 | 2024-02-15 | -0.498% | A:EQIX-MCO | $-4,593 |

## Recent Versus Historical

| Mechanism | Diagnostic | Recent | Historical |
|---|---|---:|---:|
| A | V1 Sharpe | 1.094 | 1.122 |
| A | V2 Sharpe | 0.372 | 1.023 |
| A | V1 return | 9.446% | 9.098% |
| A | V2 return | 1.919% | 4.043% |
| A | V1 volatility | 8.603% | 8.046% |
| A | V2 volatility | 5.382% | 3.953% |
| A | Sharpe change | -0.721 | -0.100 |
| A | Return change | -7.528% | -5.055% |
| A | Volatility change | -3.221% | -4.093% |
| A | Weight-flip months | 15.000 | 4.000 |
| A | Mean abs A-weight difference | 0.065 | 0.027 |
| A | Avg HR winners | 0.855 | 0.885 |
| A | Avg HR losers | 0.780 | 0.882 |
| A | V1/V2 gross ratio winners | 1.856 | 1.885 |
| A | V1/V2 gross ratio losers | 1.781 | 1.882 |
| A | Top-10-trade share of V1 advantage | 19.288 | 68.723 |
| B | V1 Sharpe | 1.141 | 1.096 |
| B | V2 Sharpe | 0.415 | 0.993 |
| B | V1 return | 9.812% | 8.832% |
| B | V2 return | 2.142% | 3.911% |
| B | V1 volatility | 8.525% | 8.011% |
| B | V2 volatility | 5.358% | 3.941% |
| B | Sharpe change | -0.726 | -0.103 |
| B | Return change | -7.670% | -4.921% |
| B | Volatility change | -3.167% | -4.069% |
| B | Weight-flip months | 15.000 | 4.000 |
| B | Mean abs A-weight difference | 0.065 | 0.027 |
| B | Avg HR winners | 0.855 | 0.885 |
| B | Avg HR losers | 0.780 | 0.882 |
| B | V1/V2 gross ratio winners | 1.856 | 1.885 |
| B | V1/V2 gross ratio losers | 1.781 | 1.882 |
| B | Top-10-trade share of V1 advantage | 18.673 | 70.803 |

## Direct Conclusion

For mechanism A, the recent Sharpe change was **-0.721**. Holding the V1 allocator fixed, changing pair sizing changed Sharpe by **-0.215**; holding V1 sizing fixed, changing the allocator path changed it by **-0.479**. The interaction residual was **-0.028**, so the larger direct bridge component was **allocator path**.
The recent winner/loser gross ratios were **1.856** and **1.781**, with average absolute HR **0.855** versus **0.780**.
For mechanism B, the recent Sharpe change was **-0.726**. Holding the V1 allocator fixed, changing pair sizing changed Sharpe by **-0.215**; holding V1 sizing fixed, changing the allocator path changed it by **-0.480**. The interaction residual was **-0.030**, so the larger direct bridge component was **allocator path**.
The recent winner/loser gross ratios were **1.856** and **1.781**, with average absolute HR **0.855** versus **0.780**.

1. **High-HR winner hypothesis:** partly supported, but not sufficient by itself. Recent winners had average abs HR 0.855 versus 0.780 for losers, and V1/V2 gross ratios 1.856 versus 1.781. HR >= 1 contributed 89.8% of the recent pair-level net V1-minus-V2 contribution difference ($2,031,363), but the correlations were weak: 0.081 with PnL sign and 0.170 with contribution difference.
2. **Allocator path:** materially different in recent data. V1 and V2 differed in 15 of 110 path-months, with mean abs A-weight difference 0.065 and maximum 0.800. Historical had 4 flips in 60 months and mean difference 0.027.
3. **V1 weights on V2 sizing:** Case 3 recovered 0.507 Sharpe points for A and 0.510 for B relative to Case 2. It left Case 3 at Sharpe 0.879/0.926, versus V1 1.094/1.141.
4. **V2 weights on V1 sizing:** Case 4 reduced recent V1 Sharpe by 0.479 points for A and 0.480 for B. The allocator path was therefore the larger direct recent Sharpe bridge component, while pair sizing remained meaningful.
5. **Concentration:** the effect was broad rather than explained by a few trades. The top 10 trades accounted for 19.3% of the recent A advantage and the top 10 daily differences accounted for 30.2%; the directional top-day table identifies the responsible trades.
6. **Historical control:** historical V2 Sharpe fell only about 0.10 versus 0.72 recently because the allocator path changed much less and the V2 path improved V1 sizing in the control. Pair sizing still lowered historical Sharpe by about 0.166, but lower V2 return came with much lower volatility.
7. **Robustness:** the old winner was not robust to the full V1 convention as a headline result, but it was not purely a sizing illusion. V2 sizing with the V1 path retained positive recent Sharpe, while switching the recent allocator path onto V1 sizing caused the larger direct drop. The original advantage is therefore dependent on both reference-leg sizing and the recent Clean40 path; the underlying signal survives, but the result is not convention-invariant.

## Files

- `allocator_path.csv`
- `allocator_path_summary.csv`
- `combined_return_series.csv`
- `trade_contributions_recent.csv`
- `daily_contributions_recent.csv`
- `top_day_trade_attribution.csv`
- `hr_bucket_analysis.csv`
- `hr_winner_loser.csv`
- `hr_correlations.csv`
- `counterfactual_results.csv`
- `counterfactual_attribution.csv`
- `concentration_analysis.csv`
- `recent_vs_historical.csv`
- `validation.json`

No README or canonical selected-book configuration was changed.
