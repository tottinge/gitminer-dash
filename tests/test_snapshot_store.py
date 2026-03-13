"""Tests for `insights/snapshot_store.py`."""

import json
from datetime import datetime, timezone
from pathlib import Path

from insights.models import AnalysisSnapshot
from insights.snapshot_store import (
    load_snapshot,
    save_snapshot,
    snapshot_path_for_inputs,
)


def test_snapshot_path_for_inputs_is_deterministic(tmp_path: Path):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 31, tzinfo=timezone.utc)

    path_one = snapshot_path_for_inputs(
        snapshot_dir=tmp_path,
        repo_path="/example/repo",
        period_start=start,
        period_end=end,
    )
    path_two = snapshot_path_for_inputs(
        snapshot_dir=tmp_path,
        repo_path="/example/repo",
        period_start=start,
        period_end=end,
    )
    different_path = snapshot_path_for_inputs(
        snapshot_dir=tmp_path,
        repo_path="/example/repo",
        period_start=start,
        period_end=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )

    assert path_one == path_two
    assert path_one != different_path


def test_save_and_load_snapshot_roundtrip(tmp_path: Path):
    snapshot = AnalysisSnapshot(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=2,
        file_commit_counts={"src/a.py": 2},
        file_recent_commits={"src/a.py": ["aaaaaaa"]},
    )

    saved_path = save_snapshot(snapshot=snapshot, snapshot_dir=tmp_path)
    assert saved_path.exists()

    payload = json.loads(saved_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0.0"

    loaded = load_snapshot(
        snapshot_dir=tmp_path,
        repo_path="/example/repo",
        period_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 1, 31, tzinfo=timezone.utc),
    )
    assert loaded == snapshot
