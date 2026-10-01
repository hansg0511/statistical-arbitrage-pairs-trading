# Research Journey

This project began as a relatively conventional statistical-arbitrage exercise:
find cointegrated equity pairs, trade their residual spread, and test the idea
with walk-forward data. It is now a more explicit research and portfolio-
construction system. The change was not driven by a desire to add complexity for
its own sake. It came from testing the early result, finding that it was more
fragile than its headline statistics suggested, and then making the selection,
replay, and reproducibility boundaries more explicit.

The stages below describe that evolution. They deliberately distinguish early
results that motivated later questions from the current canonical book. The
notebook-era files contain useful evidence of the development process, but they
are not the source of truth for the public release. Detailed historical files
are preserved in git history and at the archival tag
`pre-public-cleanup-20260909`; the current narrative is intended to stand on
its own without requiring the reader to inspect that archive.

## 1. Initial Pairs-Trading Model

The original public version focused on a small, intuitive universe of large,
mostly mega-cap equities, with same-sector pairing used to keep the economic
relationship between names plausible. Pair selection used the Engle-Granger
cointegration procedure. Prices were modeled in log space, an OLS hedge ratio
and intercept defined the residual spread, and a rolling residual distribution
provided the mean and standard deviation used for z-scores.

The trading rule was a mean-reversion rule around that spread. A sufficiently
large positive or negative z-score opened a two-leg position, a move back toward
the exit threshold closed it, and a larger excursion triggered a stop. The
engine also monitored hedge-ratio stability and could close a trade when the
relationship appeared to have structurally changed. A loss-only maximum-holding
condition and fold/session termination handled positions that did not resolve
normally. The current implementation measures that maximum-holding threshold
with calendar-date subtraction: the tested `max_holding_days=15` and
`max_holding_unit="calendar_days"` mean 15 calendar days, not 15 trading
sessions.

Validation was already intended to be walk-forward rather than a single static
in-sample fit. Formation data selected pairs and estimated parameters, and
subsequent test folds evaluated trading performance out of sample. Early work
also optimized entry, exit, stop, lookback, and related parameters over a grid.
That process produced an initial out-of-sample headline of approximately Sharpe
0.65. In the context of the original project, that was an encouraging result:
the strategy had a plausible economic structure, a defined risk rule, and
performance that was not simply an in-sample regression statistic.

It was nevertheless an earlier single-strategy result. It was based on a
narrower universe and a particular sequence of pair-selection and walk-forward
choices. It is useful as the starting point of the project, not as evidence for
the current selected portfolio. The early README and notebooks also contain
minor continuity differences, including different descriptions of fold counts
and date ranges. Those are historical artifacts rather than values to silently
promote into the current methodology.

## 2. Robustness Problems Emerge

The next question was whether the early result survived reasonable changes in
where and how the experiment started. Subsequent diagnostics showed material
sensitivity to the walk-forward start date, pair-selection window, market
regime, and the identity of the selected pairs. In one corrected baseline
comparison, five nearby starts produced Sharpe values from about -0.28 to 1.48,
with a mean near 0.48 and standard deviation near 0.66. That spread is too large
to treat the original headline as a stable description of the strategy.

Pair identity was especially unstable. Across starts, the overlap of the top
five pairs was very small, while rank correlation was weak. A later diagnostic
reported average top-five Jaccard overlap of approximately 0.036, top-five
dropout around 0.94, and Spearman rank correlation around 0.12. The exact
figures belong to the historical diagnostic, but the conclusion is more
important than any one decimal: short-window cointegration rankings could
change substantially with small changes in the start date.

This weakened confidence in a single "best pair" or a single optimized
configuration. A high score could reflect a favorable formation window, a
particular regime, or a transient relationship rather than a repeatable source
of return. The response was not to discard cointegration altogether. It was to
test the sources of instability separately and broaden the experiment so that a
configuration had to be useful for a reason stronger than one attractive run.

## 3. Earnings and Event-Risk Investigation

Some large losses appeared close to company earnings or other single-name
events, so earnings risk was investigated directly. The screen used historical
earnings dates and tested forward-window and post-event blocking variants. The
forward window was calendar-based, matching the strategy's current calendar-
based holding threshold. In the current Leg B configuration, the screen uses a
15-calendar-day forward window and a seven-calendar-day post-event block.

The investigation found real examples where an earnings announcement could
produce a large idiosyncratic spread move. It also found that the screen was not
a complete explanation for the broader performance dispersion. Across baseline
comparisons, enabling the forward screen improved 14 cases and worsened 17; the
mean Sharpe fell from roughly 0.48 to 0.41 in that comparison. A block-duration
sweep did not form a smooth optimization curve. Three and five days were
effectively identical in the observed data, and the apparent advantage of a
nine-day block depended heavily on one start. Seven days was retained as a
conservative minimum-sufficient choice for the selected historical leg, not as a
claim that earnings screening solved the strategy.

The retained conclusion was therefore limited: event screening can remove some
avoidable exposure, but it does not repair unstable pair selection or guarantee
protection from an unexpected divergence. A pair can still lose because one
stock moves for an idiosyncratic reason, even when the other leg behaves as
expected. This investigation became one input to the configuration study,
rather than the final explanation of performance.

## 4. Pair Selection and Expanded Experiment Design

The research then moved from optimizing one setup to comparing a structured set
of alternatives. The major dimensions were:

- core universe versus the broader S&P 500 universe;
- two-month versus twelve-month pair-selection windows;
- same-sector versus cross-sector pairing;
- one-month versus three-month reselection/slide schedules; and
- earnings-screen variants, including no screen and the retained block choice.

These dimensions produced 32 strategy configurations: four universe/window pool
variants multiplied by eight sector, slide, and screen combinations. A
configuration represented a complete leg-generation choice, not just a single
parameter value. This made comparisons more interpretable. It also reduced the
temptation to keep tuning the same configuration until one start date looked
good.

The expanded design produced complementary behavior rather than one universal
winner. Some short-window configurations were strong in recent data but weak or
negative in the older window. Longer selection windows were not automatically
better, and cross-sector pairing increased the candidate pool without making
rank instability disappear. A `max_pairs` sweep also showed that raw Sharpe
winners varied by period. The eventual 20-pair breadth choice was retained for
capacity and concentration reasons, not because it maximized every statistic.

This stage also clarified what a result was allowed to mean. A configuration
that performed well in one regime could motivate further testing. It could not
by itself establish a robust strategy or justify calling the other
configurations failures. The public pipeline retains the configuration
metadata so that these distinctions remain visible.

## 5. Historical Robustness

Recent performance alone was not enough. The study added an older aligned
2015--2019 research window and compared the same configuration families across
both periods. This was not a search for a magical historical score. It was a
way to identify configurations whose strengths were complementary and to
expose recent winners that did not travel well through a different market
environment.

The final comparison showed exactly that tension. Some core two-month choices
were positive in recent data but negative in the aligned historical run. The
broader S&P 500 configurations produced a different ranking in the historical
window. The eventual selected legs reflect these roles: Leg A is the recent-
strong `sp500-12m/cross_sector_slide1m_noscreen` configuration, while Leg B is
the historical-strong `sp500-2m/cross_sector_slide3m_bd7` configuration.

This use of the two windows must be stated plainly. The final portfolio pair and
allocator were selected after comparing the displayed recent and historical
evidence. Those periods are therefore not an untouched portfolio-level
holdout, even though the individual strategy evaluations use walk-forward
out-of-sample folds. The next genuinely unseen evidence must come from future,
paper, or live observations.

## 6. Portfolio Construction

Once the 32 legs had been evaluated, the research question changed from "which
one is best?" to "which complementary pair is most defensible?" Selecting two
distinct legs from 32 gives 496 two-leg candidate books. The public ranking
artifacts contain 496 candidates per mechanism and 992 ranking rows in total.

The combination is not a simple average of two independent return percentages.
The shared-account replay consumes recorded trade events and daily trade marks,
derives each event's return from its recorded target-notional basis, and applies
that return to a common accounting basis. Mechanism A re-bases active fold
sizing monthly. Mechanism B locks a fold basis at fold start and applies the
current allocation only to new entry flow, allowing realized performance to
change the later split. Neither mechanism forcibly rebalances open trades.

The candidate books were compared using multiple views of robustness: separate
scores, rank averages, and joined Sharpe, for both replay mechanisms. The
current selected pair ranks first under all configured criteria. Its runtime
roles are explicitly recorded in
`research/selected_book_config.json`, rather than inferred from the order of a
ranking table. This is why the current book exists: it combines a recent-
strong leg with a historically strong leg, while retaining a reproducible
selection rule instead of presenting one isolated "best strategy" result.

## 7. Dynamic Capital Allocation

A static 50/50 split was a useful baseline but was not the end state. The two
legs were intentionally selected for different regime strengths, so the
research tested whether recent relative behavior could inform the allocation
without looking ahead. The allocator calculates trailing Sharpe strictly before
each month, then moves the Leg A weight toward the leg with the stronger recent
score.

The locked Clean40 configuration uses an 84-day lookback, a 0.40 step, bounds
of 10% to 90%, and an initial Leg A weight of 50%. The step is a movement of up
to 40 percentage points on an allocation update, subject to the bounds; it is
not a claim that the strategy can trade continuously at those weights. The
weight lattice was considered as a practical design constraint, but the final
choice was guided by robustness and consistent replay behavior rather than by
maximizing one raw metric.

The allocation decision remains causal within each replay. It does not turn the
recent and historical selection windows into a portfolio holdout. It is a
capital-allocation rule applied to the selected legs after their candidate
evidence has been compared.

## 8. Factor Diagnostics and Limitations

The current factor report uses the pinned daily Fama-French three-factor,
Momentum, and Short-Term Reversal snapshot with HAC standard errors. Historical
annualized intercepts are positive, approximately 6.77% for Mechanism A and
6.53% for Mechanism B, but their p-values are about 0.066 and 0.077. Recent
alpha changes sign across starts and is not significant. No reported alpha
p-value establishes statistically significant pure alpha at the 5% level.

Short-term reversal is a recurring exposure in the recent diagnostics, and
recent market betas are positive. That matters for interpretation. The current
book should be presented as a low-volatility or diversifying statistical-
arbitrage research candidate, not as proven factor-neutral standalone alpha.
The factor report is a diagnostic about exposures and residual return; it does
not prove that the observed Sharpe will persist.

Other limitations remain material. The public replay does not model borrow
costs, slippage, transaction costs, realistic capacity, or production broker
constraints. Pair overlap can concentrate exposure in shared names, and the
static constituent universe can introduce survivorship concerns. These are
known boundaries of the current research, not details that the factor analysis
can eliminate.

## 9. Research Errors and Reproducibility Improvements

The research process also uncovered implementation and reproducibility issues.
Some earlier runs could route to a cached pool from the wrong selection window,
universe, or profile. An empty cached result could also be treated as missing,
causing an unintended live-selection fallback and a different candidate
universe. Runtime filtering and cache routing were made explicit, cached rows
were validated again at load time, and a genuine empty result became an
authoritative result rather than an invitation to silently change the input.

The corrected pipeline introduced metadata-bearing, deterministic pool and
price boundaries, formalized zero-pair folds, and reran decisions that depended
materially on the affected inputs. It also added replay fixtures, a pinned
factor snapshot, deterministic ranking artifacts, figure generation, and a
manifest that records source paths, hashes, and the replay input-tree hash.
These changes make the public result auditable without pretending that every
historical experiment was equally reliable.

The rule for historical interpretation is intentionally selective. A result
that merely motivated a later question does not need to be regenerated if it is
no longer used as evidence. A result that materially selected a downstream
candidate must either be rerun after correction or be labeled superseded. The
original single-strategy headline therefore remains historical context, while
affected intermediate conclusions are not presented as support for the current
book. The detailed correction analysis is preserved in the archival history,
not restored as public clutter.

## 10. Current Canonical State

The current authoritative configuration is
`research/selected_book_config.json`. It records the locked Clean40 book:

- Leg A: `sp500-12m/cross_sector_slide1m_noscreen`, selected for recent strength;
- Leg B: `sp500-2m/cross_sector_slide3m_bd7`, selected for historical strength;
- initial capital of `$1,000,000` with `pct_per_pair=0.25`;
- an 84-day causal allocator, 0.40 step, 10%--90% bounds, and 50% initial Leg A weight; and
- a loss-only `max_holding_days=15` rule tested as 15 calendar days.

The current public evidence is the shared-account replay under
`results/final/combined` when regenerated from the tracked event fixtures, the
compact metrics and rankings under `results/final/`, and the pinned factor
report under `results/final/factors/`. The reproducibility pipeline is the
combination of `research/portfolio_selection.py`,
`research/run_combined_backtest.py`, `research/factor_report.py`,
`research/plot_public_results.py`, and
`scripts/build_public_artifacts.py`.

These current artifacts supersede the earlier notebook-era results as the
public source of truth. The earlier results still explain why the project
changed, but they should not be read as additional current performance claims.
The next meaningful validation step is not another retrospective selection
from the same displayed windows. It is disciplined observation on genuinely
unseen future data, with realistic execution assumptions added as the research
continues.
