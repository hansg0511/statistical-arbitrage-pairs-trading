# Robust Mean-Reversion Research Summary

## Scope

This repository contains an offline, walk-forward research engine for
cointegrated equity pairs. It is not a live trading system and makes no claims
about broker execution, borrow availability, slippage, or capacity.

## Locked Book

The selected book is defined in
[`research/selected_book_config.json`](../research/selected_book_config.json).
It combines:

- Leg A: `sp500-12m/cross_sector_slide1m_noscreen`
- Leg B: `sp500-2m/cross_sector_slide3m_bd7`
- Capital: `$1,000,000`; `pct_per_pair=0.25`
- Causal momentum allocator: 84-day lookback, 0.40 step, 10%--90% bounds
- Initial Leg A weight: 50%

The pair universe contains 496 two-leg combinations. The selected pair ranks
first under separate-score, rank-average, and joined-Sharpe methods for both
mechanisms A and B.

## Results

Values below are from the shared-account trade-event replay. Recent values are
means over five aligned starts; historical is one aligned 2015--2019 window.

| Window | Mechanism | Annual return | Annual volatility | Sharpe | Max drawdown |
|---|---|---:|---:|---:|---:|
| Recent | A | 9.4462% | 8.6031% | 1.0937 | -5.5413% |
| Recent | B | 9.8116% | 8.5251% | 1.1413 | -5.5496% |
| Historical | A | 9.0980% | 8.0461% | 1.1222 | -8.9530% |
| Historical | B | 8.8316% | 8.0105% | 1.0963 | -8.8666% |

The compact source tables are in [`results/final/`](../results/final/):
`metrics/selected_book_metrics.csv`,
`rankings/clean40_pair_scores.csv`,
`rankings/clean40_pair_rankings.csv`,
`rankings/clean40_selected_pair.csv`, and
`factors/selected_book.md`. The factor input is pinned in
`factors/ff_daily_2015_2025.csv` with retrieval metadata beside it. The
generation manifest is `manifest.json`.

## Method

Pair selection uses the tracked corrected score snapshot in
`results/final/rankings/clean40_pair_scores.csv`. The
[`research/portfolio_selection.py`](../research/portfolio_selection.py) module
recomputes the separate score, recent and historical ranks, rank average, and
joined-Sharpe rank for all 496 pairs. It then requires the configured pair to
rank first under every criterion in both mechanisms. The two legs are not
combined by adding independent return percentages. The replay consumes trade
logs and daily trade marks, maintains one shared cash account, applies causal
monthly weights, and records realized and open-trade PnL.

The `A` and `B` columns in the candidate score tables identify an unordered
pair; the locked leg roles and runtime assignment are defined by the selected
book configuration.

Mechanism A re-bases active fold sizing monthly. Mechanism B locks a fold basis
and applies the current weight only to new entry flow. Neither mechanism forces
open trades to rebalance.

## Generation Parameters

Both legs use the S&P 500 universe, log prices, cross-sector pairing, a
cointegration p-value threshold of 0.05, return-divergence threshold 0.10,
three-month test folds, and these fixed strategy parameters: entry z-score
2.2, exit z-score 1.0, stop z-score 4.5, residual validation 90, z-score
lookback multiplier 0.5, hedge-ratio threshold 0.8, and maximum holding period
15 trading days. Each fold selects at most 20 pairs with `pct_per_pair=0.25`
and `dollar_neutral=false`.

- Leg A uses pool `sp500_12m`, 12-month selection, one-month fold slide, and no earnings screen.
- Leg B uses pool `sp500_2m`, 2-month selection, three-month fold slide, and an earnings screen with a seven-day block.
- The shared account starts at `$1,000,000`; the allocator uses an 84-day causal lookback, 0.40 step, 10%--90% bounds, and initial Leg A weight 50%.
- Replay assumptions are broker leverage 100, margin behavior `off`, 50% long and short margin, and 25%/30% maintenance requirements. Borrow, slippage, and transaction costs are not modeled.

## Factor Interpretation

The factor report uses daily FF3 + Momentum + Short-Term Reversal regressions
with HAC standard errors. Historical alpha is positive but not conventionally
significant for either mechanism. Recent alpha changes sign across starts and
is not significant. Recent market and short-term-reversal loadings are more
stable than the alpha estimates, so the results should not be presented as
evidence of factor-neutral excess return. The tracked daily factor snapshot is
from the Kenneth French Data Library; source URLs, retrieval date, row count,
and checksum are in `results/final/factors/ff_daily_2015_2025.json`.

## Reproduction

From the repository root:

```text
python -m pip install -e ".[dev]"
python -m pytest
python research/portfolio_selection.py
python research/run_combined_backtest.py --window recent --mechanism both
python research/run_combined_backtest.py --window historical --mechanism both
python research/factor_report.py
python research/plot_public_results.py
python scripts/build_public_artifacts.py
```

The combined replay reads only the tracked event fixtures under
`results/final/event_replay_inputs/`. The generic experiment runner remains an
exploratory path and requires a compatible price snapshot and pool data.

The experiment runner can load a validated local price snapshot with
`--price-snapshot`; without one it fetches prices through `yfinance`. Pool
construction is explicit and metadata-bearing:

```text
python scripts/build_pair_pool.py --selection-start 2023-01-01 --selection-stop 2023-05-01 --selection-months 12 --universe sp500 --return-divergence 0.10 --output data/pools/sp500_12m.pkl
```

The historical `fixed_diagnosis/` corpus and notebooks are evidence of the
development process, not the runtime source of truth. The archival tag
`pre-public-cleanup-20260909` preserves that development history separately.
