# Statistical Arbitrage: Equity Pairs Trading Research

A systematic investigation of equity-pairs mean reversion, walk-forward testing, and portfolio construction. The project develops statistical trading signals, evaluates their sensitivity to historical conditions, and examines whether combining different strategy configurations produces a more resilient portfolio.

This is a **research and backtesting project**, not a live trading system. The final portfolio is a candidate for forward paper-trading validation, not a demonstrated source of future returns.

## Research Objective

The central question is whether cointegration-based pairs trading can produce repeatable, economically meaningful performance across changing market conditions.

The research began with a standalone mean-reversion strategy. Evaluating it across historical periods and formation choices revealed that individual configurations could behave quite differently. This motivated a broader portfolio question: **can complementary configurations be combined under shared capital to improve robustness, rather than relying on a single backtest winner?**

The study therefore examines signal construction, walk-forward selection, portfolio combination, capital allocation, concentration, parameter stability, and transaction-cost sensitivity.

## Trading Strategy

### Pair formation and signals

1. **Form candidate pairs.** Within each walk-forward formation window, test log-price relationships using Engle–Granger cointegration (5% significance threshold), estimate an OLS hedge ratio and intercept, and assess residual half-life and other eligibility criteria. Depending on the configuration, pairing is restricted to the same sector or allowed across sectors. Up to 20 pairs are selected per fold.
2. **Trade deviations.** Model the spread as `r_t = log(P_A,t) - beta * log(P_B,t) - alpha`. Enter on sufficiently large residual z-score deviations and exit as the spread converges or when a risk rule is triggered. The strategy uses locked entry statistics, a hedge-ratio drift guard, a z-score stop, fold-end exits, and a loss-only maximum holding period.
3. **Size both legs jointly.** Allocate a defined **total gross-exposure budget** to each pair, accounting for the hedge ratio and integer share quantities. This avoids treating the reference leg alone as the capital used by a long-short position.
4. **Evaluate forward within folds.** Form and rank pairs using data available at the formation boundary, then simulate trading on subsequent observations. The walk-forward procedure is causal at the individual-strategy level.

The selected signal settings and precise sizing equations are documented in [Methodology](docs/methodology.md).

## From Standalone Strategies to Portfolio Construction

Different standalone configurations exhibited materially different behavior across historical periods and start dates. Rather than treating one configuration as universally superior, the portfolio study compared a defined family of alternatives.

The research evaluated **32 standalone configurations** across four universe/formation-window bases, each combined with sector constraints, fold-slide schedules, and optional earnings-event screening. The 32 configurations generate **496 distinct two-configuration portfolios**.

Each portfolio was reconstructed from trade events and daily marks within a shared-account replay—not by simply adding two return series. Two accounting mechanisms were compared:

- **Mechanism A — monthly fold-budget updates:** active folds receive updated sizing budgets at monthly allocation boundaries; existing open trades are not forcibly rebalanced.
- **Mechanism B — entry-flow allocation:** each fold retains its initial capital basis while updated allocation weights apply to new entries, allowing existing exposure to drift.

A causal, trailing-Sharpe allocator adjusts the relative capital weights at month boundaries using prior observations. The replay studies portfolio accounting and allocation decisions; it does not replicate broker execution.

### Selected research portfolio

| Component | Specification |
|---|---|
| Strategy A | S&P 500 universe; 12-month formation; same-sector pairs; 1-month slide; no earnings screen |
| Strategy B | S&P 500 universe; 12-month formation; same-sector pairs; 3-month slide; no earnings screen |
| Signals | Common cointegration-based residual mean-reversion rules |
| Position sizing | Fixed total pair gross-exposure budget; nominal $250,000 pair budget in a $1,000,000 research account |
| Allocation | 84-day trailing Sharpe; 40-percentage-point step; 10%–90% bounds; initial 50/50 split |

The selected combination ranked first by **average recent/historical rank** and by **joined-series Sharpe rank** under both replay mechanisms. It was not the best portfolio under every individual ranking criterion. Selection considered performance across periods rather than maximizing the most recent Sharpe alone.

## Historical Evaluation

### Portfolio replay results — before trading costs

The results below describe the historically **selected** portfolio. The recent figures average five overlapping, shifted-start evaluations; the historical comparison uses one aligned control. Each statistic is an average of start-level metrics, not a statistic calculated by joining those return paths into one artificial series.

| Evaluation | Starts | Mechanism | Mean annual return | Mean volatility | Mean Sharpe | Mean max drawdown |
|---|---:|---|---:|---:|---:|---:|
| Recent | 5 | A | 9.44% | 7.28% | 1.256 | -3.58% |
| Recent | 5 | B | 8.82% | 7.37% | 1.160 | -4.19% |
| Historical | 1 | A | 3.55% | 4.66% | 0.772 | -6.10% |
| Historical | 1 | B | 3.66% | 4.62% | 0.801 | -6.10% |

These five recent starts overlap substantially and should **not** be interpreted as five independent confirmations. Detailed results and ranking evidence are in [Results](docs/results.md).

### Robustness and allocation

The analysis examined start-date dispersion, calendar and fold concentration, individual trade/pair/symbol contributions, allocation turnover, and sensitivity to neighboring allocator settings.

A fixed-book allocation audit compared **40 dynamic allocator configurations** with an equal-weight (50/50) alternative. The selected dynamic setting belonged to a plateau of eight nearby configurations and remained in the selected parameter region under leave-one-start-out checks.

| Allocation comparison | Dynamic allocation | Static 50/50 |
|---|---:|---:|
| Recent mean Sharpe | 1.208 | 1.237 |
| Historical mean Sharpe | 0.786 | 0.503 |
| Robustness score (minimum across defined evaluation criteria) | 0.772 | 0.491 |

The dynamic allocator did **not** have the highest recent mean Sharpe. Its selection reflected the chosen cross-period robustness rule, which remains a historical model-selection decision—not independent validation.

[Recent equity curves](results/v2_book_clean40_retune/baseline_equity_recent.png) · [Allocation weights](results/v2_book_clean40_retune/baseline_weight_recent.png) · [Recent parameter sensitivity](results/v2_book_clean40_retune/clean40_surface_recent.png) · [Historical parameter sensitivity](results/v2_book_clean40_retune/clean40_surface_historical.png)

### Transaction-cost sensitivity

Execution friction materially changes the interpretation of the results. The frozen portfolio was evaluated under assumed **one-way all-in costs per traded notional** at entry and exit, without re-optimizing the strategy.

| Assumed one-way cost | Recent mean Sharpe | Historical mean Sharpe | Recent mean annual return | Historical mean annual return |
|---:|---:|---:|---:|---:|
| 0 bps | 1.208 | 0.786 | 9.13% | 3.61% |
| 5 bps | 0.833 | 0.189 | 6.34% | 0.82% |
| 10 bps | 0.460 | -0.402 | 3.50% | -2.31% |
| 20 bps | -0.282 | -1.536 | -2.38% | -10.12% |

The historical control turns negative by 10 bps, with estimated one-way break-even costs near **6.3–6.5 bps**. Execution quality is therefore a central deployment risk. These are sensitivity assumptions, **not measured live transaction costs**. See the [Transaction-Cost Report](results/transaction_cost_analysis/tca_summary.md).

## Interpretation and Limitations

**Walk-forward does not automatically mean untouched out-of-sample performance at every level.** Individual pairs are selected using preceding formation data and then traded forward. However, the portfolio, strategy combination, and allocation parameters were chosen after examining the reported historical windows. Consequently, the aggregate figures above are **research-window results, not an unbiased portfolio-level holdout estimate or a forward Sharpe forecast**.

The study also has implementation limits:

- **Execution:** the replay does not model live bid/ask spreads, fills, market impact, two-leg execution delays, borrow availability, financing, or broker margin admission. The separate cost overlay is deliberately simplified.
- **Capital and exposure:** pair overlap, variable portfolio gross leverage, and the absence of a broker-enforced gross/symbol cap limit deployability claims.
- **Data:** historical universe snapshots, survivorship, corporate actions, missing prices, and vendor revisions may affect portability and replication.
- **Statistical evidence:** overlapping recent starts, regime dependence, concentration, and adaptive model selection limit conclusions about persistence.

The appropriate next test is a **frozen forward paper-trading study** with observed orders, fills, transaction costs, borrow constraints, exposure limits, and reconciliation. [Detailed limitations](docs/limitations.md).

## Reproducibility and Research Record

The default strategy definition is [`research/selected_book_config.json`](research/selected_book_config.json). Published compact analysis tables and diagnostic figures can be reviewed directly, but **the full raw runs needed to regenerate the selected portfolio are not included in this public repository**.

An earlier experimental configuration and its original replay fixtures remain archived separately for provenance. These historical fixtures must not be presented as the final portfolio's raw inputs. Version-specific artifact names are retained in the technical files to avoid breaking reproducibility.

For environment setup and verification:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

Start with [Reproducibility](docs/reproducibility.md) for commands and input boundaries, and [Results Index](results/README.md) for the published research artifacts.

### Further reading

- [Methodology](docs/methodology.md) — pair formation, signals, sizing, shared-account mechanics
- [Results](docs/results.md) — detailed portfolio rankings and performance
- [Robustness](docs/robustness.md) — starts, concentration, allocator comparisons
- [Research Decision Log](docs/research_decision_log.md) — retrospective experiment-by-experiment rationale and decisions
- [Research Chronology](docs/research_chronology.md) — how the investigation evolved
- [Documentation Index](docs/README.md) — additional technical and historical reports

## Research Status

Historical model and portfolio selection are **frozen**. No further tuning is planned on the research windows shown here; future evidence should come from forward paper trading rather than additional optimization of the historical record.
