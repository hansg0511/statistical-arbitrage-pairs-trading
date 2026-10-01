# Limitations

## Selection Is Not a Portfolio Holdout

Individual pair strategies are evaluated on walk-forward test folds, but the
book, V2 candidate, and allocator were chosen after comparing recent and
historical results. Those aggregate windows are therefore not an untouched
portfolio-level holdout. The next meaningful evidence must come from future or
paper-trading observations.

## Replay Is Not Broker Execution

The shared-account replay is an accounting simulation over preserved trade
events and daily marks. It does not enforce or estimate:

- commissions, bid-ask spread, slippage, or financing;
- borrow availability, locate failures, or borrow cost;
- partial fills, leg asynchrony, or simultaneous execution risk;
- broker cash settlement and margin admission;
- maintenance calls or liquidation policy; or
- a deployable-capital and same-day reservation policy.

`margin_behavior=off` remains part of the preserved research boundary. Reported
margin fields are diagnostics, not order-admission decisions.

## Exposure and Capacity

V2 controls each pair's total gross entry budget, but the shared book can still
carry leverage across active pairs. Recent Clean40 runs reached approximately
2.7x peak gross leverage in the selected-book replay. There is no locked hard
gross, symbol, pair, or broker-margin cap.

Pair overlap can concentrate several trades in the same underlying name. The
concentration checks reduce uncertainty about whether one trade explains the
result, but they do not establish capacity or diversify idiosyncratic risk.

## Data and Universe Boundaries

The research uses fixed universe and price snapshots for the completed runs.
Constituent changes, survivorship, corporate actions, stale prices, missing
prices, and vendor-data revisions require separate controls. A clean rerun with
different source data is not guaranteed to reproduce every raw trade.

## Factor Interpretation

The pinned factor report under `results/final/factors/` belongs to the earlier V1
public snapshot. It found recurring recent market and short-term-reversal
loadings and no conventionally significant alpha estimate. It is not a fresh
factor-neutrality study of the V2 candidate, so it is not presented as one.

More generally, a factor regression is a diagnostic about the tested return
stream. It does not prove factor-neutral excess return or future Sharpe
persistence.

## Metric Boundaries

The V2 matrix's canonical standalone selection score for Leg A historical
performance is approximately 0.532 Sharpe. The later Clean40 full-file
diagnostic reports approximately 0.420. The difference is caused by the
evaluation-window convention, including ramp-up and wind-down rows in the later
diagnostic. These values must not be mixed as if they were one metric.

## Next Validation Gate

Before any live-capital claim, the candidate needs a paper-trading period with
timestamped orders, realistic costs and slippage, borrow and locate records,
partial-fill handling, broker margin rules, gross and symbol limits, corporate
action treatment, stale-price controls, and operational reconciliation.
