"""Momentum-param sensitivity + Fama-French for consensus survivor pairs.

Task 1 — Momentum-param sensitivity (not re-optimization): for each survivor
pair x window (recent mean over 5 starts / historical single) x mechanism (A/B),
re-run the combined return series under 5 momentum-tilt schemes plus a static
blend baseline and report Sharpe per setting.

  default : step 10%, bounds [0.25, 0.75]
  step5   : step 5%,  bounds [0.25, 0.75]
  step15  : step 15%, bounds [0.25, 0.75]
  bd20_80 : step 10%, bounds [0.20, 0.80]
  bd35_65 : step 10%, bounds [0.35, 0.65]
  static  : no switching; w_A fixed at Sh_A/(Sh_A+Sh_B) for the window

Task 2 — Fama-French (FF3 + Mom + ST_Rev, daily, HAC) on the combined daily
return series built with the default momentum config (mechs A and B, start 0).
Loadings reported with p-values in brackets.

Outputs (fixed_diagnosis/compare/):
  _MOMENTUM_FF_PAIRS.md
  momentum_sensitivity.csv
  ff_regressions.csv

Usage: python research/momentum_ff_pairs.py
"""
import os
import sys
import math
import itertools
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from research.pair_sweep_consolidated import (  # noqa: E402
    STRATEGIES, CFGS, get_leg,
)
from research.run_combined_backtest import (  # noqa: E402
    _sharpe, weight_path_momentum_causal, simulate, metrics,
)
from src.fama_french import FamaFrenchFetcher  # noqa: E402

BASE = 'fixed_diagnosis'
OUT = os.path.join(BASE, 'compare')
PCT = 0.25

# Fallback only for running this module before compare_rankings.py has created
# its inputs. Normal runs derive this list from the current fixed-data ranks.
FALLBACK_PAIRS = [
    ('core-2m', 'cross_sector_slide1m_bd7', 'sp500-12m', 'cross_sector_slide1m_noscreen'),
    ('core-2m', 'cross_sector_slide3m_bd7', 'sp500-12m', 'cross_sector_slide1m_noscreen'),
    ('core-2m', 'cross_sector_slide3m_bd7', 'sp500-12m', 'cross_sector_slide3m_bd7'),
    ('core-2m', 'cross_sector_slide3m_bd7', 'sp500-12m', 'same_sector_slide3m_noscreen'),
    ('core-2m', 'cross_sector_slide3m_noscreen', 'sp500-12m', 'cross_sector_slide1m_noscreen'),
    ('sp500-12m', 'cross_sector_slide1m_noscreen', 'sp500-2m', 'cross_sector_slide3m_bd7'),
]


def _pair_key(a, b):
    return tuple(sorted([a, b]))


def consensus_pairs(top=20):
    """Return pairs in the top ``top`` of all three methods and both mechanisms."""
    paths = [os.path.join(OUT, 'rank_comparison_%s.csv' % mech) for mech in ['A', 'B']]
    if not all(os.path.exists(p) for p in paths):
        return FALLBACK_PAIRS

    method_sets = []
    for path in paths:
        df = pd.read_csv(path)
        per_method = []
        for column in ['score_rank', 'rank_avg_rank', 'joined_rank']:
            per_method.append({_pair_key(r['A'], r['B'])
                               for _, r in df.nsmallest(top, column).iterrows()})
        method_sets.append(set.intersection(*per_method))
    selected = set.intersection(*method_sets)

    def as_tuple(pair):
        a, b = pair
        return (*a.split('/', 1), *b.split('/', 1))

    return [as_tuple(pair) for pair in sorted(selected)]


PAIRS = consensus_pairs()

SCHEMES = [
    ('default', dict(step=0.10, wmin=0.25, wmax=0.75)),
    ('step5',   dict(step=0.05, wmin=0.25, wmax=0.75)),
    ('step15',  dict(step=0.15, wmin=0.25, wmax=0.75)),
    ('bd20_80', dict(step=0.10, wmin=0.20, wmax=0.80)),
    ('bd35_65', dict(step=0.10, wmin=0.35, wmax=0.65)),
]

STATIC = 'static'


def _combined_series(sa, ca, sb, cb, window, mech, scheme, start_idx=0):
    a = get_leg(sa, ca, window, start_idx)
    b = get_leg(sb, cb, window, start_idx)
    if scheme == STATIC:
        sa_ = _sharpe(a['ret'])
        sb_ = _sharpe(b['ret'])
        if not math.isnan(sa_) and not math.isnan(sb_) and (sa_ + sb_) != 0:
            wa = sa_ / (sa_ + sb_)
        else:
            wa = 0.5
        month_ix = a['ret'].index.union(b['ret'].index).to_period('M').unique()
        wp = pd.Series(dict((m.to_timestamp(), wa) for m in month_ix))
    else:
        params = dict(SCHEMES)[scheme]
        wp = weight_path_momentum_causal(a['ret'], b['ret'], **params)
    rows, _, _, _ = simulate({'A': a, 'B': b}, wp, mech, capital=1e6, pct=PCT)
    return pd.Series([r['daily_return'] for r in rows], index=[r['date'] for r in rows])


def scheme_sharpe(sa, ca, sb, cb, mech, scheme, window):
    if window == 'recent':
        shs = [metrics(_combined_series(sa, ca, sb, cb, 'recent', mech, scheme, i))['sharpe']
               for i in range(5)]
        return statistics.mean(shs)
    return metrics(_combined_series(sa, ca, sb, cb, 'historical', mech, scheme, 0))['sharpe']


def pair_label(sa, ca, sb, cb):
    return '%s/%s + %s/%s' % (sa, ca, sb, cb)


def build_sensitivity_csv(pairs=None):
    if pairs is None:
        pairs = consensus_pairs()
    rows = []
    for sa, ca, sb, cb in pairs:
        for mech in ['A', 'B']:
            rec = {s: scheme_sharpe(sa, ca, sb, cb, mech, s, 'recent') for s, _ in SCHEMES}
            hist = {s: scheme_sharpe(sa, ca, sb, cb, mech, s, 'historical') for s, _ in SCHEMES}
            rec[STATIC] = scheme_sharpe(sa, ca, sb, cb, mech, STATIC, 'recent')
            hist[STATIC] = scheme_sharpe(sa, ca, sb, cb, mech, STATIC, 'historical')
            row = {'pair': pair_label(sa, ca, sb, cb), 'mech': mech}
            for s in [n for n, _ in SCHEMES] + [STATIC]:
                row['recent_%s' % s] = rec[s]
                row['hist_%s' % s] = hist[s]
            rows.append(row)
    return pd.DataFrame(rows)


def build_ff_rows(pairs=None):
    if pairs is None:
        pairs = consensus_pairs()
    fetcher = FamaFrenchFetcher(frequency='daily')
    rows = []
    for sa, ca, sb, cb in pairs:
        for window in ['historical', 'recent']:
            for mech in ['A', 'B']:
                r = _combined_series(sa, ca, sb, cb, window, mech, 'default', 0)
                r.name = 'combined'
                res = fetcher.regress(r, include_momentum=True, include_st_rev=True)
                row = {'pair': pair_label(sa, ca, sb, cb), 'window': window, 'mech': mech,
                       'alpha_ann': res.alpha_ann, 'alpha_tstat': res.alpha_tstat,
                       'alpha_pval': res.alpha_pval,
                       'rsquared': res.rsquared, 'adj_rsquared': res.adj_rsquared,
                       'n_obs': res.n_obs}
                for _, l in res.loadings.iterrows():
                    row['%s_beta' % l['factor']] = l['beta']
                    row['%s_pval' % l['factor']] = l['pval']
                rows.append(row)
    return pd.DataFrame(rows)


def write_md(sens, ff, desc=None):
    lines = ['# Momentum-param sensitivity & Fama-French — %d survivor pairs\n'
             % len(ff['pair'].unique())]
    if desc is None:
        desc = ('Pairs are the top-20 in all three ranking methods (min/rank-avg/joined), both '
                'mechanisms. pct=0.25, capital $1M.')
    lines.append(desc + '\n')

    lines.append('## Task 1 — Momentum-param sensitivity (not re-optimization)\n')
    lines.append('Combined daily-return series via the trade-event replay. `recent` = mean Sharpe '
                 'over the 5 aligned start-pairs; `hist` = single aligned window. Schemes: '
                 'default (step 10%, bounds 25-75%), step5, step15, bd20_80 (bounds 20-80%), '
                 'bd35_65 (bounds 35-65%), static (no switching; w_A = Sh_A/(Sh_A+Sh_B)). '
                 'lookback fixed at 63d.\n')

    scheme_cols = [n for n, _ in SCHEMES] + [STATIC]
    for mech in ['A', 'B']:
        lines.append('### Mechanism %s\n' % mech)
        lines.append('| Pair | ' + ' | '.join('rec: %s' % s for s in scheme_cols) + ' | '
                     + ' | '.join('hist: %s' % s for s in scheme_cols) + ' |')
        lines.append('|' + '---|' * (1 + 2 * len(scheme_cols)))
        sub = sens[sens['mech'] == mech]
        for _, row in sub.iterrows():
            cells = ['`%s`' % row['pair']]
            for s in scheme_cols:
                cells.append('%.2f' % row['recent_%s' % s])
            for s in scheme_cols:
                cells.append('%.2f' % row['hist_%s' % s])
            lines.append('| ' + ' | '.join(cells) + ' |')
        lines.append('')

    lines.append('## Task 2 — Fama-French (FF3 + Mom + ST_Rev, daily, HAC)\n')
    lines.append('Combined daily-return series with the default momentum config (step 10%, bounds '
                 '25-75%), mechanisms A and B, start-pair 0. Alpha annualized x252; HAC standard '
                 'errors. **Values in brackets are p-values** (the probability the true loading is '
                 'zero; p < 0.05 conventionally indicates significance at the 5% level).\n')
    lines.append('| Pair | Window | Mech | Alpha% | Mkt-RF | SMB | HML | Mom | ST_Rev | R2 | N |')
    lines.append('|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|')
    for _, row in ff.iterrows():
        lines.append('| `%s` | %s | %s | %+.2f%% (%.3f) | %.2f (%.3f) | %.2f (%.3f) | '
                     '%.2f (%.3f) | %.2f (%.3f) | %.2f (%.3f) | %.3f | %d |'
                     % (row['pair'], row['window'], row['mech'],
                        row['alpha_ann'] * 100, row['alpha_pval'],
                        row['Mkt-RF_beta'], row['Mkt-RF_pval'],
                        row['SMB_beta'], row['SMB_pval'],
                        row['HML_beta'], row['HML_pval'],
                        row['Mom_beta'], row['Mom_pval'],
                        row['ST_Rev_beta'], row['ST_Rev_pval'],
                        row['rsquared'], row['n_obs']))
    lines.append('')
    lines.append('## Data-quality notes\n')
    lines.append('1. **Earnings-screen cache bug (found & fixed 2026-08).** Every sp500 section '
                 '(07/09a/09b/10b) was routed to `research/earnings_cache/earnings_dates_sp500.pkl`, '
                 'which held only 2023-01..2025-06 dates, while `research/earnings_cache/'
                 'earnings_dates.pkl` - same 503 tickers, full 2013-2026 coverage - sat alongside '
                 'unused. Consequences: historical sp500 bd7 configs screened **nothing** (09b '
                 'same3m: 560 bd7 trades == 560 noscreen), and recent sp500 sections went '
                 'unscreened after Jun-2025. Core sections used the complete cache and screened '
                 'correctly all along (08b: 176 -> 96 trades). Fix: truncated cache deleted, all '
                 'sp500 sections repointed to the complete cache, sections 07/09a/09b/10b re-run. '
                 'Post-fix 09b same3m screens ~46% of entries (bd7=311 vs noscreen=579). No '
                 'yfinance fetching occurs: every ticker is already cached.\n')
    lines.append('2. **Pairs 2 & 4 rendered identically pre-fix — explained by note 1.** Both pairs '
                 'share the sp500-2m leg and differ only in the sp500-12m leg screen (bd7 vs '
                 'noscreen); with the screen silent their historical legs had identical trade sets, '
                 'so the combined books were near-duplicates (FF stats agreed to the 12th decimal; '
                 'md rounding made rows byte-identical). Post-fix the two legs carry different '
                 'trade sets and the pairs are genuinely distinct.\n')
    lines.append('3. **Mechanism A and B are now exposure-comparable after the B sizing fix.** Both '
                 'mechanisms compute daily returns identically as (C - C_prev)/C_prev on total book '
                 'value. Mech A re-bases entry basis monthly to `w_L * C / n_active_L`; mech B '
                 'locks an unweighted basis at fold start using `C / n_active_L` and applies the '
                 'current weight only to new entry flow. The first-entry gross deployment therefore '
                 'matches at equal weights and active-fold counts; remaining differences reflect '
                 'monthly re-basing versus locked entry sizing. Compare alpha and risk with both '
                 'exposure and timing in mind.\n')
    lines.append('4. **Runtime return-divergence re-filter removed (2026-08).** The pool cache '
                 '(sp500_2m.pkl) is seeded with return-divergence already applied '
                 '(research/seed_2m3m.py, DIVERGENCE=0.10), but run_backtest_parallel.py ALSO '
                 're-applied the filter at runtime against freshly-fetched yfinance prices. On a '
                 'rate-limited/partial fetch (~80 tickers missing, e.g. 2026-08-24), that re-filter '
                 'silently dropped ~30% of already-valid pairs and reshuffled top-20 selection - '
                 'producing a spurious 1.20 historical Sharpe (09a cross3m noscreen) that is not '
                 'reproducible. Fix: pool-backed runs now skip the runtime re-filter (selection is '
                 'deterministic and cache-driven); DataLoader now retries rate-limited fetches and '
                 'aborts loudly if <95% of tickers return. After the fix that config re-runs to '
                 'Sharpe 0.57 / 529 trades (its true value), and all sp500 sections were rebuilt '
                 'on deterministic selection.\n')
    return lines


def main():
    os.makedirs(OUT, exist_ok=True)
    print('Task 1: momentum-param sensitivity sweep...')
    sens = build_sensitivity_csv()
    print('Task 2: Fama-French regressions...')
    ff = build_ff_rows()
    lines = write_md(sens, ff)
    out = os.path.join(OUT, '_MOMENTUM_FF_PAIRS.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    sens.to_csv(os.path.join(OUT, 'momentum_sensitivity.csv'), index=False)
    ff.to_csv(os.path.join(OUT, 'ff_regressions.csv'), index=False)
    print('wrote', out)
    print('wrote', os.path.join(OUT, 'momentum_sensitivity.csv'))
    print('wrote', os.path.join(OUT, 'ff_regressions.csv'))


if __name__ == '__main__':
    main()
