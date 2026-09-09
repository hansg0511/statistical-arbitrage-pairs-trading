"""Command-line configuration for the canonical research experiment runner."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from src.config import BACKTEST_SETTINGS, FOLD_SETTINGS, MARGIN_SETTINGS, STRATEGY_PARAMS


_SECTION_ALIASES = {
    "data": {
        "universe": "universe",
        "price_snapshot": "price_snapshot",
        "pool_path": "pool_path",
    },
    "walk_forward": {
        "selection_months": "sel_months",
        "test_months": "test_months",
        "slide_months": "slide_months",
    },
    "strategy": {
        "entry_z": "entry_z",
        "exit_z": "exit_z",
        "stop_z": "stop_z",
        "resid_val": "resid_val",
        "z_m": "z_m",
        "hr_thresh": "hr_thresh",
        "max_holding_days": "max_holding_days",
        "pvalue": "pvalue",
        "log_space": "log_space",
        "fixed_params": "fixed_params",
    },
    "portfolio": {
        "initial_cash": "initial_cash",
        "pct_per_pair": "pct_per_pair",
        "max_pairs": "max_pairs",
        "dollar_neutral": "dollar_neutral",
        "broker_leverage": "broker_leverage",
    },
    "risk": {
        "earnings_screen": "earnings_screen",
        "earnings_cache": "earnings_cache",
        "earnings_block_days": "earnings_block_days",
        "margin_behavior": "margin_behavior",
        "margin_long": "margin_long",
        "margin_short": "margin_short",
        "maintenance_long": "maintenance_long",
        "maintenance_short": "maintenance_short",
        "margin_rates": "margin_rates",
    },
    "output": {"directory": "output"},
}


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML experiment file and normalize its optional sections."""
    with open(path, encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"experiment config must be a mapping: {path}")

    values: dict[str, Any] = {}
    for key, value in raw.items():
        if key in _SECTION_ALIASES:
            if not isinstance(value, dict):
                if len(_SECTION_ALIASES[key]) == 1:
                    values[next(iter(_SECTION_ALIASES[key].values()))] = value
                else:
                    raise ValueError(f"config section {key!r} must be a mapping")
            else:
                for nested_key, nested_value in value.items():
                    attr = _SECTION_ALIASES[key].get(nested_key)
                    if attr:
                        values[attr] = nested_value
        elif key == "name":
            values["name"] = value
        else:
            values[key] = value
    return values


def _provided_options(parser: argparse.ArgumentParser, argv: list[str]) -> set[str]:
    """Return destinations explicitly supplied on the command line."""
    provided = set()
    for action in parser._actions:
        if action.dest == "help":
            continue
        if any(option in argv for option in action.option_strings):
            provided.add(action.dest)
    return provided


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI flags, applying YAML values before explicit CLI overrides."""
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        description="Run the deterministic walk-forward pairs-trading experiment"
    )
    parser.add_argument("--config", type=str, help="YAML experiment configuration")
    parser.add_argument("--name", type=str, default="experiment")
    parser.add_argument("--start", type=str, default="2023-01-01")
    parser.add_argument("--end", type=str, default="2026-01-01")
    parser.add_argument("--universe", choices=["core", "sp500"], default="sp500")
    parser.add_argument("--cross-sector", action="store_true", dest="cross_sector")
    parser.add_argument("--same-sector", action="store_false", dest="cross_sector")
    parser.set_defaults(cross_sector=False)

    parser.add_argument("--entry-z", type=float, dest="entry_z", default=STRATEGY_PARAMS["entry_z"])
    parser.add_argument("--exit-z", type=float, dest="exit_z", default=STRATEGY_PARAMS["exit_z"])
    parser.add_argument("--stop-z", type=float, dest="stop_z", default=STRATEGY_PARAMS["stop_z"])
    parser.add_argument("--resid-val", type=int, dest="resid_val", default=STRATEGY_PARAMS["resid_val"])
    parser.add_argument("--z-m", type=float, dest="z_m", default=STRATEGY_PARAMS["z_m"])
    parser.add_argument("--hr-thresh", type=float, dest="hr_thresh", default=STRATEGY_PARAMS["hr_thresh"])
    parser.add_argument(
        "--max-holding-days",
        type=int,
        dest="max_holding_days",
        default=STRATEGY_PARAMS["max_holding_days"],
    )
    parser.add_argument("--pvalue", type=float, default=STRATEGY_PARAMS["pvalue_threshold"])
    parser.add_argument("--log-space", action="store_true", dest="log_space", default=BACKTEST_SETTINGS["log_space"])
    parser.add_argument("--raw-space", action="store_false", dest="log_space")
    parser.add_argument("--fixed-params", action="store_true", default=False)

    parser.add_argument("--initial-cash", type=float, dest="initial_cash", default=BACKTEST_SETTINGS["initial_cash"])
    parser.add_argument("--pct-per-pair", type=float, dest="pct_per_pair", default=BACKTEST_SETTINGS["pct_per_pair"])
    parser.add_argument("--max-pairs", type=int, dest="max_pairs", default=BACKTEST_SETTINGS["max_pairs_per_fold"])
    parser.add_argument("--broker-leverage", type=float, dest="broker_leverage", default=1.0)
    parser.add_argument("--dollar-neutral", action="store_true", default=BACKTEST_SETTINGS["dollar_neutral"])
    parser.add_argument("--return-divergence", type=float, default=None)
    parser.add_argument("--sel-months", type=int, dest="sel_months", default=FOLD_SETTINGS["sel_months"])
    parser.add_argument("--test-months", type=int, dest="test_months", default=FOLD_SETTINGS["test_months"])
    parser.add_argument("--slide-months", type=int, dest="slide_months", default=FOLD_SETTINGS["slide_months"])

    parser.add_argument("--earnings-screen", action="store_true", default=False)
    parser.add_argument("--no-earnings-screen", action="store_false", dest="earnings_screen")
    parser.add_argument("--earnings-cache", type=str, default=None)
    parser.add_argument("--earnings-block-days", type=int, default=0)

    parser.add_argument("--margin-behavior", choices=["off", "report", "reject"], default=MARGIN_SETTINGS["margin_behavior"])
    parser.add_argument("--margin-long", type=float, default=MARGIN_SETTINGS["margin_long"])
    parser.add_argument("--margin-short", type=float, default=MARGIN_SETTINGS["margin_short"])
    parser.add_argument("--maintenance-long", type=float, default=MARGIN_SETTINGS["maintenance_long"])
    parser.add_argument("--maintenance-short", type=float, default=MARGIN_SETTINGS["maintenance_short"])
    parser.add_argument("--margin-rates", type=str, default=None)

    parser.add_argument("--pool-path", type=str, default=None)
    parser.add_argument("--price-snapshot", type=str, default=None)
    parser.add_argument("--write-price-snapshot", type=str, default=None)
    parser.add_argument("--no-warmup", action="store_true")
    parser.add_argument("--market-invest", action="store_true", default=False)
    parser.add_argument("--spy-cost-bps", type=float, default=1.0)
    parser.add_argument("--output", type=str, default="results/runs/experiment")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args(argv)
    provided = _provided_options(parser, argv)
    if args.config:
        config_values = load_config(args.config)
        for attr, value in config_values.items():
            if hasattr(args, attr) and attr not in provided:
                setattr(args, attr, value)
                provided.add(attr)
    if args.price_snapshot and args.write_price_snapshot:
        parser.error("--price-snapshot and --write-price-snapshot are mutually exclusive")
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    args._provided = provided
    return args
