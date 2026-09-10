"""Regenerate the compact public figures from shared-account replay output."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMBINED = ROOT / "results" / "final" / "combined"
DEFAULT_OUTPUT = ROOT / "results" / "final" / "figures"


def _daily_returns(path: Path) -> pd.Series:
    frame = pd.read_csv(path, parse_dates=["date"])
    required = {"date", "daily_return"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"replay output is missing columns: {sorted(missing)}: {path}")
    return frame.set_index("date")["daily_return"].astype(float)


def _equity(path: Path) -> pd.Series:
    return (1.0 + _daily_returns(path).fillna(0.0)).cumprod()


def _run_paths(combined_root: Path, window: str, mechanism: str) -> list[Path]:
    paths = sorted((combined_root / window).glob(f"start_*/{mechanism}/daily_returns.csv"))
    if not paths:
        raise FileNotFoundError(
            f"no {window} replay outputs found for mechanism {mechanism} under {combined_root}"
        )
    return paths


def _format_axis(axis) -> None:
    axis.grid(alpha=0.25)
    axis.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))


def plot_recent(combined_root: Path, output_root: Path) -> Path:
    figure, axis = plt.subplots(figsize=(13, 5.5))
    colors = {"A": "#1769aa", "B": "#b04a00"}
    for mechanism in ("A", "B"):
        for path in _run_paths(combined_root, "recent", mechanism):
            axis.plot(
                _equity(path),
                color=colors[mechanism],
                alpha=0.35,
                linewidth=1.0,
                label=f"Mechanism {mechanism} {path.parent.parent.name}",
            )
    axis.set_title("Recent selected-book shared-account replay")
    axis.set_ylabel("Growth of $1")
    _format_axis(axis)
    axis.legend(loc="best", fontsize=7, ncol=2)
    figure.tight_layout()
    path = output_root / "pair_equity_recent.png"
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_historical(combined_root: Path, output_root: Path) -> Path:
    figure, axis = plt.subplots(figsize=(11, 5.5))
    for mechanism, color in (("A", "#1769aa"), ("B", "#b04a00")):
        path = _run_paths(combined_root, "historical", mechanism)[0]
        axis.plot(
            _equity(path),
            color=color,
            linewidth=1.5,
            label=f"Mechanism {mechanism}",
        )
    axis.set_title("Historical selected-book shared-account replay")
    axis.set_ylabel("Growth of $1")
    _format_axis(axis)
    axis.legend(loc="best")
    figure.tight_layout()
    path = output_root / "pair_equity_historical.png"
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_weights(combined_root: Path, output_root: Path) -> Path:
    figure, axis = plt.subplots(figsize=(13, 4.5))
    paths = sorted((combined_root / "recent").glob("start_*/A/weight_path.csv"))
    if not paths:
        raise FileNotFoundError(f"no recent weight paths found under {combined_root}")
    for path in paths:
        frame = pd.read_csv(path, parse_dates=["date"])
        if "weight_A" not in frame.columns:
            raise ValueError(f"weight output is missing weight_A: {path}")
        axis.step(
            frame["date"],
            frame["weight_A"].astype(float),
            where="post",
            linewidth=1.1,
            alpha=0.8,
            label=path.parent.parent.name,
        )
    axis.axhline(0.5, color="gray", linestyle="--", linewidth=0.8)
    axis.set_ylim(0.05, 0.95)
    axis.set_title("Recent causal allocator weight on Leg A")
    axis.set_ylabel("Weight A")
    _format_axis(axis)
    axis.legend(loc="best", fontsize=8, ncol=3)
    figure.tight_layout()
    path = output_root / "weightA_recent.png"
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_public_results(
    combined_root: str | Path = DEFAULT_COMBINED,
    output_root: str | Path = DEFAULT_OUTPUT,
) -> list[Path]:
    combined_root = Path(combined_root)
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    return [
        plot_recent(combined_root, output_root),
        plot_historical(combined_root, output_root),
        plot_weights(combined_root, output_root),
    ]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--combined-root", default=str(DEFAULT_COMBINED))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)
    for path in plot_public_results(args.combined_root, args.output_root):
        print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
