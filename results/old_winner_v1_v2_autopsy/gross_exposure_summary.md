# Gross-Exposure Comparison

This focused experiment used the preserved old-winner raw runs and exact
archived price snapshots. It performed no full-matrix rerun.

## Validation

- Overall status: **pass**
- Focused traces run: **10**; full matrix rerun: **False**
- Daily PnL reconciliation: **pass**
- Marked exposure reconstruction: **pass**
- Native V2 daily-exposure reconciliation: **pass**
- Previous return/path consistency: **pass**
- V2 gross-budget invariants: **pass**
- Protected public hash unchanged: **True**

Exposure timing convention: positions are live from the first observed
close after the entry signal through the exit signal date, before the close
order fills. Return-on-gross uses beginning-of-interval marked exposure,
priced at the prior observed close; zero-support observations are NaN.

## Leverage

| Scope | V1 mean | V1 median | V1 p95 | V1 max | V2 mean | V2 median | V2 p95 | V2 max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 0.8865 | 0.8321 | 1.9464 | 3.4605 | 0.4547 | 0.4367 | 1.0026 | 1.8114 |
| B | 0.8668 | 0.8093 | 1.9144 | 3.4605 | 0.4450 | 0.4024 | 0.9930 | 1.7681 |
| all | 0.8767 | 0.8259 | 1.9375 | 3.4605 | 0.4498 | 0.4243 | 0.9995 | 1.8114 |

## Return On Gross

| Scope | V1 mean | V1 median | V1 efficiency Sharpe-like | V2 mean | V2 median | V2 efficiency Sharpe-like |
|---|---:|---:|---:|---:|---:|---:|
| A | 0.00022977 | 0.00023729 | 0.6472 | 0.00011320 | 0.00013896 | 0.2903 |
| B | 0.00020623 | 0.00020148 | 0.5864 | 0.00009390 | 0.00015650 | 0.2425 |
| all | 0.00021800 | 0.00020859 | 0.6170 | 0.00010355 | 0.00014514 | 0.2665 |

## Exposure-Matched Counterfactuals

The detailed per-start/per-mechanism metrics are in
`gross_exposure_matched_counterfactuals.csv`. Matching is performed
daily by scaling V1 or V2 trade-level PnL by the ratio of target to
source beginning-of-interval gross exposure.

| Scope | Actual V1 Sharpe | Actual V2 Sharpe | V1 matched-to-V2 Sharpe | V2 matched-to-V1 Sharpe | Mean V1 gap removed by V1->V2 matching |
|---|---:|---:|---:|---:|---:|
| start_0_A | 0.7579 | 0.5033 | 0.7700 | 0.5181 | 73.34% |
| start_0_B | 0.8214 | 0.5679 | 0.8304 | 0.5871 | 76.19% |
| start_1_A | 1.0135 | 0.0908 | 0.7442 | 0.2409 | 68.70% |
| start_1_B | 1.0422 | 0.1174 | 0.7671 | 0.2731 | 69.64% |
| start_2_A | 1.3325 | 0.3020 | 1.3572 | 0.1757 | 62.77% |
| start_2_B | 1.3242 | 0.3008 | 1.3472 | 0.1789 | 62.78% |
| start_3_A | 1.1193 | 0.7670 | 1.0506 | 0.8387 | 82.32% |
| start_3_B | 1.1774 | 0.8154 | 1.0826 | 0.9110 | 85.10% |
| start_4_A | 1.2452 | 0.1989 | 0.9237 | 0.3876 | 71.54% |
| start_4_B | 1.3411 | 0.2757 | 1.0196 | 0.4636 | 72.84% |
| A | 1.0937 | 0.3724 | 0.9691 | 0.4322 | 71.73% |
| B | 1.1413 | 0.4154 | 1.0094 | 0.4828 | 73.31% |
| all | 1.1175 | 0.3939 | 0.9893 | 0.4575 | 72.52% |

## Conclusions

1. V1/V2 total marked gross exposure ratio had pooled median 1.962x and p95 3.431x on V2-active observations.
2. Pooled active-day mean gross leverage was 0.877x for V1 versus 0.450x for V2; the p95 values were 1.938x and 1.000x.
3. Mean return-on-gross was 0.00021800 for V1 versus 0.00010355 for V2 on observations with supporting exposure.
4. Matching V1 daily gross to V2 reduced the mean final V1-minus-V2 equity gap from 0.140015 to 0.040482; the mean removed share was 72.52%.
5. V1 was not simply a more leveraged V2 if the exposure-matched V1 gap remains positive; the counterfactual table reports the per-start result rather than assuming a universal causal percentage.
6. The remaining gap after matching total gross is the evidence available for V1 internal HR-dependent weighting/economics; it should not be conflated with the separate Clean40 allocator-path effect.
7. The prior differing-weight mask covers 628 pooled observations versus 3876 identical-weight observations; this experiment provides matched and unmatched comparisons within that same mask.
8. V2 remains the cleaner convention for future cross-pair and cross-book comparison because it fixes total pair gross exposure, while V1 remains a useful historical control.

## Artifacts

- `gross_exposure_comparison_recent.csv`
- `gross_exposure_matched_counterfactuals.csv`
- `gross_exposure_summary.json`
- Representative PNGs listed in the JSON summary
