# V2 Sizing Experiment

This is a limited, deterministic comparison of the existing reference-leg
sizing and the V2 gross-exposure sizing rule. It is diagnostic research, not a
change to the canonical V1 book. The runs use four recent profiles, two sizing
modes, one worker, and the preserved local price/pair inputs. The raw run tree
is intentionally ignored; the compact review tables are tracked under
`results/sizing_v2_summary/`.

## 1. Gross-Exposure Sizing

### Semantics

The production sizing call is in `PairTradingStrategy.next()` in
`src/backtest.py`. The execution chain is:

`research/run_sizing_v2_experiment.py` -> `research.run_experiment.run_experiment()` -> fold execution -> `PairTradingStrategy.next()` -> `calculate_pair_sizes()`.

There is one production call to `calculate_pair_sizes()`; the other calls are
tests and diagnostic recomputation. The call is made after the signal,
hedge-ratio guard, and earnings gates and immediately before the two entry
orders. It passes:

| Input | Production value |
|---|---|
| `sizing_capital` | `self.p.initial_cash`, fixed at `$1,000,000` in these runs |
| `equity_fraction` | `0.25` |
| `price1`, `price2` | current close prices at the sizing bar |
| `hr_entry` | current hedge ratio |
| `log_space` | `True` |
| `dollar_neutral` | `False` |
| `pair_sizing_mode` | `reference_leg` or `gross_exposure` |

The fixed budget in every run is therefore `$250,000` per entry attempt.

In `reference_leg` mode, the budget is the reference-leg notional. The hedge
leg is additional exposure. `pair_gross_budget` is recorded as a comparison
baseline and is not enforced.

In `gross_exposure` mode, the same budget is the total pair gross budget. In
log space the sizing conversion is:

```text
B = sizing_capital * equity_fraction
R = B / (1 + abs(hr_entry))
size2 = floor(R / price2)
size1 = floor(abs(size2 * hr_entry * price2 / price1))
gross = size1 * price1 + size2 * price2
```

The V2 result marks `pair_gross_budget_enforced=True` and rejects invalid
inputs rather than silently falling back to V1. `target_notional` remains only
as the legacy PnL-normalization field and equals `sizing_budget`.

The trade log now records the sizing mode, sizing capital and budget, entry
hedge ratio, reference-leg notional, sizing-time prices, share quantities,
execution prices, each leg's exposure, total gross exposure, long and short
exposure, and estimated initial and maintenance margin requirements. The
sizing-time fields make integer-rounding diagnostics independent of later
execution-price movement.

### Fixed replay results

Utilization values are multiples of current account equity. Margin assumptions
for the replay are 50% initial margin on both long and short legs, 25%
maintenance margin on long exposure, and 30% maintenance margin on short
exposure. `margin_behavior=off` is retained for this comparison, so these are
measurements rather than order-admission rules.

| Profile | Pair pool / selection window | Slide | Earnings screen | Test dates |
|---|---|---:|---|---|
| selected_leg_a_recent | `sp500_12m` / 12 months | 1 month | none | 2023-01-01 to 2026-01-01 |
| selected_leg_b_recent | `sp500_2m` / 2 months | 3 months | forward/post block 7 days | 2023-11-01 to 2026-01-01 |
| contrast_12m_slide3_recent | `sp500_12m` / 12 months | 3 months | none | 2023-01-01 to 2026-01-01 |
| contrast_2m_slide1_recent | `sp500_2m` / 2 months | 1 month | none | 2023-01-01 to 2026-01-01 |

| Profile | Mode | Ann. return | Volatility | Sharpe | Max drawdown | Trades | Win rate | Gross avg | Gross median | Gross p95 | Gross peak | Initial margin avg | Initial margin p95 | Initial margin peak | Maintenance avg | Maintenance p95 | Maintenance peak |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| selected_leg_a_recent | reference_leg | 14.1933% | 12.0656% | 1.3650 | -15.2280% | 548 | 54.5620% | 1.0229 | 0.9547 | 2.0048 | 2.6814 | 0.5115 | 1.0024 | 1.3407 | 0.2810 | 0.5527 | 0.7347 |
| selected_leg_a_recent | gross_exposure | 7.0161% | 5.9953% | 1.1805 | -7.4015% | 548 | 54.5620% | 0.5556 | 0.5069 | 1.0870 | 1.6390 | 0.2778 | 0.5435 | 0.8195 | 0.1525 | 0.2995 | 0.4376 |
| selected_leg_b_recent | reference_leg | -3.7700% | 10.2615% | -0.3244 | -11.3139% | 108 | 44.4444% | 0.4791 | 0.0000 | 2.2294 | 4.6715 | 0.2396 | 1.1147 | 2.3358 | 0.1317 | 0.6076 | 1.2754 |
| selected_leg_b_recent | gross_exposure | -0.4577% | 6.0949% | -0.0453 | -5.4119% | 108 | 44.4444% | 0.2688 | 0.0000 | 1.1998 | 1.9585 | 0.1344 | 0.5999 | 0.9793 | 0.0740 | 0.3310 | 0.5353 |
| contrast_12m_slide3_recent | reference_leg | 14.9198% | 15.5874% | 0.9697 | -9.5331% | 200 | 53.5000% | 1.1573 | 1.0016 | 2.8592 | 6.6316 | 0.5787 | 1.4296 | 3.3158 | 0.3186 | 0.7846 | 1.8754 |
| contrast_12m_slide3_recent | gross_exposure | 6.1665% | 7.8615% | 0.8002 | -4.8784% | 200 | 53.5000% | 0.5999 | 0.5083 | 1.4589 | 2.2824 | 0.3000 | 0.7294 | 1.1412 | 0.1647 | 0.4030 | 0.6420 |
| contrast_2m_slide1_recent | reference_leg | -2.1166% | 10.4539% | -0.1571 | -17.1614% | 773 | 47.2186% | 0.9859 | 0.9255 | 2.0092 | 2.8104 | 0.4929 | 1.0046 | 1.4052 | 0.2715 | 0.5583 | 0.7661 |
| contrast_2m_slide1_recent | gross_exposure | -1.7845% | 6.3101% | -0.2546 | -11.9273% | 773 | 47.2186% | 0.5632 | 0.5136 | 1.1253 | 1.5827 | 0.2816 | 0.5626 | 0.7913 | 0.1551 | 0.3138 | 0.4434 |

The selected pair and entry decisions did not change when only the sizing mode
changed. The exact trade counts were 548, 108, 200, and 773 by profile, with
zero V1-only trades, zero V2-only trades, zero changed exit reasons, matching
entry keys, matching selected pair keys, matching signal inputs, and matching
rejection multisets. The two selected profiles also matched their public
reference daily returns, trade marks, and trade-log keys. This comparison
checks selected `(fold_id, pair, rank)` keys; it does not publish a complete
candidate-universe ranking artifact.

### Sizing diagnostics

The budget ratio is actual gross entry exposure divided by the recorded
`pair_gross_budget`. The rounding check uses sizing-time prices and the
following conservative log-space bound:

```text
budget - sizing_gross <= price1 + (1 + abs(hr_entry)) * price2
```

The raw-space diagnostic uses `price1 + price2 + abs(hr_entry) * price1`.

| Profile | Mode | Gross ratio mean | Gross ratio median | Gross ratio p95 | Gross ratio peak | Mean absolute budget error | Median absolute budget error | p95 absolute budget error | Max absolute budget error | HR error p95 | Rounding violations | Budget overruns | Invariant |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| selected_leg_a_recent | reference_leg | 1.8714 | 1.8101 | 2.7310 | 4.0539 | n/a | n/a | n/a | n/a | 0.001424 | n/a | n/a | n/a |
| selected_leg_a_recent | gross_exposure | 0.998940 | 0.999295 | 0.999816 | 0.999970 | $264.93 | $176.16 | $765.62 | $1,940.55 | 0.003006 | 0 | 0 | pass |
| selected_leg_b_recent | reference_leg | 1.7414 | 1.6395 | 2.4378 | 3.4178 | n/a | n/a | n/a | n/a | 0.001675 | n/a | n/a | n/a |
| selected_leg_b_recent | gross_exposure | 0.999051 | 0.999298 | 0.999870 | 0.999990 | $237.24 | $175.40 | $624.89 | $1,080.46 | 0.002058 | 0 | 0 | pass |
| contrast_12m_slide3_recent | reference_leg | 1.9635 | 1.8655 | 3.3955 | 4.0539 | n/a | n/a | n/a | n/a | 0.001401 | n/a | n/a | n/a |
| contrast_12m_slide3_recent | gross_exposure | 0.998976 | 0.999351 | 0.999839 | 0.999958 | $256.05 | $162.22 | $733.68 | $1,940.55 | 0.003279 | 0 | 0 | pass |
| contrast_2m_slide1_recent | reference_leg | 1.7350 | 1.6389 | 2.6075 | 4.3005 | n/a | n/a | n/a | n/a | 0.001483 | n/a | n/a | n/a |
| contrast_2m_slide1_recent | gross_exposure | 0.999002 | 0.999324 | 0.999886 | 0.999990 | $249.49 | $169.02 | $626.03 | $6,676.75 | 0.002176 | 0 | 0 | pass |

The largest V2 shortfall is the `NVR-TSCO` entry on 2025-06-05 in the
2-month/1-month contrast. It has `size1=14`, `size2=2849`, a `$7,194.47`
first-leg sizing price, a `$50.05` second-leg price, and a `$6,676.75`
shortfall. The calculated log-space rounding bound is `$7,282.20`, so this is
an expected integer-share under-allocation, not a gross-budget violation.

## 2. Sizing-Capital Audit

The audit is implemented in `research/run_sizing_capital_audit.py` and consumes
the ignored raw `sizing_audit.csv` files. It does not change strategy sizing,
order admission, or the canonical results.

At each pre-entry sizing attempt the strategy records:

| Field | Meaning |
|---|---|
| `initial_equity` / `sizing_capital` | Fixed `self.p.initial_cash`, `$1,000,000` in this experiment |
| `current_equity` | `broker.getvalue()` at the entry decision, including marked unrealized PnL |
| `current_cash` | `broker.getcash()` at the same point; observed, not used as the sole capacity proxy |
| `current_gross_exposure` | Marked dollar exposure of open long and short legs |
| `current_initial_margin_required` | Estimated initial margin on existing positions |
| `naive_dynamic_budget` | `current_equity * equity_fraction`, a hypothetical alternative budget |
| `free_funded_capacity` | `current_equity - current_gross_exposure` |
| `free_margin` | `current_equity - current_initial_margin_required` |

The fixed experiment uses Backtrader broker leverage `100.0` and submits both
legs with `set_coc(True)`. Cash can include short-sale proceeds and can differ
substantially from net liquidation equity. The audit therefore reports cash,
equity, existing exposure, and margin separately. It does not call
`getvalue()` from production sizing and does not claim that either diagnostic
headroom measure is deployable cash.

The fully-funded model independently asks whether a hypothetical current-equity
size would fit in `current_equity - current_gross_exposure`. The margin model
independently asks whether its estimated initial margin would fit in
`current_equity - current_initial_margin_required`. The current equity in both
models includes unrealized PnL; a production policy would need to decide
whether unrealized gains are deployable and specify broker, borrow, settlement,
and liquidation rules.

| Profile | Mode | Equity ratio median / mean | Equity ratio p5 / p95 | Dynamic budget ratio median / mean | Current cash mean | Cash minus equity mean |
|---|---|---:|---:|---:|---:|---:|
| selected_leg_a_recent | reference_leg | 1.0039 / 1.0165 | 0.9447 / 1.1335 | 1.0039 / 1.0165 | $1,533,061 | $516,535 |
| selected_leg_a_recent | gross_exposure | 1.0017 / 1.0087 | 0.9703 / 1.0670 | 1.0017 / 1.0087 | $1,279,683 | $270,953 |
| selected_leg_b_recent | reference_leg | 1.0000 / 1.0017 | 0.9499 / 1.0598 | 1.0000 / 1.0017 | $1,424,692 | $423,020 |
| selected_leg_b_recent | gross_exposure | 1.0000 / 1.0037 | 0.9677 / 1.0397 | 1.0000 / 1.0037 | $1,228,622 | $224,908 |
| contrast_12m_slide3_recent | reference_leg | 1.0033 / 1.0195 | 0.9398 / 1.1335 | 1.0033 / 1.0195 | $1,606,772 | $587,322 |
| contrast_12m_slide3_recent | gross_exposure | 1.0011 / 1.0099 | 0.9734 / 1.0647 | 1.0011 / 1.0099 | $1,302,736 | $292,870 |
| contrast_2m_slide1_recent | reference_leg | 1.0000 / 1.0012 | 0.9192 / 1.0802 | 1.0000 / 1.0012 | $1,498,738 | $497,547 |
| contrast_2m_slide1_recent | gross_exposure | 1.0000 / 0.9996 | 0.9430 / 1.0461 | 1.0000 / 0.9996 | $1,283,660 | $284,075 |

The full distribution, including current equity, cash, current exposure,
existing margin, and capacity extrema, is in
`results/sizing_v2_summary/sizing_capital_audit.csv`.

## 3. Capacity-Conflict Audit

Conflict rates below use valid sizing attempts as the denominator. They are
not counts of every signal because the strategy records separate audit rows for
hedge-ratio, earnings, and other pre-sizing gates. Direct conflicts test each
opportunity against its observed pre-entry state independently. Sequential
conflicts apply a deterministic same-day reservation ledger in audit order so
that an admitted hypothetical entry reduces capacity for later entries on the
same date.

| Profile | Mode | Profile dates | Attempts | Fully funded fit / conflict | Fully funded conflict rate | Margin fit / conflict | Margin conflict rate | Sequential funded conflicts | Sequential margin conflicts | Fully funded conflict dates | Same-day groups / opportunities / max |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| selected_leg_a_recent | reference_leg | 2023-01-01 to 2026-01-01 | 554 | 171 / 383 | 69.13% | 408 / 146 | 26.35% | 420 | 181 | 2024-01-04 to 2025-12-16 | 110 / 271 / 9 |
| selected_leg_a_recent | gross_exposure | 2023-01-01 to 2026-01-01 | 554 | 395 / 159 | 28.70% | 552 / 2 | 0.36% | 215 | 8 | 2024-01-04 to 2025-11-12 | 110 / 271 / 9 |
| selected_leg_b_recent | reference_leg | 2023-11-01 to 2026-01-01 | 110 | 64 / 46 | 41.82% | 85 / 25 | 22.73% | 60 | 31 | 2024-01-22 to 2025-10-07 | 23 / 61 / 6 |
| selected_leg_b_recent | gross_exposure | 2023-11-01 to 2026-01-01 | 110 | 84 / 26 | 23.64% | 109 / 1 | 0.91% | 31 | 4 | 2024-07-11 to 2025-06-25 | 23 / 61 / 6 |
| contrast_12m_slide3_recent | reference_leg | 2023-01-01 to 2026-01-01 | 203 | 48 / 155 | 76.35% | 141 / 62 | 30.54% | 167 | 80 | 2024-01-04 to 2025-12-16 | 40 / 100 / 9 |
| contrast_12m_slide3_recent | gross_exposure | 2023-01-01 to 2026-01-01 | 203 | 139 / 64 | 31.53% | 202 / 1 | 0.49% | 89 | 3 | 2024-01-04 to 2025-11-12 | 40 / 100 / 9 |
| contrast_2m_slide1_recent | reference_leg | 2023-01-01 to 2026-01-01 | 778 | 295 / 483 | 62.08% | 607 / 171 | 21.98% | 551 | 233 | 2023-03-13 to 2025-11-07 | 163 / 425 / 7 |
| contrast_2m_slide1_recent | gross_exposure | 2023-01-01 to 2026-01-01 | 778 | 551 / 227 | 29.18% | 757 / 21 | 2.70% | 308 | 44 | 2023-04-26 to 2025-11-03 | 163 / 425 / 7 |

Gross-exposure sizing materially reduces both exposure-based and margin-based
conflicts relative to reference-leg sizing, but it does not make every
hypothetical entry admissible. The remaining fully-funded conflicts are the
result of existing gross exposure and the current-equity hypothetical budget;
the margin results are much less restrictive under the simple 50% assumptions.
Sequential conflicts are larger where several pairs compete for the same
pre-entry headroom, which is why same-day state consistency matters.

The capacity policy is intentionally not enabled in production by this change.
Before using dynamic sizing or rejection, choose and document one explicit
policy for deployable capital, unrealized PnL, initial and maintenance margin,
short-sale proceeds, borrow, and same-day reservation ordering. The current
fixed V2 implementation is the safer review boundary: it makes pair gross
exposure explicit while leaving capacity admission as a separate, testable
decision.

## Reproduction

From the repository root, with the preserved local inputs present:

```text
python -m pytest -q
python research/run_sizing_v2_experiment.py
python research/run_sizing_capital_audit.py
```

The experiment refuses missing deterministic inputs and does not fall back to
live downloads or live pair selection. The compact outputs are:

- `results/sizing_v2_summary/v1_vs_v2_metrics.csv`
- `results/sizing_v2_summary/sizing_capital_audit.csv`

The raw per-run tables, including trade metadata and pre-entry sizing audit
rows, remain under ignored `results/sizing_v2/`.
