# Methodology

## Scope

The system evaluates walk-forward equity-pairs strategies and combines their
recorded trade events into a shared-account research replay. The current public
candidate uses the V2 `gross_exposure` sizing convention. V1
`reference_leg` sizing remains available as a historical control.

The latest matrix uses four strategy bases:

- `core-2m`
- `sp500-2m`
- `core-12m`
- `sp500-12m`

Each base is crossed with eight pairing configurations: same-sector or
cross-sector, one-month or three-month slide, and no earnings screen or a
seven-day post-event block. This produces 32 standalone configurations.

## Pair Formation

Formation is performed inside each walk-forward fold. The tracked pipeline uses:

- log prices for the selected signal configuration;
- Engle-Granger cointegration testing with a `0.05` log-space p-value threshold;
- OLS intercept and hedge-ratio estimation;
- an optional `0.10` cumulative-return-divergence pre-filter;
- a positive log-space half-life filter;
- at most 20 selected pairs per fold; and
- same-sector or cross-sector restrictions supplied by the configuration.

The pair selector recomputes raw, log, and normalized diagnostics, but the
configured ranking and half-life filter use the log-space path. Pair selection
uses only information available through the formation boundary.

## Signal and Trade Rules

The selected configuration records the following shared strategy settings:

| Setting | Value |
|---|---:|
| Entry z-score | 2.2 |
| Exit z-score | 1.0 |
| Stop z-score | 4.5 |
| Residual validation window | 90 |
| z-score multiplier | 0.5 |
| Hedge-ratio guard threshold | 0.8 |
| Maximum holding period | 15 calendar days, loss-only check |
| Dollar-neutral mode | False |

Z-scores use the residual relationship and can lock the hedge ratio and rolling
standard deviation at entry. The hedge-ratio guard can close a position when the
relationship changes materially. Earnings-screen settings belong to each leg;
the V2 selected legs are both `sp500-12m` and use the no-screen configuration.

The 15-day limit is elapsed calendar time, not 15 trading sessions. Fold and
session termination also close positions that remain open at the boundary.

## V1 and V2 Sizing

Both sizing modes use an initial capital of `$1,000,000` and
`pct_per_pair=0.25`, so the configured pair budget is `$250,000`.

V1 treats that amount as the reference-leg notional and adds the hedge leg. Its
total gross exposure therefore varies with the hedge ratio.

V2 treats the same amount as the total two-leg gross budget. In log space the
integer-share conversion is:

```text
B = sizing_capital * equity_fraction
R = B / (1 + abs(hr_entry))
size2 = floor(R / price2)
size1 = floor(abs(size2 * hr_entry * price2 / price1))
gross = size1 * price1 + size2 * price2
```

V2 validates the resulting gross budget and never silently falls back to V1.
Integer rounding can leave unused budget, but the controlled matrix reported no
gross-budget overruns.

## Shared-Account Replay

The combined replay consumes recorded trade logs, daily marks, fold boundaries,
and target-notional information. It does not add the two legs' return
percentages. Instead, each trade event is marked through time and applied to a
common accounting pool.

The allocator uses a trailing Sharpe path calculated strictly before each
month. It starts at 50% Leg A weight, moves by the configured step, and respects
the configured bounds.

Mechanism A re-bases active fold sizing monthly. Mechanism B leaves each fold's
capital basis fixed and applies the current weight only to new entry flow. Open
trades are not forcibly rebalanced in either mechanism.

## Book Selection

The expanded comparison forms 496 unordered two-leg books from the standalone
configurations. Each mechanism has recent and historical scores, separate
recent/historical ranks, rank-average evidence, and joined-series evidence.

The current V2 candidate is:

- Leg A: `sp500-12m/same_sector_slide1m_noscreen`
- Leg B: `sp500-12m/same_sector_slide3m_noscreen`

The selected-book cross-check confirms the handoff candidate against the V2
ranking artifacts without rerunning the 496-book matrix or writing the V1
canonical outputs.

## Clean40 Allocation Audit

The allocator audit keeps the V2 book and V2 sizing fixed. It tests 40
lattice-aligned dynamic configurations:

- lookbacks: 42, 63, 84, 105, and 126 days;
- steps: 0.10, 0.20, 0.30, and 0.40; and
- aligned bounds: 40/60, 30/70, 20/80, and 10/90;
- plus a static 50/50 control.

The primary score is the maximin of the recent 20th-percentile Sharpe and the
historical Sharpe across both mechanisms. Tie-breaks use recent median floor,
recent mean Sharpe, historical mean Sharpe, worst drawdown, and lower allocator
turnover. A configuration is on the plateau when it is within 0.05 Sharpe of
the best robust floor.

The result kept the existing `lb84_s0.40_b0.10_0.90` allocator. This is an
allocator decision only; it does not reopen pair selection or signal tuning.

## Evaluation Windows

The V2 12-month recent starts are 2023-01-01 through 2023-05-01. The historical
12-month control starts on 2014-01-01 and corresponds to the preserved
2015--2019 test window. Recent metrics are means across five starts. Historical
metrics use one aligned control start.

Walk-forward folds are out of sample for individual strategy evaluation. The
book and allocator were selected after looking across the displayed windows, so
the aggregate candidate is not a portfolio-level holdout.
