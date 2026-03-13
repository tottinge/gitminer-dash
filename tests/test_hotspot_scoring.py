"""Tests for `insights/hotspot_scoring.py`."""

from insights.hotspot_scoring import rank_hotspots
from insights.models import AnalysisSnapshot


def test_rank_hotspots_orders_by_score_then_file_path():
    snapshot = AnalysisSnapshot(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=5,
        file_commit_counts={"z.py": 2, "a.py": 2, "b.py": 1},
        file_recent_commits={
            "a.py": ["1111111"],
            "z.py": ["2222222"],
            "b.py": ["3333333"],
        },
    )

    hotspots = rank_hotspots(snapshot=snapshot, top_n=2)

    assert [item.file_path for item in hotspots] == ["a.py", "z.py"]
    assert [item.score for item in hotspots] == [2.0, 2.0]
    assert len(hotspots[0].evidence) >= 2
    assert hotspots[0].evidence[0].kind == "file"
    assert hotspots[0].evidence[1].kind == "metric"


def test_rank_hotspots_returns_empty_for_non_positive_top_n():
    snapshot = AnalysisSnapshot(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=1,
        file_commit_counts={"a.py": 1},
        file_recent_commits={"a.py": ["1111111"]},
    )

    assert rank_hotspots(snapshot=snapshot, top_n=0) == []


def test_rank_hotspots_defaults_to_top_five():
    snapshot = AnalysisSnapshot(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=7,
        file_commit_counts={
            "a.py": 7,
            "b.py": 6,
            "c.py": 5,
            "d.py": 4,
            "e.py": 3,
            "f.py": 2,
        },
        file_recent_commits={
            "a.py": ["aaaaaaa"],
            "b.py": ["bbbbbbb"],
            "c.py": ["ccccccc"],
            "d.py": ["ddddddd"],
            "e.py": ["eeeeeee"],
            "f.py": ["fffffff"],
        },
    )

    hotspots = rank_hotspots(snapshot=snapshot)

    assert len(hotspots) == 5
    assert [item.file_path for item in hotspots] == [
        "a.py",
        "b.py",
        "c.py",
        "d.py",
        "e.py",
    ]
