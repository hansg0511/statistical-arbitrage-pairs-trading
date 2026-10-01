# Full V2 gross-exposure matrix

This generated report compares the canonical pct=0.25 reference-leg V1 sweep with
the same 32 standalone configurations rerun using total pair gross-exposure sizing.
The combined tables use the locked 84-day causal allocator (step 0.40, bounds
0.10--0.90) and the existing trade-event replay.

## Standalone ranking

Rank change is `V1 rank - V2 rank`; positive values improve under V2.

| V2 rank | Leg | V1 rank | Rank change | V1 score | V2 score | V1 recent | V2 recent | V1 hist | V2 hist | Decisions |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `sp500-12m/same_sector_slide1m_bd7` | 2 | +1 | 0.5030 | 0.7006 | 0.6762 | 0.9641 | 0.5030 | 0.7006 | unchanged |
| 2 | `sp500-12m/cross_sector_slide1m_bd7` | 1 | -1 | 0.5621 | 0.6531 | 1.2865 | 1.0772 | 0.5621 | 0.6531 | unchanged |
| 3 | `sp500-12m/cross_sector_slide1m_noscreen` | 3 | +0 | 0.4440 | 0.5374 | 1.8436 | 1.5781 | 0.4440 | 0.5374 | unchanged |
| 4 | `sp500-12m/same_sector_slide1m_noscreen` | 5 | +1 | 0.4046 | 0.5320 | 1.3267 | 1.4211 | 0.4046 | 0.5320 | unchanged |
| 5 | `sp500-12m/same_sector_slide3m_noscreen` | 6 | +1 | 0.3669 | 0.4630 | 0.8107 | 0.9660 | 0.3669 | 0.4630 | unchanged |
| 6 | `sp500-12m/cross_sector_slide3m_bd7` | 8 | +2 | 0.2963 | 0.3223 | 0.8135 | 0.7167 | 0.2963 | 0.3223 | unchanged |
| 7 | `core-12m/cross_sector_slide1m_bd7` | 7 | +0 | 0.3196 | 0.3012 | 0.5059 | 0.4181 | 0.3196 | 0.3012 | unchanged |
| 8 | `sp500-2m/cross_sector_slide3m_noscreen` | 4 | -4 | 0.4051 | 0.2627 | 0.4051 | 0.2627 | 0.6248 | 0.3152 | unchanged |
| 9 | `sp500-12m/same_sector_slide3m_bd7` | 10 | +1 | 0.1906 | 0.1948 | 0.4374 | 0.7193 | 0.1906 | 0.1948 | unchanged |
| 10 | `core-12m/same_sector_slide1m_bd7` | 12 | +2 | 0.1335 | 0.1659 | 0.2811 | 0.3131 | 0.1335 | 0.1659 | unchanged |
| 11 | `sp500-2m/same_sector_slide3m_noscreen` | 11 | +0 | 0.1903 | 0.1467 | 0.3339 | 0.3349 | 0.1903 | 0.1467 | unchanged |
| 12 | `sp500-2m/same_sector_slide3m_bd7` | 9 | -3 | 0.1967 | 0.1426 | 0.2888 | 0.2429 | 0.1967 | 0.1426 | unchanged |
| 13 | `core-2m/cross_sector_slide1m_bd7` | 18 | +5 | -0.1159 | 0.0575 | 0.3290 | 0.0575 | -0.1159 | 0.0839 | unchanged |
| 14 | `core-2m/cross_sector_slide3m_noscreen` | 20 | +6 | -0.1783 | -0.0125 | 0.7938 | 0.6345 | -0.1783 | -0.0125 | unchanged |
| 15 | `core-12m/cross_sector_slide3m_bd7` | 15 | +0 | -0.0976 | -0.0222 | 0.3137 | 0.2511 | -0.0976 | -0.0222 | unchanged |
| 16 | `sp500-2m/cross_sector_slide1m_noscreen` | 13 | -3 | 0.1282 | -0.0363 | 0.4530 | 0.2945 | 0.1282 | -0.0363 | unchanged |
| 17 | `core-2m/same_sector_slide1m_bd7` | 17 | +0 | -0.1012 | -0.0413 | 1.2971 | 0.9524 | -0.1012 | -0.0413 | unchanged |
| 18 | `core-2m/cross_sector_slide3m_bd7` | 19 | +1 | -0.1398 | -0.0495 | -0.0089 | -0.0495 | -0.1398 | 0.0396 | unchanged |
| 19 | `core-2m/same_sector_slide1m_noscreen` | 16 | -3 | -0.0997 | -0.1190 | 1.2807 | 1.0627 | -0.0997 | -0.1190 | unchanged |
| 20 | `sp500-2m/same_sector_slide1m_noscreen` | 14 | -6 | -0.0398 | -0.1475 | -0.0398 | -0.1475 | 0.2754 | 0.2946 | unchanged |
| 21 | `sp500-12m/cross_sector_slide3m_noscreen` | 21 | +0 | -0.2208 | -0.2073 | 1.0972 | 0.9442 | -0.2208 | -0.2073 | unchanged |
| 22 | `core-12m/same_sector_slide3m_bd7` | 22 | +0 | -0.3366 | -0.2334 | 0.1164 | 0.1543 | -0.3366 | -0.2334 | unchanged |
| 23 | `sp500-2m/cross_sector_slide3m_bd7` | 23 | +0 | -0.3771 | -0.3296 | -0.3771 | -0.3296 | 0.8784 | 0.6425 | unchanged |
| 24 | `sp500-2m/cross_sector_slide1m_bd7` | 24 | +0 | -0.3859 | -0.3533 | -0.3859 | -0.3533 | 0.3892 | 0.2866 | unchanged |
| 25 | `core-12m/cross_sector_slide1m_noscreen` | 26 | +1 | -0.4434 | -0.3725 | 0.8149 | 0.5578 | -0.4434 | -0.3725 | unchanged |
| 26 | `core-2m/same_sector_slide3m_noscreen` | 27 | +1 | -0.5635 | -0.3968 | 0.5034 | 0.4636 | -0.5635 | -0.3968 | unchanged |
| 27 | `core-2m/cross_sector_slide1m_noscreen` | 28 | +1 | -0.5668 | -0.4249 | 1.5054 | 0.9699 | -0.5668 | -0.4249 | unchanged |
| 28 | `sp500-2m/same_sector_slide1m_bd7` | 25 | -3 | -0.3859 | -0.4938 | -0.3859 | -0.4938 | -0.2340 | -0.1664 | unchanged |
| 29 | `core-12m/cross_sector_slide3m_noscreen` | 30 | +1 | -0.6987 | -0.5151 | 0.4096 | 0.2550 | -0.6987 | -0.5151 | unchanged |
| 30 | `core-2m/same_sector_slide3m_bd7` | 29 | -1 | -0.6442 | -0.5247 | 0.4702 | 0.3955 | -0.6442 | -0.5247 | unchanged |
| 31 | `core-12m/same_sector_slide1m_noscreen` | 31 | +0 | -0.7898 | -0.8136 | 0.2865 | 0.2561 | -0.7898 | -0.8136 | unchanged |
| 32 | `core-12m/same_sector_slide3m_noscreen` | 32 | +0 | -0.9010 | -0.8518 | 0.2660 | 0.1869 | -0.9010 | -0.8518 | unchanged |

## Combined-book ranking

The complete V2 score and ranking tables contain 496 books per mechanism.
The tables below show the top 20 by the existing separate score
`min(recent_sh, hist_sh)`; all ranks are in the generated CSV artifacts.

### Mechanism A

| Rank | Leg A | Leg B | Recent | Historical | Score | Joined |
|---:|---|---|---:|---:|---:|---:|
| 1 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-12m/same_sector_slide3m_noscreen` | 0.9983 | 0.7980 | 0.7980 | 0.8501 |
| 2 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-12m/same_sector_slide1m_bd7` | 0.7970 | 0.8447 | 0.7970 | 0.8290 |
| 3 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-2m/same_sector_slide1m_noscreen` | 0.7800 | 0.8741 | 0.7800 | 0.8250 |
| 4 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-12m/same_sector_slide3m_noscreen` | 1.2559 | 0.7722 | 0.7722 | 0.9268 |
| 5 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-2m/same_sector_slide3m_noscreen` | 0.9179 | 0.7592 | 0.7592 | 0.8029 |
| 6 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-12m/same_sector_slide1m_bd7` | 1.1635 | 0.7333 | 0.7333 | 0.8656 |
| 7 | `sp500-12m/cross_sector_slide1m_bd7` | `sp500-12m/same_sector_slide3m_noscreen` | 0.7193 | 0.7797 | 0.7193 | 0.7631 |
| 8 | `sp500-12m/cross_sector_slide3m_bd7` | `sp500-12m/same_sector_slide3m_noscreen` | 1.1476 | 0.6905 | 0.6905 | 0.8112 |
| 9 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/cross_sector_slide3m_bd7` | 0.7609 | 0.6713 | 0.6713 | 0.6999 |
| 10 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-12m/same_sector_slide3m_bd7` | 1.1883 | 0.6350 | 0.6350 | 0.8166 |
| 11 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-12m/same_sector_slide3m_bd7` | 0.6174 | 0.7828 | 0.6174 | 0.7241 |
| 12 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-2m/same_sector_slide1m_noscreen` | 1.2049 | 0.6132 | 0.6132 | 0.8123 |
| 13 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-2m/cross_sector_slide3m_bd7` | 1.0751 | 0.6124 | 0.6124 | 0.7587 |
| 14 | `sp500-12m/same_sector_slide1m_bd7` | `sp500-12m/same_sector_slide3m_bd7` | 0.9896 | 0.6107 | 0.6107 | 0.7237 |
| 15 | `sp500-12m/cross_sector_slide1m_bd7` | `sp500-12m/same_sector_slide3m_bd7` | 0.6589 | 0.6031 | 0.6031 | 0.6129 |
| 16 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/same_sector_slide3m_bd7` | 1.0650 | 0.5710 | 0.5710 | 0.7266 |
| 17 | `core-2m/cross_sector_slide1m_noscreen` | `sp500-12m/cross_sector_slide1m_bd7` | 1.0567 | 0.5644 | 0.5644 | 0.7241 |
| 18 | `sp500-12m/same_sector_slide1m_bd7` | `sp500-2m/cross_sector_slide1m_bd7` | 0.5583 | 0.7299 | 0.5583 | 0.6465 |
| 19 | `sp500-12m/same_sector_slide3m_noscreen` | `core-2m/cross_sector_slide1m_bd7` | 0.6533 | 0.5409 | 0.5409 | 0.5864 |
| 20 | `sp500-12m/cross_sector_slide1m_bd7` | `sp500-2m/same_sector_slide1m_noscreen` | 0.5325 | 0.5408 | 0.5325 | 0.5311 |

### Mechanism B

| Rank | Leg A | Leg B | Recent | Historical | Score | Joined |
|---:|---|---|---:|---:|---:|---:|
| 1 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-12m/same_sector_slide1m_bd7` | 0.8041 | 0.8799 | 0.8041 | 0.8528 |
| 2 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-12m/same_sector_slide3m_noscreen` | 1.1604 | 0.8006 | 0.8006 | 0.9120 |
| 3 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-12m/same_sector_slide3m_noscreen` | 1.0224 | 0.7653 | 0.7653 | 0.8361 |
| 4 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-12m/same_sector_slide1m_bd7` | 1.0626 | 0.7482 | 0.7482 | 0.8367 |
| 5 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-2m/same_sector_slide3m_noscreen` | 0.9523 | 0.7338 | 0.7338 | 0.7963 |
| 6 | `sp500-12m/cross_sector_slide1m_bd7` | `sp500-12m/same_sector_slide3m_noscreen` | 0.6997 | 0.7860 | 0.6997 | 0.7577 |
| 7 | `sp500-12m/cross_sector_slide1m_noscreen` | `sp500-2m/same_sector_slide1m_noscreen` | 0.6865 | 0.9532 | 0.6865 | 0.8395 |
| 8 | `sp500-12m/cross_sector_slide3m_bd7` | `sp500-12m/same_sector_slide3m_noscreen` | 1.1409 | 0.6860 | 0.6860 | 0.8060 |
| 9 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/cross_sector_slide3m_bd7` | 0.7590 | 0.6673 | 0.6673 | 0.6964 |
| 10 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-2m/cross_sector_slide3m_bd7` | 1.0095 | 0.6579 | 0.6579 | 0.7666 |
| 11 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-12m/same_sector_slide3m_bd7` | 0.6125 | 0.7794 | 0.6125 | 0.7198 |
| 12 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-12m/same_sector_slide3m_bd7` | 1.1034 | 0.6062 | 0.6062 | 0.7682 |
| 13 | `sp500-12m/cross_sector_slide1m_bd7` | `sp500-12m/same_sector_slide3m_bd7` | 0.6443 | 0.6011 | 0.6011 | 0.6054 |
| 14 | `sp500-12m/same_sector_slide1m_bd7` | `sp500-2m/cross_sector_slide1m_bd7` | 0.5943 | 0.7900 | 0.5943 | 0.6938 |
| 15 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-2m/same_sector_slide1m_noscreen` | 1.0052 | 0.5817 | 0.5817 | 0.7208 |
| 16 | `sp500-12m/same_sector_slide1m_bd7` | `sp500-12m/same_sector_slide3m_bd7` | 1.0147 | 0.5678 | 0.5678 | 0.7038 |
| 17 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/same_sector_slide3m_bd7` | 1.0581 | 0.5672 | 0.5672 | 0.7211 |
| 18 | `sp500-12m/same_sector_slide1m_noscreen` | `sp500-2m/cross_sector_slide1m_bd7` | 1.1121 | 0.5545 | 0.5545 | 0.7440 |
| 19 | `sp500-12m/same_sector_slide1m_bd7` | `core-2m/cross_sector_slide1m_bd7` | 0.7406 | 0.5309 | 0.5309 | 0.5894 |
| 20 | `sp500-12m/same_sector_slide3m_noscreen` | `sp500-2m/same_sector_slide1m_noscreen` | 0.5878 | 0.5259 | 0.5259 | 0.5399 |

## Validation

- Standalone run instances: 192 (expected 192).
- Combined V1 rows: 992 (expected 992).
- Combined V2 rows: 992 (expected 992).
- Standalone configurations with changed decisions: 0.
- V2 standalone gross-budget invariant failures: 0.
- Canonical public V1 score-table comparison: match

Raw runs are under the ignored `results/sizing_v2_full/` tree. Compact outputs are:
`standalone_v1_v2.csv`, `standalone_decision_comparison.csv`,
`combined_v1_scores.csv`, `combined_v2_scores.csv`,
`combined_v1_rankings.csv`, `combined_v2_rankings.csv`, and
`combined_rank_delta.csv`.
