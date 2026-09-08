"""Multi-start Fama-French on a two-leg combined pair.

Extends the single-start FF used by momentum_ff_pairs.py (which only uses
start_idx=0 for the recent window) to ALL 5 recent start-pairs, for both
mechanisms, so the recent alpha sign can be checked for start-to-start
stability. Historical window is single-start by construction (2015-2019).

Outputs (fixed_diagnosis/compare/):
  _FF_PAIR_MULTISTART_<sa>_<ca>_<sb>_<cb>.md / .csv

Usage: python research/run_ff_pair_multistart.py
"""
import os
import sys
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from research.momentum_ff_pairs import _combined_series  # noqa: E402
from research.run_combined_backtest import metrics  # noqa: E402
from src.fama_french import FamaFrenchFetcher  # noqa: E402

BASE = 'fixed_diagnosis'
OUT = os.path.join(BASE, 'compare')
N_STARTS = 5

PAIR = ('sp500-12m', 'cross_sector_slide1m_noscreen',
        'sp500-2m', 'cross_sector_slide3m_bd7')


def _run_ff(pair, window, mech, start_idx):
    sa, ca, sb, cb = pair
    r = _combined_series(sa, ca, sb, cb, window, mech, 'default', start_idx)
    sharpe = metrics(r)['sharpe']
    r.name = 'combined'
    res = FamaFrenchFetcher(frequency='daily').regress(
        r, include_momentum=True, include_st_rev=True)
    row = {'window': window, 'mech': mech, 'start': start_idx,
           'sharpe': sharpe,
           'alpha_ann': res.alpha_ann, 'alpha_tstat': res.alpha_tstat,
           'alpha_pval': res.alpha_pval,
           'rsquared': res.rsquared, 'n_obs': res.n_obs}
    for _, l in res.loadings.iterrows():
        row['%s_beta' % l['factor']] = l['beta']
        row['%s_pval' % l['factor']] = l['pval']
    return row


def main():
    sa, ca, sb, cb = PAIR
    label = '%s/%s + %s/%s' % (sa, ca, sb, cb)

    rows = []
    for mech in ['A', 'B']:
        rows.append(_run_ff(PAIR, 'historical', mech, 0))
        for i in range(N_STARTS):
            rows.append(_run_ff(PAIR, 'recent', mech, i))
    df = pd.DataFrame(rows)

    tag = '%s_%s_%s_%s' % (sa, ca, sb, cb)
    csv_path = os.path.join(OUT, '_FF_PAIR_MULTISTART_%s.csv' % tag)
    md_path = os.path.join(OUT, '_FF_PAIR_MULTISTART_%s.md' % tag)
    df.to_csv(csv_path, index=False)

    lines = ['# Multi-start Fama-French (FF3 + Mom + ST_Rev, daily, HAC) — pair `%s`\n' % label]
    lines.append('Combined daily-return series via the trade-event replay, default momentum config '
                 '(step 10%%, bounds 25-75%%). Historical = single window (2015-2019). Recent = each '
                 'of the %d aligned start-pairs (all trading strictly 2024-2025). Alpha annualized '
                 'x252; HAC standard errors. **Values in brackets are p-values**.\n' % N_STARTS)
    lines.append('| Window | Start | Mech | Alpha% | Mkt-RF | SMB | HML | Mom | ST_Rev | Sharpe | R2 | N |')
    lines.append('|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    for _, r in df.iterrows():
        lines.append('| %s | %s | %s | %+.2f%% (%.3f) | %.2f (%.3f) | %.2f (%.3f) | '
                     '%.2f (%.3f) | %.2f (%.3f) | %.2f (%.3f) | %.2f | %.3f | %d |'
                     % (r['window'], r['start'], r['mech'],
                        r['alpha_ann'] * 100, r['alpha_pval'],
                        r['Mkt-RF_beta'], r['Mkt-RF_pval'],
                        r['SMB_beta'], r['SMB_pval'],
                        r['HML_beta'], r['HML_pval'],
                        r['Mom_beta'], r['Mom_pval'],
                        r['ST_Rev_beta'], r['ST_Rev_pval'],
                        r['sharpe'], r['rsquared'], r['n_obs']))
    lines.append('')

    lines.append('## Recent alpha across the %d starts (per mechanism)\n' % N_STARTS)
    lines.append('| Mech | hist alpha | recent mean | recent min | recent max | # positive | # p<0.05 |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|')
    for mech in ['A', 'B']:
        rec = df[(df['mech'] == mech) & (df['window'] == 'recent')]
        hist = df[(df['mech'] == mech) & (df['window'] == 'historical')]
        alphas = rec['alpha_ann'].tolist()
        n_pos = sum(1 for a in alphas if a > 0)
        n_sig = sum(1 for a, p in zip(alphas, rec['alpha_pval']) if p < 0.05)
        lines.append('| %s | %+.2f%% | %+.2f%% | %+.2f%% | %+.2f%% | %d | %d |'
                     % (mech, hist['alpha_ann'].iloc[0] * 100,
                        statistics.mean(alphas) * 100, min(alphas) * 100,
                        max(alphas) * 100, n_pos, n_sig))
    lines.append('')
    lines.append('Caveat: alphas are annualized point estimates; with ~400-500 recent obs and HAC '
                 'errors, p<0.05 is a high bar. The recent sign is informative only if it is '
                 'consistent across starts.\n')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', md_path)
    print('wrote', csv_path)


if __name__ == '__main__':
    main()
