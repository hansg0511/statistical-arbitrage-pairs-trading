"""Guard the public V2 default without rewriting the archived V1 replay."""
import json
from pathlib import Path

from research.run_combined_backtest import load_selected_book_config

ROOT = Path(__file__).resolve().parents[1]


def test_default_describes_frozen_v2_book():
    cfg = load_selected_book_config()
    assert cfg["status"] == "locked"
    assert cfg["name"] == "v2_gross_exposure_clean40_selected_book"
    assert cfg["pair"]["leg_a"]["path"] == "sp500-12m/same_sector_slide1m_noscreen"
    assert cfg["pair"]["leg_b"]["path"] == "sp500-12m/same_sector_slide3m_noscreen"
    assert cfg["book"]["sizing_mode"] == "gross_exposure"
    assert cfg["momentum"] == {
        "lookback_days": 84,
        "step": 0.4,
        "weight_bounds": {"min": 0.1, "max": 0.9},
        "initial_weight_leg_a": 0.5,
    }
    assert cfg["leg_generation"]["leg_a"]["selection_months"] == 12
    assert cfg["leg_generation"]["leg_b"]["selection_months"] == 12
    assert cfg["leg_generation"]["leg_b"]["earnings_screen"] is False
    assert not cfg["event_replay"]["windows"]["recent"]["starts"]
    assert not cfg["event_replay"]["windows"]["historical"]["starts"]


def test_legacy_v1_archive_remains_distinct_and_usable():
    with (ROOT / "research" / "selected_book_v1_legacy.json").open(encoding="utf-8") as handle:
        v1 = json.load(handle)
    assert v1["status"] == "locked"
    assert v1["pair"]["leg_a"]["path"] == "sp500-12m/cross_sector_slide1m_noscreen"
    assert v1["pair"]["leg_b"]["path"] == "sp500-2m/cross_sector_slide3m_bd7"
    assert v1["event_replay"]["input_root"] == "results/final/event_replay_inputs"
    assert v1["event_replay"]["windows"]["recent"]["starts"]
