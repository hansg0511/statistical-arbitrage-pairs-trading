# Research Chronology

This is a concise public chronology. The detailed experiment-level record is in
[`research_decision_log.md`](research_decision_log.md).

## 1. Initial Signal Framework

The project began with cointegrated equity pairs, log-price hedge relationships,
residual z-scores, walk-forward folds, hedge-ratio guards, stops, and holding
limits. Early results motivated broader testing but were not treated as evidence
for the current book.

## 2. Robustness Questions

Start-date, regime, pair-identity, and earnings-event diagnostics showed that a
single strong result could be sensitive to formation choices. The response was
to compare explicit configuration families rather than continue tuning one
setup.

## 3. Expanded Book Study

Four strategy bases and eight configuration variants produced 32 standalone
configurations. Their two-leg combinations produced 496 candidate books per
replay mechanism. Recent and historical windows, separate scores, rank averages,
and joined-book evidence became part of the selection boundary.

## 4. V1 Public Snapshot

The earlier public artifact generation locked the V1 reference-leg book on
2026-09-08. It remains in `research/selected_book_config.json` and
`results/final/` for reproducibility. It is preserved, not promoted as the
latest V2 candidate.

## 5. V2 Gross-Exposure Convention

The sizing investigation identified that V1's `pct_per_pair` controlled a
reference leg while the hedge leg added exposure. V2 instead treats the same
budget as total pair gross exposure. The underlying signals and trade identities
remain controlled; V1 is retained as the historical sizing control.

The completed comparison covered 32 configurations, 192 standalone instances,
496 books, both mechanisms, and both sizing modes. It found that combined-book
rankings were more sensitive than standalone decisions, so the V2 candidate was
audited directly rather than treated as a new alpha signal.

## 6. V2 Candidate and Focused Cross-Check

The current V2 rank-average candidate became:

- `sp500-12m/same_sector_slide1m_noscreen`; and
- `sp500-12m/same_sector_slide3m_noscreen`.

The selected-book cross-check replayed the old V1 book and this V2 candidate
under both sizing modes on the same preserved trade identities. Validation
passed, protected V1 outputs remained unchanged, and the exposure-adjusted
result favored V2 for the current V2-selected book. This did not establish that
V2 is universally superior.

## 7. V2 Clean40 Audit

The final completed research audit held the V2 book and V2 sizing fixed. It
checked per-start results, concentration, native exposure, trade identity,
calendar and fold attribution, a 40-configuration lattice, static 50/50, nearby
settings, leave-one-start-out selection, and allocator-only cost sensitivity.

The existing 84-day, 0.40, 10%--90% allocator remained the defensible choice:
robust floor 0.772, static floor 0.491, plateau size 8, and one leave-one-start-
out selected region. The decision was `keep_old_clean40`.

## 8. Current Presentation Boundary

This branch reorganizes the evidence for public reading. It does not change
research code, rerun the matrix, replace the V1 config, or rewrite the lower-
level decision log. The next research question is unseen paper-trading behavior
under realistic costs, borrow, execution, margin, and reconciliation controls.
