# Consolidated combined book: mechanisms A & B


Trade-event replay of the two pct=0.25 legs into a **single shared 1M account**. Each leg keeps its native walk-forward grid, universe and per-fold structure; the combination happens at the trade-event level (real entry/exit dates, per-trade daily marks). No forced rebalancing in either mechanism - open trades ride to their logged exits.

Pairs are modeled as cash-neutral (buy ~notional one leg / short ~notional the other), matching the engine, which never rejects on cash in these runs. The momentum weight (trailing 63d Sharpe, +/-10% step, clamp 25-75%) sets the leg capital split.

**Mechanism A** - monthly re-base of fold capital to `w_L * C / n_active`; new entries sized `0.25 * basis`. Weight re-applied monthly (approximates the CSV momentum book).

**Mechanism B** - fold basis locked at fold start (`C / n_active_L`, equal slice of that leg); each entry sized `0.25 * w_L(entry month) * basis`; no monthly re-tilt, the leg split drifts.

Weight timing is causal (trailing 63d Sharpe **strictly before** each month). The CSV book used data through the month, a subtle in-sample tilt that the simulator removes.

## Recent window

| Series | Sharpe | Ann ret | Ann vol | MDD | days | note |
|---|---:|---:|---:|---:|---:|---|
| Leg A sp500-12m cross1m noscreen | 0.850 | 10.00% | 12.07% | -15.2% |  |  |
| Leg B sp500-2m cross3m bd7 | -0.324 | -3.77% | 10.26% | -11.3% |  |  |
| CSV book (return arithmetic) | n/a | n/a | n/a | n/a | | not regenerated; legacy artifact absent |
| Consolidated mech A | 0.523 | 4.22% | 8.62% | -6.9% | 492 | final=1.08M, PnL err=0k |
| Consolidated mech B | 0.612 | 5.03% | 8.62% | -6.2% | 492 | final=1.10M, PnL err=0k |

### Validation

| Mechanism | initial | final | sum daily pnl | |final-initial - sum pnl| |
|---|---:|---:|---:|---:|
| A | 1.000M | 1.0841M | 0.0841M | 0.00 |
| B | 1.000M | 1.1006M | 0.1006M | 0.00 |

Rejected entries (no basis): 0 in both mechanisms (fold basis is always set before its first entry).

## Historical window

| Series | Sharpe | Ann ret | Ann vol | MDD | days | note |
|---|---:|---:|---:|---:|---:|---|
| Leg A sp500-12m cross1m noscreen | 0.371 | 2.67% | 7.97% | -19.0% |  |  |
| Leg B sp500-2m cross3m bd7 | 0.878 | 7.69% | 8.88% | -8.8% |  |  |
| CSV book (return arithmetic) | n/a | n/a | n/a | n/a | | not regenerated; legacy artifact absent |
| Consolidated mech A | 1.139 | 8.08% | 7.04% | -5.1% | 1258 | final=1.47M, PnL err=0k |
| Consolidated mech B | 1.094 | 7.73% | 7.03% | -5.1% | 1258 | final=1.45M, PnL err=0k |

### Validation

| Mechanism | initial | final | sum daily pnl | |final-initial - sum pnl| |
|---|---:|---:|---:|---:|
| A | 1.000M | 1.4738M | 0.4738M | 0.00 |
| B | 1.000M | 1.4500M | 0.4500M | 0.00 |

Rejected entries (no basis): 0 in both mechanisms (fold basis is always set before its first entry).

## Reading

- **CSV arithmetic comparison:** the legacy CSV book is not present, so no CSV-vs-consolidated claim is made here.

- **Mech B vs A:** B locks each fold basis at fold start. Recent Sharpe/return are 0.612 / 5.03% for B versus 0.523 / 4.22% for A; historical values are 1.094 / 7.73% for B versus 1.139 / 8.08% for A.

- The standalone legs already embed their own fold-overlap normalization (leg B = capital-weighted blend of 2-3 overlapping 1M folds), so the shared-account book inherits that structure unchanged.

