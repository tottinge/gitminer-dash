"""Tests for `insights/cli.py`."""

import json
from unittest.mock import MagicMock, patch

import pytest

from insights.cli import main
from insights.models import EvidenceRef, HotspotCandidate, InsightReport


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
                "--repo",
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
                "--repo",
                ".",
                "--from",
                "2026-02-01",
                "--to",
                "2026-01-01",
            ]
        )

    assert caught.value.code == 2
