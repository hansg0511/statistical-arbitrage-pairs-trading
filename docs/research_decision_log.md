# Research Decision Log

Every substantive research experiment should append an entry describing the
question, motivation, method, result, interpretation, decision, and next
question. Implementation-only changes do not require research entries unless
they materially affect methodology or results.

The entries below are a **Retrospective reconstruction** of the substantive
research path. Exact dates are intentionally omitted where they cannot be
reconstructed reliably.

### Research entry: Initial pairs-trading research

**Status:** completed

**Question**

Can equity pairs provide a repeatable statistical-arbitrage signal after
selection and walk-forward validation?

**Why this mattered**

The project needed a standalone alpha framework before comparing portfolio
construction choices.

**Method**

The research used Engle-Granger pair selection, a log-price OLS hedge
relationship, residual z-score mean reversion, frozen entry statistics,
walk-forward testing, a hedge-ratio guard, and stop/timeout rules. Same-sector
and broader cross-sector configurations were tested.

**Result**

The framework produced a reproducible set of standalone pair-trading
strategies with measurable out-of-sample behavior.

**Interpretation**

The signal framework was sufficiently stable to support comparisons of
universe, configuration, sizing, and portfolio allocation.

**Decision**

Retain the standalone strategy framework and evaluate it through controlled
walk-forward experiments.

**Next question**

How should multiple standalone strategy outputs be combined into a portfolio?

**Artifacts / branch / commit**

Retrospective reconstruction; research history predates the current branch
record.

### Research entry: Combined-book research

**Status:** completed

**Question**

Does combining standalone strategy configurations produce a more robust book
than selecting a single strategy by one-period performance?

**Why this mattered**

Standalone rankings did not describe how correlated or complementary strategy
returns behaved when capital was shared.

**Method**

The research organized four strategy bases with eight configurations each,
creating 32 standalone configurations. All two-leg combinations produced 496
candidate books. Each book was evaluated under mechanisms A and B across
recent and historical periods using a Clean40 dynamic allocator: approximately
an 84-day trailing Sharpe lookback, 40-percentage-point allocation steps,
10%--90% bounds, and a 50/50 initial allocation. Books were ranked with
multiple robustness criteria rather than a single-period Sharpe.

**Result**

Combined-book behavior differed materially from standalone rankings, and the
two replay mechanisms provided useful sensitivity checks.

**Interpretation**

Portfolio construction and capital allocation were first-order research
variables, not just implementation details.

**Decision**

Keep both combined replay mechanisms and evaluate book robustness across
recent and historical windows.

**Next question**

Are the capital-allocation semantics economically comparable across pairs with
different hedge ratios?

**Artifacts / branch / commit**

Retrospective reconstruction; the controlled matrix artifacts are preserved
under `results/sizing_v2_full/`.

### Research entry: Discovery of reference-leg sizing ambiguity

**Status:** completed

**Question**

What exactly did `pct_per_pair` control in the original pair-sizing logic?

**Why this mattered**

The same configured pair allocation could produce different total gross
exposure depending on hedge ratio, making cross-pair and cross-book results
harder to compare.

**Method**

The original convention was traced to a reference-leg target notional. Under
V1, `pct_per_pair` effectively controlled the reference/S2 leg, and the hedge
leg was then added according to the hedge ratio.

**Result**

Total pair gross exposure was not constant. A high-hedge-ratio pair could
consume materially more gross exposure than another pair with the same
configured allocation.

**Interpretation**

V1 was not necessarily mathematically incorrect; it represented a specific
reference-leg sizing convention. Its economic exposure, however, varied with
hedge ratio.

**Decision**

Treat the convention as a methodology choice and test a fixed-total-gross
alternative rather than silently changing V1.

**Next question**

Does fixed-total-gross sizing preserve the signal rankings while improving
comparability?

**Artifacts / branch / commit**

Retrospective reconstruction; V1 behavior remains preserved in the canonical
V1 raw runs.

### Research entry: Definition of V2 gross-exposure sizing

**Status:** completed

**Question**

Can pair allocations be made economically comparable across hedge ratios?

**Why this mattered**

Comparing books with implicit, HR-dependent gross exposure confounded signal
quality with the amount of capital deployed.

**Method**

V2 defines `pct_per_pair` as total pair gross exposure. The hedge ratio splits
that fixed gross budget between the two legs. V1 remains a separate sizing
mode and is not overwritten.

**Result**

V2 provides a fixed gross-budget convention while preserving the underlying
trade decisions and signal logic.

**Interpretation**

V2 is cleaner for comparing pairs and books on a like-for-like capital basis,
while V1 remains necessary for historical attribution.

**Decision**

Use V2 as the comparison convention and retain V1 as the historical control.

**Next question**

How much do standalone and combined rankings change under the controlled
convention change?

**Artifacts / branch / commit**

Retrospective reconstruction; V1/V2 sizing implementation is on
`sizing-v2-gross-exposure`.

### Research entry: Controlled full V1/V2 rerun

**Status:** completed

**Question**

Does changing only pair-sizing semantics materially alter strategy or book
selection?

**Why this mattered**

The sizing change was intended to improve comparability without changing the
underlying alpha decisions.

**Method**

The controlled rerun covered all 32 standalone configurations, 192 standalone
instances, 496 books, both mechanisms, and both sizing modes. Trade decisions
and signals were preserved while V1 and V2 sizing were compared.

**Result**

Standalone rankings changed relatively little, with high V1/V2 rank
correlation and most leading configurations remaining near the top. Combined
book rankings moved substantially more, and the old canonical winner
deteriorated dramatically under V2 in the recent period.

**Interpretation**

Combined portfolio behavior was more sensitive to sizing semantics than
standalone signal quality.

**Decision**

Do not infer that a V2 ranking change represents a new alpha signal. Diagnose
the portfolio mechanics before selecting a replacement winner.

**Next question**

Why did the old V1 winner lose so much recent combined Sharpe under V2?

**Artifacts / branch / commit**

Retrospective reconstruction; preserved matrix summary artifacts are under
`results/sizing_v2_full_summary/`.

### Research entry: Old V1 winner

**Status:** completed

**Question**

What makes the old V1 winner unusually strong under V1 and fragile under V2?

**Why this mattered**

The book was a concrete case where a convention change produced a large
recent result change but a much smaller historical change.

**Method**

The locked book was Leg A
`sp500-12m/cross_sector_slide1m_noscreen` plus Leg B
`sp500-2m/cross_sector_slide3m_bd7`.

**Result**

Its recent Sharpe fell from approximately 1.09/1.14 under V1 to 0.37/0.42
under V2 for mechanisms A/B, while historical Sharpe fell only from about
1.12/1.10 to 1.02/0.99.

**Interpretation**

The old winner was a useful controlled diagnostic because the recent failure
was much larger than the historical control failure.

**Decision**

Analyze this book directly instead of rerunning or retuning the full universe.

**Next question**

Is the V2 result caused by pair sizing, the Clean40 path, hedge-ratio effects,
or some combination?

**Artifacts / branch / commit**

Retrospective reconstruction; locked inputs are in
`research/selected_book_config.json`.

### Research entry: Current V2 winner candidate

**Status:** ongoing

**Question**

Which book is currently strongest under V2 and rank-average evaluation?

**Why this mattered**

The sizing convention change produced a different leading candidate that must
be distinguished from the historical canonical winner.

**Method**

Compare the V2 ranked combined-book outputs across both mechanisms and
robustness criteria.

**Result**

The strongest current candidate became
`sp500-12m/same_sector_slide1m_noscreen` plus
`sp500-12m/same_sector_slide3m_noscreen`, ranking extremely well under both
mechanisms.

**Interpretation**

This is a current V2 research candidate, not automatically a permanent
canonical selection.

**Decision**

Keep it as a candidate pending further exposure and robustness diagnostics.

**Next question**

Does the old winner's V1 advantage survive controlled attribution?

**Artifacts / branch / commit**

Retrospective reconstruction; candidate ranking is preserved in the V2 matrix
summary artifacts.

### Research entry: Old-winner V1/V2 autopsy

**Status:** completed

**Question**

Why did the old winner's recent combined Sharpe collapse under V2?

**Why this mattered**

The full rerun showed that combined books were much more sensitive than
standalone strategies, so the next step was to separate sizing, allocation,
and trade-level explanations.

**Method**

The focused autopsy compared four counterfactuals: V1 sizing + V1 allocator,
V2 sizing + V2 allocator, V2 sizing + V1 allocator, and V1 sizing + V2
allocator. It also examined hedge-ratio winner/loser buckets, correlations,
recent versus historical behavior, daily attribution, and concentration.

**Result**

Both pair sizing and allocator behavior mattered. The allocator path was the
larger direct recent Sharpe bridge component, but the high-HR-winner hypothesis
was not sufficient: the correlations were weak and the effect was
path-dependent.

**Interpretation**

The old winner was not merely a signal that disappeared under V2, and it was
not explained by a single high-hedge-ratio trade rule. Its result depended on
both sizing and portfolio path.

**Decision**

Preserve V1/V2 as separate conventions and investigate the equity path before
changing the allocator or selecting a new canonical book.

**Next question**

How much of the gap occurs on the relatively few dates when Clean40 weights
differ?

**Artifacts / branch / commit**

`research/run_old_winner_v1_v2_autopsy.py`,
`results/old_winner_v1_v2_autopsy/`, and
`docs/old_winner_v1_v2_autopsy.md`; branch
`sizing-v2-gross-exposure`, commit `9dc8771`.

### Research entry: Clean40 weight-path investigation

**Status:** completed

**Question**

Did the V1/V2 allocator paths differ often enough to explain the recent gap?

**Why this mattered**

The Clean40 step is large, so a small number of path differences could still
have large portfolio consequences.

**Method**

The existing recent return series were joined with the complete monthly V1/V2
Clean40 paths across all five recent start iterations and both mechanisms.

**Result**

Most monthly allocations were identical. Only 15 of 110 pooled recent path
months differed, but some differences were 80 percentage points in Leg A
weight, such as 90/10 versus 10/90. Differences were concentrated in a few
periods.

**Interpretation**

The flips were rare but potentially consequential because of the 40-point
step size.

**Decision**

Test the equity gap conditional on differing versus identical weights rather
than assuming the flips caused the entire result.

**Next question**

How much of the final V1/V2 equity gap is present while weights are identical?

**Artifacts / branch / commit**

`research/run_recent_equity_path_comparison.py`,
`results/old_winner_v1_v2_autopsy/equity_path_comparison_recent.csv`, and
related interval/summary files; branch
`sizing-v2-gross-exposure`, follow-up artifacts were generated after commit
`9dc8771`.

### Research entry: Equity-gap attribution

**Status:** completed

**Question**

How much of the V1/V2 equity gap occurs on differing-weight versus
identical-weight days?

**Why this mattered**

This tests whether the rare Clean40 flips were the primary cause of the large
recent Sharpe divergence.

**Method**

Exact standalone daily return series were joined to the existing combined
event-replay returns and monthly weights. Differing-weight intervals were
identified per start and mechanism. Arithmetic daily-return sums, compounded
equity comparisons, sequential replacements, and log-equity attribution were
reported.

**Result**

Across the five recent starts, differing-weight days accounted for about 46%
of the compounded gap by symmetric attribution and about 49% by log-equity
attribution. Identical-weight days accounted for the remaining share. The
flips often coincided with A leading B, but not uniformly.

**Interpretation**

The rare allocator flips were materially important but did not explain the
entire V1 advantage. A substantial difference remained while Clean40 applied
the same A/B weights.

**Decision**

Return to the sizing question and measure actual gross exposure and
performance per unit of exposure.

**Next question**

V1 generally carries more gross exposure. How much of its superior account
equity is compensation for that exposure, and how much remains at equal gross
exposure?

**Artifacts / branch / commit**

`results/old_winner_v1_v2_autopsy/equity_path_comparison_recent_intervals.csv`
and `equity_path_comparison_recent_summary.{json,md}`; branch
`sizing-v2-gross-exposure`, follow-up artifacts were generated after commit
`9dc8771`.

### Research entry: Gross-exposure comparison

**Status:** completed

**Question**

V1 generally carries more gross exposure. How much of its superior account
equity is compensation for that exposure, and how much remains at equal gross
exposure?

**Why this mattered**

The equity-gap experiment showed that roughly half of the recent gap remained
on identical-weight days, pointing back toward HR-dependent sizing and actual
exposure rather than only Clean40 flips.

**Method**

Reconstruct marked leg and book exposure from the preserved trade quantities,
entry metadata, daily marks, and the exact price snapshots referenced by the
old-winner runs. V1 sizes were reconstructed from the matched V2 entry prices
using the preserved reference-leg convention. The replay covered the five
recent paired starts and both mechanisms A/B, for 10 focused traces. Native V2
`daily_exposure.csv` rows were independently reconciled to marked positions;
V1 had no native exposure file and was reconstructed with the same source order
timing. Compare account returns with return-on-gross diagnostics, then scale V1
to V2's daily total gross exposure and V2 to V1's as uniform trade-level
counterfactuals that preserve each version's internal relative weighting.

**Result**

The pooled V1/V2 total marked gross-exposure ratio had median `1.962x` and p95
`3.431x` on V2-active observations. Mean active-day gross leverage was `0.877x`
for V1 versus `0.450x` for V2; p95 leverage was `1.938x` versus `1.000x`.
Mean return-on-gross was `0.00021800` for V1 versus `0.00010355` for V2.
Matching V1 to V2's daily gross exposure reduced the mean final V1-minus-V2
equity gap from `0.140015` to `0.040482`, removing `72.52%` of the gap. The
exposure reconstruction and all PnL, allocator-path, budget, snapshot, and
protected-output checks passed.

**Interpretation**

Most of the old V1 advantage was compensation for carrying more marked gross
exposure, but the positive residual after equal-gross matching shows that V1
was not only a more leveraged version of V2. The residual is consistent with
the V1 internal hedge-ratio-dependent leg weighting and its resulting trade
economics. This result is separate from the Clean40 allocator-path effect,
which was measured in the preceding entries.

**Decision**

Keep V1 as the historical control and use V2 as the cleaner future comparison
convention because it fixes total pair gross exposure. Do not change the
canonical book or retune the allocator from this focused result.

**Next question**

Does the same exposure-adjusted conclusion hold for the current V2 winner and
for the historical control window without reopening the full matrix?

**Artifacts / branch / commit**

`research/run_gross_exposure_autopsy.py`,
`results/old_winner_v1_v2_autopsy/gross_exposure_comparison_recent.csv`,
`gross_exposure_matched_counterfactuals.csv`,
`gross_exposure_summary.{json,md}`, and representative gross-exposure plots;
branch `sizing-v2-gross-exposure`.
