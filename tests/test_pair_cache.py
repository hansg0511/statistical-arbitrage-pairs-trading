import pickle

import pandas as pd
import pytest

from src.pair_cache import (
    PoolCache,
    PoolCacheError,
    filter_pairs_by_return_divergence,
)


SECTORS = {"Tech": ["AAA", "BBB"], "Energy": ["CCC"]}


def _pool_frame():
    return pd.DataFrame(
        [
            {
                "pair": "AAA-BBB",
                "cointegration_pvalue_log": 0.01,
                "half_life_log": 5.0,
            },
            {
                "pair": "AAA-CCC",
                "cointegration_pvalue_log": 0.01,
                "half_life_log": 5.0,
            },
            {
                "pair": "BBB-CCC",
                "cointegration_pvalue_log": 0.01,
                "half_life_log": -1.0,
            },
        ]
    )


def test_pool_hit_is_deterministic_and_respects_sector_filter(tmp_path):
    path = tmp_path / "pool.pkl"
    cache = PoolCache(path, {"return_divergence_applied": True})
    cache.set("2020-01-01", _pool_frame())
    cache.save()

    loaded = PoolCache(path)
    assert loaded.has("2020-01-01")
    cross = loaded.select("2020-01-01", "test", SECTORS, True)
    same = loaded.select("2020-01-01", "test", SECTORS, False)
    assert cross["pair"].tolist() == ["AAA-BBB", "AAA-CCC"]
    assert same["pair"].tolist() == ["AAA-BBB"]
    assert loaded.divergence_applied


def test_return_divergence_filter_is_explicit():
    prices = pd.DataFrame(
        {
            "AAA": [100.0, 110.0],
            "BBB": [100.0, 105.0],
            "CCC": [100.0, 130.0],
        },
        index=pd.to_datetime(["2020-01-01", "2020-01-02"]),
    )
    candidates = pd.DataFrame({"pair": ["AAA-BBB", "AAA-CCC"]})
    result = filter_pairs_by_return_divergence(
        candidates, prices, "2020-01-01", "2020-01-02", 0.10
    )
    assert result["pair"].tolist() == ["AAA-BBB"]


def test_empty_pool_is_a_valid_zero_pair_source(tmp_path):
    path = tmp_path / "empty.pkl"
    cache = PoolCache(path)
    cache.set("2020-01-01", pd.DataFrame(columns=["pair"]))
    cache.save()
    assert cache.select("2020-01-01", "test", SECTORS, True).empty


def test_missing_pool_is_not_a_hit(tmp_path):
    cache = PoolCache(tmp_path / "missing.pkl")
    assert not cache.has("2020-01-01")
    assert cache.get_pool("2020-01-01") is None


def test_corrupt_pool_fails_loudly(tmp_path):
    path = tmp_path / "corrupt.pkl"
    path.write_bytes(b"not a pickle")
    with pytest.raises(PoolCacheError):
        PoolCache(path)
