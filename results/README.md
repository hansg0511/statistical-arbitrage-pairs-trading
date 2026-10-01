# Results Index

This directory contains several result generations. The paths below are kept
separate so that an older canonical V1 replay is not confused with the latest V2
candidate or with a focused diagnostic.

## Current V2 Presentation Sources

### Full V1/V2 Matrix

`results/sizing_v2_full_summary/` contains the compact output of the completed
V1/V2 sizing comparison:

- `report.md`: human-readable standalone and combined-book tables;
- `combined_v2_rankings.csv`: 992 V2 combined ranking rows;
- `combined_v2_scores.csv`: raw V2 combined scores;
- `combined_v1_rankings.csv` and `combined_v1_scores.csv`: V1 control tables;
- `standalone_v1_v2.csv`: standalone comparison;
- `standalone_decision_comparison.csv`: selection-decision comparison;
- `combined_rank_delta.csv`: V1-to-V2 rank changes; and
- `full_manifest.json`: counts, input hashes, and validation metadata.

The raw run tree is separate under `results/sizing_v2_full/` and is not part of
the compact public boundary.

### Selected-Book Cross-Check

`results/v1_v2_selected_book_crosscheck/` compares the earlier V1-selected book
and the current V2-selected book under both sizing conventions. It reports
trade-identity, replay-PnL, native-exposure, gross-budget, and protected-output
checks.

Start with:

- `selected_book_crosscheck_summary.md`;
- `selected_book_crosscheck_summary.json`; and
- `allocator_path_attribution.csv`.

### Clean40 Audit

`results/v2_book_clean40_retune/` contains the fixed-V2-book allocator audit.
The principal files are:

- `clean40_summary.md` and `clean40_summary.json`;
- `clean40_aggregate_rankings.csv`;
- `clean40_static_50_50_comparison.csv`;
- `clean40_neighbor_sensitivity.csv`;
- `clean40_leave_one_start_out.csv`;
- `clean40_cost_sensitivity.csv`;
- `baseline_per_start.csv`;
- concentration and period attribution CSVs; and
- four presentation figures for equity, weights, and robustness surfaces.

The machine-readable summary reports `status: pass`, unchanged protected
hashes, valid V2 native exposure, valid gross budgets, and no full-matrix rerun.

## Transaction-Cost Sensitivity

`results/transaction_cost_analysis/` is the final small historical sensitivity
overlay on the frozen V2 candidate. It contains:

- `tca_per_start.csv`: all five recent starts, the historical control, both mechanisms, and 0/5/10/20 bps;
- `tca_summary.csv`: recent and historical means using the public aggregation convention;
- `tca_break_even.csv`: per-start and recent mean/median break-even estimates;
- `tca_summary.md`: interpretation, turnover, reconciliation, and tables; and
- two compact plots for Sharpe and annualized return versus cost.

The 0 bps rows reproduce the Clean40 gross metrics within numerical tolerance.
The exit-cost proxy uses exit-date close snapshots because exact exit execution
prices are not present in the preserved compact trade logs. This is not a full
execution model; observed live implementation costs remain unknown. Historical
research is frozen, and future validation belongs to forward paper trading.

## Historical V1 Public Snapshot

`results/final/` is the earlier locked V1 public artifact set. Its manifest,
event fixtures, rankings, metrics, factor snapshot, and figures remain
unchanged. It is the source for the V1 reproduction commands and historical
control, not the current V2 headline table.

## Other Diagnostics

`results/old_winner_v1_v2_autopsy/` contains the earlier V1-winner and exposure
path investigations. Those files explain why the V2 candidate required a
focused cross-check, but they are not additional current performance claims.

## Provenance Rule

Read the manifest and summary beside a result before comparing numbers across
directories. In particular, the V2 matrix standalone score and the later
Clean40 full-file leg diagnostic use different evaluation-window conventions;
the difference is documented in [`docs/results.md`](../docs/results.md).
