import math

import backtrader as bt
import numpy as np
import pandas as pd

from src.backtest import PairTradingStrategy, ZScoreData, calculate_pair_sizes
from research.run_experiment import summarize_exposure
from research.run_sizing_capital_audit import (
    assess_capacity,
    margin_requirement,
    sequential_capacity_ledger,
)


def test_reference_leg_sizing_preserves_canonical_log_space_math():
    result = calculate_pair_sizes(
        1_000_000.0,
        0.25,
        100.0,
        50.0,
        0.4,
        log_space=True,
        pair_sizing_mode='reference_leg',
    )

    assert result['sizing_capital'] == 1_000_000.0
    assert result['sizing_budget'] == 250_000.0
    assert result['reference_leg_notional'] == 250_000.0
    assert result['target_notional'] == 250_000.0
    assert result['pair_gross_budget'] == result['sizing_budget']
    assert result['pair_gross_budget_enforced'] is False
    assert result['size2'] == 5_000
    assert result['size1'] == 1_000
    assert result['actual_gross_exposure'] == 350_000.0


def test_reference_leg_zero_size_is_rejected_without_changing_valid_math():
    result = calculate_pair_sizes(
        1_000_000.0,
        0.25,
        100.0,
        1_000_000.0,
        0.4,
        log_space=True,
        pair_sizing_mode='reference_leg',
    )

    assert not result['valid']
    assert result['reason'] == 'zero_size'
    assert result['size1'] == 0
    assert result['size2'] == 0


def test_reference_leg_nonfinite_hedge_ratio_is_rejected():
    result = calculate_pair_sizes(
        1_000_000.0,
        0.25,
        100.0,
        50.0,
        np.nan,
        log_space=True,
        pair_sizing_mode='reference_leg',
    )

    assert not result['valid']
    assert result['reason'] == 'invalid_hedge_ratio'


def test_gross_exposure_sizing_preserves_hr_below_one_after_rounding():
    result = calculate_pair_sizes(
        1_000_000.0,
        0.25,
        100.0,
        50.0,
        0.4,
        log_space=True,
        pair_sizing_mode='gross_exposure',
    )

    assert result['pair_gross_budget'] == 250_000.0
    assert result['sizing_capital'] == 1_000_000.0
    assert result['sizing_budget'] == 250_000.0
    assert result['reference_leg_notional'] == 250_000.0 / 1.4
    assert result['target_notional'] == result['sizing_budget']
    assert result['valid']
    assert result['actual_gross_exposure'] <= result['pair_gross_budget']
    assert math.isclose(
        result['actual_gross_exposure'], result['pair_gross_budget'], rel_tol=0.001
    )
    assert result['pair_gross_budget'] - result['actual_gross_exposure'] <= (
        100.0 + (1.0 + 0.4) * 50.0
    )
    actual_hr = result['size1'] * 100.0 / (result['size2'] * 50.0)
    assert math.isclose(actual_hr, 0.4, rel_tol=0.005)


def test_gross_exposure_sizing_preserves_hr_above_one_after_rounding():
    result = calculate_pair_sizes(
        1_000_000.0,
        0.25,
        100.0,
        50.0,
        1.8,
        log_space=True,
        pair_sizing_mode='gross_exposure',
    )

    assert result['valid']
    assert result['actual_gross_exposure'] <= result['pair_gross_budget']
    assert math.isclose(
        result['actual_gross_exposure'], result['pair_gross_budget'], rel_tol=0.001
    )
    assert result['pair_gross_budget'] - result['actual_gross_exposure'] <= (
        100.0 + (1.0 + 1.8) * 50.0
    )
    actual_hr = result['size1'] * 100.0 / (result['size2'] * 50.0)
    assert math.isclose(actual_hr, 1.8, rel_tol=0.005)


def test_gross_exposure_raw_space_uses_the_budget_with_share_hedge_math():
    result = calculate_pair_sizes(
        1_000_000.0,
        0.25,
        50.0,
        100.0,
        0.4,
        log_space=False,
        pair_sizing_mode='gross_exposure',
    )

    assert result['valid']
    assert result['actual_gross_exposure'] <= result['pair_gross_budget']
    assert math.isclose(
        result['actual_gross_exposure'], result['pair_gross_budget'], rel_tol=0.001
    )
    assert result['pair_gross_budget'] - result['actual_gross_exposure'] <= (
        50.0 + 100.0 + 0.4 * 50.0
    )
    actual_hr = result['size1'] / result['size2']
    assert math.isclose(actual_hr, 0.4, rel_tol=0.005)


def test_gross_budget_arithmetic_is_independent_of_trade_direction_and_accepts_negative_hr():
    positive = calculate_pair_sizes(
        1_000_000.0, 0.25, 100.0, 50.0, 0.4,
        log_space=True, pair_sizing_mode='gross_exposure',
    )
    negative = calculate_pair_sizes(
        1_000_000.0, 0.25, 100.0, 50.0, -0.4,
        log_space=True, pair_sizing_mode='gross_exposure',
    )

    assert (positive['size1'], positive['size2']) == (
        negative['size1'], negative['size2']
    )
    for signs in ((1, -1), (-1, 1), (1, 1), (-1, -1)):
        exposure = abs(signs[0] * positive['size1'] * 100.0)
        exposure += abs(signs[1] * positive['size2'] * 50.0)
        assert exposure == positive['actual_gross_exposure']


def test_invalid_gross_hedge_ratios_are_rejected_without_v1_fallback():
    for hr in (0.0, np.nan, np.inf, -np.inf):
        result = calculate_pair_sizes(
            1_000_000.0, 0.25, 100.0, 50.0, hr,
            log_space=True, pair_sizing_mode='gross_exposure',
        )
        assert not result['valid']
        assert result['reason'] == 'invalid_hedge_ratio'
        assert result['size1'] == 0
        assert result['size2'] == 0


def test_gross_exposure_does_not_silently_use_dollar_neutral_sizing():
    try:
        calculate_pair_sizes(
            1_000_000.0, 0.25, 100.0, 50.0, 1.0,
            dollar_neutral=True, pair_sizing_mode='gross_exposure',
        )
    except ValueError as exc:
        assert 'dollar_neutral' in str(exc)
    else:
        raise AssertionError('gross sizing silently accepted dollar-neutral mode')


def test_trade_metadata_records_actual_gross_exposure_and_daily_diagnostics():
    dates = pd.bdate_range('2024-01-02', periods=8)
    zscore = np.array([0.0, 0.0, -3.0, -3.0, 0.0, 0.0, 0.0, 0.0])
    n = len(dates)
    df1 = pd.DataFrame({
        'close': np.full(n, 100.0),
        'zscore': zscore,
        'hedge_ratio': np.full(n, 0.4),
        'intercept': np.zeros(n),
        'phi': np.full(n, np.nan),
        'sigma_eq': np.full(n, np.nan),
        'rolling_std': np.full(n, 0.05),
        'rolling_mean': np.zeros(n),
    }, index=dates)
    df2 = pd.DataFrame({'close': np.full(n, 50.0)}, index=dates)

    cerebro = bt.Cerebro()
    cerebro.broker.setcash(1_000_000.0)
    cerebro.broker.set_coc(True)
    cerebro.adddata(ZScoreData(dataname=df1, name='S1'))
    cerebro.adddata(bt.feeds.PandasData(dataname=df2, name='S2'))
    cerebro.addstrategy(
        PairTradingStrategy,
        entry_z=2.0,
        exit_z=1.0,
        stop_z=999.0,
        max_holding_days=999,
        hr_threshold=0.99,
        is_stats={'S1-S2': {'hr': 0.4}},
        log_space=True,
        lock_hr_for_zscore=False,
        lock_std_for_zscore=False,
        dollar_neutral=False,
        pair_sizing_mode='gross_exposure',
        initial_cash=1_000_000.0,
        equity_fraction=0.25,
        margin_behavior='off',
    )

    result = cerebro.run()[0]
    assert len(result.trade_logs) == 1
    trade = result.trade_logs[0]
    required = {
        'pair_sizing_mode', 'sizing_capital', 'sizing_budget', 'hr_entry',
        'reference_leg_notional', 'target_notional', 'pair_gross_budget',
        'pair_gross_budget_enforced',
        'size1', 'size2', 'sizing_price1', 'sizing_price2',
        'sizing_log_space', 'sizing_dollar_neutral',
        'entry_price1', 'entry_price2', 'sizing_gross_exposure',
        'leg1_entry_exposure', 'leg2_entry_exposure', 'gross_entry_exposure',
        'long_entry_exposure', 'short_entry_exposure',
        'estimated_initial_margin_requirement',
        'estimated_maintenance_margin_requirement',
    }
    assert required <= trade.keys()
    assert trade['pair_sizing_mode'] == 'gross_exposure'
    assert trade['sizing_capital'] == 1_000_000.0
    assert trade['sizing_budget'] == 250_000.0
    assert math.isclose(
        trade['reference_leg_notional'],
        trade['sizing_budget'] / (1.0 + abs(trade['hr_entry'])),
    )
    assert trade['target_notional'] == trade['sizing_budget']
    assert trade['pair_gross_budget'] == trade['sizing_budget']
    assert trade['sizing_log_space'] is True
    assert trade['sizing_dollar_neutral'] is False
    assert trade['sizing_gross_exposure'] == (
        trade['size1'] * trade['sizing_price1']
        + trade['size2'] * trade['sizing_price2']
    )
    assert trade['pair_gross_budget_enforced'] is True
    assert trade['gross_entry_exposure'] == (
        trade['leg1_entry_exposure'] + trade['leg2_entry_exposure']
    )
    assert trade['gross_entry_exposure'] <= trade['pair_gross_budget']
    assert math.isclose(
        trade['gross_entry_exposure'], trade['pair_gross_budget'], rel_tol=0.001
    )
    assert trade['long_entry_exposure'] + trade['short_entry_exposure'] == (
        trade['gross_entry_exposure']
    )

    exposure = pd.DataFrame(result.daily_exposure)
    assert not exposure.empty
    assert {
        'gross_exposure', 'gross_utilization', 'open_pairs',
        'initial_margin_utilization',
    } <= set(exposure.columns)


def test_exposure_summary_merges_fold_accounts_before_calculating_ratios():
    rows = [
        {
            'date': '2024-01-02',
            'equity': 100.0,
            'gross_exposure': 60.0,
            'open_pairs': 1,
            'estimated_initial_margin_requirement': 30.0,
            'estimated_maintenance_margin_requirement': 20.0,
        },
        {
            'date': '2024-01-02',
            'equity': 300.0,
            'gross_exposure': 120.0,
            'open_pairs': 2,
            'estimated_initial_margin_requirement': 60.0,
            'estimated_maintenance_margin_requirement': 30.0,
        },
        {
            'date': '2024-01-03',
            'equity': 400.0,
            'gross_exposure': 0.0,
            'open_pairs': 0,
            'estimated_initial_margin_requirement': 0.0,
            'estimated_maintenance_margin_requirement': 0.0,
        },
    ]

    summary = summarize_exposure(rows)

    assert summary['average_gross_utilization'] == 0.225
    assert summary['peak_gross_utilization'] == 0.45
    assert summary['average_open_pairs'] == 1.5
    assert summary['peak_open_pairs'] == 3
    assert summary['peak_margin_utilization'] == 0.225


def test_capacity_models_keep_funded_and_margin_headroom_separate():
    capacity = assess_capacity(
        current_equity=100.0,
        current_gross_exposure=60.0,
        existing_initial_margin=20.0,
        desired_gross_exposure=50.0,
        desired_initial_margin=30.0,
    )

    assert capacity['fully_funded_free_capacity'] == 40.0
    assert capacity['fully_funded_excess'] == 10.0
    assert capacity['fully_funded_fits'] is False
    assert capacity['free_margin'] == 80.0
    assert capacity['margin_excess'] == 0.0
    assert capacity['margin_fits'] is True


def test_margin_requirement_uses_side_specific_rates():
    assert margin_requirement(
        10, 20, 100, 50, 'long', 'short', margin_long=0.50,
        margin_short=0.25,
    ) == 750.0


def test_sequential_capacity_ledger_reserves_admitted_same_day_entries():
    frame = pd.DataFrame([
        {
            'fold_id': 1,
            'date': '2024-01-02',
            'audit_sequence': 1,
            'pair': 'A-B',
            'pair_index': 0,
            'fully_funded_free_capacity': 100.0,
            'free_margin': 100.0,
            'naive_dynamic_gross_exposure': 60.0,
            'naive_dynamic_initial_margin_required': 70.0,
        },
        {
            'fold_id': 1,
            'date': '2024-01-02',
            'audit_sequence': 2,
            'pair': 'C-D',
            'pair_index': 1,
            'fully_funded_free_capacity': 100.0,
            'free_margin': 100.0,
            'naive_dynamic_gross_exposure': 50.0,
            'naive_dynamic_initial_margin_required': 40.0,
        },
    ])

    funded = sequential_capacity_ledger(frame, 'fully_funded')
    margin = sequential_capacity_ledger(frame, 'margin')

    assert funded['admitted'].tolist() == [True, False]
    assert margin['admitted'].tolist() == [True, False]
