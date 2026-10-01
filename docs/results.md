# Results

## Current Candidate

The latest completed V2 candidate uses:

- `sp500-12m/same_sector_slide1m_noscreen` as Leg A;
- `sp500-12m/same_sector_slide3m_noscreen` as Leg B;
- V2 `gross_exposure` sizing with a `$250,000` total pair gross budget; and
- the existing 84-day Clean40 allocator.

## V2 Selected-Book Replay

The table reports mean start-level metrics. It does not concatenate the five
recent paths into one synthetic time series.

| Window | Starts | Mechanism | Mean annual return | Mean volatility | Mean Sharpe | Mean max drawdown | Mean gross leverage |
|---|---:|---|---:|---:|---:|---:|---:|
| Recent | 5 | A | 9.4363% | 7.2767% | 1.2559 | -3.5814% | 0.619x |
| Recent | 5 | B | 8.8177% | 7.3718% | 1.1604 | -4.1857% | 0.610x |
| Historical | 1 | A | 3.5519% | 4.6604% | 0.7722 | -6.0976% | 0.618x |
| Historical | 1 | B | 3.6603% | 4.6241% | 0.8006 | -6.1037% | 0.618x |

The recent and historical annualized return, volatility, and drawdown values are
from the V2 combined ranking table. Gross leverage values are the corresponding
mean active-day values from the selected-book audit; they are accounting
diagnostics, not broker capacity limits.

## Candidate Comparison

The full V2 report ranks books by the existing separate score
`min(recent Sharpe, historical Sharpe)`, while the selected candidate is also
checked using rank-average and joined evidence.

| Mechanism | Candidate | Recent Sharpe | Historical Sharpe | Separate score | Joined Sharpe | Separate rank |
|---|---|---:|---:|---:|---:|---:|
| A | V2 selected book | 1.2559 | 0.7722 | 0.7722 | 0.9268 | 4 |
| A | `sp500-12m/cross_sector_slide1m_noscreen` + `sp500-12m/same_sector_slide3m_noscreen` | 0.9983 | 0.7980 | 0.7980 | 0.8501 | 1 |
| B | V2 selected book | 1.1604 | 0.8006 | 0.8006 | 0.9120 | 2 |
| B | `sp500-12m/same_sector_slide3m_noscreen` + `sp500-12m/same_sector_slide1m_bd7` | 0.8041 | 0.8799 | 0.8041 | 0.8528 | 1 |

The selected book is not justified by recent Sharpe alone. It is the V2
rank-average consensus leader across the configured evidence and then survives
the focused cross-check and Clean40 audit. The candidate comparison is an
attribution of the completed ranking, not a new selection run.

## Clean40 Decision

| Measure | Existing dynamic | Static 50/50 |
|---|---:|---:|
| Recent mean cumulative return | 17.014% | 16.800% |
| Historical mean cumulative return | 19.245% | 11.562% |
| Recent mean Sharpe | 1.208 | 1.237 |
| Historical mean Sharpe | 0.786 | 0.503 |
| Robust floor | 0.772 | 0.491 |

The existing setting is in a plateau of 8 dynamic configurations. Every
leave-one-start-out selection returned the existing baseline, and no candidate
cleared the required 0.05 robust-floor improvement. The decision is therefore
`keep_old_clean40`.

## Metric Convention Note

The completed matrix report lists the V2 standalone historical score for the
selected Leg A as approximately `0.5320`. The later Clean40 audit lists the
same leg's full-file diagnostic as approximately `0.4203`. These are not mixed
or averaged in the tables above:

- the matrix score uses the canonical standalone selection/evaluation window;
- the Clean40 diagnostic includes the later audit's full-file replay convention,
  including ramp-up and wind-down rows; and
- the difference is an evaluation-window convention, not a claim that a new
  strategy was found.

Leg B is approximately `0.4630` under both reported conventions.

## Earlier V1 Snapshot

The tracked `results/final/` tree is a complete earlier V1 public snapshot. Its
locked configuration and headline metrics remain unchanged for auditability.
The V2 presentation does not relabel those V1 values as current V2 results.

## Source Artifacts

- [`results/sizing_v2_full_summary/report.md`](../results/sizing_v2_full_summary/report.md): full V1/V2 matrix summary
- [`results/sizing_v2_full_summary/full_manifest.json`](../results/sizing_v2_full_summary/full_manifest.json): matrix provenance and validation
- [`results/v1_v2_selected_book_crosscheck/selected_book_crosscheck_summary.md`](../results/v1_v2_selected_book_crosscheck/selected_book_crosscheck_summary.md): focused comparison
- [`results/v2_book_clean40_retune/clean40_summary.md`](../results/v2_book_clean40_retune/clean40_summary.md): allocator audit
- [`results/v2_book_clean40_retune/clean40_summary.json`](../results/v2_book_clean40_retune/clean40_summary.json): machine-readable decision and checks
