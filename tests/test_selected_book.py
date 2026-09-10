import json
from pathlib import Path

import pytest

from research.run_combined_backtest import leg_specs, load_selected_book_config


ROOT = Path(__file__).resolve().parents[1]


def test_selected_book_is_locked_and_has_one_pair():
    path = ROOT / "research" / "selected_book_config.json"
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)

    assert config["status"] == "locked"
    assert config["schema_version"] == 2
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
    assert Path(specs["A"][0]).as_posix() == (
        "results/final/event_replay_inputs/recent/start_01/A"
    )
    assert config["event_replay"]["output_root"] == "results/final/combined"


def test_configured_replay_inputs_are_complete():
    config = load_selected_book_config(ROOT / "research" / "selected_book_config.json")
    input_root = ROOT / config["event_replay"]["input_root"]
    required = (
        "daily_returns.csv",
        "metrics.json",
        "oos_fold_summary.csv",
        "trade_marks.csv",
        "trade_logs/test_trade_log.csv",
    )

    for window in config["event_replay"]["windows"].values():
        for start in window["starts"]:
            for relative_path in start.values():
                run_dir = input_root / relative_path
                for filename in required:
                    assert (run_dir / filename).is_file(), run_dir / filename


def test_config_records_generation_and_execution_assumptions():
    config = load_selected_book_config(ROOT / "research" / "selected_book_config.json")
    generation = config["leg_generation"]
    assert generation["leg_a"] == {
        "pool": "sp500_12m",
        "selection_months": 12,
        "slide_months": 1,
        "earnings_screen": False,
        "earnings_block_days": 0,
    }
    assert generation["leg_b"] == {
        "pool": "sp500_2m",
        "selection_months": 2,
        "slide_months": 3,
        "earnings_screen": True,
        "earnings_block_days": 7,
    }
    assert generation["shared"]["strategy"]["max_holding_days"] == 15
    assert generation["shared"]["strategy"]["max_holding_unit"] == "calendar_days"
    assert config["execution_assumptions"]["margin_behavior"] == "off"
    assert config["execution_assumptions"]["broker_leverage"] == 100.0


def test_selected_book_requires_calendar_holding_unit(tmp_path):
    source = ROOT / "research" / "selected_book_config.json"
    with source.open(encoding="utf-8") as handle:
        config = json.load(handle)
    config["leg_generation"]["shared"]["strategy"]["max_holding_unit"] = (
        "trading_sessions"
    )
    path = tmp_path / "selected_book_config.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(ValueError, match="max_holding_unit"):
        load_selected_book_config(path)


def test_public_replay_metadata_does_not_publish_price_paths():
    config = load_selected_book_config(ROOT / "research" / "selected_book_config.json")
    input_root = ROOT / config["event_replay"]["input_root"]
    for window in config["event_replay"]["windows"].values():
        for start in window["starts"]:
            for relative_path in start.values():
                metrics_path = input_root / relative_path / "metrics.json"
                with metrics_path.open(encoding="utf-8") as handle:
                    payload = json.load(handle)
                assert payload["price_snapshot"] is None
                assert payload["price_snapshot_mode"] == "not_published"
