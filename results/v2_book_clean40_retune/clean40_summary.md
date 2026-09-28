# V2 Book Clean40 Robustness Audit and Retune

This experiment keeps the current V2-selected book and V2 gross-exposure
sizing fixed. It audits the frozen Clean40 configuration before evaluating
a predeclared lattice-aware parameter grid against a static 50/50 replay.

## Research Boundary

- V2-selected Leg A: `sp500-12m/same_sector_slide1m_noscreen`
- V2-selected Leg B: `sp500-12m/same_sector_slide3m_noscreen`
- Ranking identity verified against current artifacts: **True**
- Sizing mode: **gross_exposure**; pair budget: `$250,000`
- Frozen Clean40 baseline: `lb84_s0.40_b0.10_0.90`
- Full-matrix rerun: **False**; pair/book selection changes: **False**

## Baseline Per-Start Results

Metrics below are the current V2 book under V2 sizing and frozen Clean40.
Recent rows are not averaged together in this table.

| Window | Start | Mech | Sharpe | Ann return | Vol | MDD | Trades | Win rate | Mean gross leverage | Peak gross leverage | Allocator changes |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| historical | 1 | A | 0.772 | 3.55% | 4.66% | -6.10% | 2141 | 53.62% | 0.618x | 1.826x | 15 |
| historical | 1 | B | 0.801 | 3.66% | 4.62% | -6.10% | 2141 | 53.62% | 0.618x | 1.753x | 15 |
| recent | 1 | A | 1.358 | 9.90% | 7.14% | -3.20% | 830 | 57.83% | 0.644x | 2.271x | 7 |
| recent | 1 | B | 1.357 | 9.92% | 7.16% | -3.22% | 830 | 57.83% | 0.638x | 2.263x | 7 |
| recent | 2 | A | 0.917 | 5.93% | 6.51% | -3.48% | 773 | 56.40% | 0.592x | 2.175x | 5 |
| recent | 2 | B | 0.785 | 5.07% | 6.58% | -4.49% | 773 | 56.40% | 0.600x | 2.169x | 5 |
| recent | 3 | A | 1.465 | 13.03% | 8.61% | -4.67% | 748 | 59.36% | 0.598x | 2.702x | 9 |
| recent | 3 | B | 1.439 | 12.81% | 8.64% | -4.67% | 748 | 59.36% | 0.612x | 2.700x | 9 |
| recent | 4 | A | 1.393 | 10.50% | 7.36% | -3.23% | 715 | 59.02% | 0.625x | 2.271x | 9 |
| recent | 4 | B | 1.339 | 10.05% | 7.35% | -3.45% | 715 | 59.02% | 0.621x | 2.263x | 9 |
| recent | 5 | A | 1.146 | 7.82% | 6.76% | -3.33% | 668 | 57.93% | 0.584x | 2.175x | 5 |
| recent | 5 | B | 0.883 | 6.24% | 7.14% | -5.10% | 668 | 57.93% | 0.596x | 2.169x | 5 |

## Calendar and Fold Concentration

Calendar PnL is attributed by the actual daily replay PnL. Period
contribution is additive PnL divided by initial capital; it is not a
claim that calendar periods are independent samples.

- Recent total PnL is distributed across `96` year/quarter rows; historical across `50`.
- Top recent calendar-quarter share of total PnL: `35.63%`.
- Positive recent fold observations: `147` of `200`; top-fold PnL share: `33.63%`.
- Removing the best recent fold changes mean Sharpe from `1.208` to `0.861`.

The report does not assign unobserved regime labels. The observable
contrast is calendar period: the current V2 book is tested on the
recent 2024--2025 12-month-selection runs versus the 2015--2019
historical control represented by the preserved 09b run.

## Trade, Pair, and Symbol Concentration

- Recent top-trade absolute-PnL share: `1.50%`; trade HHI: `0.0036`.
- Removing the best trade changes recent mean Sharpe from `1.208` to `1.115`.
- Removing the best five trades changes recent mean Sharpe to `0.853`.
- Recent top-pair absolute-PnL share: `3.20%`; worst pair: `ADI-WDC`.
- Recent top-symbol absolute-PnL share uses an equal 50/50 attribution of each pair trade to its two symbols; it is a concentration diagnostic, not leg-level causal PnL: `2.18%`.

## Clean40 Dependence and Standalone Legs

- Frozen Clean40 mean recent Leg A weight: `63.12%`; fraction at 50/50: `22.40%`.
- Frozen Clean40 mean daily time at bounds: lower `22.40%`, upper `55.20%`; mean monthly changes: `7.000`.
- Standalone Leg A recent/historical Sharpe: `1.458` / `0.420`.
- Standalone Leg B recent/historical Sharpe: `0.966` / `0.463`.
- Daily A/B return correlation: `0.776`; rolling 63-day range: `0.254` to `0.969`.
- Static 50/50 recent/historical mean Sharpe: `1.237` / `0.503`.

## Predeclared Search and Selection

- Lookbacks: `42, 63, 84, 105, 126` days.
- Steps: `0.10, 0.20, 0.30, 0.40`.
- Bounds presets: 50/50 static control, 40/60, 30/70, 20/80, 10/90.
- Lattice-aligned dynamic configurations evaluated: `40`; static control: `1`.
- Primary robustness criterion: maximin floor of each mechanism's recent 20th-percentile Sharpe and historical Sharpe.
- Selection tie-breaks: minimum recent median Sharpe floor, recent mean Sharpe, historical mean Sharpe, worst drawdown, then lower allocator turnover.
- Plateau definition: within `0.05` Sharpe of the best robust floor.

| Configuration | Robust floor | Recent mean Sharpe | Historical mean Sharpe | Worst MDD | Annualized allocator turnover | Plateau |
|---|---:|---:|---:|---:|---:|---|
| `lb84_s0.40_b0.10_0.90` | 0.772 | 1.208 | 0.786 | -6.10% | 155.39% | True |
| `lb84_s0.20_b0.10_0.90` | 0.768 | 1.207 | 0.772 | -6.50% | 116.73% | True |
| `lb63_s0.20_b0.10_0.90` | 0.762 | 1.222 | 0.782 | -5.79% | 137.50% | True |
| `lb105_s0.20_b0.10_0.90` | 0.749 | 1.221 | 0.761 | -6.84% | 110.07% | True |
| `lb126_s0.20_b0.10_0.90` | 0.745 | 1.226 | 0.765 | -7.25% | 101.84% | True |
| `lb84_s0.10_b0.10_0.90` | 0.743 | 1.242 | 0.746 | -6.74% | 79.51% | True |
| `lb63_s0.10_b0.10_0.90` | 0.734 | 1.248 | 0.757 | -6.53% | 88.55% | True |
| `lb105_s0.10_b0.10_0.90` | 0.724 | 1.254 | 0.739 | -6.93% | 75.10% | True |
| `lb105_s0.40_b0.10_0.90` | 0.711 | 1.253 | 0.724 | -7.20% | 149.48% | False |
| `lb84_s0.30_b0.20_0.80` | 0.710 | 1.220 | 0.723 | -6.07% | 115.88% | False |

## Neighbor and Leave-One-Start-Out Checks

- Best dynamic configuration under the predeclared rule: `lb84_s0.40_b0.10_0.90`.
- Dynamic plateau size: `8` configurations.
- Neighbor rows inspected: `6`.
- Leave-one-start-out selected regions: `1`.

| Neighbor | Relation | Robust floor | Recent mean Sharpe | Historical mean Sharpe |
|---|---|---:|---:|---:|
| `lb105_s0.40_b0.10_0.90` | lookback_neighbor | 0.711 | 1.253 | 0.724 |
| `lb126_s0.40_b0.10_0.90` | lookback_neighbor | 0.690 | 1.266 | 0.703 |
| `lb42_s0.40_b0.10_0.90` | lookback_neighbor | 0.488 | 1.344 | 0.503 |
| `lb63_s0.40_b0.10_0.90` | lookback_neighbor | 0.704 | 1.208 | 0.719 |
| `lb84_s0.20_b0.10_0.90` | step_neighbor | 0.768 | 1.207 | 0.772 |
| `lb84_s0.40_b0.10_0.90` | selected | 0.772 | 1.208 | 0.786 |

## Decision

- Final research decision: **keep_old_clean40**.
- Candidate dynamic configuration: `lb84_s0.40_b0.10_0.90`.
- Existing frozen Clean40 robust floor: `0.772`.
- Candidate dynamic robust floor: `0.772`.
- Static 50/50 robust floor: `0.491`.

The decision is intentionally not based on the highest recent Sharpe.
The V2 book and V2 sizing remain fixed. A dynamic candidate is only
preferred when it clears the predeclared robustness margin and lives in
a plateau; otherwise the existing allocator or static 50/50 remains the
more defensible live-research control.

## Turnover and Live Readiness

- Cost sensitivity uses allocator-only one-way capital movement at `1.0, 5.0, 10.0, 20.0` bps; pair entry/exit costs are not modeled.
- Already modeled: preserved trade events, walk-forward fold boundaries, integer-share V2 sizing, V2 gross budgets, entry/exit dates, and native marked exposure.
- Simplified but acceptable for current research: shared-account bookkeeping, no forced rebalancing of open trades, and replay-level monthly allocator timing.
- Must be addressed in paper trading: commissions, spread/slippage, borrow availability/cost, partial fills, simultaneous two-leg execution, symbol overlap, and deployable-capital policy.
- Must be addressed before live capital: broker margin/maintenance rules, borrow and locate constraints, corporate-action/dividend treatment, stale/missing price handling, operational reconciliation, and hard gross/single-symbol/pair exposure limits.

## What This Does Not Establish

- It does not create an independent portfolio holdout; the displayed recent and historical windows already informed prior book selection.
- It does not prove factor-neutral alpha or live profitability; prior diagnostics found short-term-reversal exposure and insignificant alpha.
- It does not validate broker execution, borrow, costs, or capacity.
- It does not justify changing pair selection, pair parameters, V2 sizing, or the locked canonical configuration.

## Falsifiers

- A future paper-trading period with materially negative or unstable returns after realistic costs.
- Repeated concentration in one pair, symbol, fold, or allocator flip that fails to reproduce out of sample.
- Native exposure or trade-identity reconciliation failure.
- A live-capital policy that cannot support the observed gross, margin, borrow, or partial-fill requirements.

## Artifacts

- `baseline_per_start.csv`
- `baseline_daily.csv`
- `baseline_period_attribution.csv`
- `baseline_fold_attribution.csv`
- `baseline_fold_leave_one_out.csv`
- `baseline_trade_concentration.csv`
- `baseline_trade_contributions.csv`
- `baseline_pair_concentration.csv`
- `baseline_symbol_concentration.csv`
- `baseline_leg_diagnostics.csv`
- `clean40_grid_results.csv`
- `clean40_mechanism_aggregate.csv`
- `clean40_aggregate_rankings.csv`
- `clean40_neighbor_sensitivity.csv`
- `clean40_leave_one_start_out.csv`
- `clean40_static_50_50_comparison.csv`
- `clean40_turnover_analysis.csv`
- `clean40_cost_sensitivity.csv`
- `clean40_summary.json`
- `clean40_summary.md`
- `baseline_equity_recent.png`
- `baseline_weight_recent.png`
- `clean40_surface_recent.png`
- `clean40_surface_historical.png`
