"""Run Fama-French (FF3 + Mom + ST_Rev, HAC) on the combined pct0.25 book and its
legs, for both windows, and write fixed_diagnosis/_FF_COMBINED_PCT25.md.

Usage: python research/run_ff_combined.py
"""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fama_french import FamaFrenchFetcher  # noqa: E402

BASE = 'fixed_diagnosis'

# (window, label, daily_returns.csv path, name)
SERIES = {
    'recent': [
        ('combined momentum', '_combined/sweep_pct25/recent/daily_returns.csv', 'combined_pct25'),
        ('leg A core-2m cross3m bd7', '_pct25/2023-11-01_cross_sector_slide3m_bd7/daily_returns.csv',
         'legA_core2m_cross3m_bd7'),
        ('leg B sp500-12m cross1m noscreen', '_pct25/2023-01-01_cross_sector_slide1m_noscreen/daily_returns.csv',
         'legB_sp50012m_cross1m_noscreen'),
    ],
    'historical': [
        ('combined momentum', '_combined/sweep_pct25/historical/daily_returns.csv', 'combined_pct25'),
        ('leg A core-2m cross3m bd7', '_pct25/2014-11-01_cross_sector_slide3m_bd7/daily_returns.csv',
         'legA_core2m_cross3m_bd7'),
        ('leg B sp500-12m cross1m noscreen', '_pct25/2014-01-01_cross_sector_slide1m_noscreen/daily_returns.csv',
         'legB_sp50012m_cross1m_noscreen'),
    ],
}


def main():
    fetcher = FamaFrenchFetcher(frequency='daily')
    lines = []
    lines.append('# Fama-French on combined pct=0.25 book and legs\n')
    lines.append('Model: FF3 + Momentum + ST_Reversal, daily factors, HAC standard errors. '
                 'Alpha annualized x252. Both windows use the winning pair '
                 '(core-2m cross3m bd7 + sp500-12m cross1m noscreen).\n')

    for window in ['recent', 'historical']:
        lines.append('## %s window\n' % window.capitalize())
        for label, rel, name in SERIES[window]:
            p = os.path.join(BASE, rel)
            df = pd.read_csv(p, parse_dates=['date']).set_index('date')
            r = df['daily_return'].rename(name)
            res = fetcher.regress(r, include_momentum=True, include_st_rev=True)
            lines.append('### %s\n' % label)
            lines.append('```')
            lines.append(res.summary())
            lines.append('```\n')

    out = os.path.join(BASE, '_FF_COMBINED_PCT25.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', out)


if __name__ == '__main__':
    main()
