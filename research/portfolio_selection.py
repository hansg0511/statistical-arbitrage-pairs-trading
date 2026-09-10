"""Reproduce the locked portfolio selection from compact public score inputs.

The score table is a pinned public snapshot of the corrected all-496 evaluation.
This module recomputes the dense ranks and writes both the full ranking evidence
and the selected-pair extract. It deliberately does not read legacy directories.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "research" / "selected_book_config.json"
DEFAULT_SCORES = ROOT / "results" / "final" / "rankings" / "clean40_pair_scores.csv"
DEFAULT_RANKINGS = ROOT / "results" / "final" / "rankings" / "clean40_pair_rankings.csv"
DEFAULT_SELECTED = ROOT / "results" / "final" / "rankings" / "clean40_selected_pair.csv"

MECHANISMS = ("A", "B")
RANK_COLUMNS = ("recent_rank", "hist_rank", "rank_avg", "score_rank",
                "rank_avg_rank", "joined_rank")
SCORE_COLUMNS = ("recent_sh", "recent_ret", "recent_vol", "recent_mdd",
                 "hist_sh", "hist_ret", "hist_vol", "hist_mdd",
                 "joined_sh", "joined_ret", "rejected_entries")


def _pair_key(left: str, right: str) -> frozenset[str]:
    return frozenset((str(left), str(right)))


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        config = json.load(handle)
    if config.get("status") != "locked":
        raise ValueError(f"selected book config is not locked: {path}")
    return config


def load_score_table(path: str | Path = DEFAULT_SCORES) -> pd.DataFrame:
    """Load and validate the pinned score snapshot.

    Rank columns are intentionally rejected so the output cannot silently reuse
    ranks copied from an older generation.
    """
    frame = pd.read_csv(path)
    required = {"mechanism", "A", "B", *SCORE_COLUMNS}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"score table is missing columns: {sorted(missing)}")
    present_ranks = set(RANK_COLUMNS).intersection(frame.columns)
    if present_ranks:
        raise ValueError(
            "score table must contain raw scores, not precomputed rank columns: "
            f"{sorted(present_ranks)}"
        )

    frame = frame.copy()
    frame["mechanism"] = frame["mechanism"].astype(str)
    if set(frame["mechanism"]) != set(MECHANISMS):
        raise ValueError(f"expected mechanisms {MECHANISMS}, got {sorted(frame['mechanism'].unique())}")

    numeric = list(SCORE_COLUMNS)
    values = frame[numeric].apply(pd.to_numeric, errors="coerce")
    if values.isna().any().any() or not np.isfinite(values.to_numpy()).all():
        raise ValueError("score table contains non-finite numeric values")
    frame[numeric] = values

    for mechanism in MECHANISMS:
        subset = frame[frame["mechanism"] == mechanism]
        if len(subset) != 496:
            raise ValueError(
                f"expected 496 pairs for mechanism {mechanism}, got {len(subset)}"
            )
        keys = subset.apply(lambda row: _pair_key(row["A"], row["B"]), axis=1)
        if keys.duplicated().any():
            raise ValueError(f"duplicate unordered pair in mechanism {mechanism}")
        if any(row["A"] == row["B"] for _, row in subset.iterrows()):
            raise ValueError(f"self-pair in mechanism {mechanism}")

    return frame


def _dense_rank(values: pd.Series, reverse: bool = True) -> list[int]:
    ordered_values = [float(value) for value in values]
    order = sorted(range(len(ordered_values)), key=ordered_values.__getitem__, reverse=reverse)
    ranks = [0] * len(ordered_values)
    previous = None
    rank = 0
    for position, index in enumerate(order):
        value = ordered_values[index]
        if previous is None or abs(previous - value) > 1e-12:
            rank = position + 1
            previous = value
        ranks[index] = rank
    return ranks


def rank_pairs(scores: pd.DataFrame) -> pd.DataFrame:
    """Recompute the corrected dense ranks for every pair and mechanism."""
    ranked_frames = []
    for mechanism in MECHANISMS:
        frame = scores[scores["mechanism"] == mechanism].copy()
        frame["score"] = frame[["recent_sh", "hist_sh"]].min(axis=1)
        frame["recent_rank"] = _dense_rank(frame["recent_sh"], reverse=True)
        frame["hist_rank"] = _dense_rank(frame["hist_sh"], reverse=True)
        frame["rank_avg"] = (frame["recent_rank"] + frame["hist_rank"]) / 2
        frame["score_rank"] = _dense_rank(frame["score"], reverse=True)
        frame["rank_avg_rank"] = _dense_rank(frame["rank_avg"], reverse=False)
        frame["joined_rank"] = _dense_rank(frame["joined_sh"], reverse=True)
        ranked_frames.append(frame)

    base_columns = [column for column in scores.columns if column not in RANK_COLUMNS and column != "score"]
    output_columns = base_columns + ["score", *RANK_COLUMNS]
    return pd.concat(ranked_frames, ignore_index=True)[output_columns]


def select_consensus(ranked: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Return the configured pair and require rank one under every locked method."""
    target = _pair_key(
        config["pair"]["leg_a"]["path"], config["pair"]["leg_b"]["path"]
    )
    selected = ranked[
        ranked.apply(lambda row: _pair_key(row["A"], row["B"]) == target, axis=1)
    ].copy()
    if len(selected) != len(MECHANISMS):
        raise ValueError(f"selected pair must have one row per mechanism, got {len(selected)}")
    if not (selected[list(("score_rank", "rank_avg_rank", "joined_rank"))] == 1).all().all():
        raise ValueError("configured pair is not rank one under every locked criterion")
    return selected.sort_values("mechanism").reset_index(drop=True)


def write_selection_artifacts(
    config_path: str | Path = DEFAULT_CONFIG,
    scores_path: str | Path = DEFAULT_SCORES,
    rankings_path: str | Path = DEFAULT_RANKINGS,
    selected_path: str | Path = DEFAULT_SELECTED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate full ranking evidence and the selected-pair extract."""
    config = load_config(config_path)
    ranked = rank_pairs(load_score_table(scores_path))
    selected = select_consensus(ranked, config)
    rankings_path = Path(rankings_path)
    selected_path = Path(selected_path)
    rankings_path.parent.mkdir(parents=True, exist_ok=True)
    selected_path.parent.mkdir(parents=True, exist_ok=True)
    ranked.sort_values(["mechanism", "score_rank", "A", "B"]).to_csv(
        rankings_path, index=False
    )
    selected.to_csv(selected_path, index=False)
    return ranked, selected


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--scores", default=str(DEFAULT_SCORES))
    parser.add_argument("--rankings", default=str(DEFAULT_RANKINGS))
    parser.add_argument("--selected", default=str(DEFAULT_SELECTED))
    args = parser.parse_args(argv)
    ranked, selected = write_selection_artifacts(
        args.config, args.scores, args.rankings, args.selected
    )
    print(f"Ranked {len(ranked)} rows across {len(MECHANISMS)} mechanisms -> {args.rankings}")
    print(f"Selected {len(selected)} rows -> {args.selected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
