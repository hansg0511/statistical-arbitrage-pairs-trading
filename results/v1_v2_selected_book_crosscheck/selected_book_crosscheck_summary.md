# Selected-Book V1/V2 Cross-Check

This focused replay compares the books selected by the V1 and V2
research conventions under both sizing modes. It uses preserved raw
runs and does not rerun the 496-book matrix or modify canonical outputs.

## Selection

- V1-selected book: `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-2m/cross_sector_slide3m_bd7`
- V2-selected book: `sp500-12m/same_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen`
- V2 handoff candidate matches current ranking: **True**
- Allocator: 84-day causal lookback, 0.40 step, 0.10--0.90 bounds, 0.50 initial A weight
- These allocator settings are held fixed and were inherited from the broader research; they are not neutral proof for either sizing convention.

## Validation

- Overall status: **pass**
- Focused groups: **24**; full matrix rerun: **False**
- Trade identity matching: **pass**
- Replay PnL equivalence: **pass**
- Native V2 marked exposure reconciliation: **pass**
- V2 gross-budget invariants: **pass**
- Existing old-winner outputs unchanged: **True**
- Protected public hashes unchanged: **True**

## Recent Aggregate Comparison

The table reports mean metrics across the five recent starts. Gross and
leverage statistics are means of each run's active-day statistics.

| Origin | Mechanism | Scenario | Mean Sharpe | Mean cumulative return | Mean final equity | Mean gross leverage | Mean return on gross |
|---|---|---|---:|---:|---:|---:|---:|
| v1_selected | A | v1 / actual | 1.0937 | 17.3182% | $1,173,182 | 0.888x | 0.00023261 |
| v1_selected | A | v1 / matched_to_v2 | 0.9691 | 7.5656% | $1,075,656 | 0.447x | 0.00023261 |
| v1_selected | A | v2 / actual | 0.3724 | 3.4578% | $1,034,578 | 0.455x | 0.00011521 |
| v1_selected | A | v2 / matched_to_v1 | 0.4322 | 7.3288% | $1,073,288 | 0.928x | 0.00011521 |
| v1_selected | B | v1 / actual | 1.1413 | 18.0031% | $1,180,031 | 0.868x | 0.00020841 |
| v1_selected | B | v1 / matched_to_v2 | 1.0094 | 7.8491% | $1,078,491 | 0.438x | 0.00020841 |
| v1_selected | B | v2 / actual | 0.4154 | 3.8606% | $1,038,606 | 0.445x | 0.00009537 |
| v1_selected | B | v2 / matched_to_v1 | 0.4828 | 8.3065% | $1,083,065 | 0.905x | 0.00009537 |
| v2_selected | A | v1 / actual | 1.0064 | 25.0964% | $1,250,964 | 1.143x | 0.00029629 |
| v2_selected | A | v1 / matched_to_v2 | 1.1011 | 14.9976% | $1,149,976 | 0.623x | 0.00029629 |
| v2_selected | A | v2 / actual | 1.2559 | 17.5763% | $1,175,763 | 0.619x | 0.00040422 |
| v2_selected | A | v2 / matched_to_v1 | 1.1792 | 30.3128% | $1,303,128 | 1.130x | 0.00040422 |
| v2_selected | B | v1 / actual | 0.9218 | 23.3642% | $1,233,642 | 1.128x | 0.00026498 |
| v2_selected | B | v1 / matched_to_v2 | 1.0204 | 14.0989% | $1,140,989 | 0.613x | 0.00026498 |
| v2_selected | B | v2 / actual | 1.1604 | 16.4526% | $1,164,526 | 0.610x | 0.00037040 |
| v2_selected | B | v2 / matched_to_v1 | 1.0817 | 28.1895% | $1,281,895 | 1.117x | 0.00037040 |

## Exposure-Matched Selection Interaction

The primary comparison is V1 matched to V2 gross versus V2 actual.
Positive gap means the matched V1 final equity exceeded V2 actual;
this is an attribution result, not a causal estimate.

| Origin | Mechanism | Mean actual V1-V2 gap | Mean matched V1-V2 gap | Matched V1 Sharpe > V2 | Positive matched gap |
|---|---|---:|---:|---:|---:|
| v1_selected | A | $138,604 | $41,079 | 5/5 | 5/5 |
| v1_selected | B | $141,425 | $39,885 | 5/5 | 5/5 |
| v2_selected | A | $75,201 | $-25,786 | 1/5 | 1/5 |
| v2_selected | B | $69,116 | $-23,537 | 1/5 | 1/5 |

## Allocator-Path Attribution

Shares describe where the arithmetic or log-equity gap accumulated
under the fixed replay paths. They do not identify causality.

| Origin | Mechanism | Start | Comparison | Different-weight return-gap share | Identical-weight return-gap share | Different-weight log-gap share |
|---|---|---:|---|---:|---:|---:|
| v1_selected | A | 0 | v1_matched_to_v2_minus_v2 | 50.4% | 49.6% | 51.4% |
| v1_selected | A | 1 | v1_matched_to_v2_minus_v2 | 85.1% | 14.9% | 85.1% |
| v1_selected | A | 2 | v1_matched_to_v2_minus_v2 | 85.4% | 14.6% | 85.6% |
| v1_selected | A | 3 | v1_matched_to_v2_minus_v2 | 64.4% | 35.6% | 65.2% |
| v1_selected | A | 4 | v1_matched_to_v2_minus_v2 | 86.0% | 14.0% | 86.1% |
| v1_selected | B | 0 | v1_matched_to_v2_minus_v2 | 51.6% | 48.4% | 52.7% |
| v1_selected | B | 1 | v1_matched_to_v2_minus_v2 | 87.8% | 12.2% | 87.8% |
| v1_selected | B | 2 | v1_matched_to_v2_minus_v2 | 87.1% | 12.9% | 87.3% |
| v1_selected | B | 3 | v1_matched_to_v2_minus_v2 | 71.3% | 28.7% | 72.0% |
| v1_selected | B | 4 | v1_matched_to_v2_minus_v2 | 87.7% | 12.3% | 87.8% |
| v2_selected | A | 0 | v1_matched_to_v2_minus_v2 | 32.4% | 67.6% | 32.5% |
| v2_selected | A | 1 | v1_matched_to_v2_minus_v2 | 94.5% | 5.5% | 95.6% |
| v2_selected | A | 2 | v1_matched_to_v2_minus_v2 | 135.3% | -35.3% | 130.6% |
| v2_selected | A | 3 | v1_matched_to_v2_minus_v2 | 1.6% | 98.4% | 1.5% |
| v2_selected | A | 4 | v1_matched_to_v2_minus_v2 | 84.7% | 15.3% | 85.5% |
| v2_selected | B | 0 | v1_matched_to_v2_minus_v2 | 34.7% | 65.3% | 34.8% |
| v2_selected | B | 1 | v1_matched_to_v2_minus_v2 | 95.9% | 4.1% | 97.3% |
| v2_selected | B | 2 | v1_matched_to_v2_minus_v2 | 132.8% | -32.8% | 128.1% |
| v2_selected | B | 3 | v1_matched_to_v2_minus_v2 | 1.7% | 98.3% | 1.6% |
| v2_selected | B | 4 | v1_matched_to_v2_minus_v2 | 85.7% | 14.3% | 86.7% |

## What This Establishes

- It directly tests the old V1-selected and current V2-selected books under both sizing conventions on the same preserved recent and historical trade identities.
- It shows whether V1's equal-gross residual survives book selection, rather than treating the old V1-selected book as a universal sizing test.
- It separates realized leverage, return-on-gross, allocator-path differences, and forced allocator-path counterfactuals.
- V2 remains methodologically cleaner for cross-pair and cross-book comparison because its configured pair allocation is total pair gross exposure.

## What This Does Not Establish

- It does not prove that V1 or V2 is intrinsically superior from two selected books.
- It does not make the inherited Clean40 parameters neutral; they were held fixed only to isolate this interaction.
- It does not identify causal shares from differing-weight days; the attribution is conditional decomposition.
- It does not replace a broader out-of-sample selection study or retune the allocator.

## Artifacts

- `selected_book_crosscheck_per_run.csv`
- `selected_book_crosscheck_daily.csv`
- `selected_book_crosscheck_summary.csv`
- `selected_book_crosscheck_summary.json`
- `selected_book_crosscheck_summary.md`
- `allocator_path_attribution.csv`
- `allocator_path_counterfactuals.csv`
