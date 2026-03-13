"""Tests for `insights/snapshot_builder.py`."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from insights.schema_version import ANALYSIS_SCHEMA_VERSION
from insights.snapshot_builder import build_analysis_snapshot


def _mock_commit(hexsha: str, when: datetime, files: list[str]) -> MagicMock:
    commit = MagicMock()
    commit.hexsha = hexsha
    commit.committed_datetime = when
    commit.stats.files = {file_path: {} for file_path in files}
    return commit


def test_build_analysis_snapshot_is_deterministic_and_counts_files():
    repo = MagicMock()
    repo.working_tree_dir = "/example/repo"

    older = _mock_commit(
        hexsha="a" * 40,
        when=datetime(2026, 1, 1, tzinfo=timezone.utc),
        files=["src/a.py", "src/b.py"],
    )
    newer = _mock_commit(
        hexsha="b" * 40,
        when=datetime(2026, 1, 2, tzinfo=timezone.utc),
        files=["src/a.py"],
    )

    with patch(
        "insights.snapshot_builder.get_commits_for_period",
        return_value=[newer, older],
    ):
        snapshot = build_analysis_snapshot(
            repo=repo,
            period_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            period_end=datetime(2026, 1, 31, tzinfo=timezone.utc),
        )

    assert snapshot.schema_version == ANALYSIS_SCHEMA_VERSION
    assert snapshot.total_commits == 2
    assert snapshot.file_commit_counts == {"src/a.py": 2, "src/b.py": 1}
    assert snapshot.file_recent_commits["src/a.py"] == ["aaaaaaa", "bbbbbbb"]
    assert snapshot.file_recent_commits["src/b.py"] == ["aaaaaaa"]


def test_build_analysis_snapshot_respects_max_evidence_commits_per_file():
    repo = MagicMock()
    repo.working_tree_dir = "/example/repo"
    commits = [
        _mock_commit(
            hexsha="a" * 40,
            when=datetime(2026, 1, 1, tzinfo=timezone.utc),
            files=["src/a.py"],
        ),
        _mock_commit(
            hexsha="b" * 40,
            when=datetime(2026, 1, 2, tzinfo=timezone.utc),
            files=["src/a.py"],
        ),
        _mock_commit(
            hexsha="c" * 40,
            when=datetime(2026, 1, 3, tzinfo=timezone.utc),
            files=["src/a.py"],
        ),
    ]

    with patch(
        "insights.snapshot_builder.get_commits_for_period",
        return_value=commits,
    ):
        snapshot = build_analysis_snapshot(
            repo=repo,
            period_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            period_end=datetime(2026, 1, 31, tzinfo=timezone.utc),
            max_evidence_commits_per_file=2,
        )

    assert snapshot.file_commit_counts["src/a.py"] == 3
    assert snapshot.file_recent_commits["src/a.py"] == ["aaaaaaa", "bbbbbbb"]
