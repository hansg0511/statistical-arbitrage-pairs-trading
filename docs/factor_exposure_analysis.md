# Factor Exposure Analysis — Selected Research Portfolio

## Purpose and interpretation

This is a **descriptive, post-selection diagnostic** of the final frozen two-configuration portfolio, using preserved account-level daily returns. It does **not** reopen strategy, book, or allocator optimization and provides no independent portfolio-level holdout evidence.

The portfolio combines `sp500-12m/same_sector_slide1m_noscreen` and `sp500-12m/same_sector_slide3m_noscreen`, with fixed total gross-exposure sizing and the 84-day / 40-percentage-point / 10%–90% allocation rule.

## Data and specification

- **Daily portfolio returns:** [selected-book audit daily data](../results/v2_book_clean40_retune/baseline_daily.csv), 12 account-level return paths (historical: 2015-01-05 to 2019-12-31, A and B; recent: five shifted starts between 2024-01-02 and 2024-05-01, each ending 2025-12-24, A and B).
- **Factor observations:** [pinned Kenneth French daily snapshot](../results/final/factors/ff_daily_2015_2025.csv), last recorded retrieval 2026-07-23, covering 2015-01-02 to 2025-12-31.
- **Regression:** portfolio daily return minus daily risk-free rate, against (1) market excess return alone and (2) market excess return, SMB, HML, Momentum, and Short-Term Reversal, with an intercept.
- **Inference:** OLS with HAC (Bartlett/Newey–West-style) covariance; integer truncation of `n_obs ** 0.25` for maximum lag (five historical, four recent). Annualized alpha is **252 × daily intercept**, not compounded annual return. Two-sided p-values and 95% normal-approximation confidence intervals.
- **Calendar treatment:** retain all recorded days, including zero-return days (36 across the 12 account paths). Match exact daily dates to the pinned factor snapshot. Every recorded observation has a matching factor row.
- **Return convention:** gross historical replay returns, with no broker execution or trading costs subtracted. Evaluations are already subject to adaptive portfolio selection.

## Factor-adjusted intercepts

The table reports the expanded five-regressor model (FF3 + Momentum + Short-Term Reversal). All alpha estimates are statistically indistinguishable from zero at the conventional 5% level.

| Window | Start | Mechanism | Annualized alpha | Alpha p-value | R² | Daily observations |
|---|---:|---|---:|---:|---:|---:|
| Historical | 1 | A | +1.44% | 0.490 | 0.057 | 1,252 |
| Historical | 1 | B | +1.53% | 0.457 | 0.059 | 1,252 |
| Recent | 1 | A | +1.69% | 0.657 | 0.175 | 496 |
| Recent | 1 | B | +1.70% | 0.657 | 0.174 | 496 |
| Recent | 2 | A | −2.29% | 0.468 | 0.267 | 475 |
| Recent | 2 | B | −3.07% | 0.341 | 0.262 | 475 |
| Recent | 3 | A | +2.98% | 0.479 | 0.303 | 448 |
| Recent | 3 | B | +2.79% | 0.512 | 0.302 | 448 |
| Recent | 4 | A | +1.73% | 0.679 | 0.199 | 429 |
| Recent | 4 | B | +1.38% | 0.745 | 0.198 | 429 |
| Recent | 5 | A | −1.16% | 0.740 | 0.294 | 413 |
| Recent | 5 | B | −2.63% | 0.532 | 0.281 | 413 |

### Factor exposures

The expanded regressions exhibit a **positive, statistically significant Short-Term Reversal loading across all 12 paths** (p-values below 0.05). HML (value) is negative and conventionally significant on all ten recent start/mechanism paths, but not on either historical path. Market excess-return beta is positive across all paths and statistically significant in both historical paths and one recent start (both mechanisms), using the expanded model. Other individual factor results vary.

This is consistent with a strategy whose observed returns are associated with known equity return effects. It does **not** establish that those factors causally generate the strategy's PnL. The alpha confidence intervals include zero, but that is **not** proof that true alpha equals zero.

The simpler **market-only** regressions also show no statistically significant intercepts. Their market exposures can differ from the expanded model because other correlated factors are excluded.

### Interpretation boundaries

- The five recent runs overlap in calendar time; neither the starts nor mechanisms are independent replications. Do not pool their p-values or interpret twelve insignificant intercepts as twelve independent disproofs.
- The final book and allocator were selected after historical performance was inspected. Factor regressions on those same historical windows are exploratory diagnostics, **not an independent OOS test**.
- A significant factor beta should not be confused with statistically significant positive alpha. The absence of significant alpha does not prove absence of an edge.
- Reported factor associations are conditional on this specific daily model and factor library; omitted factors and time-varying exposures remain possible.
- Gross account returns and factor risk-free rates are used as recorded. Trading friction, borrow costs, financing, shorting feasibility, and margin constraints remain unresolved deployment questions.
- The archived [earlier portfolio factor report](../results/final/factors/selected_book.md) uses a different book and sizing convention. Its alpha coefficients must not be compared as though they came from this final portfolio.

## Reproduction

Run from the repository root after installing the package dependencies:

```bash
python research/run_selected_portfolio_factors.py
```

This reads the two pinned input CSVs and regenerates:

- [Full coefficient, HAC p-value, confidence-interval, and R² table](../results/factor_exposure/selected_portfolio_factor_regressions.csv)

The script does not rerun the strategy or generate new trading decisions, and it writes only to `results/factor_exposure/`. It retains flat days rather than using the older general regression helper's nonzero-day filter.

**Status:** diagnostic completed; the candidate remains frozen for forward paper trading.
