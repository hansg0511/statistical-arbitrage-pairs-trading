import pandas as pd

from src.pool_builder import build_selection_window, selection_windows


def test_selection_windows_are_month_stepped():
    assert selection_windows("2020-01-01", "2020-03-01", 2) == [
        ("2020-01-01", "2020-02-29"),
        ("2020-02-01", "2020-03-31"),
        ("2020-03-01", "2020-04-30"),
    ]


def test_pool_builder_applies_divergence_before_analysis(monkeypatch):
    dates = pd.date_range("2020-01-01", periods=30, freq="D")
    prices = pd.DataFrame(
        {
            "AAA": range(100, 130),
            "BBB": range(100, 130),
            "CCC": range(100, 160, 2),
        },
        index=dates,
        dtype=float,
    )
    calls = []

    def fake_analyze(left, right):
        calls.append((left.name, right.name))
        return {
            "cointegration_pvalue_log": 0.01,
            "half_life_log": 5.0,
        }

    monkeypatch.setattr("src.pool_builder.PairSelector.analyze_pair", fake_analyze)
    result = build_selection_window(
        prices,
        {"Tech": ["AAA", "BBB"], "Energy": ["CCC"]},
        ["AAA", "BBB", "CCC"],
        "2020-01-01",
        "2020-01-30",
        return_divergence=0.10,
    )

    assert result["pair"].tolist() == ["AAA-BBB"]
    assert calls == [("AAA", "BBB")]
