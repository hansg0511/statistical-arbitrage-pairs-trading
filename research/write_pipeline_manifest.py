"""Write provenance for the corrected research pipeline.

The manifest intentionally hashes the report inputs and generators used by the
replacement pipeline, but not the generated manifest itself or the original
user-curated pipeline note.

Usage: python research/write_pipeline_manifest.py
"""
import hashlib
import json
import os
from datetime import datetime, timezone


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'RESEARCH_PIPELINE_FIXED_MANIFEST.json')

INPUTS = [
    'RESEARCH_PIPELINE_FIXED.md',
    'research/selected_book_config.json',
    'notebooks/08_combined_momentum_book.ipynb',
    'CACHE_BUG_FIX_REPORT.md',
    'diagnosis/01_baseline_instability (old)/findings.md',
    'diagnosis/02_earnings_screen_baseline (old)/findings.md',
    'diagnosis/02b_earnings_sweep_full/findings.md',
    'diagnosis/03_pair_stability (old)/findings.md',
    'diagnosis/03_pair_stability (old)/comparison_findings.md',
    'diagnosis/04_max_pairs_sweep/findings.md',
    'fixed_diagnosis/05/findings.md',
    'fixed_diagnosis/06/findings.md',
    'fixed_diagnosis/07/findings.md',
    'fixed_diagnosis/08a/findings.md',
    'fixed_diagnosis/08b/findings.md',
    'fixed_diagnosis/09a/findings.md',
    'fixed_diagnosis/09b/findings.md',
    'fixed_diagnosis/10/findings.md',
    'fixed_diagnosis/10a/findings.md',
    'fixed_diagnosis/10b/findings.md',
    'fixed_diagnosis/_combined/consolidated/recent/A/metrics.json',
    'fixed_diagnosis/_combined/consolidated/recent/B/metrics.json',
    'fixed_diagnosis/_combined/consolidated/historical/A/metrics.json',
    'fixed_diagnosis/_combined/consolidated/historical/B/metrics.json',
    'fixed_diagnosis/08b/2014-01-01_same_sector_slide1m_bd7/metrics.json',
    'fixed_diagnosis/09b/2014-01-01_same_sector_slide1m_bd7/metrics.json',
    'fixed_diagnosis/_sweep_pct25/08b/2014-01-01_same_sector_slide1m_bd7/metrics.json',
    'fixed_diagnosis/_sweep_pct25/09b/2014-01-01_same_sector_slide1m_bd7/metrics.json',
    'fixed_diagnosis/_COMPARISON_WITH_PIPELINE.md',
    'fixed_diagnosis/_CONSOLIDATED_COMPARISON.md',
    'fixed_diagnosis/_FF_COMBINED_PCT25.md',
    'fixed_diagnosis/separate/_COMBINED_BOOK_CONSOLIDATED.md',
    'fixed_diagnosis/separate/_PAIRS_WITH_HIST1.md',
    'fixed_diagnosis/separate/_PAIRS_WITH_RECENT1.md',
    'fixed_diagnosis/separate/_TOP15_CONFIG_PAIRS.md',
    'fixed_diagnosis/separate/_TOP15_PER_PERIOD.md',
    'fixed_diagnosis/joint/_JOINED_CONFIG_PAIRS.md',
    'fixed_diagnosis/joint/_JOINED_PER_PERIOD.md',
    'fixed_diagnosis/joint/_JOINT_VS_SEPARATE.md',
    'fixed_diagnosis/joint/compare_pairs.csv',
    'fixed_diagnosis/joint/joined_legs.csv',
    'fixed_diagnosis/joint/joined_pairs.csv',
    'fixed_diagnosis/compare/_RANK_COMPARISON.md',
    'fixed_diagnosis/compare/rank_comparison_A.csv',
    'fixed_diagnosis/compare/rank_comparison_B.csv',
    'fixed_diagnosis/compare/_HUMAN_ANALYSIS_DEFAULT.md',
    'fixed_diagnosis/compare/_STEP_ROBUSTNESS.csv',
    'fixed_diagnosis/compare/_LOOKBACK_ROBUSTNESS.csv',
    'fixed_diagnosis/compare/_JOINT_ROBUSTNESS.csv',
    'fixed_diagnosis/compare/_BOUNDS_ROBUSTNESS.csv',
    'fixed_diagnosis/compare/_FRONTIER_ROBUSTNESS.csv',
    'fixed_diagnosis/compare/_FINAL_ROBUSTNESS.csv',
    'fixed_diagnosis/compare/_CLEAN_ROBUSTNESS.csv',
    'fixed_diagnosis/compare/_MOMENTUM_FF_PAIRS.md',
    'fixed_diagnosis/compare/momentum_sensitivity.csv',
    'fixed_diagnosis/compare/ff_regressions.csv',
    'fixed_diagnosis/compare/_FF_PAIR_MULTISTART_sp500-12m_cross_sector_slide1m_noscreen_sp500-2m_cross_sector_slide3m_bd7.md',
    'fixed_diagnosis/compare/_FF_PAIR_MULTISTART_sp500-12m_cross_sector_slide1m_noscreen_sp500-2m_cross_sector_slide3m_bd7.csv',
    'fixed_diagnosis/compare/_FF_LEG_sp500-12m_cross_sector_slide1m_noscreen.md',
    'fixed_diagnosis/compare/_FF_LEG_sp500-12m_cross_sector_slide1m_noscreen.csv',
    'fixed_diagnosis/compare/_FF_LEG_sp500-2m_cross_sector_slide3m_bd7.md',
    'fixed_diagnosis/compare/_FF_LEG_sp500-2m_cross_sector_slide3m_bd7.csv',
    'fixed_diagnosis/rankavg/_RANKAVG_SELECTION.md',
    'fixed_diagnosis/rankavg/_MOMENTUM_FF_RANKAVG.md',
    'fixed_diagnosis/rankavg/momentum_sensitivity.csv',
    'fixed_diagnosis/rankavg/ff_regressions.csv',
    'fixed_diagnosis/clean40/_CLEAN40_PAIR_RANKS.md',
    'fixed_diagnosis/clean40/_CLEAN40_PAIR_RANKS_A.csv',
    'fixed_diagnosis/clean40/_CLEAN40_PAIR_RANKS_B.csv',
    'fixed_diagnosis/clean40/_HUMAN_ANALYSIS.md',
    'fixed_diagnosis/clean40/_FF_PAIR_MULTISTART_clean40.md',
    'fixed_diagnosis/clean40/_FF_PAIR_MULTISTART_clean40.csv',
    'fixed_diagnosis/clean40/_FF_COMPARE_clean40_vs_default.md',
    'research/run_combined_backtest.py',
    'research/combined_backtest_synthetic_test.py',
    'research/pair_sweep_consolidated.py',
    'research/compare_rankings.py',
    'research/write_human_analysis.py',
    'research/write_joint_eval.py',
    'research/write_joint_vs_separate.py',
    'research/write_top7_period.py',
    'research/write_pairs_with_hist1.py',
    'research/write_pairs_with_recent1.py',
    'research/write_consolidated_comparison.py',
    'run_fixed_comparison.py',
    'run_fixed_reports.py',
    'regen_04_02b.py',
    'run_sweep_earnings_full.py',
    'research/momentum_ff_pairs.py',
    'research/momentum_ff_rankavg.py',
    'research/evaluate_clean40.py',
    'research/run_ff_combined.py',
    'research/run_ff_pair_multistart.py',
    'research/run_ff_leg.py',
    'research/plot_ff_best84.py',
    'research/step_robustness.py',
    'research/write_pipeline_manifest.py',
]

COMMANDS = [
    'python run_fixed_reports.py',
    'python research/run_combined_backtest.py --window recent --mechanism both --lookback 63 --step 0.10 --clamp 0.25 0.75',
    'python research/run_combined_backtest.py --window historical --mechanism both --lookback 63 --step 0.10 --clamp 0.25 0.75',
    'python research/combined_backtest_synthetic_test.py',
    'python research/pair_sweep_consolidated.py --mechanism both --pct 0.25 --top 20 --report',
    'python research/write_joint_eval.py',
    'python research/write_joint_vs_separate.py',
    'python research/compare_rankings.py',
    'python research/write_human_analysis.py',
    'python research/write_top7_period.py',
    'python research/write_pairs_with_hist1.py',
    'python research/write_pairs_with_recent1.py',
    'python research/evaluate_clean40.py',
    'python research/step_robustness.py step --force',
    'python research/step_robustness.py lookback --force',
    'python research/step_robustness.py joint --force',
    'python research/step_robustness.py bounds --force',
    'python research/step_robustness.py frontier --force',
    'python research/step_robustness.py final --force',
    'python research/step_robustness.py clean --force',
    'python research/momentum_ff_pairs.py',
    'python research/momentum_ff_rankavg.py',
    'python research/run_ff_leg.py sp500-12m cross_sector_slide1m_noscreen',
    'python research/run_ff_leg.py sp500-2m cross_sector_slide3m_bd7',
    'python research/run_ff_pair_multistart.py',
    'python research/run_ff_combined.py',
    'python research/plot_ff_best84.py clean40 --reports-only',
    'python research/plot_ff_best84.py clean40 --plots-only',
    'python research/write_consolidated_comparison.py',
    'python run_fixed_comparison.py',
    'python research/write_pipeline_manifest.py',
]

SNAPSHOTS = {
    'core_recent_2m': {
        'path': 'research/archive/pct25_comparison_audit/snapshots/core_recent.pkl',
        'sha256': 'c3ca1a34a687deb11f11ce71230b3ef529e59f7137794fd1ab14b21524f6d241',
    },
    'core_recent_12m': {
        'path': 'research/archive/pct25_comparison_audit/snapshots/core_recent_12m.pkl',
        'sha256': '3503f51d44ea43894c451ed6a686d625b299b40778d6f050f80abc1ba31b48fd',
    },
    'core_historical_2m': {
        'path': 'research/archive/pct25_comparison_audit/snapshots/core_historical.pkl',
        'sha256': '0858947a9be19c4291b244cddc192f918fb4df1a0505961059e5137d20a83669',
    },
    'core_historical_12m': {
        'path': 'research/archive/pct25_comparison_audit/snapshots/core_historical_12m.pkl',
        'sha256': '44092f80ea9b692098f951fd0b8eea9900f1deaf1f67a85995800732055665e9',
    },
    'sp500_recent_2m': {
        'path': 'research/archive/pct25_comparison_audit/snapshots/sp500_recent.pkl',
        'sha256': '96fec4515ff77cbdfad495785f3fa6beb543055e475702f5a8a1b6ff47b5df0b',
    },
    'sp500_recent_12m': {
        'path': 'research/archive/pct25_comparison_audit/snapshots/sp500_recent_12m.pkl',
        'sha256': '3b79b2a7ba56b1638d3ccccb6187f7bc551291ff058685f6e13eb98833311482',
    },
    'sp500_historical_2m': {
        'path': 'research/archive/pct25_comparison_audit/snapshots/sp500_historical.pkl',
        'sha256': 'a3cea24a8471dc532653cf0a759edb9440df53384169bfd25a1c2ac0c561cc5c',
    },
    'sp500_historical_12m': {
        'path': 'research/archive/pct25_comparison_audit/snapshots/sp500_historical_12m.pkl',
        'sha256': '409c92be33e411d32ec3d612886c49fd0a2fd1d95565580a45125fb0ee774ece',
    },
}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    files = {}
    for rel in INPUTS:
        path = os.path.join(ROOT, rel)
        files[rel] = {
            'exists': os.path.exists(path),
            'sha256': sha256(path) if os.path.isfile(path) else None,
        }
    snapshots = {}
    for name, spec in SNAPSHOTS.items():
        path = os.path.join(ROOT, spec['path'])
        actual = sha256(path) if os.path.isfile(path) else None
        snapshots[name] = dict(spec, exists=os.path.isfile(path), actual_sha256=actual,
                               matches=(actual == spec['sha256']))

    payload = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'pipeline': 'RESEARCH_PIPELINE_FIXED.md',
        'fixed_leg_root': 'fixed_diagnosis/_sweep_pct25',
        'pct_per_pair': 0.25,
        'capital': 1000000,
        'momentum': {
            'lookback_days': 84,
            'step': 0.40,
            'weight_bounds': [0.10, 0.90],
            'initial_weight_A': 0.50,
        },
        'locked_pair': [
            'sp500-12m/cross_sector_slide1m_noscreen',
            'sp500-2m/cross_sector_slide3m_bd7',
        ],
        'price_snapshots': snapshots,
        'selection': {
            'status': 'locked_quantitative_selection',
            'pair_universe': 496,
            'leg_universe': 32,
            'recent_starts': 5,
            'historical_starts': 1,
            'consensus_rule': 'top 20 by separate score, rank-average, and joined Sharpe in both mechanisms',
            'human_criteria_applied': False,
        },
        'commands': COMMANDS,
        'inputs': files,
        'original_pipeline_preserved': True,
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)
        f.write('\n')
    print('wrote', OUT)


if __name__ == '__main__':
    main()
