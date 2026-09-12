"""Audit fixed and hypothetical dynamic sizing on the limited V1/V2 runs.

The script consumes the ignored raw runs produced by
``run_sizing_v2_experiment.py``. It never changes order admission or sizing;
the current-equity and capacity calculations are diagnostic only.

Usage::

    python research/run_sizing_capital_audit.py
    python research/run_sizing_capital_audit.py --profile selected_leg_a_recent
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.run_sizing_v2_experiment import (
    OUTPUT_ROOT,
    PROFILES,
    _load_run,
)
from src.backtest import calculate_pair_sizes


SUMMARY_ROOT = ROOT / 'results' / 'sizing_v2_summary'
CAPACITY_TOLERANCE = 1e-9


def _distribution(values):
    values = pd.to_numeric(values, errors='coerce')
    values = values.replace([np.inf, -np.inf], np.nan).dropna()
    if values.empty:
        return {
            'median': 0.0,
            'mean': 0.0,
            'p5': 0.0,
            'p95': 0.0,
            'min': 0.0,
            'max': 0.0,
        }
    return {
        'median': float(values.median()),
        'mean': float(values.mean()),
        'p5': float(values.quantile(0.05)),
        'p95': float(values.quantile(0.95)),
        'min': float(values.min()),
        'max': float(values.max()),
    }


def margin_requirement(
    size1,
    size2,
    price1,
    price2,
    side1,
    side2,
    margin_long=0.50,
    margin_short=0.50,
):
    """Return initial margin for a two-leg position under simple rates."""
    rates = {'long': float(margin_long), 'short': float(margin_short)}
    if side1 not in rates or side2 not in rates:
        raise ValueError(f'unknown position side: {side1!r}, {side2!r}')
    return (
        rates[side1] * abs(float(size1) * float(price1))
        + rates[side2] * abs(float(size2) * float(price2))
    )


def assess_capacity(
    current_equity,
    current_gross_exposure,
    existing_initial_margin,
    desired_gross_exposure,
    desired_initial_margin,
):
    """Assess independent fully-funded and margin capacity constraints."""
    equity = float(current_equity)
    funded_free = equity - float(current_gross_exposure)
    margin_free = equity - float(existing_initial_margin)
    desired_gross = float(desired_gross_exposure)
    desired_margin = float(desired_initial_margin)
    return {
        'fully_funded_free_capacity': funded_free,
        'free_margin': margin_free,
        'fully_funded_excess': max(0.0, desired_gross - funded_free),
        'margin_excess': max(0.0, desired_margin - margin_free),
        'fully_funded_fits': desired_gross <= funded_free + CAPACITY_TOLERANCE,
        'margin_fits': desired_margin <= margin_free + CAPACITY_TOLERANCE,
    }


def sequential_capacity_ledger(frame, capacity_model):
    """Apply a hypothetical deterministic same-day reservation ledger.

    The first row for each fold/date supplies the observed pre-entry account
    state. Later rows reserve the requested dynamic position only when the
    earlier rows were admitted. This models future sequential admission; it
    does not alter the canonical run.
    """
    if frame.empty:
        return pd.DataFrame()
    if capacity_model == 'fully_funded':
        free_column = 'fully_funded_free_capacity'
        request_column = 'naive_dynamic_gross_exposure'
    elif capacity_model == 'margin':
        free_column = 'free_margin'
        request_column = 'naive_dynamic_initial_margin_required'
    else:
        raise ValueError(f'unknown capacity model: {capacity_model!r}')

    ordered = frame.copy()
    ordered['date'] = pd.to_datetime(ordered['date'])
    for column in ('fold_id', 'audit_sequence', 'pair_index'):
        if column not in ordered:
            ordered[column] = 0
    ordered = ordered.sort_values(
        ['fold_id', 'date', 'audit_sequence', 'pair_index', 'pair']
    )
    rows = []
    for (fold_id, date), group in ordered.groupby(
        ['fold_id', 'date'], sort=False, dropna=False
    ):
        base_free = float(group.iloc[0][free_column])
        reserved = 0.0
        for _, source in group.iterrows():
            requested = float(source[request_column])
            available = base_free - reserved
            fits = requested <= available + CAPACITY_TOLERANCE
            if fits:
                reserved += requested
            rows.append({
                'fold_id': fold_id,
                'date': date,
                'pair': source['pair'],
                'audit_sequence': source['audit_sequence'],
                'requested': requested,
                'available_before': available,
                'admitted': bool(fits),
                'conflict': bool(not fits),
                'reserved_after': reserved,
            })
    return pd.DataFrame(rows)


def _bool_value(value):
    return str(value).strip().lower() in {'1', 'true', 'yes'}


def _prepare_attempts(profile_name, mode, run):
    raw = run['sizing_audit'].copy()
    if raw.empty:
        raise RuntimeError(
            f'{profile_name} {mode} has no sizing_audit.csv; rerun the fixed experiment'
        )
    attempted = raw[raw['sizing_attempted'].map(_bool_value)].copy()
    if attempted.empty:
        raise RuntimeError(f'{profile_name} {mode} has no sizing attempts')

    metrics = run['metrics']
    log_space = bool(metrics.get('log_space', True))
    dollar_neutral = bool(metrics.get('dollar_neutral', False))
    margin_long = float(metrics.get('margin_long', 0.50))
    margin_short = float(metrics.get('margin_short', 0.50))
    prepared = []
    for _, source in attempted.iterrows():
        row = source.to_dict()
        initial_equity = float(source['initial_equity'])
        current_equity = float(source['current_equity'])
        equity_fraction = float(source['equity_fraction'])
        price1 = float(source['price1'])
        price2 = float(source['price2'])
        hr = float(source['hr_entry'])
        fixed = calculate_pair_sizes(
            initial_equity,
            equity_fraction,
            price1,
            price2,
            hr,
            log_space=log_space,
            dollar_neutral=dollar_neutral,
            pair_sizing_mode=mode,
        )
        dynamic_budget = current_equity * equity_fraction
        dynamic = calculate_pair_sizes(
            current_equity,
            equity_fraction,
            price1,
            price2,
            hr,
            log_space=log_space,
            dollar_neutral=dollar_neutral,
            pair_sizing_mode=mode,
        )
        if dynamic['valid']:
            dynamic_margin = margin_requirement(
                dynamic['size1'], dynamic['size2'], price1, price2,
                source['side1'], source['side2'], margin_long, margin_short,
            )
            capacity = assess_capacity(
                current_equity,
                source['current_gross_exposure'],
                source['current_initial_margin_required'],
                dynamic['actual_gross_exposure'],
                dynamic_margin,
            )
        else:
            dynamic_margin = float('nan')
            capacity = {
                'fully_funded_free_capacity': (
                    current_equity - float(source['current_gross_exposure'])
                ),
                'free_margin': (
                    current_equity - float(source['current_initial_margin_required'])
                ),
                'fully_funded_excess': float('nan'),
                'margin_excess': float('nan'),
                'fully_funded_fits': np.nan,
                'margin_fits': np.nan,
            }
        fixed_budget = float(fixed['sizing_budget'])
        row.update({
            'profile': profile_name,
            'mode': mode,
            'fixed_desired_budget': fixed_budget,
            'naive_dynamic_budget': dynamic_budget,
            'equity_ratio': (
                current_equity / initial_equity if initial_equity > 0 else np.nan
            ),
            'naive_dynamic_budget_ratio': (
                dynamic_budget / fixed_budget if fixed_budget > 0 else np.nan
            ),
            'budget_delta': dynamic_budget - fixed_budget,
            'fixed_desired_gross_exposure': fixed['actual_gross_exposure'],
            'naive_dynamic_valid': bool(dynamic['valid']),
            'naive_dynamic_size1': dynamic['size1'],
            'naive_dynamic_size2': dynamic['size2'],
            'naive_dynamic_reference_leg_notional': dynamic[
                'reference_leg_notional'
            ],
            'naive_dynamic_pair_gross_budget': dynamic['pair_gross_budget'],
            'naive_dynamic_gross_exposure': dynamic['actual_gross_exposure'],
            'naive_dynamic_initial_margin_required': dynamic_margin,
            'fully_funded_free_capacity': capacity[
                'fully_funded_free_capacity'
            ],
            'free_margin': capacity['free_margin'],
            'fully_funded_excess': capacity['fully_funded_excess'],
            'margin_excess': capacity['margin_excess'],
            'fully_funded_fits': capacity['fully_funded_fits'],
            'margin_fits': capacity['margin_fits'],
        })
        prepared.append(row)
    return pd.DataFrame(prepared), raw


def _same_day_summary(attempts):
    if attempts.empty:
        return {
            'same_day_multiple_group_count': 0,
            'same_day_multiple_opportunity_count': 0,
            'max_same_day_opportunities': 0,
            'same_day_preentry_state_consistent': True,
        }
    groups = attempts.groupby(['fold_id', 'date'], dropna=False)
    multi = [group for _, group in groups if len(group) > 1]
    state_columns = [
        'current_equity', 'current_cash', 'current_gross_exposure',
        'current_initial_margin_required',
    ]
    consistent = True
    for group in multi:
        for column in state_columns:
            values = pd.to_numeric(group[column], errors='coerce').dropna()
            if not values.empty and float(values.max() - values.min()) > 1e-7:
                consistent = False
    return {
        'same_day_multiple_group_count': len(multi),
        'same_day_multiple_opportunity_count': sum(len(group) for group in multi),
        'max_same_day_opportunities': max((len(group) for group in multi), default=0),
        'same_day_preentry_state_consistent': consistent,
    }


def _excess_distribution(attempts, column):
    values = pd.to_numeric(attempts[column], errors='coerce').dropna()
    values = values[values > CAPACITY_TOLERANCE]
    stats = _distribution(values)
    return {
        'p50': stats['median'],
        'p95': stats['p95'],
        'max': stats['max'],
    }


def _summary_row(profile_name, mode, run, attempts, raw):
    profile = PROFILES[profile_name]
    equity_stats = _distribution(attempts['equity_ratio'])
    budget_ratio_stats = _distribution(attempts['naive_dynamic_budget_ratio'])
    budget_delta_stats = _distribution(attempts['budget_delta'])
    current_equity_stats = _distribution(attempts['current_equity'])
    current_gross_stats = _distribution(attempts['current_gross_exposure'])
    current_margin_stats = _distribution(
        attempts['current_initial_margin_required']
    )
    funded_capacity_stats = _distribution(
        attempts['fully_funded_free_capacity']
    )
    free_margin_stats = _distribution(attempts['free_margin'])
    cash_stats = _distribution(attempts['current_cash'])
    cash_equity_delta_stats = _distribution(
        attempts['current_cash'] - attempts['current_equity']
    )
    same_day = _same_day_summary(attempts)
    valid_mask = attempts['naive_dynamic_valid'].astype(bool)
    valid_attempts = attempts[valid_mask]
    funded_ledger = sequential_capacity_ledger(valid_attempts, 'fully_funded')
    margin_ledger = sequential_capacity_ledger(valid_attempts, 'margin')
    funded_conflicts = valid_attempts[~valid_attempts['fully_funded_fits']]
    margin_conflicts = valid_attempts[~valid_attempts['margin_fits']]
    row = {
        'profile': profile_name,
        'profile_start': profile['start'],
        'profile_end': profile['end'],
        'mode': mode,
        'broker_leverage': float(run['metrics'].get('broker_leverage', 1.0)),
        'entry_opportunities_total': int(len(raw)),
        'sizing_attempts': int(len(attempts)),
        'orders_submitted': int((raw['status'] == 'orders_submitted').sum()),
        'dynamic_sizing_valid_count': int(len(valid_attempts)),
        'current_cash_negative_count': int(
            (pd.to_numeric(attempts['current_cash'], errors='coerce') < 0).sum()
        ),
        'current_cash_mean': cash_stats['mean'],
        'current_cash_min': cash_stats['min'],
        'current_cash_max': cash_stats['max'],
        'cash_minus_equity_mean': cash_equity_delta_stats['mean'],
        'cash_minus_equity_min': cash_equity_delta_stats['min'],
        'cash_minus_equity_max': cash_equity_delta_stats['max'],
        'current_equity_mean': current_equity_stats['mean'],
        'current_equity_min': current_equity_stats['min'],
        'current_equity_max': current_equity_stats['max'],
        'current_gross_exposure_mean': current_gross_stats['mean'],
        'current_gross_exposure_min': current_gross_stats['min'],
        'current_gross_exposure_max': current_gross_stats['max'],
        'current_initial_margin_mean': current_margin_stats['mean'],
        'current_initial_margin_min': current_margin_stats['min'],
        'current_initial_margin_max': current_margin_stats['max'],
        'fully_funded_free_capacity_min': funded_capacity_stats['min'],
        'fully_funded_free_capacity_max': funded_capacity_stats['max'],
        'free_margin_min': free_margin_stats['min'],
        'free_margin_max': free_margin_stats['max'],
        'fully_funded_fit_count': int(valid_attempts['fully_funded_fits'].sum()),
        'fully_funded_conflict_count': int(len(funded_conflicts)),
        'fully_funded_conflict_rate': (
            float(len(funded_conflicts) / len(attempts)) if len(attempts) else 0.0
        ),
        'margin_fit_count': int(valid_attempts['margin_fits'].sum()),
        'margin_conflict_count': int(len(margin_conflicts)),
        'margin_conflict_rate': (
            float(len(margin_conflicts) / len(attempts)) if len(attempts) else 0.0
        ),
        'sequential_funded_admitted_count': int(funded_ledger['admitted'].sum())
        if not funded_ledger.empty else 0,
        'sequential_funded_conflict_count': int(funded_ledger['conflict'].sum())
        if not funded_ledger.empty else 0,
        'sequential_margin_admitted_count': int(margin_ledger['admitted'].sum())
        if not margin_ledger.empty else 0,
        'sequential_margin_conflict_count': int(margin_ledger['conflict'].sum())
        if not margin_ledger.empty else 0,
        'conflict_first_date': (
            min(pd.to_datetime(funded_conflicts['date']).dt.date).isoformat()
            if not funded_conflicts.empty else ''
        ),
        'conflict_last_date': (
            max(pd.to_datetime(funded_conflicts['date']).dt.date).isoformat()
            if not funded_conflicts.empty else ''
        ),
    }
    for prefix, stats in (
        ('equity_ratio', equity_stats),
        ('naive_dynamic_budget_ratio', budget_ratio_stats),
        ('budget_delta', budget_delta_stats),
    ):
        for key, value in stats.items():
            row[f'{prefix}_{key}'] = value
    for prefix, column in (
        ('fully_funded_excess', 'fully_funded_excess'),
        ('margin_excess', 'margin_excess'),
    ):
        for key, value in _excess_distribution(attempts, column).items():
            row[f'{prefix}_{key}'] = value
    row.update(same_day)
    return row


def run_audit(selected_profiles):
    rows = []
    for profile_name in selected_profiles:
        for mode in ('reference_leg', 'gross_exposure'):
            run_path = OUTPUT_ROOT / 'runs' / profile_name / mode
            if not (run_path / 'run_status.json').is_file():
                raise FileNotFoundError(
                    f'missing fixed experiment output: {run_path / "run_status.json"}'
                )
            run = _load_run(run_path)
            attempts, raw = _prepare_attempts(profile_name, mode, run)
            rows.append(_summary_row(profile_name, mode, run, attempts, raw))

    SUMMARY_ROOT.mkdir(parents=True, exist_ok=True)
    output = SUMMARY_ROOT / 'sizing_capital_audit.csv'
    pd.DataFrame(rows).to_csv(output, index=False)
    return pd.DataFrame(rows), output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=sorted(PROFILES), action='append')
    args = parser.parse_args(argv)
    profiles = args.profile or list(PROFILES)
    summary, output = run_audit(profiles)
    display = [
        'profile', 'mode', 'sizing_attempts',
        'equity_ratio_median', 'equity_ratio_mean',
        'naive_dynamic_budget_ratio_median',
        'fully_funded_conflict_count', 'margin_conflict_count',
        'same_day_multiple_group_count',
        'sequential_funded_conflict_count',
        'sequential_margin_conflict_count',
    ]
    print(summary[display].to_string(index=False))
    print(f'Output written to {output}')


if __name__ == '__main__':
    main()
