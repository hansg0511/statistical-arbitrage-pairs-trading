"""Fama-French regression on a single leg's own daily returns.

Runs the same daily FF3 + Mom + ST_Rev (HAC) regression used for the combined
books, but on the standalone leg series, for the historical window and each of
the 5 recent start-pairs.

Usage: python research/run_ff_leg.py [strat] [cfg]
   e.g. python research/run_ff_leg.py sp500-12m cross_sector_slide1m_noscreen
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from research.pair_sweep_consolidated import (  # noqa: E402
    get_leg, STARTS_12M, STARTS_2M,
)
from src.fama_french import FamaFrenchFetcher  # noqa: E402

BASE = 'fixed_diagnosis'
OUT = os.path.join(BASE, 'compare')

DEFAULT_STRAT = 'sp500-12m'
DEFAULT_CFG = 'cross_sector_slide1m_noscreen'


def _ff_row(leg_label, window, start_label, ret):
    ret.name = 'combined'
    res = FamaFrenchFetcher(frequency='daily').regress(
        ret, include_momentum=True, include_st_rev=True)
    row = {'leg': leg_label, 'window': window, 'start': start_label,
           'alpha_ann': res.alpha_ann, 'alpha_tstat': res.alpha_tstat,
           'alpha_pval': res.alpha_pval,
           'rsquared': res.rsquared, 'adj_rsquared': res.adj_rsquared,
           'n_obs': res.n_obs}
    for _, l in res.loadings.iterrows():
        row['%s_beta' % l['factor']] = l['beta']
        row['%s_pval' % l['factor']] = l['pval']
    return row


def main():
    strat = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STRAT
    cfg = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_CFG
    label = '%s/%s' % (strat, cfg)
    starts = STARTS_12M if strat.endswith('12m') else STARTS_2M

    rows = []
    hist_ret = get_leg(strat, cfg, 'historical', 0)['ret']
    hist_start = '2014-01-01' if strat.endswith('12m') else '2014-11-01'
    rows.append(_ff_row(label, 'historical', hist_start, hist_ret))
    for i, s in enumerate(starts):
        rec_ret = get_leg(strat, cfg, 'recent', i)['ret']
        rows.append(_ff_row(label, 'recent', s, rec_ret))
    df = pd.DataFrame(rows)

    out_base = '_FF_LEG_%s_%s' % (strat, cfg)
    md_path = os.path.join(OUT, out_base + '.md')
    csv_path = os.path.join(OUT, out_base + '.csv')
    df.to_csv(csv_path, index=False)

    lines = ['# Fama-French (FF3 + Mom + ST_Rev, daily, HAC) — single leg `%s`\n' % label]
    lines.append('Standalone leg daily returns (pct=0.25 trade book). Historical = single '
                 'window; recent = each of the 5 start-pairs. Alpha annualized x252; HAC '
                 'standard errors. **Values in brackets are p-values**.\n')
    lines.append('| Leg | Window | Start | Alpha% | Mkt-RF | SMB | HML | Mom | ST_Rev | R2 | N |')
    lines.append('|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|')
    for _, row in df.iterrows():
        lines.append('| `%s` | %s | %s | %+.2f%% (%.3f) | %.2f (%.3f) | %.2f (%.3f) | '
                     '%.2f (%.3f) | %.2f (%.3f) | %.2f (%.3f) | %.3f | %d |'
                     % (row['leg'], row['window'], row['start'],
                        row['alpha_ann'] * 100, row['alpha_pval'],
                        row['Mkt-RF_beta'], row['Mkt-RF_pval'],
                        row['SMB_beta'], row['SMB_pval'],
                        row['HML_beta'], row['HML_pval'],
                        row['Mom_beta'], row['Mom_pval'],
                        row['ST_Rev_beta'], row['ST_Rev_pval'],
                        row['rsquared'], row['n_obs']))
    lines.append('')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', md_path)
    print('wrote', csv_path)


if __name__ == '__main__':
    main()
