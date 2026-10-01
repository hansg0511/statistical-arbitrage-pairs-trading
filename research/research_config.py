"""Shared immutable configuration for the completed research artifacts."""

from __future__ import annotations


STARTS_2M = (
    "2023-11-01",
    "2023-12-01",
    "2024-01-01",
    "2024-02-01",
    "2024-03-01",
)

STARTS_12M = (
    "2023-01-01",
    "2023-02-01",
    "2023-03-01",
    "2023-04-01",
    "2023-05-01",
)


STRATEGIES = {
    "core-2m": {
        "universe": "core",
        "sel_months": 2,
        "pool": "core_2m.pkl",
        "recent_section": "06",
        "historical_section": "08a",
        "recent_starts": STARTS_2M,
        "historical_start": "2014-11-01",
        "recent_snapshot": "core_recent.pkl",
        "historical_snapshot": "core_historical.pkl",
    },
    "sp500-2m": {
        "universe": "sp500",
        "sel_months": 2,
        "pool": "sp500_2m.pkl",
        "recent_section": "07",
        "historical_section": "09a",
        "recent_starts": STARTS_2M,
        "historical_start": "2014-11-01",
        "recent_snapshot": "sp500_recent.pkl",
        "historical_snapshot": "sp500_historical.pkl",
    },
    "core-12m": {
        "universe": "core",
        "sel_months": 12,
        "pool": "sp500_12m.pkl",
        "recent_section": "10a",
        "historical_section": "08b",
        "recent_starts": STARTS_12M,
        "historical_start": "2014-01-01",
        "recent_snapshot": "core_recent_12m.pkl",
        "historical_snapshot": "core_historical_12m.pkl",
    },
    "sp500-12m": {
        "universe": "sp500",
        "sel_months": 12,
        "pool": "sp500_12m.pkl",
        "recent_section": "10b",
        "historical_section": "09b",
        "recent_starts": STARTS_12M,
        "historical_start": "2014-01-01",
        "recent_snapshot": "sp500_recent_12m.pkl",
        "historical_snapshot": "sp500_historical_12m.pkl",
    },
}
