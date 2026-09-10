from pathlib import Path

import numpy as np
import pandas as pd

from research.factor_report import build_factor_rows


ROOT = Path(__file__).resolve().parents[1]


def test_pinned_factor_report_matches_published_csv(monkeypatch):
    def fail_network(*args, **kwargs):
        raise AssertionError("network access")

    monkeypatch.setattr("src.fama_french.urlopen", fail_network)
    published = pd.read_csv(ROOT / "results" / "final" / "factors" / "selected_book.csv")
    regenerated = build_factor_rows(ROOT / "research" / "selected_book_config.json")

    assert regenerated[["window", "start_index", "mechanism"]].equals(
        published[["window", "start_index", "mechanism"]]
    )
    numeric = [column for column in published.columns if column not in {"window", "start_index", "mechanism"}]
    np.testing.assert_allclose(
        regenerated[numeric].to_numpy(dtype=float),
        published[numeric].to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-12,
    )
