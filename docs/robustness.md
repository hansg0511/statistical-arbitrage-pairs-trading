# Robustness

The robustness audit keeps the V2 selected book and V2 gross-exposure sizing
fixed. It tests start-date dispersion, historical behavior, fold and calendar
concentration, trade and symbol concentration, allocator dependence, and a
small predeclared Clean40 lattice.

## Start-Date Dispersion

Recent Sharpe values are shown by start index. These are the five recent
12-month-selection runs, not five independent samples.

| Start | Mechanism A | Mechanism B |
|---:|---:|---:|
| 1 | 1.358 | 1.357 |
| 2 | 0.917 | 0.785 |
| 3 | 1.465 | 1.439 |
| 4 | 1.393 | 1.339 |
| 5 | 1.146 | 0.883 |
| Historical control | 0.772 | 0.801 |

The recent mean is 1.208 across mechanisms and starts under the Clean40 audit.
Removing the best recent fold lowers that mean to 0.861. This is evidence of
dispersion and concentration, not a claim that the remaining observations are
independent regime tests.

## Calendar and Fold Concentration

- The top recent calendar-quarter share of total PnL is 35.63%.
- The top recent fold share is 33.63%.
- 147 of 200 recent fold observations are positive.
- Recent PnL spans 96 calendar year/quarter rows and 200 fold observations.

The calendar attribution uses actual daily replay PnL. It is additive
contribution analysis, not a claim that calendar periods are independent.

## Trade, Pair, and Symbol Concentration

- The largest recent trade is 1.50% of absolute PnL; trade HHI is 0.0036.
- Removing the best trade changes mean Sharpe from 1.208 to 1.115.
- Removing the best five trades changes mean Sharpe to 0.853.
- The largest pair is 3.20% of absolute PnL; the worst pair is `ADI-WDC`.
- The largest symbol share is 2.18% using equal pair-trade attribution.

The symbol figure is a diagnostic allocation of pair PnL, not leg-level causal
PnL.

## Allocator Dependence

The frozen Clean40 path has:

- mean recent Leg A weight of 63.12%;
- 22.40% of recent daily observations at the lower bound;
- 22.40% at 50/50;
- 55.20% at the upper bound; and
- 7.0 mean monthly weight changes.

Leg A and Leg B daily returns have correlation 0.776, with a rolling 63-day
range from 0.254 to 0.969. Static 50/50 has higher recent mean Sharpe but lower
historical mean Sharpe and a lower robust floor.

## Parameter Neighborhood

The predeclared grid selected the existing configuration:

| Configuration | Robust floor | Recent mean Sharpe | Historical mean Sharpe | Plateau |
|---|---:|---:|---:|---|
| `lb84_s0.40_b0.10_0.90` | 0.772 | 1.208 | 0.786 | Yes |
| `lb84_s0.20_b0.10_0.90` | 0.768 | 1.207 | 0.772 | Yes |
| `lb63_s0.20_b0.10_0.90` | 0.762 | 1.222 | 0.782 | Yes |
| `lb105_s0.20_b0.10_0.90` | 0.749 | 1.221 | 0.761 | Yes |
| `lb126_s0.20_b0.10_0.90` | 0.745 | 1.226 | 0.765 | Yes |
| `lb42_s0.40_b0.10_0.90` | 0.488 | 1.344 | 0.503 | No |

The high recent Sharpe of the 42-day neighbor is not sufficient because its
historical floor is weak. Eight dynamic configurations are within 0.05 Sharpe
of the best robust floor, and leave-one-start-out selection returns one region:
the existing baseline.

## Validation Checks

The Clean40 audit reports:

- V2 book identity: pass;
- V2 gross-budget invariant: pass;
- native V2 exposure reconciliation: pass;
- trade identity across allocator configurations: pass;
- PnL/equity reconciliation: pass;
- protected hashes unchanged: true; and
- full-matrix rerun: false.

The selected-book cross-check independently reports pass for trade identity,
replay PnL, native exposure, gross-budget invariants, and protected public
outputs.

## Figures

- [Recent equity](../results/v2_book_clean40_retune/baseline_equity_recent.png)
- [Recent weights](../results/v2_book_clean40_retune/baseline_weight_recent.png)
- [Recent Clean40 surface](../results/v2_book_clean40_retune/clean40_surface_recent.png)
- [Historical Clean40 surface](../results/v2_book_clean40_retune/clean40_surface_historical.png)
