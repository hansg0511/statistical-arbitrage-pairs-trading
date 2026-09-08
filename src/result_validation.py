"""Validation helpers for deciding whether a backtest output is complete."""

import json
import os
import re


_FOLD_COUNT_RE = re.compile(r"Generated\s+(\d+)\s+walk-forward folds")
_ERROR_RE = re.compile(
    r"(?:^\s*ERROR:|^\s*\[ERROR\]|Traceback \(most recent call last\):|"
    r"(?:ValueError|TypeError|KeyError|RuntimeError):)",
    re.MULTILINE,
)


def validate_run_output(output_dir):
    """Return validity and reasons for one completed backtest directory.

    Older outputs without ``run_status.json`` remain readable, but must still
    have a complete fold summary and an error-free run log.
    """
    reasons = []
    log_path = os.path.join(output_dir, 'run.log')
    log_text = ''
    if not os.path.exists(log_path):
        reasons.append('missing run.log')
    else:
        with open(log_path, encoding='utf-8', errors='replace') as f:
            log_text = f.read()
        if _ERROR_RE.search(log_text):
            reasons.append('run.log contains an error or traceback')

    metrics_path = os.path.join(output_dir, 'metrics.json')
    metrics = None
    if not os.path.exists(metrics_path):
        reasons.append('missing metrics.json')
    else:
        try:
            with open(metrics_path, encoding='utf-8') as f:
                metrics = json.load(f)
        except (OSError, ValueError) as exc:
            reasons.append(f'invalid metrics.json: {exc}')

    status_path = os.path.join(output_dir, 'run_status.json')
    status = None
    if os.path.exists(status_path):
        try:
            with open(status_path, encoding='utf-8') as f:
                status = json.load(f)
            if status.get('status') != 'success':
                reasons.append(f"run status is {status.get('status', 'unknown')}")
        except (OSError, ValueError) as exc:
            reasons.append(f'invalid run_status.json: {exc}')

    expected_folds = None
    if status and status.get('expected_folds') is not None:
        expected_folds = status['expected_folds']
    elif metrics and metrics.get('expected_folds') is not None:
        expected_folds = metrics['expected_folds']
    else:
        match = _FOLD_COUNT_RE.search(log_text)
        if match:
            expected_folds = int(match.group(1))

    if expected_folds is None:
        reasons.append('missing expected fold count')

    completed_folds = None
    if status and status.get('completed_folds') is not None:
        completed_folds = status['completed_folds']
    elif metrics and metrics.get('completed_folds') is not None:
        completed_folds = metrics['completed_folds']
    elif metrics and metrics.get('total_folds') is not None:
        completed_folds = metrics['total_folds']

    if completed_folds is None:
        reasons.append('missing completed fold count')
    elif expected_folds is not None and int(completed_folds) != int(expected_folds):
        reasons.append(
            f'completed folds {completed_folds} != expected folds {expected_folds}'
        )

    summary_path = os.path.join(output_dir, 'oos_fold_summary.csv')
    if not os.path.exists(summary_path):
        reasons.append('missing oos_fold_summary.csv')
    elif expected_folds is not None:
        try:
            with open(summary_path, encoding='utf-8', errors='replace') as f:
                summary_rows = max(0, sum(1 for _ in f) - 1)
            if summary_rows != int(expected_folds):
                reasons.append(
                    f'oos fold rows {summary_rows} != expected folds {expected_folds}'
                )
        except OSError as exc:
            reasons.append(f'cannot read oos_fold_summary.csv: {exc}')

    return {
        'valid': not reasons,
        'reasons': reasons,
        'expected_folds': expected_folds,
        'completed_folds': completed_folds,
    }
