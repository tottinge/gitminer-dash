"""Tests narrative output mode in `insights/cli.py`."""

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


class _ValidNarrativeClient:
    def generate_narrative(self, prompt_payload):
        return (
            "src/a.py changed frequently "
            "[file:src/a.py] [metric:commit_count=3]"
        )


class _InvalidNarrativeClient:
    def generate_narrative(self, prompt_payload):
        return "src/a.py changed frequently without evidence refs."


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


def test_main_returns_strict_narrative_when_citations_validate(capsys):
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with (
        patch("insights.cli.Repo", return_value=mock_repo),
        patch("insights.cli.build_analysis_snapshot", return_value=_snapshot()),
        patch("insights.cli.build_insight_report", return_value=_report()),
        patch(
            "insights.cli.get_llm_client",
            return_value=_ValidNarrativeClient(),
        ),
    ):
        exit_code = main(
            [
                ".",
                "--from",
                "2026-01-01",
                "--to",
                "2026-01-31",
                "--narrative",
                "--strict-citations",
            ]
        )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["narrative"]["status"] == "passed"
    assert payload["narrative"]["citation_validation"]["passed"] is True
    assert "[file:src/a.py]" in payload["narrative"]["text"]


def test_main_returns_report_when_strict_narrative_fails_validation(capsys):
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with (
        patch("insights.cli.Repo", return_value=mock_repo),
        patch("insights.cli.build_analysis_snapshot", return_value=_snapshot()),
        patch("insights.cli.build_insight_report", return_value=_report()),
        patch(
            "insights.cli.get_llm_client",
            return_value=_InvalidNarrativeClient(),
        ),
    ):
        exit_code = main(
            [
                ".",
                "--from",
                "2026-01-01",
                "--to",
                "2026-01-31",
                "--narrative",
                "--strict-citations",
            ]
        )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report"]["hotspots"][0]["file_path"] == "src/a.py"
    assert payload["narrative"]["status"] == "failed"
    assert payload["narrative"]["citation_validation"]["passed"] is False
    assert "text" not in payload["narrative"]


def test_main_requires_narrative_flag_for_strict_citations():
    with pytest.raises(SystemExit) as caught:
        main(
            [
                ".",
                "--from",
                "2026-01-01",
                "--to",
                "2026-01-31",
                "--strict-citations",
            ]
        )

    assert caught.value.code == 2
