"""Tests for `insights/cli.py`."""

import json
from unittest.mock import MagicMock, patch

import pytest

from insights.cli import main
from insights.models import (
    AnalysisSnapshot,
    EvidenceRef,
    HotspotCandidate,
    InsightReport,
)


def test_main_emits_report_json_and_passes_top_n(capsys):
    snapshot = MagicMock()
    report = InsightReport(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T23:59:59+00:00",
        total_commits=3,
        hotspots=[
            HotspotCandidate(
                file_path="src/a.py",
                score=2.0,
                evidence=[
                    EvidenceRef(kind="file", value="src/a.py"),
                    EvidenceRef(kind="metric", value="commit_count=2"),
                ],
            )
        ],
    )

    with (
        patch("insights.cli.Repo") as mock_repo_type,
        patch(
            "insights.cli.build_analysis_snapshot",
            return_value=snapshot,
        ) as mock_build_snapshot,
        patch(
            "insights.cli.build_insight_report",
            return_value=report,
        ) as mock_build_report,
    ):
        exit_code = main(
            [
                ".",
                "--from",
                "2026-01-01",
                "--to",
                "2026-01-31",
                "--top",
                "4",
            ]
        )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "1.0.0"
    assert payload["hotspots"][0]["file_path"] == "src/a.py"
    mock_repo_type.assert_called_once_with(".")
    called_kwargs = mock_build_snapshot.call_args.kwargs
    assert called_kwargs["period_start"].tzinfo is not None
    assert called_kwargs["period_end"].tzinfo is not None
    mock_build_report.assert_called_once_with(snapshot=snapshot, top_n=4)


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


def test_main_reuses_saved_snapshot_when_available(capsys):
    loaded_snapshot = AnalysisSnapshot(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=2,
        file_commit_counts={"src/a.py": 2},
        file_recent_commits={"src/a.py": ["aaaaaaa"]},
    )
    report = InsightReport(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=2,
        hotspots=[],
    )
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with (
        patch("insights.cli.Repo", return_value=mock_repo),
        patch(
            "insights.cli.load_snapshot",
            return_value=loaded_snapshot,
        ) as mock_load,
        patch("insights.cli.build_analysis_snapshot") as mock_build,
        patch("insights.cli.save_snapshot") as mock_save,
        patch(
            "insights.cli.build_insight_report",
            return_value=report,
        ) as mock_build_report,
    ):
        exit_code = main(
            [
                ".",
                "--from",
                "2026-01-01",
                "--to",
                "2026-01-31",
                "--save-snapshot",
            ]
        )

    assert exit_code == 0
    assert capsys.readouterr().out
    mock_load.assert_called_once()
    mock_build.assert_not_called()
    mock_save.assert_not_called()
    mock_build_report.assert_called_once_with(snapshot=loaded_snapshot, top_n=3)


def test_main_saves_snapshot_when_missing(capsys):
    built_snapshot = AnalysisSnapshot(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=2,
        file_commit_counts={"src/a.py": 2},
        file_recent_commits={"src/a.py": ["aaaaaaa"]},
    )
    report = InsightReport(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=2,
        hotspots=[],
    )
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with (
        patch("insights.cli.Repo", return_value=mock_repo),
        patch("insights.cli.load_snapshot", return_value=None),
        patch(
            "insights.cli.build_analysis_snapshot",
            return_value=built_snapshot,
        ) as mock_build,
        patch("insights.cli.save_snapshot") as mock_save,
        patch(
            "insights.cli.build_insight_report",
            return_value=report,
        ),
    ):
        exit_code = main(
            [
                ".",
                "--from",
                "2026-01-01",
                "--to",
                "2026-01-31",
                "--save-snapshot",
            ]
        )

    assert exit_code == 0
    assert capsys.readouterr().out
    mock_build.assert_called_once()
    mock_save.assert_called_once()
