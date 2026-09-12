"""Run the limited V1/V2 sizing comparison on preserved deterministic inputs.

This intentionally does not touch ``results/final``. The archived price
snapshots and local pair pools are required; missing inputs are an error rather
than a reason to fall back to live downloads or live pair selection.

Usage::

    python research/run_sizing_v2_experiment.py
    python research/run_sizing_v2_experiment.py --profile selected_leg_a_recent
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.run_experiment import run_experiment


ARCHIVE = ROOT / 'research' / 'archive'
SNAPSHOTS = ARCHIVE / 'pct25_comparison_audit' / 'snapshots'
POOLS = ROOT / 'research' / 'cache'
EARNINGS_CACHE = ARCHIVE / 'earnings_cache' / 'earnings_dates.pkl'
OUTPUT_ROOT = ROOT / 'results' / 'sizing_v2'


PROFILES = {
    'selected_leg_a_recent': {
        'start': '2023-01-01',
        'end': '2026-01-01',
        'sel_months': 12,
        'test_months': 3,
        'slide_months': 1,
        'pool': 'sp500_12m.pkl',
        'snapshot': 'sp500_recent_12m.pkl',
        'earnings_screen': False,
        'earnings_block_days': 0,
        'source_label': 'selected Leg A: sp500-12m/cross_sector_slide1m_noscreen',
    },
    'selected_leg_b_recent': {
        'start': '2023-11-01',
        'end': '2026-01-01',
        'sel_months': 2,
        'test_months': 3,
        'slide_months': 3,
        'pool': 'sp500_2m.pkl',
        'snapshot': 'sp500_recent.pkl',
        'earnings_screen': True,
        'earnings_block_days': 7,
        'source_label': 'selected Leg B: sp500-2m/cross_sector_slide3m_bd7',
    },
    'contrast_12m_slide3_recent': {
        'start': '2023-01-01',
        'end': '2026-01-01',
        'sel_months': 12,
        'test_months': 3,
        'slide_months': 3,
        'pool': 'sp500_12m.pkl',
        'snapshot': 'sp500_recent_12m.pkl',
        'earnings_screen': False,
        'earnings_block_days': 0,
        'source_label': 'contrast: sp500-12m/cross_sector_slide3m_noscreen',
    },
    'contrast_2m_slide1_recent': {
        'start': '2023-01-01',
        'end': '2026-01-01',
        'sel_months': 2,
        'test_months': 3,
        'slide_months': 1,
        'pool': 'sp500_2m.pkl',
        'snapshot': 'sp500_recent.pkl',
        'earnings_screen': False,
        'earnings_block_days': 0,
        'source_label': 'contrast: sp500-2m/cross_sector_slide1m_noscreen',
    },
}


PUBLIC_REFERENCE_RUNS = {
    'selected_leg_a_recent': ROOT / 'results' / 'final' / 'event_replay_inputs'
    / 'recent' / 'start_01' / 'A',
    'selected_leg_b_recent': ROOT / 'results' / 'final' / 'event_replay_inputs'
    / 'recent' / 'start_01' / 'B',
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _require_inputs(profile):
    snapshot = SNAPSHOTS / profile['snapshot']
    pool = POOLS / profile['pool']
    for path in (snapshot, pool):
        if not path.is_file():
            raise FileNotFoundError(
                f'required deterministic input is missing: {path}'
            )
    if profile['earnings_screen'] and not EARNINGS_CACHE.is_file():
        raise FileNotFoundError(
            f'required earnings cache is missing: {EARNINGS_CACHE}'
        )
    return snapshot, pool


def _argv(profile_name, profile, mode, output):
    snapshot, pool = _require_inputs(profile)
    argv = [
        '--name', f'sizing_v2_{profile_name}_{mode}',
        '--start', profile['start'],
        '--end', profile['end'],
        '--universe', 'sp500',
        '--cross-sector',
        '--log-space',
        '--initial-cash', '1000000.0',
        '--pct-per-pair', '0.25',
        '--max-pairs', '20',
        '--pair-sizing-mode', mode,
        '--broker-leverage', '100.0',
        '--return-divergence', '0.10',
        '--sel-months', str(profile['sel_months']),
        '--test-months', str(profile['test_months']),
        '--slide-months', str(profile['slide_months']),
        '--earnings-block-days', str(profile['earnings_block_days']),
        '--pool-path', str(pool),
        '--price-snapshot', str(snapshot),
        '--margin-behavior', 'off',
        '--workers', '1',
        '--output', str(output),
    ]
    if profile['earnings_screen']:
        argv.extend(['--earnings-screen', '--earnings-cache', str(EARNINGS_CACHE)])
    else:
        argv.append('--no-earnings-screen')
    return argv


def _read_csv(path, parse_dates=()):
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=list(parse_dates))


def _load_run(path: Path):
    with (path / 'metrics.json').open(encoding='utf-8') as handle:
        metrics = json.load(handle)
    trades = _read_csv(
        path / 'trade_logs' / 'test_trade_log.csv',
        ('entry_date', 'exit_date'),
    )
    daily = _read_csv(path / 'daily_returns.csv', ('date',))
    marks = _read_csv(path / 'trade_marks.csv', ('date',))
    exposure = _read_csv(path / 'daily_exposure.csv', ('date',))
    selected = _read_csv(path / 'selected_pairs.csv')
    signal = _read_csv(path / 'signal_log.csv', ('date',))
    rejected = _read_csv(path / 'rejected_orders.csv', ('date',))
    return {
        'metrics': metrics,
        'trades': trades,
        'daily': daily,
        'marks': marks,
        'exposure': exposure,
        'selected': selected,
        'signal': signal,
        'rejected': rejected,
    }


def _compare_frames(left, right, columns):
    if len(left) != len(right):
        return {
            'rows_left': len(left),
            'rows_right': len(right),
            'differences': abs(len(left) - len(right)),
        }
    if left.empty and right.empty:
        return {'rows_left': 0, 'rows_right': 0, 'differences': 0}
    differences = 0
    for column in columns:
        if column not in left.columns or column not in right.columns:
            differences += 1
            continue
        if column in {'date', 'pair'}:
            differences += int(
                (left[column].fillna('<NA>').astype(str).to_numpy()
                 != right[column].fillna('<NA>').astype(str).to_numpy()).sum()
            )
        else:
            differences += int(
                (~np.isclose(
                    pd.to_numeric(left[column], errors='coerce'),
                    pd.to_numeric(right[column], errors='coerce'),
                    equal_nan=True,
                )).sum()
            )
    return {
        'rows_left': len(left),
        'rows_right': len(right),
        'differences': differences,
    }


def _compare_public_reference(profile_name, run):
    baseline = PUBLIC_REFERENCE_RUNS.get(profile_name)
    if baseline is None:
        return {'status': 'not_applicable'}
    metrics_path = baseline / 'metrics.json'
    if not metrics_path.is_file():
        return {
            'status': 'unavailable',
            'path': str(metrics_path.relative_to(ROOT)).replace('\\', '/'),
        }

    with metrics_path.open(encoding='utf-8') as handle:
        expected = json.load(handle)
    actual = run['metrics']
    metric_fields = [
        'total_trades', 'annualized_return', 'annualized_sharpe',
        'mean_active_trades', 'total_days', 'days_active_lt10',
        'broker_leverage', 'log_space', 'dollar_neutral', 'margin_rejections',
    ]
    mismatches = {}
    for field in metric_fields:
        if field not in expected or field not in actual:
            mismatches[field] = {
                'actual': actual.get(field),
                'expected': expected.get(field),
            }
            continue
        actual_value = actual[field]
        expected_value = expected[field]
        if isinstance(expected_value, (int, str, bool)):
            matches = actual_value == expected_value
        else:
            matches = math.isclose(
                float(actual_value), float(expected_value), abs_tol=1e-9
            )
        if not matches:
            mismatches[field] = {
                'actual': actual_value,
                'expected': expected_value,
            }

    expected_daily = _read_csv(baseline / 'daily_returns.csv', ('date',))
    daily_comparison = _compare_frames(
        run['daily'], expected_daily, ['date', 'daily_return']
    )
    expected_marks = _read_csv(
        baseline / 'trade_marks.csv', ('date',)
    )
    marks_comparison = _compare_frames(
        run['marks'], expected_marks,
        ['date', 'pair', 'mark_pnl', 'target_notional'],
    )
    expected_trade_path = baseline / 'trade_logs' / 'test_trade_log.csv'
    if expected_trade_path.is_file():
        expected_trades = _read_csv(
            expected_trade_path, ('entry_date', 'exit_date')
        )
        trade_comparison = _compare_key_multisets(
            run['trades'], expected_trades, _trade_key
        )
    else:
        trade_comparison = {
            'status': 'unavailable',
            'path': str(expected_trade_path.relative_to(ROOT)).replace('\\', '/'),
        }

    expected_selected_path = baseline / 'selected_pairs.csv'
    if expected_selected_path.is_file():
        expected_selected = _read_csv(expected_selected_path)
        selected_comparison = {
            'status': (
                'match'
                if _selection_keys(run['selected']) == _selection_keys(expected_selected)
                else 'mismatch'
            ),
            'rows_actual': len(run['selected']),
            'rows_expected': len(expected_selected),
        }
    else:
        selected_comparison = {
            'status': 'not_published',
            'path': str(expected_selected_path.relative_to(ROOT)).replace('\\', '/'),
        }
    return {
        'status': (
            'match'
            if not mismatches
            and daily_comparison['differences'] == 0
            and marks_comparison['differences'] == 0
            and trade_comparison.get('differences', 1) == 0
            and trade_comparison.get('status', 'match') == 'match'
            and selected_comparison['status'] in {'match', 'not_published'}
            else 'mismatch'
        ),
        'path': str(baseline.relative_to(ROOT)).replace('\\', '/'),
        'metric_mismatches': mismatches,
        'daily_return_comparison': daily_comparison,
        'trade_mark_comparison': marks_comparison,
        'trade_log_comparison': trade_comparison,
        'selected_pair_comparison': selected_comparison,
    }


def _daily_metrics(run):
    daily = run['daily']
    if daily.empty:
        return {'volatility': 0.0, 'max_drawdown': 0.0}
    returns = pd.to_numeric(daily['daily_return'], errors='coerce').dropna()
    if returns.empty:
        return {'volatility': 0.0, 'max_drawdown': 0.0}
    volatility = float(returns.std() * math.sqrt(252))
    curve = (1.0 + returns).cumprod()
    max_drawdown = float((curve / curve.cummax() - 1.0).min())
    return {'volatility': volatility, 'max_drawdown': max_drawdown}


def _metric_row(profile_name, mode, run):
    metrics = run['metrics']
    daily_metrics = _daily_metrics(run)
    trades = run['trades']
    win_rate = (
        float((pd.to_numeric(trades['pnl'], errors='coerce') > 0).mean())
        if not trades.empty else 0.0
    )
    return {
        'profile': profile_name,
        'mode': mode,
        'annualized_return': float(metrics.get('annualized_return', 0.0)),
        'sharpe': float(metrics.get('annualized_sharpe', 0.0)),
        'volatility': daily_metrics['volatility'],
        'max_drawdown': daily_metrics['max_drawdown'],
        'trade_count': int(len(trades)),
        'win_rate': win_rate,
        'average_gross_utilization': float(
            metrics.get('average_gross_utilization', 0.0)
        ),
        'gross_utilization_p95': float(
            metrics.get('gross_utilization_p95', 0.0)
        ),
        'gross_utilization_p99': float(
            metrics.get('gross_utilization_p99', 0.0)
        ),
        'peak_gross_utilization': float(
            metrics.get('peak_gross_utilization', 0.0)
        ),
        'average_margin_utilization': float(
            metrics.get('average_margin_utilization', 0.0)
        ),
        'margin_utilization_p95': float(
            metrics.get('margin_utilization_p95', 0.0)
        ),
        'margin_utilization_p99': float(
            metrics.get('margin_utilization_p99', 0.0)
        ),
        'peak_margin_utilization': float(
            metrics.get('peak_margin_utilization', 0.0)
        ),
        'average_maintenance_margin_utilization': float(
            metrics.get('average_maintenance_margin_utilization', 0.0)
        ),
        'maintenance_margin_utilization_p95': float(
            metrics.get('maintenance_margin_utilization_p95', 0.0)
        ),
        'maintenance_margin_utilization_p99': float(
            metrics.get('maintenance_margin_utilization_p99', 0.0)
        ),
        'peak_maintenance_margin_utilization': float(
            metrics.get('peak_maintenance_margin_utilization', 0.0)
        ),
        'average_open_pairs': float(metrics.get('average_open_pairs', 0.0)),
        'peak_open_pairs': int(metrics.get('peak_open_pairs', 0)),
        'rejected_entries': int(len(run['rejected'])),
    }


def _date_text(value):
    if pd.isna(value):
        return '<NA>'
    return pd.Timestamp(value).date().isoformat()


def _trade_key(row):
    return (
        int(row.get('fold_id', 0)),
        str(row['pair']),
        _date_text(row['entry_date']),
        _date_text(row['exit_date']),
        str(row['exit_reason']),
    )


def _entry_key(row):
    return (
        int(row.get('fold_id', 0)),
        str(row['pair']),
        _date_text(row['entry_date']),
    )


def _compare_key_multisets(left, right, key_fn):
    left_counts = Counter(key_fn(row) for _, row in left.iterrows())
    right_counts = Counter(key_fn(row) for _, row in right.iterrows())
    left_only = list((left_counts - right_counts).elements())
    right_only = list((right_counts - left_counts).elements())
    return {
        'rows_left': len(left),
        'rows_right': len(right),
        'common_keys': sum((left_counts & right_counts).values()),
        'left_only': [list(key) for key in sorted(left_only, key=repr)],
        'right_only': [list(key) for key in sorted(right_only, key=repr)],
        'differences': len(left_only) + len(right_only),
    }


def _rejection_key(row):
    return (
        int(row.get('fold_id', 0)),
        str(row.get('pair', '')),
        _date_text(row.get('date')),
        str(row.get('reason', '')),
        str(row.get('leg', '')),
        str(row.get('ticker', '')),
    )


def _selection_keys(frame):
    if frame.empty:
        return []
    return sorted(
        (
            int(row.get('fold_id', 0)),
            str(row['pair']),
            int(row.get('rank', 0)),
        )
        for _, row in frame.iterrows()
    )


def _signal_differences(left, right):
    numeric_columns = ['z', 'entry_z', 'exit_z', 'stop_z', 'hr', 'anchor_hr']
    state_columns = ['pos2', 'order_state', 'in_active', 'in_pending']
    columns = ['date', 'pair'] + numeric_columns + state_columns
    if left.empty or right.empty:
        return {
            'rows_left': len(left),
            'rows_right': len(right),
            'differences': int(len(left) != len(right)),
        }

    l = left.copy()
    r = right.copy()
    for frame in (l, r):
        if 'fold_id' not in frame:
            frame['fold_id'] = 0
        if 'pos2' in frame:
            frame['pos2'] = np.sign(
                pd.to_numeric(frame['pos2'], errors='coerce').fillna(0.0)
            )

    keys = ['date', 'pair', 'fold_id']
    available = [column for column in keys if column in l.columns and column in r.columns]
    if not available:
        return {'rows_left': len(left), 'rows_right': len(right), 'differences': -1}
    compare_columns = [
        column for column in columns
        if column in l.columns and column in r.columns and column not in available
    ]
    merged = l[available + compare_columns].merge(
        r[available + compare_columns],
        on=available,
        how='outer',
        suffixes=('_v1', '_v2'),
        indicator=True,
    )
    differences = int((merged['_merge'] != 'both').sum())
    both = merged[merged['_merge'] == 'both']
    for column in compare_columns:
        left_column = f'{column}_v1'
        right_column = f'{column}_v2'
        if left_column not in both or right_column not in both:
            continue
        if column in numeric_columns or column == 'pos2':
            differences += int(
                (~np.isclose(
                    pd.to_numeric(both[left_column], errors='coerce'),
                    pd.to_numeric(both[right_column], errors='coerce'),
                    equal_nan=True,
                )).sum()
            )
        else:
            left_values = both[left_column].fillna('<NA>').astype(str)
            right_values = both[right_column].fillna('<NA>').astype(str)
            differences += int((left_values != right_values).sum())
    return {'rows_left': len(left), 'rows_right': len(right), 'differences': differences}


def _compare_trades(v1, v2):
    v1_keys = [_trade_key(row) for _, row in v1['trades'].iterrows()]
    v2_keys = [_trade_key(row) for _, row in v2['trades'].iterrows()]
    c1 = Counter(v1_keys)
    c2 = Counter(v2_keys)
    v1_only = list((c1 - c2).elements())
    v2_only = list((c2 - c1).elements())
    entry_v1 = [_entry_key(row) for _, row in v1['trades'].iterrows()]
    entry_v2 = [_entry_key(row) for _, row in v2['trades'].iterrows()]
    selected_same = _selection_keys(v1['selected']) == _selection_keys(v2['selected'])
    signal = _signal_differences(v1['signal'], v2['signal'])
    v1_rejection_reasons = (
        v1['rejected']['reason'].value_counts().to_dict()
        if not v1['rejected'].empty else {}
    )
    v2_rejection_reasons = (
        v2['rejected']['reason'].value_counts().to_dict()
        if not v2['rejected'].empty else {}
    )
    rejection_comparison = _compare_key_multisets(
        v1['rejected'], v2['rejected'], _rejection_key
    )
    rejections_match = rejection_comparison['differences'] == 0
    return {
        'v1_trade_count': len(v1_keys),
        'v2_trade_count': len(v2_keys),
        'common_trade_count': sum((c1 & c2).values()),
        'v1_only_trades': v1_only,
        'v2_only_trades': v2_only,
        'entry_keys_match': Counter(entry_v1) == Counter(entry_v2),
        'selected_pair_keys_match': selected_same,
        'signal_input_comparison': signal,
        'v1_rejection_count': len(v1['rejected']),
        'v2_rejection_count': len(v2['rejected']),
        'v1_rejection_reasons': v1_rejection_reasons,
        'v2_rejection_reasons': v2_rejection_reasons,
        'rejections_match': rejections_match,
        'rejection_key_comparison': rejection_comparison,
        'decision_status': (
            'unchanged'
            if not v1_only and not v2_only and selected_same
            and signal['differences'] == 0 and rejections_match
            else 'changed_or_execution_feasibility'
        ),
    }


def _sizing_row(profile_name, mode, run):
    trades = run['trades']
    if trades.empty:
        return {
            'profile': profile_name,
            'mode': mode,
            'budget_basis': (
                'pair_gross_budget'
                if mode == 'gross_exposure'
                else 'reference_notional_baseline'
            ),
            'trades': 0,
            'mean_hr_abs': 0.0,
            'median_hr_abs': 0.0,
            'mean_budget_ratio': 0.0,
            'median_budget_ratio': 0.0,
            'gross_entry_p95_ratio': 0.0,
            'gross_entry_peak_ratio': 0.0,
            'mean_gross_entry_exposure': 0.0,
            'mean_pair_gross_budget': 0.0,
        }
    hr = pd.to_numeric(trades['hr_entry'], errors='coerce').abs()
    gross = pd.to_numeric(trades['gross_entry_exposure'], errors='coerce')
    budget = pd.to_numeric(trades['pair_gross_budget'], errors='coerce')
    ratio = gross / budget.replace(0, np.nan)
    return {
        'profile': profile_name,
        'mode': mode,
        'budget_basis': (
            'pair_gross_budget'
            if mode == 'gross_exposure'
            else 'reference_notional_baseline'
        ),
        'trades': int(len(trades)),
        'mean_hr_abs': float(hr.mean()),
        'median_hr_abs': float(hr.median()),
        'mean_budget_ratio': float(ratio.mean()),
        'median_budget_ratio': float(ratio.median()),
        'gross_entry_p95_ratio': float(ratio.quantile(0.95)),
        'gross_entry_peak_ratio': float(ratio.max()),
        'mean_gross_entry_exposure': float(gross.mean()),
        'mean_pair_gross_budget': float(budget.mean()),
    }


def _write_manifest(selected_profiles):
    inputs = {}
    for profile_name in selected_profiles:
        profile = PROFILES[profile_name]
        snapshot, pool = _require_inputs(profile)
        inputs[profile_name] = {
            'snapshot': str(snapshot.relative_to(ROOT)).replace('\\', '/'),
            'snapshot_sha256': _sha256(snapshot),
            'pool': str(pool.relative_to(ROOT)).replace('\\', '/'),
            'pool_sha256': _sha256(pool),
        }
        if profile['earnings_screen']:
            inputs[profile_name]['earnings_cache'] = str(
                EARNINGS_CACHE.relative_to(ROOT)
            ).replace('\\', '/')
            inputs[profile_name]['earnings_cache_sha256'] = _sha256(EARNINGS_CACHE)
    try:
        revision = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True
        ).strip()
        branch = subprocess.check_output(
            ['git', 'branch', '--show-current'], cwd=ROOT, text=True
        ).strip()
        working_tree_dirty = bool(
            subprocess.check_output(
                ['git', 'status', '--porcelain'], cwd=ROOT, text=True
            ).strip()
        )
    except (OSError, subprocess.CalledProcessError):
        revision = None
        branch = None
        working_tree_dirty = None
    payload = {
        'experiment': 'limited_v1_vs_v2_pair_sizing',
        'branch': branch,
        'source_revision': revision,
        'working_tree_dirty': working_tree_dirty,
        'pct_per_pair': 0.25,
        'modes': ['reference_leg', 'gross_exposure'],
        'profiles': selected_profiles,
        'inputs': inputs,
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_ROOT / 'experiment_manifest.json').open('w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=sorted(PROFILES), action='append')
    args = parser.parse_args(argv)
    profiles = args.profile or list(PROFILES)

    _write_manifest(profiles)
    comparison_rows = []
    sizing_rows = []
    trade_comparisons = {}
    loaded = {}

    for profile_name in profiles:
        profile = PROFILES[profile_name]
        loaded[profile_name] = {}
        for mode in ('reference_leg', 'gross_exposure'):
            output = OUTPUT_ROOT / 'runs' / profile_name / mode
            status = run_experiment(_argv(profile_name, profile, mode, output))
            if status != 0:
                raise RuntimeError(
                    f'{profile_name} {mode} run failed with status {status}'
                )
            run = _load_run(output)
            loaded[profile_name][mode] = run
            comparison_rows.append(_metric_row(profile_name, mode, run))
            sizing_rows.append(_sizing_row(profile_name, mode, run))
        trade_comparisons[profile_name] = _compare_trades(
            loaded[profile_name]['reference_leg'],
            loaded[profile_name]['gross_exposure'],
        )
        trade_comparisons[profile_name]['public_reference_comparison'] = (
            _compare_public_reference(
                profile_name, loaded[profile_name]['reference_leg']
            )
        )

    public_reference_failures = [
        profile_name for profile_name, result in trade_comparisons.items()
        if result['public_reference_comparison']['status']
        in {'mismatch', 'unavailable'}
    ]
    if public_reference_failures:
        raise RuntimeError(
            'public reference comparison failed for: '
            + ', '.join(public_reference_failures)
        )

    comparison = pd.DataFrame(comparison_rows)
    sizing = pd.DataFrame(sizing_rows)
    comparison.to_csv(OUTPUT_ROOT / 'comparison.csv', index=False)
    sizing.to_csv(OUTPUT_ROOT / 'sizing_diagnostics.csv', index=False)
    comparison[
        [
            'profile', 'mode', 'average_gross_utilization',
            'gross_utilization_p95', 'gross_utilization_p99',
            'peak_gross_utilization', 'average_margin_utilization',
            'margin_utilization_p95', 'margin_utilization_p99',
            'peak_margin_utilization',
            'average_maintenance_margin_utilization',
            'maintenance_margin_utilization_p95',
            'maintenance_margin_utilization_p99',
            'peak_maintenance_margin_utilization',
            'average_open_pairs', 'peak_open_pairs',
        ]
    ].to_csv(OUTPUT_ROOT / 'exposure_utilization.csv', index=False)
    with (OUTPUT_ROOT / 'trade_comparison.json').open('w', encoding='utf-8') as handle:
        json.dump(trade_comparisons, handle, indent=2, default=str)

    delta_rows = []
    metric_columns = [
        'annualized_return', 'sharpe', 'volatility', 'max_drawdown',
        'trade_count', 'win_rate', 'average_gross_utilization',
        'gross_utilization_p95', 'gross_utilization_p99',
        'peak_gross_utilization', 'average_margin_utilization',
        'margin_utilization_p95', 'margin_utilization_p99',
        'peak_margin_utilization',
        'average_maintenance_margin_utilization',
        'maintenance_margin_utilization_p95',
        'maintenance_margin_utilization_p99',
        'peak_maintenance_margin_utilization',
        'average_open_pairs', 'peak_open_pairs',
    ]
    for profile_name in profiles:
        pair = comparison[comparison['profile'] == profile_name].set_index('mode')
        row = {'profile': profile_name}
        for column in metric_columns:
            row[f'v1_{column}'] = float(pair.loc['reference_leg', column])
            row[f'v2_{column}'] = float(pair.loc['gross_exposure', column])
            row[f'v2_minus_v1_{column}'] = (
                row[f'v2_{column}'] - row[f'v1_{column}']
            )
        delta_rows.append(row)
    pd.DataFrame(delta_rows).to_csv(OUTPUT_ROOT / 'comparison_delta.csv', index=False)

    display_columns = [
        'profile', 'mode', 'annualized_return', 'sharpe', 'volatility',
        'max_drawdown', 'trade_count', 'win_rate',
        'average_gross_utilization', 'gross_utilization_p95',
        'peak_gross_utilization', 'average_margin_utilization',
        'peak_margin_utilization', 'peak_maintenance_margin_utilization',
    ]
    print(comparison[display_columns].to_string(index=False))
    print('\nTrade-decision comparison:')
    for profile_name, result in trade_comparisons.items():
        print(
            f"{profile_name}: status={result['decision_status']}, "
            f"entries_match={result['entry_keys_match']}, "
            f"v1_only={len(result['v1_only_trades'])}, "
            f"v2_only={len(result['v2_only_trades'])}, "
            f"public_reference={result['public_reference_comparison']['status']}"
        )
    print(f'Outputs written under {OUTPUT_ROOT}')


if __name__ == '__main__':
    main()
