import json
from pathlib import Path

from research.portfolio_selection import load_config, load_score_table, rank_pairs, select_consensus
from scripts.build_public_artifacts import collect_metrics


ROOT = Path(__file__).resolve().parents[1]


def test_collect_metrics_flattens_combined_summary(tmp_path):
    root = tmp_path / "combined" / "recent"
    root.mkdir(parents=True)
    (root / "metrics.json").write_text(
        json.dumps(
            {
                "window": "recent",
                "n_starts": 5,
                "mechanisms": {
                    "A": {
                        "ann_ret": 0.1,
                        "ann_vol": 0.08,
                        "sharpe": 1.2,
                        "mdd": -0.05,
                        "rejected_entries": 0,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    result = collect_metrics(tmp_path / "combined")
    assert result.iloc[0]["sharpe"] == 1.2
    assert result.iloc[0]["n_starts"] == 5


def test_selected_pair_is_rank_one_in_both_mechanisms():
    config = load_config(ROOT / "research" / "selected_book_config.json")
    ranked = rank_pairs(
        load_score_table(ROOT / "results" / "final" / "rankings" / "clean40_pair_scores.csv")
    )

    assert ranked.groupby("mechanism").size().to_dict() == {"A": 496, "B": 496}
    selected = select_consensus(ranked, config)
    assert selected["mechanism"].tolist() == ["A", "B"]
    assert selected[["score_rank", "rank_avg_rank", "joined_rank"]].to_numpy().tolist() == [
        [1, 1, 1],
        [1, 1, 1],
    ]


def test_manifest_records_hashed_relative_public_artifacts():
    manifest_path = ROOT / "results" / "final" / "manifest.json"
    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)

    assert manifest["schema_version"] == 2
    assert manifest["source_revision"]
    assert manifest["event_replay"]["input_file_count"] == 60
    assert manifest["selection"]["rankings"]["rows"] == 992
    assert manifest["selection"]["selected_pair"]["rows"] == 2
    paths = [
        manifest["config"]["path"],
        manifest["selection"]["score_source"]["path"],
        manifest["selection"]["rankings"]["path"],
        manifest["selection"]["selected_pair"]["path"],
        manifest["event_replay"]["input_root"],
        manifest["artifacts"]["metrics"]["path"],
        manifest["artifacts"]["factors"]["csv"]["path"],
        manifest["artifacts"]["factors"]["markdown"]["path"],
        manifest["artifacts"]["factors"]["snapshot_metadata"]["path"],
        manifest["artifacts"]["factors"]["snapshot"]["path"],
        *(item["path"] for item in manifest["artifacts"]["figures"]),
    ]
    assert all(not Path(path).is_absolute() for path in paths)
    assert all(len(entry["sha256"]) == 64 for entry in [
        manifest["selection"]["score_source"],
        manifest["selection"]["rankings"],
        manifest["selection"]["selected_pair"],
        manifest["artifacts"]["metrics"],
        manifest["artifacts"]["factors"]["csv"],
        manifest["artifacts"]["factors"]["markdown"],
        manifest["artifacts"]["factors"]["snapshot_metadata"],
        manifest["artifacts"]["factors"]["snapshot"],
        *manifest["artifacts"]["figures"],
    ])
