import json
from pathlib import Path

from research.run_combined_backtest import leg_specs, load_selected_book_config


ROOT = Path(__file__).resolve().parents[1]


def test_selected_book_is_locked_and_has_one_pair():
    path = ROOT / "research" / "selected_book_config.json"
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)

    assert config["status"] == "locked"
    assert config["pair"]["leg_a"]["path"] == "sp500-12m/cross_sector_slide1m_noscreen"
    assert config["pair"]["leg_b"]["path"] == "sp500-2m/cross_sector_slide3m_bd7"
    assert config["momentum"] == {
        "lookback_days": 84,
        "step": 0.4,
        "weight_bounds": {"min": 0.1, "max": 0.9},
        "initial_weight_leg_a": 0.5,
    }
    assert config["book"]["pct_per_pair"] == 0.25


def test_combined_replay_uses_configured_inputs_and_output():
    config = load_selected_book_config(ROOT / "research" / "selected_book_config.json")
    specs = leg_specs(config, "recent")
    assert Path(specs["A"][0]).as_posix().endswith(
        "fixed_diagnosis/_sweep_pct25/10b/2023-01-01_cross_sector_slide1m_noscreen"
    )
    assert config["event_replay"]["output_root"] == "results/final/combined"
