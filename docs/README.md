# Public Research Guide

This directory separates the public explanation from the lower-level experiment
log. The current public narrative is the V2 gross-exposure candidate described
in the files below.

## Reading Order

- [`methodology.md`](methodology.md): what is measured and how the replay works
- [`results.md`](results.md): the selected V2 book and headline numbers
- [`robustness.md`](robustness.md): start, fold, concentration, and allocator checks
- [`limitations.md`](limitations.md): what the research does not establish
- [`reproducibility.md`](reproducibility.md): commands, inputs, and provenance
- [`research_chronology.md`](research_chronology.md): concise chronology of the research decisions

## Supporting Record

- [`research_decision_log.md`](research_decision_log.md) is the detailed,
  retrospective experiment log. It is intentionally more granular than the
  public narrative.
- [`old_winner_v1_v2_autopsy.md`](old_winner_v1_v2_autopsy.md) documents the
  earlier V1-winner investigation.
- [`research_summary.md`](research_summary.md) describes the earlier V1 public
  artifact generation and remains useful as a historical reference.
- [`research_journey.md`](research_journey.md) contains the longer development
  narrative. Its V1 current-state sections are superseded by the V2 artifact
  boundary documented here.
- [`sizing_v2_experiment.md`](sizing_v2_experiment.md) contains lower-level V1/V2
  sizing implementation details and diagnostics.

## Current Source of Truth

The current V2 presentation uses:

- `results/sizing_v2_full_summary/` for the completed full-matrix comparison;
- `results/v1_v2_selected_book_crosscheck/` for focused selection and sizing validation; and
- `results/v2_book_clean40_retune/` for the frozen V2-book allocator audit.

The tracked `results/final/` tree and
`research/selected_book_config.json` are preserved V1 public artifacts. They are
not rewritten by the V2 presentation.
