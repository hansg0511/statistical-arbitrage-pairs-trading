"""Build compact public artifacts from tracked source inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd

if __package__ in {None, ""}:  # Support both `python scripts/...` and `python -m ...`.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.portfolio_selection import (
    DEFAULT_RANKINGS,
    DEFAULT_SELECTED,
    DEFAULT_SCORES,
    write_selection_artifacts,
)
from research.run_combined_backtest import DEFAULT_CONFIG, load_selected_book_config


def _relative(path: str | Path) -> str:
    return Path(os.path.relpath(path, Path.cwd())).as_posix()


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_sha256(root: str | Path) -> tuple[int, str]:
    root = Path(root)
    if not root.is_dir():
        raise FileNotFoundError(f"public input directory not found: {root}")
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return len(files), digest.hexdigest()


def _source_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable in clean export"


def collect_metrics(combined_root: str | Path) -> pd.DataFrame:
    rows = []
    root = Path(combined_root)
    for metrics_path in sorted(root.glob("*/metrics.json")):
        payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        for mechanism, values in payload.get("mechanisms", {}).items():
            rows.append(
                {
                    "window": payload["window"],
                    "mechanism": mechanism,
                    "n_starts": payload["n_starts"],
                    "ann_ret": values["ann_ret"],
                    "ann_vol": values["ann_vol"],
                    "sharpe": values["sharpe"],
                    "mdd": values["mdd"],
                    "rejected_entries": values["rejected_entries"],
                }
            )
    if not rows:
        raise FileNotFoundError(f"no combined summary metrics found under {root}")
    return pd.DataFrame(rows).sort_values(["window", "mechanism"])


def _required_public_files(output: Path) -> list[Path]:
    return [
        output / "factors" / "selected_book.csv",
        output / "factors" / "selected_book.md",
        output / "factors" / "ff_daily_2015_2025.csv",
        output / "factors" / "ff_daily_2015_2025.json",
        output / "figures" / "pair_equity_recent.png",
        output / "figures" / "pair_equity_historical.png",
        output / "figures" / "weightA_recent.png",
    ]


def build_public_artifacts(
    config_path=DEFAULT_CONFIG,
    combined_root="results/final/combined",
    ranking_source=DEFAULT_SCORES,
    output_root="results/final",
):
    config = load_selected_book_config(config_path)
    output = Path(output_root)
    rankings_path = output / "rankings" / DEFAULT_RANKINGS.name
    selected_path = output / "rankings" / DEFAULT_SELECTED.name
    ranked, selected = write_selection_artifacts(
        config_path,
        ranking_source,
        rankings_path,
        selected_path,
    )

    metrics = collect_metrics(combined_root)
    metrics_path = output / "metrics" / "selected_book_metrics.csv"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(metrics_path, index=False)

    missing = [path for path in _required_public_files(output) if not path.is_file()]
    if missing:
        paths = ", ".join(_relative(path) for path in missing)
        raise FileNotFoundError(
            "public factors and figures must be generated before the manifest: " + paths
        )

    input_root = Path(config["event_replay"]["input_root"])
    input_count, input_hash = _tree_sha256(input_root)
    factor_metadata_path = output / "factors" / "ff_daily_2015_2025.json"
    factor_metadata = json.loads(factor_metadata_path.read_text(encoding="utf-8"))
    manifest_path = output / "manifest.json"
    manifest = {
        "schema_version": 2,
        "source_revision": _source_revision(),
        "config": {
            "path": _relative(config_path),
            "sha256": _sha256(config_path),
            "schema_version": config.get("schema_version"),
            "locked_on": config.get("locked_on"),
        },
        "selection": {
            "score_source": {
                "path": _relative(ranking_source),
                "sha256": _sha256(ranking_source),
            },
            "rankings": {
                "path": _relative(rankings_path),
                "sha256": _sha256(rankings_path),
                "rows": len(ranked),
            },
            "selected_pair": {
                "path": _relative(selected_path),
                "sha256": _sha256(selected_path),
                "rows": len(selected),
            },
            "pair_count_per_mechanism": config["selection_evidence"]["pair_universe"],
            "criteria": [
                "separate_score = min(recent Sharpe, historical Sharpe)",
                "rank_average = mean of dense recent and historical Sharpe ranks",
                "joined_sharpe = Sharpe of joined historical and recent series",
                "selected pair is rank one under all criteria in mechanisms A and B",
            ],
            "generator": "research/portfolio_selection.py",
            "command": "python research/portfolio_selection.py",
        },
        "event_replay": {
            "input_root": _relative(input_root),
            "input_file_count": input_count,
            "input_tree_sha256": input_hash,
            "combined_output_root": config["event_replay"]["output_root"],
            "generator": "research/run_combined_backtest.py",
        },
        "artifacts": {
            "metrics": {
                "path": _relative(metrics_path),
                "sha256": _sha256(metrics_path),
            },
            "factors": {
                "csv": {
                    "path": _relative(output / "factors" / "selected_book.csv"),
                    "sha256": _sha256(output / "factors" / "selected_book.csv"),
                },
                "markdown": {
                    "path": _relative(output / "factors" / "selected_book.md"),
                    "sha256": _sha256(output / "factors" / "selected_book.md"),
                },
                "snapshot_metadata": {
                    "path": _relative(factor_metadata_path),
                    "sha256": _sha256(factor_metadata_path),
                },
                "snapshot": {
                    "path": _relative(output / "factors" / "ff_daily_2015_2025.csv"),
                    "sha256": _sha256(output / "factors" / "ff_daily_2015_2025.csv"),
                    "source": factor_metadata["source"],
                    "retrieved_at": factor_metadata["retrieved_at"],
                },
            },
            "figures": [
                {"path": _relative(path), "sha256": _sha256(path)}
                for path in _required_public_files(output)[4:]
            ],
        },
        "generation_commands": [
            "python research/portfolio_selection.py",
            "python research/run_combined_backtest.py --window recent --mechanism both",
            "python research/run_combined_backtest.py --window historical --mechanism both",
            "python research/factor_report.py",
            "python research/plot_public_results.py",
            "python scripts/build_public_artifacts.py",
        ],
        "code_paths": [
            "research/selected_book_config.json",
            "research/portfolio_selection.py",
            "research/run_combined_backtest.py",
            "research/factor_report.py",
            "research/plot_public_results.py",
            "scripts/build_public_artifacts.py",
        ],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {metrics_path}")
    print(f"Wrote {rankings_path}")
    print(f"Wrote {selected_path}")
    print(f"Wrote {manifest_path}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--combined-root", default="results/final/combined")
    parser.add_argument("--ranking-source", default=str(DEFAULT_SCORES))
    parser.add_argument("--output-root", default="results/final")
    args = parser.parse_args(argv)
    build_public_artifacts(
        args.config,
        args.combined_root,
        args.ranking_source,
        args.output_root,
    )


if __name__ == "__main__":
    main()
