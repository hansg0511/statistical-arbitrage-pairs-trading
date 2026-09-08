"""Run Fama-French (FF3 + Mom + ST_Rev, HAC) on the top survivor pair's combined
book and its two legs, both windows, and write fixed_diagnosis/_FF_COMBINED_PCT25.md.

Uses the current clean-data survivor pair (sp500-12m/cross_sector_slide1m_noscreen +
sp500-2m/cross_sector_slide3m_bd7), mechanism A, pct=0.25. The combined
series is built on the fly via research.momentum_ff_pairs._combined_series; the
two legs come from their _sweep_pct25 daily_returns.csv.

Usage: python research/run_ff_combined.py
"""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fama_french import FamaFrenchFetcher  # noqa: E402
from research.momentum_ff_pairs import _combined_series, pair_label  # noqa: E402

BASE = 'fixed_diagnosis'
SWEEP = os.path.join(BASE, '_sweep_pct25')

PAIR = ('sp500-12m', 'cross_sector_slide1m_noscreen', 'sp500-2m', 'cross_sector_slide3m_bd7')
# (window, section/start for each leg)
LEG_DIRS = {
    'recent': ('10b/2023-01-01_cross_sector_slide1m_noscreen',
               '07/2023-11-01_cross_sector_slide3m_bd7'),
    'historical': ('09b/2014-01-01_cross_sector_slide1m_noscreen',
                   '09a/2014-11-01_cross_sector_slide3m_bd7'),
}


def main():
    fetcher = FamaFrenchFetcher(frequency='daily')
    lines = []
    lines.append('# Fama-French on combined pct=0.25 book and legs\n')
    lines.append('Model: FF3 + Momentum + ST_Reversal, daily factors, HAC standard errors. '
                 'Alpha annualized x252. Pair = current #1 survivor (%s), mechanism A, pct=0.25.\n'
                 % pair_label(*PAIR))

    for window in ['recent', 'historical']:
        lines.append('## %s window\n' % window.capitalize())
        leg_a_rel, leg_b_rel = LEG_DIRS[window]
        series = [
            ('combined momentum', _combined_series(*PAIR, window, 'A', 'default', 0), 'combined_pct25'),
            ('leg A sp500-12m cross1m noscreen',
             pd.read_csv(os.path.join(SWEEP, leg_a_rel, 'daily_returns.csv'),
                         parse_dates=['date']).set_index('date')['daily_return'],
             'legA_sp50012m_cross1m_noscreen'),
            ('leg B sp500-2m cross3m bd7',
             pd.read_csv(os.path.join(SWEEP, leg_b_rel, 'daily_returns.csv'),
                         parse_dates=['date']).set_index('date')['daily_return'],
             'legB_sp5002m_cross3m_bd7'),
        ]
        for label, r, name in series:
            r = r.rename(name)
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
