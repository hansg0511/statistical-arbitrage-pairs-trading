# Bug-Fix Report - Cache Routing, Empty Pools, and pct=0.25

**The arc in one line:** Found that an old cache-shadow path could substitute the wrong
pair universe → replaced it with window-keyed pool routing → preserved the seeded 10%
return-divergence universe → stopped empty cache hits from falling through to live
selection → made zero-pair folds valid → regenerated and audited the affected sizing
comparison.

This is a companion report to `RESEARCH_PIPELINE.md`. The existing pipeline, including
its user-curated TL;DR table, is intentionally unchanged.

## TL;DR - one line per section

| # | Test / repair | Key result | Decision |
|---|---|---|---|
| [**01**](#01---cache-shadow-contamination) | Trace the historical cache path | 24 preserved historical runs used the wrong H&A/SP500 pair source on matching keys | Mark those runs contaminated; retain them only as an audit record |
| [**02**](#02---pool-routing-redesign) | Replace overlapping cache paths with window-keyed pools | Routing is now determined by selection window, universe, and profile | Use `PoolCache`; keep legacy cache files unused |
| [**03**](#03---load-time-filtering-and-selection-safety) | Reapply universe, sector, p-value, half-life, and indexing rules safely | Cached rows are filtered in the active price space; pandas parameter indexing is explicit | Keep the fixed filters in the runtime path |
| [**04**](#04---empty-cache-hit) | Test a cache key whose viable result is empty | `2023-05-01` is a real pool hit with zero valid same-sector core pairs; live fallback is not used | Treat an empty cached result as authoritative |
| [**05**](#05---zero-pair-fold-contract) | Make empty formation windows valid folds | The affected fold records zero pairs, zero trades, zero P&L, and successful completion | Do not drop or fail a legitimate zero-trade fold |
| [**06**](#06---pct025-comparison-audit) | Regenerate 0.045 and 0.25 affected grids | 80 `10a` runs regenerated; full audit is 192/192 within tolerance | Accept only documented allocation-dependent exit timing |
| [**07**](#07---scope-of-notebooks-01-05) | Check early notebook provenance | Their 2-month runs were always live and did not use these caches | Leave notebooks 01-05 and their runs unchanged |
| [**08**](#08---final-policy) | Consolidate the operating policy | Cache hits are deterministic, misses are explicit, and empty windows remain valid | Use corrected behavior for cache-backed runs |

---

## 01 - `cache_shadow` contamination

**Context:** The original backtest had more than one selection-cache path. A non-`huck2015`
baseline run could consult the H&A cache by bare `sel_start` before using the cache that
matched its actual selection window and universe.

**Test:** Reconstruct the old path from the preserved run metadata and compare it with the
intended configuration.

**Failure mode:** When a selection key overlapped the H&A cache range, a baseline/core run
could consume 12-month SP500 cross-sector pairs instead of the intended core 2-month
selection. The sector and core-universe restrictions were bypassed. The bug was a cache
source substitution, not a market-data or strategy effect.

The affected preserved archive contains 24 runs:

| Property | Contaminated behavior |
|---|---|
| Profile | `baseline` |
| Intended universe | Core |
| Wrong source | H&A / `huck2015` 12-month SP500 cache |
| Wrong selection behavior | Cross-sector pairs supplied on matching bare keys |
| Affected key range | Selection starts in approximately `2015-01` through `2020-01` |
| Observed Sharpe range | `0.80` to `1.51` |
| Archive | `diagnosis/08b_core_12m_sel_2015_2020_preserved (old)/` |

The preserved manifest explicitly labels all 24 runs as contaminated. They remain useful
for demonstrating the size of the error, but they are not valid evidence of strategy edge.

### Corrected comparison

| Run family | Corrected result | Interpretation |
|---|---|---|
| Core 2-month, 2015-2019 (`08a`) | Best cross-sector cells around `0.50-0.51` Sharpe; same-sector 3-month cells negative | The strong preserved results were not a clean core baseline |
| Core 12-month, 2015-2019 (`08b` redo) | `cross_sector_slide1m_bd7` = `0.34` Sharpe, `+0.29%` annualized, 740 trades | Sector-masked 12-month core is marginal, not the preserved `0.8-1.5` result |
| SP500 2-month, 2015-2019 (`09a`) | Best `cross_sector_slide3m` = `0.62` Sharpe | SP500 2-month selection is a separate, valid experiment |
| SP500 12-month, 2015-2019 (`09b`) | Best `same_sector_slide1m_noscreen` = `0.43` Sharpe | Wider-universe 12-month behavior is evaluated independently |

**Decision:** The contaminated historical archive is preserved and explicitly marked. The
clean reruns, not the archive, are the source for conclusions.

## 02 - `pool_routing` redesign

**Context:** The old design mixed a two-tier pair-selection cache with profile-specific
cache behavior. Bare date keys made it possible for a valid key from one selection method
to look like a valid key for another method.

**Test:** Route all non-Gatev cointegration runs through a single window-keyed pool path,
while retaining the `huck2015` profile's separate raw-space filtering semantics.

**Implementation:**

- `PoolCache` is keyed by bare `sel_start`, with the selection-window method encoded by the pool file.
- `pool_path_for()` chooses the pool from `sel_months`, universe, and profile.
- `PairSelectionCache` remains available for legacy research artifacts but is no longer used by the backtest runners.
- `--cache_dir` remains accepted for old commands, but it is not used to select runtime pair results.
- The runtime 12-month pool is `sp500_12m.pkl` for both H&A and non-H&A profiles; only the H&A branch applies the raw-space H&A filters.

### Runtime routing table

| Run context | Runtime pool | Filters / source property | Reason for the choice |
|---|---|---|---|
| Baseline, core, 2-month selection | `research/cache/core_2m.pkl` | Prefiltered core rows; log p-value and sector semantics are already represented | Preserves the historical core 2-month experiment without importing another pool |
| Golden or SP500, 2-month selection | `research/cache/sp500_2m.pkl` | Superset rows; divergence `<= 0.10` at seed time; universe, p-value, and half-life filters at load time | Keeps the wider universe separate from the core pool |
| Non-H&A, 12-month selection | `research/cache/sp500_12m.pkl` | Superset pool; divergence `<= 0.10` in the seeded source; core/universe, sector, log p-value, and active-space half-life filters at load time | One source supports both recent and historical 12-month windows |
| `huck2015` profile | The routed 12-month pool read as H&A data | Profile-specific raw p-value and half-life behavior | Prevents H&A behavior from shadowing other profiles |

The pool seed scripts retain the original `DIVERGENCE = 0.10` prefilter. In particular,
`research/seed_fixed_gaps.py`, `research/seed_12m_recent.py`, and the preserved
`research/archive/seed_sp500_huck2015.py` reject candidate pairs whose selection-window
cumulative returns differ by more than 10 percentage points. The divergence check needs
active prices, so `PoolCache.select()` does not recompute it from the stored pair metrics;
the fixed pool-backed runs rely on the same seed-time bound.

**Decision:** A selection window has one authoritative pool source. Universe and sector
semantics are applied to that source instead of silently switching sources after an empty
result; divergence remains a seed-time property of the pool.

## 03 - `load_time_filtering` and selection safety

**Context:** A universe-free pool is useful only if loading it reproduces the filters
expected by the active backtest. The old code also relied on positional-looking pandas
indexing that can become label-based or fail as pandas versions change.

**Repairs:**

- Unfiltered pools apply the log-space cointegration p-value threshold at load time.
- Same-sector runs apply the sector map before ranking.
- `filter_pairs_by_half_life()` requires a finite, positive half-life in the price space consumed by the run.
- Log-space runs use `half_life_log`; raw-space H&A runs use `half_life`.
- `PairSelector` now uses `.iloc` for regression coefficient positions instead of ambiguous integer indexing.
- Cached rows are validated again before the `max_pairs * 3` candidate window is ranked.

**Why this configuration:** The strategy's final ranking is by log-space cointegration
p-value, while the half-life input is selected by `log_space`. Applying those two filters
in different spaces can silently drop valid rows or retain rows unusable by the strategy.
The fixed path makes the cache and live selector obey the same active-space contract.

**Decision:** Cache loading is a filtering step, not a shortcut around runtime validity
checks.

## 04 - `empty_cache_hit`

**Context:** After the routing fix, one recent 12-month pool key exposed a second bug. The
key existed, but its filtered result contained no viable pair. The previous code treated
`empty` as equivalent to `missing` and invoked live selection.

**Test:** Inspect the `2023-05-01` key in `sp500_12m.pkl` under the baseline core,
same-sector configuration.

**Result:**

| Stage | Result |
|---|---:|
| Pool key | Present for `2023-05-01` to `2024-04-30` |
| Core/same-sector candidates before final log p-value cutoff | 57 |
| Best observed log p-value | Approximately `0.053` (`BAC-GS`) |
| Other top candidates | `LMT-RTX` approximately `0.078`; `CRM-MSFT` approximately `0.079` |
| Candidates passing log p-value `< 0.05` | 0 |
| Live fallback | Not allowed |

The earlier live fallback found six pairs that were not members of the seeded 10%-bounded
candidate universe. Those pairs were an artifact of relaxing the cache result, not an
alternative interpretation of the cached window.

**Implementation:** Both runners now distinguish the two states explicitly:

- `pool_cache.has(sel_start) == True`: call `PoolCache.select()` once, even if it returns an empty DataFrame.
- No pool or missing key: call the live selector.
- An empty DataFrame from a real cache hit never triggers live selection.

**Decision:** Preserve the original cached universe and its 10% divergence constraint.
An empty cached result means that no eligible pair was found for that formation window.

## 05 - `zero_pair_fold` contract

**Context:** Returning an empty pair DataFrame was not enough. The old runner discarded the
fold or produced no daily returns, which made a legitimate no-trade window appear to be a
failed or incomplete run.

**Test configuration:** The focused test uses the same structure as the affected recent
12-month runs:

```text
profile=baseline, universe=core, selection=12m, test=3m, slide=1m
max_pairs=20, pct_per_pair=0.045, broker_leverage=100
price snapshot=core_recent_12m.pkl
```

**Result:** The 22-fold parallel run completed successfully. Fold 4 has:

| Field | Value |
|---|---|
| Selection window | `2023-05-01` to `2024-04-30` |
| Test window | `2024-05-01` to `2024-07-31` |
| Pool result | Cache hit, 0 pairs |
| Fold pairs | 0 |
| Fold trades | 0 |
| Fold Sharpe | 0.0 |
| Fold daily P&L | All zero |

The full run has 22/22 completed folds, 102 trades outside the zero fold, annualized
return `0.20%`, annualized Sharpe `0.28`, and 419 trimmed daily observations. The serial
runner produces the same focused result.

**Implementation:**

- Parallel `_collect_zero_pair_fold()` returns a complete fold summary and zero daily rows.
- Serial execution appends the same zero fold summary and zero daily rows.
- Zero active counts and zero deployed capital are emitted for the test dates.
- If edge trimming removes every date from an all-zero run, the untrimmed zero-return dates are retained.
- Aggregate return and active-count date columns are normalized with `pd.to_datetime()` before grouping.

The final date normalization was necessary because Backtrader daily returns and zero-fold
rows arrived as different Python date-like types. Before the normalization, aggregation
could fail with `Timestamp`/`datetime.date` or `datetime.date`/`datetime.datetime`
comparison errors.

**Decision:** A no-pair formation window is a successful zero-trade fold, not a worker
failure, missing artifact, or reason to discover new live pairs.

## 06 - `pct025` comparison audit

**Context:** The higher `pct_per_pair=0.25` runs were introduced to test sizing and to
produce trade marks for the later combined-book work. They were not intended to change
selection. The cache-policy correction affected the recent core 12-month `10a` suite,
so both sides of that suite had to be regenerated.

**Configuration choice:**

- `max_pairs=20` preserves the deployment-breadth decision from the earlier max-pairs sweep.
- `pct_per_pair=0.045` is the reference control used by the main grid.
- `pct_per_pair=0.25` is the sizing stress/mark run, not a new selection rule.
- `broker_leverage=100` and `margin_behavior=off` keep the comparison focused on strategy sizing rather than broker rejection.
- The same local price snapshot is used by both sides.
- The same five 12-month start dates and eight sector/slide/screen configurations are used.

**Regeneration:**

- `fixed_diagnosis/10a/`: 40 reference runs at `pct_per_pair=0.045`.
- `fixed_diagnosis/_sweep_pct25/10a/`: 40 matching runs at `pct_per_pair=0.25`.
- All 80 affected runs passed their output validators.

### Full comparison result

The audit compares the eight later sections, not the live-selection notebooks 01-05.
The return tolerance is `0.01` absolute, or one percentage point.

| Section | Runs | Exact within tolerance | Classified discrepancies |
|---|---:|---:|---:|
| 06 | 40 | 40 | 0 |
| 07 | 40 | 40 | 0 |
| 08a | 8 | 8 | 0 |
| 08b | 8 | 8 | 0 |
| 09a | 8 | 8 | 0 |
| 09b | 8 | 8 | 0 |
| 10a | 40 | 40 | 0 |
| 10b | 40 | 40 | 0 |
| **Total** | **192** | **192** | **0** |

The event evidence contains only documented, explainable differences:

| Difference | Count | Explanation |
|---|---:|---|
| Expected new events after old `zero_size` attempts | 12 | The higher-size run can fill an entry that rounded to zero at the reference size |
| Accepted allocation-dependent exit events | 24 | Higher allocation changes whether the same position reaches `max_holding_loss` before the next signal/stop event |
| Return differences over 1 percentage point | 0 | No common event exceeded the audit tolerance |
| Unexplained selection/entry differences | 0 | Pair selections and entries match after the accepted cases |

The standalone `run_sweep_pct25_marks.py --verify` command is intentionally stricter than
the audit and reports eight `10a` jobs because it requires every reference event key to
appear unchanged. Those are the `COP-TMO` allocation-dependent `max_holding_loss` timing
changes listed in `event_differences.csv`; the authoritative audit classifies them as
accepted rather than unexplained.

**Decision:** The 0.25 runs are suitable for sizing and trade-mark analysis. They should
not be described as a perfectly identical event stream, because allocation can affect
exit timing. No evidence indicates a cache-policy mismatch after regeneration.

## 07 - Scope of notebooks 01-05

**Context:** The early notebooks document the initial live-selection research. The cache
and 0.25 mechanics were introduced later.

**Provenance check:**

- The 2-month runs behind notebooks 01-05 selected pairs live.
- They did not use `PoolCache`, `PairSelectionCache`, or the later window-keyed pools.
- Their primary sizing was `pct_per_pair=0.18` or lower; the `0.25` values visible in notebook 02 are result values such as win rate, not evidence of 25% position sizing.
- Notebook 03 is a pair-ranking stability analysis, not a cached backtest.
- Notebook 04 contains legacy/hard-coded OOS presentation, which is a reproducibility limitation but not cache contamination.
- Notebook 05 interprets the preceding regime results and does not introduce the later cache or 0.25 mechanics.

**Decision:** Leave notebooks 01-05 and their original runs as they are. They cannot be
tainted by the cache-shadow, empty-cache-hit, zero-fold, or 0.25 allocation mechanics
described in this report.

## 08 - Final policy

The corrected policy is:

1. Route a run to the pool matching its selection-window method and universe.
2. Treat an existing pool key as authoritative, including when its filtered result is empty.
3. Invoke live selection only when the pool key is genuinely missing or no pool is configured.
4. Keep the original 10% divergence constraint in the seeded candidate universe and explicit cross-sector configurations.
5. Record zero-pair windows as successful zero-trade folds with zero P&L.
6. Normalize date types before aggregate grouping.
7. Use `pct_per_pair=0.25` only as a deliberate sizing/mark comparison, not as a selection change.
8. Treat the preserved cache-shadow runs as historical contamination evidence, not as clean results.

### Configuration rationale

The specific focused validation configuration was chosen because it targets the known
failure while changing as little else as possible:

- `baseline/core` isolates the intended same-sector core universe.
- `sel_months=12` reaches the exact pool key that exposed the empty-result problem.
- `slide_months=1` matches the affected recent 12-month grid.
- `max_pairs=20` matches the selected deployment breadth.
- `pct_per_pair=0.045` keeps the zero-fold test independent of the 0.25 sizing stress.
- `broker_leverage=100` avoids turning bookkeeping exposure into an unrelated margin failure.
- The frozen price snapshot makes the rerun reproducible and prevents market-data drift from being mistaken for a code effect.

The baseline profile still has `return_divergence=None` for a genuine live-selection miss.
That is intentional for the historical baseline semantics: the corrected affected runs
all hit the seeded 12-month pool, whose candidate construction already applied the 10%
limit. If a future experiment requires the 10% rule on every possible live-miss fallback,
that should be made an explicit new configuration and audited separately rather than
silently changing the baseline.

## Where these results live

```text
CACHE_BUG_FIX_REPORT.md

diagnosis/08b_core_12m_sel_2015_2020_preserved (old)/
    MANIFEST.md
    RECREATE_ALL.json

diagnosis/08b_core_12m_sel_2015_2020 (old)/
diagnosis/08a_core_2015_2020 (old)/
diagnosis/09_sp500_2015_2020 (old)/
diagnosis/09b_sp500_12m_sel_2015_2020 (old)/

fixed_diagnosis/10a/
fixed_diagnosis/_sweep_pct25/10a/

research/archive/pct25_comparison_audit/
    findings.md
    run_comparison.csv
    event_differences.csv
    selected_half_life_report.md
    cache_flow_zero_full_test/
    cache_flow_zero_serial_postfix_full/
```

## Validation commands

```text
python run_fixed_grids.py --only 10a --force --workers 2 --pause 0 --snapshot-dir research/archive/pct25_comparison_audit/snapshots --broker-leverage 100
python run_sweep_pct25_marks.py --only 10a --force --workers 2 --pause 0 --snapshot-dir research/archive/pct25_comparison_audit/snapshots
python audit_pct25_comparison.py
python report_selected_half_lives.py --root fixed_diagnosis --output-dir research/archive/pct25_comparison_audit
python -m py_compile run_backtest.py run_backtest_parallel.py src/pair_cache.py src/pair_selection.py
git diff --check
```

## Honest bottom line

The cache-shadow bug materially contaminated a later historical run family and inflated
some apparent results. That issue is isolated, preserved, and corrected. The early
notebooks 01-05 are not affected because their 2-month pair selection was always live and
their runs predate the 0.25 sizing work.

The later fixes now make cached research deterministic: a cache hit cannot silently turn
into a different live universe, an empty cached window is represented honestly as a
zero-trade fold, and date normalization prevents valid zero folds from breaking run
aggregation. The refreshed 192-run audit found no unexplained differences beyond the
explicitly documented allocation-dependent event timing.

The practical conclusion is therefore narrower and more reliable: use the clean reruns
for cache-backed sections, keep notebooks 01-05 as historical live-selection research,
and do not interpret 0.25 sizing as a change to pair-selection quality.
