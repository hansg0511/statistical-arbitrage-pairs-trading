"""Regression check for shared-account mechanism-B fold sizing.

Run with::

    python research/combined_backtest_synthetic_test.py

With one active fold per leg and a 50/50 weight, mechanism B must deploy the
same amount as mechanism A on the first entry.  The old implementation divided
the locked basis by both legs' active-fold count and therefore deployed half as
much per leg.
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from research.run_combined_backtest import simulate


def _leg(name, entry, exit_date):
    return {
        'trades': [{
            'pair': name,
            'fold_id': 0,
            'entry': entry,
            'exit': exit_date,
            'reason': 'synthetic_exit',
            'ret': 0.01,
            'daily': {entry: 0.0, exit_date: 0.01},
            'fold_start': entry,
            'fold_end': exit_date,
        }],
        'folds': pd.DataFrame([{
            'fold': 0,
            'start': entry,
            'end': exit_date,
        }]),
        'ret': pd.Series([0.0, 0.01], index=[entry, exit_date]),
    }


def main():
    entry, exit_date = pd.bdate_range('2024-01-02', periods=2)
    legs = {'A': _leg('leg_a', entry, exit_date),
            'B': _leg('leg_b', entry, exit_date)}
    weights = pd.Series([0.5, 0.5], index=[entry, exit_date])

    results = {}
    for mech in ['A', 'B']:
        rows, ledger, rejected, _ = simulate(
            legs, weights, mech, capital=1_000_000.0, pct=0.25)
        results[mech] = (rows, ledger)
        assert not rejected, '%s unexpectedly rejected an entry: %s' % (mech, rejected)

    a_ledger = results['A'][1][0]
    b_ledger = results['B'][1][0]
    for leg in ['legA_deployed', 'legB_deployed', 'total_deployed']:
        assert abs(a_ledger[leg] - b_ledger[leg]) < 1e-9, (
            '%s sizing differs: A=%s B=%s' % (leg, a_ledger[leg], b_ledger[leg]))

    expected_leg = 125_000.0
    assert abs(b_ledger['legA_deployed'] - expected_leg) < 1e-9
    assert abs(b_ledger['legB_deployed'] - expected_leg) < 1e-9
    print('PASS: mechanism B uses the leg-specific active-fold denominator')


if __name__ == '__main__':
    main()
