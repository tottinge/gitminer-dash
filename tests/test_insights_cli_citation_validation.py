"""Tests citation validation mode in `insights/cli.py`."""

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


def _snapshot() -> AnalysisSnapshot:
    return AnalysisSnapshot(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=3,
        file_commit_counts={"src/a.py": 3},
        file_recent_commits={"src/a.py": ["aaaaaaa"]},
    )


def _report() -> InsightReport:
    return InsightReport(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=3,
        hotspots=[
            HotspotCandidate(
                file_path="src/a.py",
                score=3.0,
                evidence=[
                    EvidenceRef(kind="file", value="src/a.py"),
                    EvidenceRef(kind="metric", value="commit_count=3"),
                    EvidenceRef(kind="commit", value="aaaaaaa"),
                ],
            )
        ],
    )


def test_main_validates_narrative_claims_against_report_evidence(
    capsys, tmp_path
):
    narrative_file = tmp_path / "narrative.txt"
    narrative_file.write_text(
        "src/a.py changed [file:src/a.py] [metric:commit_count=3]",
        encoding="utf-8",
    )
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with (
        patch("insights.cli.Repo", return_value=mock_repo),
        patch("insights.cli.build_analysis_snapshot", return_value=_snapshot()),
        patch("insights.cli.build_insight_report", return_value=_report()),
    ):
        exit_code = main(
            [
                ".",
                "--from",
                "2026-01-01",
                "--to",
                "2026-01-31",
                "--narrative-file",
                str(narrative_file),
                "--validate-citations",
            ]
        )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["citation_validation"]["passed"] is True
    assert payload["citation_validation"]["invalid_claims"] == []


def test_main_reports_invalid_or_uncited_claims(capsys, tmp_path):
    narrative_file = tmp_path / "narrative.txt"
    narrative_file.write_text(
        "claim with no citation\n"
        "claim with unknown citation [metric:commit_count=99]",
        encoding="utf-8",
    )
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with (
        patch("insights.cli.Repo", return_value=mock_repo),
        patch("insights.cli.build_analysis_snapshot", return_value=_snapshot()),
        patch("insights.cli.build_insight_report", return_value=_report()),
    ):
        exit_code = main(
            [
                ".",
                "--from",
                "2026-01-01",
                "--to",
                "2026-01-31",
                "--narrative-file",
                str(narrative_file),
                "--validate-citations",
            ]
        )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["citation_validation"]["passed"] is False
    assert payload["citation_validation"]["invalid_claims"] == [
        {
            "line": 1,
            "reason": "missing_citation",
            "claim": "claim with no citation",
        },
        {
            "line": 2,
            "reason": "unknown_citation",
            "claim": "claim with unknown citation [metric:commit_count=99]",
            "unknown_citations": ["metric:commit_count=99"],
        },
    ]


def test_main_requires_narrative_file_when_validate_citations_enabled():
    with pytest.raises(SystemExit) as caught:
        main(
            [
                ".",
                "--from",
                "2026-01-01",
                "--to",
                "2026-01-31",
                "--validate-citations",
            ]
        )

    assert caught.value.code == 2
