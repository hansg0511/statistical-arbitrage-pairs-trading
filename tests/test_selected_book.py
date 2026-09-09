import json
from pathlib import Path


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
