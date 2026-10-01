# Reproducibility

## Environment

The project requires Python 3.10 or newer. Install the package and development
dependencies from the repository root:

```text
python -m pip install -e ".[dev]"
python -m pytest -q
```

## Published V1 Snapshot

These commands reproduce the tracked V1 public selection and replay artifacts
from the tracked event fixtures. They use the locked V1 configuration and are
not commands for the current V2 candidate:

```text
python research/portfolio_selection.py
python research/run_combined_backtest.py --window recent --mechanism both
python research/run_combined_backtest.py --window historical --mechanism both
python research/factor_report.py
python research/plot_public_results.py
python scripts/build_public_artifacts.py
```

The V1 replay input boundary is `results/final/event_replay_inputs/`. The
combined replay output is generated locally.

## Completed V2 Audit Artifacts

The V2 compact summaries are already generated and indexed in
[`results/README.md`](../results/README.md). Their raw run trees are intentionally
not part of the compact public artifact set.

The focused audit entry points are:

```text
python research/run_selected_book_crosscheck.py
python research/run_v2_book_clean40_retune.py
```

Both scripts use preserved local raw runs and write their fixed output
directories. They do not expose a separate `--help` mode and should not be
called with that flag.

The full matrix can be regenerated only when the preserved V1 and V2 raw trees
and deterministic snapshots are present:

```text
python research/run_sizing_v2_full_matrix.py --phase combined
```

The default roots are `results/sizing_v2_full/v1_canonical` and
`results/sizing_v2_full/v2`. A standalone or full run is substantially more
expensive and is outside the scope of this presentation pass.

## Inputs and Provenance

The V2 compact manifest records:

- 32 standalone configurations;
- 192 standalone run instances;
- 496 combined books;
- 992 combined rows per sizing mode;
- V1 and V2 sizing modes;
- the 84-day, 0.40, 10%--90% allocator; and
- hashes for the deterministic snapshots used by the completed matrix.

The full raw V2 run tree is excluded because it is large and environment-bound.
The compact matrix outputs, selected-book cross-check, and Clean40 result tree
are the public audit boundary for this branch.

## Transaction-Cost Overlay

With the preserved V2 raw runs and a compatible Python/NumPy environment:

```text
python research/run_transaction_cost_analysis.py
```

The preserved snapshots were generated under the project's Python 3.14/NumPy
environment on the research workstation. A different pickle/runtime
combination may require the corresponding compatible environment. The command
does not accept strategy, sizing, allocator, or cost-grid tuning arguments; it
uses the frozen study definition and writes
`results/transaction_cost_analysis/`.

## Verification Commands

For a documentation-only change, the required verification is:

```text
python -m pytest -q
git diff --check
```

Also inspect the generated manifest and summary files rather than trusting a
newly rerun result. The presentation branch does not rerun the 496-book matrix,
change pair selection, or regenerate the locked V1 public artifacts.
