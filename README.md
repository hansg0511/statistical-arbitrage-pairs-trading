# Robust Mean-Reversion Research

Offline research code for walk-forward cointegrated equity-pairs experiments.
The repository is designed to make selection, event replay, and diagnostics
auditable. It is not a live trading system.

## Current Result

The locked selected book is defined in
[`research/selected_book_config.json`](research/selected_book_config.json).

- Leg A: `sp500-12m/cross_sector_slide1m_noscreen`
- Leg B: `sp500-2m/cross_sector_slide3m_bd7`
- Capital: `$1,000,000`; `pct_per_pair=0.25`
- Allocator: 84-day causal lookback, 0.40 step, 10%--90% bounds
- Pair universe: 496 two-leg combinations

Recent values are means over five aligned starts. Historical is one aligned
2015--2019 window.

| Window | Mechanism | Annual return | Volatility | Sharpe | Max drawdown |
|---|---|---:|---:|---:|---:|
| Recent | A | 9.4462% | 8.6031% | 1.0937 | -5.5413% |
| Recent | B | 9.8116% | 8.5251% | 1.1413 | -5.5496% |
| Historical | A | 9.0980% | 8.0461% | 1.1222 | -8.9530% |
| Historical | B | 8.8316% | 8.0105% | 1.0963 | -8.8666% |

Compact tables, factor diagnostics, replay inputs, and figures are under
[`results/final/`](results/final/).

The all-pair score input and recomputed ranking evidence are in
`results/final/rankings/`. The factor report uses the tracked
`factors/ff_daily_2015_2025.csv` snapshot; live downloads are opt-in only.
Candidate ranking rows treat the two pair paths as unordered; the locked book
configuration defines the Leg A and Leg B runtime roles.

## Workflow

1. `research/run_experiment.py` runs one declarative walk-forward experiment.
2. `scripts/build_pair_pool.py` builds a metadata-bearing selection pool.
3. `research/portfolio_selection.py` recomputes the 496-pair rankings from the tracked score snapshot.
4. `research/run_combined_backtest.py` replays leg trade events in one shared account.
5. `research/factor_report.py` runs daily FF3 + Momentum + Short-Term Reversal diagnostics from the pinned snapshot.
6. `research/plot_public_results.py` regenerates the public figures from replay outputs.
7. `scripts/build_public_artifacts.py` writes compact metrics and the provenance manifest.

The shared-account replay uses trade logs and daily trade marks rather than
adding independent leg return percentages. Mechanism A re-bases active fold
sizing monthly. Mechanism B locks a fold basis and applies the current weight
only to new entry flow. Open trades are not forcibly rebalanced.

## Quick Start

From the repository root:

```text
python -m pip install -e ".[dev]"
python -m pytest
```

## Reproduce Published Artifacts

Run the locked event replay, diagnostics, and artifact builders with:

```text
python research/portfolio_selection.py
python research/run_combined_backtest.py --window recent --mechanism both
python research/run_combined_backtest.py --window historical --mechanism both
python research/factor_report.py
python research/plot_public_results.py
python scripts/build_public_artifacts.py
```

The published replay boundary is `results/final/event_replay_inputs/`; it
contains trade events and daily marks rather than raw prices or private data.
The combined replay output is generated locally and is not part of the compact
tracked artifact set.

## Full-Leg Exploration

The generic experiment runner requires compatible pools and market data. Use
`--price-snapshot PATH` for a fixed local market-data input. Without a snapshot,
the runner fetches prices through `yfinance` and records the input when
`--write-price-snapshot PATH` is supplied. Build a selection pool explicitly
when a cached pool is not available:

```text
python research/run_experiment.py --config configs/recent_sweep.yaml
python scripts/build_pair_pool.py --selection-start 2023-01-01 --selection-stop 2023-05-01 --selection-months 12 --universe sp500 --return-divergence 0.10 --output data/pools/sp500_12m.pkl
```

## Limitations

- No borrow costs, slippage, transaction costs, or realistic capacity model are locked yet.
- Earnings and other single-name events can create large idiosyncratic spread moves.
- Pair overlap can concentrate exposure in the same underlying names.
- Fama-French alpha estimates are diagnostics, not proof of factor-neutral excess return.
- Exact full-leg reproduction requires the same price snapshot and fixed event inputs; vendor downloads can change.
- The published factor diagnostics are reproducible from the pinned snapshot; use `--live-factors` only for exploratory comparisons.
