"""Audit 0.045 reference runs against their 0.25 trade-mark counterparts.

The two suites are expected to differ only in position size and broker buying
power. This tool makes every other observed difference explicit instead of
reducing it to a single pass/fail count.

Usage:
    python audit_pct25_comparison.py
    python audit_pct25_comparison.py --only 06
    python audit_pct25_comparison.py --output-dir research/archive/pct25_audit
"""

import argparse
import json
import os
import re
from collections import Counter, defaultdict

import pandas as pd

from run_sweep_pct25_marks import BASE, OUT_ROOT, SECTIONS, out_dir
from src.result_validation import validate_run_output


EVENT_COLUMNS = ('pair', 'entry_date', 'exit_date', 'exit_reason')
ENTRY_COLUMNS = ('pair', 'entry_date', 'fold_id')
RETURN_TOLERANCE = 0.01
STATIC_METRIC_KEYS = (
    'profile', 'mode', 'universe', 'cross_sector', 'start', 'end',
    'sel_months', 'test_months', 'slide_months', 'entry_z', 'exit_z',
    'stop_z', 'resid_val', 'z_m', 'hr_thresh', 'max_holding_days',
    'pvalue', 'max_pairs', 'log_space', 'dollar_neutral',
    'expected_folds', 'completed_folds', 'margin_behavior',
    'price_snapshot_mode', 'price_snapshot_sha256',
)
FOLD_RE = re.compile(r'--- Processing Fold (\d+)')
SELECTED_RE = re.compile(r'Selected \d+ pairs: (.*)')


def _read_json(path):
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)


def _read_trade_log(path):
    frame = pd.read_csv(path)
    missing = set(EVENT_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f'{path} missing trade-log columns: {sorted(missing)}')
    if 'fold_id' not in frame.columns:
        frame['fold_id'] = -1
    return frame


def _event_key(row):
    return tuple(str(row[column]) for column in EVENT_COLUMNS)


def _entry_key(row):
    return tuple(str(row[column]) for column in ENTRY_COLUMNS)


def _event_map(frame):
    records = {}
    duplicates = []
    for _, row in frame.iterrows():
        key = _event_key(row)
        if key in records:
            duplicates.append(key)
        records[key] = row.to_dict()
    return records, duplicates


def _entry_map(frame):
    entries = defaultdict(list)
    for _, row in frame.iterrows():
        entries[_entry_key(row)].append(row.to_dict())
    return entries


def _pair_fold(event):
    return str(event['pair']), str(event.get('fold_id', -1))


def _selected_pairs(path):
    if not os.path.exists(path):
        return {}, 'missing run.log'

    selected = {}
    fold = None
    with open(path, encoding='utf-8', errors='replace') as handle:
        for line in handle:
            fold_match = FOLD_RE.search(line)
            if fold_match:
                fold = int(fold_match.group(1))
                continue
            selected_match = SELECTED_RE.search(line)
            if fold is not None and selected_match:
                pairs = tuple(pair for pair in selected_match.group(1).split(', ') if pair)
                selected[fold] = pairs
    return selected, None


def _rejections(path):
    if not os.path.exists(path):
        return Counter()
    frame = pd.read_csv(path)
    if 'reason' not in frame.columns:
        return Counter({'unknown': len(frame)})
    return Counter(str(reason) for reason in frame['reason'])


def _zero_size_entry_attempts(path):
    """Return reference entries that only fail because a rounded leg is zero."""
    if not os.path.exists(path):
        return set()
    frame = pd.read_csv(path)
    required = {'pair', 'date', 'reason'}
    if not required.issubset(frame.columns):
        return set()
    zero_size = frame[frame['reason'].astype(str).isin({'zero_size', 'zero_fill'})]
    return {
        (str(row['pair']), str(row['date']))
        for _, row in zero_size.iterrows()
    }


def _static_metric_differences(old_metrics, new_metrics):
    differences = []
    for key in STATIC_METRIC_KEYS:
        # Older reference metrics predate run-status fields. Missing metadata
        # does not establish a configuration difference.
        if key in old_metrics and key in new_metrics and old_metrics[key] != new_metrics[key]:
            differences.append(key)
    return differences


def _compare_run(section, start, label):
    new_dir = out_dir(section, start, label)
    old_dir = os.path.join(BASE, section, f'{start}_{label}')
    old_log = os.path.join(old_dir, 'trade_logs', 'test_trade_log.csv')
    new_log = os.path.join(new_dir, 'trade_logs', 'test_trade_log.csv')
    old_metrics_path = os.path.join(old_dir, 'metrics.json')
    new_metrics_path = os.path.join(new_dir, 'metrics.json')

    row = {
        'section': section,
        'start': start,
        'label': label,
        'old_dir': old_dir,
        'new_dir': new_dir,
    }
    details = []

    if not all(os.path.exists(path) for path in (old_log, new_log, old_metrics_path, new_metrics_path)):
        row['classification'] = 'missing_artifact'
        row['artifact_error'] = True
        return row, details

    old_valid = validate_run_output(old_dir)
    new_valid = validate_run_output(new_dir)
    row['old_valid'] = old_valid['valid']
    row['new_valid'] = new_valid['valid']
    row['old_validation'] = '; '.join(old_valid['reasons'])
    row['new_validation'] = '; '.join(new_valid['reasons'])

    old_metrics = _read_json(old_metrics_path)
    new_metrics = _read_json(new_metrics_path)
    static_diffs = _static_metric_differences(old_metrics, new_metrics)
    row['static_metric_differences'] = ','.join(static_diffs)
    row['old_pct_per_pair'] = old_metrics.get('pct_per_pair')
    row['new_pct_per_pair'] = new_metrics.get('pct_per_pair')
    row['old_broker_leverage'] = old_metrics.get('broker_leverage')
    row['new_broker_leverage'] = new_metrics.get('broker_leverage')
    row['old_total_trades'] = old_metrics.get('total_trades')
    row['new_total_trades'] = new_metrics.get('total_trades')

    old_selected, old_selection_error = _selected_pairs(os.path.join(old_dir, 'run.log'))
    new_selected, new_selection_error = _selected_pairs(os.path.join(new_dir, 'run.log'))
    selection_error = old_selection_error or new_selection_error
    fold_keys = set(old_selected) | set(new_selected)
    selection_mismatch_folds = [
        fold for fold in sorted(fold_keys)
        if old_selected.get(fold, ()) != new_selected.get(fold, ())
    ]
    row['selection_error'] = selection_error or ''
    row['selection_fold_count_old'] = len(old_selected)
    row['selection_fold_count_new'] = len(new_selected)
    row['selection_mismatch_folds'] = ','.join(str(fold) for fold in selection_mismatch_folds)

    old_rejections_path = os.path.join(old_dir, 'rejected_orders.csv')
    new_rejections_path = os.path.join(new_dir, 'rejected_orders.csv')
    old_rejections = _rejections(old_rejections_path)
    new_rejections = _rejections(new_rejections_path)
    old_zero_size_attempts = _zero_size_entry_attempts(old_rejections_path)
    row['old_rejections'] = sum(old_rejections.values())
    row['new_rejections'] = sum(new_rejections.values())
    row['old_rejection_reasons'] = json.dumps(old_rejections, sort_keys=True)
    row['new_rejection_reasons'] = json.dumps(new_rejections, sort_keys=True)

    old_frame = _read_trade_log(old_log)
    new_frame = _read_trade_log(new_log)
    old_events, old_duplicates = _event_map(old_frame)
    new_events, new_duplicates = _event_map(new_frame)
    old_keys = set(old_events)
    new_keys = set(new_events)
    old_only = old_keys - new_keys
    new_only = new_keys - old_keys
    old_entries = _entry_map(old_frame)
    new_entries = _entry_map(new_frame)
    accepted_exit_pair_folds = set()
    unaccepted_exit_changes = 0
    for key in old_entries.keys() & new_entries.keys():
        old_entry_events = {_event_key(event) for event in old_entries[key]}
        new_entry_events = {_event_key(event) for event in new_entries[key]}
        if old_entry_events == new_entry_events:
            continue
        reasons = {
            event['exit_reason']
            for event in old_entries[key] + new_entries[key]
        }
        if reasons == {'max_holding_loss'}:
            accepted_exit_pair_folds.add((key[0], key[2]))
        else:
            unaccepted_exit_changes += 1
    accepted_old_only = {
        key for key in old_only if _pair_fold(old_events[key]) in accepted_exit_pair_folds
    }
    accepted_new_only = {
        key for key in new_only if _pair_fold(new_events[key]) in accepted_exit_pair_folds
    }
    expected_new_only = {
        key for key in new_only - accepted_new_only
        if (key[0], key[1]) in old_zero_size_attempts
    }
    unexplained_old_only = old_only - accepted_old_only
    unexplained_new_only = new_only - expected_new_only - accepted_new_only

    row['old_log_rows'] = len(old_frame)
    row['new_log_rows'] = len(new_frame)
    row['old_duplicate_event_keys'] = len(old_duplicates)
    row['new_duplicate_event_keys'] = len(new_duplicates)
    row['old_only_events'] = len(old_only)
    row['new_only_events'] = len(new_only)
    row['accepted_allocation_exit_events'] = len(accepted_old_only) + len(accepted_new_only)
    row['unexplained_old_only_events'] = len(unexplained_old_only)
    row['expected_new_events_after_old_zero_size'] = len(expected_new_only)
    row['unexplained_new_only_events'] = len(unexplained_new_only)

    old_entry_keys = set(old_entries)
    new_entry_keys = set(new_entries)
    row['old_only_entries'] = len(old_entry_keys - new_entry_keys)
    row['new_only_entries'] = len(new_entry_keys - old_entry_keys)
    expected_new_entries = {
        entry for entry in new_entry_keys - old_entry_keys
        if (entry[0], entry[1]) in old_zero_size_attempts
    }
    row['expected_new_entries_after_old_zero_size'] = len(expected_new_entries)
    accepted_old_entries = {
        key for key in old_entry_keys - new_entry_keys
        if (key[0], key[2]) in accepted_exit_pair_folds
    }
    accepted_new_entries = {
        key for key in new_entry_keys - old_entry_keys
        if (key[0], key[2]) in accepted_exit_pair_folds
    }
    row['accepted_allocation_exit_entries'] = len(accepted_old_entries) + len(accepted_new_entries)
    row['unexplained_old_only_entries'] = len(old_entry_keys - new_entry_keys - accepted_old_entries)
    row['unexplained_new_only_entries'] = len(
        new_entry_keys - old_entry_keys - expected_new_entries - accepted_new_entries
    )
    row['same_entry_changed_exit'] = unaccepted_exit_changes

    return_differences = []
    for key in old_keys & new_keys:
        difference = abs(float(old_events[key]['return']) - float(new_events[key]['return']))
        if difference:
            return_differences.append((key, difference))
        if difference > RETURN_TOLERANCE:
            details.append({
                'difference_type': 'return_difference_over_tolerance',
                'section': section,
                'start': start,
                'label': label,
                'event_key': '|'.join(key),
                'old_return': old_events[key]['return'],
                'new_return': new_events[key]['return'],
                'return_difference': difference,
            })
    row['common_events_with_return_difference'] = len(return_differences)
    row['common_events_return_difference_over_tolerance'] = sum(
        difference > RETURN_TOLERANCE for _, difference in return_differences
    )
    row['max_common_event_return_difference'] = max(
        (difference for _, difference in return_differences), default=0.0
    )

    for difference_type, keys, events in (
        ('accepted_allocation_exit_event', accepted_old_only, old_events),
        ('accepted_allocation_exit_event', accepted_new_only, new_events),
        ('old_only_event', unexplained_old_only, old_events),
        ('expected_new_event_after_old_zero_size', expected_new_only, new_events),
        ('new_only_event', unexplained_new_only, new_events),
    ):
        for key in sorted(keys):
            event = events[key]
            details.append({
                'difference_type': difference_type,
                'section': section,
                'start': start,
                'label': label,
                'event_key': '|'.join(key),
                'fold_id': event.get('fold_id'),
                'return': event.get('return'),
            })

    classifications = []
    if not old_valid['valid'] or not new_valid['valid']:
        classifications.append('invalid_run')
    if static_diffs:
        classifications.append('static_config_difference')
    if selection_error:
        classifications.append('selection_log_unavailable')
    elif selection_mismatch_folds:
        classifications.append('pair_selection_difference')
    expected_rejection_difference = (
        bool(old_rejections)
        and not new_rejections
        and set(old_rejections).issubset({'zero_size', 'zero_fill'})
    )
    if old_rejections != new_rejections and not expected_rejection_difference:
        classifications.append('rejection_difference')
    if row['unexplained_old_only_entries'] or row['unexplained_new_only_entries']:
        classifications.append('entry_event_difference')
    if unaccepted_exit_changes:
        classifications.append('exit_event_difference')
    if row['common_events_return_difference_over_tolerance']:
        classifications.append('return_difference')
    row['classification'] = ';'.join(classifications) or 'exact_within_tolerance'
    return row, details


def _write_markdown(path, summary):
    lines = [
        '# pct=0.25 Trade-Event Comparison Audit',
        '',
        f"Runs compared: {len(summary)}",
        '',
        '| Section | Runs | Exact within tolerance | Any discrepancy | Accepted allocation exits | Unexplained old-only events | Expected new after zero-size | Unexplained new-only events | Return differences > 1pp |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for section, frame in summary.groupby('section', sort=True):
        exact = int((frame['classification'] == 'exact_within_tolerance').sum())
        rows = len(frame)
        lines.append(
            f'| {section} | {rows} | {exact} | {rows - exact} | '
            f"{int(frame['accepted_allocation_exit_events'].sum())} | "
            f"{int(frame['unexplained_old_only_events'].sum())} | "
            f"{int(frame['expected_new_events_after_old_zero_size'].sum())} | "
            f"{int(frame['unexplained_new_only_events'].sum())} | "
            f"{int(frame['common_events_return_difference_over_tolerance'].sum())} |"
        )
    lines.extend([
        '',
        'A discrepancy is evidence to investigate, not a conclusion about its cause. '
        'The CSV files contain the per-run and per-event evidence.',
        '',
    ])
    with open(path, 'w', encoding='utf-8', newline='') as handle:
        handle.write('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', choices=sorted(SECTIONS), help='Audit one section only.')
    parser.add_argument(
        '--output-dir', default=os.path.join('research', 'archive', 'pct25_comparison_audit'),
        help='Directory for generated CSV and Markdown evidence.',
    )
    args = parser.parse_args()

    sections = [args.only] if args.only else list(SECTIONS)
    summary_rows = []
    detail_rows = []
    for section in sections:
        for start in SECTIONS[section]['starts']:
            for label, _ in SECTIONS[section]['grid']:
                summary, details = _compare_run(section, start, label)
                summary_rows.append(summary)
                detail_rows.extend(details)

    os.makedirs(args.output_dir, exist_ok=True)
    summary_frame = pd.DataFrame(summary_rows)
    detail_frame = pd.DataFrame(detail_rows)
    summary_path = os.path.join(args.output_dir, 'run_comparison.csv')
    detail_path = os.path.join(args.output_dir, 'event_differences.csv')
    report_path = os.path.join(args.output_dir, 'findings.md')
    summary_frame.to_csv(summary_path, index=False)
    detail_frame.to_csv(detail_path, index=False)
    _write_markdown(report_path, summary_frame)

    exact = int((summary_frame['classification'] == 'exact_within_tolerance').sum())
    print(f'Compared {len(summary_frame)} runs: {exact} exact within tolerance, '
          f'{len(summary_frame) - exact} with discrepancies.')
    print(f'Run evidence: {summary_path}')
    print(f'Event evidence: {detail_path}')
    print(f'Report: {report_path}')


if __name__ == '__main__':
    main()
