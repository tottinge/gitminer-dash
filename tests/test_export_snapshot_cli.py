"""Tests for `insights/export_snapshot_cli.py`."""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from insights.export_snapshot_cli import main
from insights.models import AnalysisSnapshot


def test_main_exports_snapshot_and_emits_metadata(capsys, tmp_path: Path):
    snapshot = AnalysisSnapshot(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=2,
        file_commit_counts={"src/a.py": 2},
        file_recent_commits={"src/a.py": ["aaaaaaa"]},
    )
    saved_path = tmp_path / "abcd1234.json"
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with (
        patch("insights.export_snapshot_cli.Repo", return_value=mock_repo),
        patch(
            "insights.export_snapshot_cli.build_analysis_snapshot",
            return_value=snapshot,
        ) as mock_build,
        patch(
            "insights.export_snapshot_cli.save_snapshot",
            return_value=saved_path,
        ) as mock_save,
    ):
        exit_code = main(
            [
                ".",
                "--from",
                "2026-01-01",
                "--to",
                "2026-01-31",
                "--snapshot-dir",
                str(tmp_path),
            ]
        )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["snapshot_path"] == str(saved_path)
    assert payload["schema_version"] == "1.0.0"
    assert payload["repo_path"] == "/example/repo"
    called = mock_build.call_args.kwargs
    assert called["period_start"].tzinfo is not None
    assert called["period_end"].tzinfo is not None
    mock_save.assert_called_once_with(snapshot=snapshot, snapshot_dir=tmp_path)


def test_main_rejects_invalid_period_order():
    with pytest.raises(SystemExit) as caught:
        main(
            [
                ".",
                "--from",
                "2026-02-01",
                "--to",
                "2026-01-01",
            ]
        )
    assert caught.value.code == 2


def test_main_rerun_with_same_inputs_keeps_snapshot_path(
    capsys, tmp_path: Path
):
    snapshot = AnalysisSnapshot(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=2,
        file_commit_counts={"src/a.py": 2},
        file_recent_commits={"src/a.py": ["aaaaaaa"]},
    )
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with (
        patch("insights.export_snapshot_cli.Repo", return_value=mock_repo),
        patch(
            "insights.export_snapshot_cli.build_analysis_snapshot",
            return_value=snapshot,
        ),
    ):
        first_exit = main(
            [
                ".",
                "--from",
                "2026-01-01",
                "--to",
                "2026-01-31",
                "--snapshot-dir",
                str(tmp_path),
            ]
        )
        first_payload = json.loads(capsys.readouterr().out)

        second_exit = main(
            [
                ".",
                "--from",
                "2026-01-01",
                "--to",
                "2026-01-31",
                "--snapshot-dir",
                str(tmp_path),
            ]
        )
        second_payload = json.loads(capsys.readouterr().out)

    assert first_exit == 0
    assert second_exit == 0
    assert first_payload["snapshot_path"] == second_payload["snapshot_path"]

    snapshot_file = Path(first_payload["snapshot_path"])
    assert snapshot_file.exists()
    file_payload = json.loads(snapshot_file.read_text(encoding="utf-8"))
    assert file_payload["schema_version"] == "1.0.0"
    assert file_payload["period_start"] == "2026-01-01T00:00:00+00:00"
    assert file_payload["period_end"] == "2026-01-31T00:00:00+00:00"
