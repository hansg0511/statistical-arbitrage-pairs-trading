# Transaction-Cost Sensitivity

This is a small historical sensitivity overlay on the frozen V2-selected
book. It does not change pair selection, sizing, Clean40, signal rules, or
the replay mechanisms.

## Frozen Strategy

- Leg A: `sp500-12m/same_sector_slide1m_noscreen`
- Leg B: `sp500-12m/same_sector_slide3m_noscreen`
- Sizing: V2 `gross_exposure`
- Clean40: 84-day lookback, 0.40 step, 10%--90% bounds, 50/50 initial weight
- Replay: Mechanisms A and B
- Periods: five existing recent starts and one historical control

## Cost Convention

Costs are one-way all-in basis points of traded notional. Native V2 share
quantities and recorded entry prices are scaled by the frozen replay
allocation. Exit notional uses the preserved exit-date close snapshot
because exact exit execution prices are not recorded. This is a historical
sensitivity proxy, not a live execution or broker model.

Scenarios are 0, 5, 10, and 20 bps. The 0 bps row is the gross baseline.

## Zero-Bps Reconciliation

- Runs checked: `12`
- Maximum equity-path difference: `0.000e+00`
- Maximum daily-return difference: `1.110e-16`
- Final equity difference: `0.000e+00`
- Status: **pass**

## Turnover

| Window | Mechanism | Mean trades | Mean traded notional | Mean turnover / initial capital |
|---|---|---:|---:|---:|
| historical | A | 2141.0 | $302,949,401 | 302.95x |
| historical | B | 2141.0 | $301,084,373 | 301.08x |
| recent | A | 746.8 | $105,762,925 | 105.76x |
| recent | B | 746.8 | $106,370,122 | 106.37x |

## Recent Aggregate

Recent rows are means across the same five starts used by the public
research. They are not a concatenated overlapping return series.

| Cost | A net annualized return | A net Sharpe | B net annualized return | B net Sharpe | Positive A/B starts |
|---:|---:|---:|---:|---:|---:|
| 0 | 9.44% | 1.256 | 8.82% | 1.160 | 5/5 |
| 5 | 6.67% | 0.881 | 6.02% | 0.786 | 5/5 |
| 10 | 3.84% | 0.506 | 3.16% | 0.413 | 5/4 |
| 20 | -2.01% | -0.237 | -2.75% | -0.326 | 1/1 |

## Historical Control

| Cost | A net annualized return | A net Sharpe | B net annualized return | B net Sharpe |
|---:|---:|---:|---:|---:|
| 0 | 3.55% | 0.772 | 3.66% | 0.801 |
| 5 | 0.75% | 0.174 | 0.89% | 0.203 |
| 10 | -2.40% | -0.417 | -2.22% | -0.388 |
| 20 | -10.28% | -1.548 | -9.97% | -1.523 |

## Cost Burden

The cost percentage is total transaction cost divided by gross PnL for
the same start and mechanism.

| Window | Mechanism | 5 bps cost / gross PnL | 10 bps cost / gross PnL | 20 bps cost / gross PnL |
|---|---|---:|---:|---:|
| recent | A | 31.95% | 63.90% | 127.79% |
| recent | B | 35.88% | 71.76% | 143.51% |
| historical | A | 80.00% | 160.00% | 319.99% |
| historical | B | 76.98% | 153.97% | 307.94% |

## Absolute Cost

| Window | Mechanism | Mean cost at 5 bps | Mean cost at 10 bps | Mean cost at 20 bps |
|---|---|---:|---:|---:|
| recent | A | $52,881 | $105,763 | $211,526 |
| recent | B | $53,185 | $106,370 | $212,740 |
| historical | A | $151,475 | $302,949 | $605,899 |
| historical | B | $150,542 | $301,084 | $602,169 |

## Approximate Break-Even Cost

Break-even is the one-way rate at which final net PnL reaches zero,
reported as an approximate interpolation from gross PnL and total
traded notional.

| Window | Mechanism | Per-start range | Recent mean | Recent median |
|---|---|---:|---:|---:|
| recent | A | 11.2--21.8 bps | 16.5 bps | 17.0 bps |
| recent | B | 9.4--21.0 bps | 15.2 bps | 17.1 bps |
| historical | A | 6.3--6.3 bps | n/a | n/a |
| historical | B | 6.5--6.5 bps | n/a | n/a |

## Interpretation

This overlay does not retune the candidate after observing costs. The
gross result is the 0 bps row; the 5, 10, and 20 bps rows show the
mechanical deterioration from the assumed traded-notional friction.

At 20 bps, 2/10 recent mechanism-start combinations have positive net annualized return.
At 20 bps, 0/2 historical mechanism-start combinations have positive net annualized return.

The study therefore measures cost sensitivity, not live implementability.
The next stage is forward paper testing with execution telemetry; no
historical strategy optimization follows from this overlay.

## Artifacts

- `tca_per_start.csv`
- `tca_summary.csv`
- `tca_break_even.csv`
- `sharpe_vs_cost.png`
- `annualized_return_vs_cost.png`
