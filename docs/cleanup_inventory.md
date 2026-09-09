# Cleanup Inventory

This inventory records the public-cleanup baseline before implementation.

## Baseline

- Pre-cleanup commit: `8dc3ac60cf0ceb7c2c648dcc0d444849e5d34f5e`
- Archival tag: `pre-public-cleanup-20260909`
- Selected configuration: `research/selected_book_config.json`
- Locked leg A: `sp500-12m/cross_sector_slide1m_noscreen`
- Locked leg B: `sp500-2m/cross_sector_slide3m_bd7`
- Locked allocator: 84-day lookback, 0.40 step, 10%--90% bounds, initial A weight 50%
- Locked book sizing: `$1,000,000` capital and `pct_per_pair=0.25`

The selected-book evaluation reports recent means over five aligned starts and one
2015--2019 historical window. The recorded headline values are:

| Mechanism | Recent Sharpe / return | Historical Sharpe / return | Joined Sharpe / return |
|---|---:|---:|---:|
| A | 1.0937 / 9.45% | 1.1222 / 9.10% | 1.1114 / 9.17% |
| B | 1.1413 / 9.81% | 1.0963 / 8.83% | 1.1058 / 9.07% |

The original committed consolidated replay used hardcoded momentum defaults
(63 days, 0.10 step, 25%--75% bounds) even though the locked configuration was
84 days, 0.40, and 10%--90%. After wiring the replay to the locked config, the
generated `results/final/combined` summaries reproduce the clean40 recent and
historical values above. This is an explicit configuration correction; the
trade-event simulation code was not changed to alter strategy math.

## Current Call Graph

- The two root runners duplicate fold selection, signal preparation, Backtrader setup, and result aggregation. Most launchers invoke `run_backtest_parallel.py`; `run_backtest.py` is imported by the parallel runner for argument/profile handling.
- `src/pair_cache.py` is imported by both runners and by the three historical pool seeders. `PairSelectionCache` is only referenced by migration/seeding utilities; current runs use `PoolCache`.
- `research/run_combined_backtest.py` is the canonical shared-account event replay. `research/pair_sweep_consolidated.py`, `research/evaluate_clean40.py`, the factor scripts, plotting scripts, and robustness scripts import it.
- `research/pair_sweep.py` and `research/combine_legs.py` implement superseded arithmetic-return combinations and are not sources for the locked result.
- `research/seed_2m3m.py`, `research/seed_12m_recent.py`, `research/seed_fixed_gaps.py`, and `research/rebuild_pools.py` overlap in pool construction and migration logic.
- `research/write_*.py`, `run_fixed_reports.py`, and comparison launchers are generated-report or one-time migration utilities rather than runtime strategy modules.
- Gatev and optimizer modules have no callers in the corrected coint pipeline and are benchmark candidates, not current production research.

## Classification

| Current location | Classification | Cleanup disposition |
|---|---|---|
| `src/backtest.py`, `src/signal.py`, `src/hedge_ratio_guard.py` | canonical/current | retain unchanged mathematically |
| `src/pair_selection.py`, `src/walk_forward.py`, `src/data_loader.py` | canonical/current | retain and expose through the generic runner |
| `src/pair_cache.py` | canonical/current plus legacy cache code | retain `PoolCache`, remove `PairSelectionCache` |
| `run_backtest.py`, `run_backtest_parallel.py` | duplicate current entry points | consolidate as `research.run_experiment` |
| root `run_*` grid/sweep scripts | duplicate launchers | replace with YAML configurations |
| `research/run_combined_backtest.py` | canonical/current | retain as shared-account replay implementation |
| `research/pair_sweep_consolidated.py` | canonical/current selection workflow | consolidate as portfolio selection |
| `research/pair_sweep.py`, `research/combine_legs.py` | superseded research | remove after archival tag |
| `research/run_ff_*.py`, `momentum_ff_*.py` | overlapping generated-report utilities | consolidate factor/allocator interfaces |
| `research/seed_*.py`, `rebuild_pools.py` | migration/forensic utilities | replace with `scripts/build_pair_pool.py` |
| `src/gatev_*.py`, `src/optimization.py` | benchmark/unused | isolate under benchmark namespace or remove |
| `diagnosis/`, `fixed_diagnosis/` | generated historical corpora | remove from the public working tree |
| `notebooks/01`--`08` | historical notebooks | remove after the archival tag; use Markdown summary |

The archival tag preserves the full pre-cleanup tree. The working tree may also
contain unrelated local experimental changes; those are not included in cleanup
commits and are not reverted.
