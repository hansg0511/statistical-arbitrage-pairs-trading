# Robust Mean-Reversion Pairs Trading

This repository is a research system for walk-forward statistical arbitrage in
equity pairs. It covers pair formation, residual mean reversion, sizing,
shared-account replay, portfolio selection, and robustness checks. It is not a
broker integration or a live-trading system.

The public presentation on this branch describes the latest completed V2
gross-exposure research. The older V1 public snapshot remains in the repository
unchanged so that the sizing comparison and audit trail remain reproducible.

## Research Question

The research asks whether a book of walk-forward cointegrated-pair strategies
can remain useful across recent and older periods after:

- comparing 32 explicit strategy configurations;
- combining two legs into 496 candidate books;
- replaying both shared-account allocation mechanisms; and
- fixing the pair gross-exposure convention before comparing V2 books.

The displayed periods are research windows that informed selection. They are not
an untouched portfolio-level holdout.

## Current V2 Candidate

The latest completed V2 candidate is:

| Item | Value |
|---|---|
| Leg A | `sp500-12m/same_sector_slide1m_noscreen` |
| Leg B | `sp500-12m/same_sector_slide3m_noscreen` |
| Sizing | V2 `gross_exposure`; `$250,000` total pair budget |
| Capital | `$1,000,000` replay account |
| Allocator | 84-day causal lookback, `0.40` step, `10%--90%` bounds, 50/50 initial weight |
| Pair universe | 496 two-leg candidate books per mechanism |
| Clean40 decision | Keep the existing allocator: `lb84_s0.40_b0.10_0.90` |

The V2 candidate was selected from the completed matrix using the existing
multi-view ranking convention. It is not a new pair-selection or signal
parameter search performed during this documentation pass.

### Artifact Boundary

`research/selected_book_config.json` and `results/final/` are the earlier locked
V1 public snapshot. They intentionally continue to describe:

- `sp500-12m/cross_sector_slide1m_noscreen`; and
- `sp500-2m/cross_sector_slide3m_bd7`.

Those artifacts are historical controls, not silently replaced V2 outputs. The
current V2 evidence is indexed in [`results/README.md`](results/README.md).

## Headline Replay Results

The following rows are the V2 selected book under V2 gross-exposure sizing.
Recent values are means across five starts; historical has one aligned control
start. Annual return, volatility, and drawdown are means of start-level replay
metrics, not metrics from a concatenated pseudo-series.

| Window | Starts | Mechanism | Mean annual return | Mean volatility | Mean Sharpe | Mean max drawdown |
|---|---:|---|---:|---:|---:|---:|
| Recent | 5 | A | 9.4363% | 7.2767% | 1.2559 | -3.5814% |
| Recent | 5 | B | 8.8177% | 7.3718% | 1.1604 | -4.1857% |
| Historical | 1 | A | 3.5519% | 4.6604% | 0.7722 | -6.0976% |
| Historical | 1 | B | 3.6603% | 4.6241% | 0.8006 | -6.1037% |

These figures come from the compact V2 matrix and selected-book cross-check
artifacts. See [`docs/results.md`](docs/results.md) for definitions and the
comparison with the earlier V1 book.

## Why This Book

The V2 matrix covered 32 standalone configurations, 192 standalone run
instances, 496 books per mechanism, and 992 combined rows per sizing mode. No
standalone configuration changed its selection decision under V2, and the V2
gross-budget invariant passed for every retained run.

The selected book is the current rank-average consensus leader under the V2
ranking evidence. It is not the highest recent-Sharpe pair under every view:
the separate-score rank is 4 for Mechanism A and 2 for Mechanism B. That is
intentional. The selection gives weight to recent and historical behavior and
joined-book behavior together.

## Clean40 Robustness

The Clean40 audit held the V2 book and V2 sizing fixed. It evaluated 40
lattice-aligned dynamic configurations plus a static 50/50 control.

| Measure | Existing dynamic | Static 50/50 |
|---|---:|---:|
| Recent mean Sharpe | 1.208 | 1.237 |
| Historical mean Sharpe | 0.786 | 0.503 |
| Robust floor | 0.772 | 0.491 |

The existing dynamic setting remained the selection because it cleared the
predeclared robustness rule, sat in a plateau of 8 configurations, and was
selected in every leave-one-start-out region. The result is `keep_old_clean40`,
not a claim that dynamic allocation wins every recent path.

Public audit figures are retained with the result artifacts:

- [Recent equity paths](results/v2_book_clean40_retune/baseline_equity_recent.png)
- [Recent allocator weights](results/v2_book_clean40_retune/baseline_weight_recent.png)
- [Recent robustness surface](results/v2_book_clean40_retune/clean40_surface_recent.png)
- [Historical robustness surface](results/v2_book_clean40_retune/clean40_surface_historical.png)

## Transaction-Cost Sensitivity

The frozen candidate was also tested with a simple one-way all-in cost overlay
on traded notional. These are means across mechanisms using the same recent and
historical aggregation convention; they are not live execution estimates.

| Cost | Recent mean Sharpe | Historical mean Sharpe | Recent mean annualized return | Historical mean annualized return |
|---:|---:|---:|---:|---:|
| 0 bps | 1.208 | 0.786 | 9.13% | 3.61% |
| 5 bps | 0.833 | 0.189 | 6.34% | 0.82% |
| 10 bps | 0.460 | -0.402 | 3.50% | -2.31% |
| 20 bps | -0.282 | -1.536 | -2.38% | -10.12% |

At 5 bps, all existing recent starts and the historical control remain
positive. At 20 bps, only 2 of 10 recent mechanism-start combinations remain
positive and neither historical control does. Approximate recent break-even
costs are 16.5 bps for Mechanism A and 15.2 bps for Mechanism B on a mean
basis; the historical controls break even near 6.3--6.5 bps. See the full
[transaction-cost report](results/transaction_cost_analysis/tca_summary.md).

## Methodology

The research pipeline is described in [`docs/methodology.md`](docs/methodology.md).
At a high level it:

1. forms pairs from log-price data using Engle-Granger tests, OLS hedge ratios,
   residual diagnostics, sector rules, and walk-forward formation windows;
2. trades residual z-score excursions with locked entry statistics, a hedge-ratio
   guard, stop and exit rules, earnings gates, and a loss-only calendar holding
   limit;
3. compares the legacy V1 reference-leg sizing with V2 fixed-total-gross sizing;
4. replays recorded trade events and daily marks in one shared account; and
5. ranks books across recent, historical, separate, rank-average, and joined
   evidence before auditing the allocator.

## Limitations

The result is a research candidate, not evidence of live profitability. The
replay does not model commissions, spread, slippage, borrow, financing,
partial fills, asynchronous two-leg execution, broker margin admission, or a
deployable-capital policy. Gross leverage can exceed 1x, and pair overlap,
calendar concentration, factor exposure, static-universe effects, and selection
dependence remain material.

See [`docs/limitations.md`](docs/limitations.md) for the full boundary and the
paper-trading validation gate.

## Reproduce and Audit

Start with [`docs/reproducibility.md`](docs/reproducibility.md). The compact V2
matrix summary, selected-book cross-check, and Clean40 audit are already
generated artifacts. Full V2 regeneration requires the preserved local raw run
trees and deterministic input snapshots; it is not required to read the public
tables.

The basic test command is:

```text
python -m pytest -q
```

## Repository Guide

- [`docs/README.md`](docs/README.md): public documentation index
- [`docs/results.md`](docs/results.md): headline metrics and selection evidence
- [`docs/robustness.md`](docs/robustness.md): starts, folds, concentration, and allocator checks
- [`docs/methodology.md`](docs/methodology.md): signal, sizing, and replay definitions
- [`docs/limitations.md`](docs/limitations.md): interpretation and live-readiness boundary
- [`docs/reproducibility.md`](docs/reproducibility.md): commands, inputs, and provenance
- [`docs/research_chronology.md`](docs/research_chronology.md): concise research chronology
- [`docs/research_decision_log.md`](docs/research_decision_log.md): lower-level experiment log
- [`results/README.md`](results/README.md): result-generation index and artifact boundaries

The next meaningful validation step is disciplined paper trading with realistic
costs, borrow, execution, margin, capacity, and reconciliation controls on
future data.
