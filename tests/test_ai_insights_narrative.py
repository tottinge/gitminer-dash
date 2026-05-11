"""Behavior-focused tests for strict narrative handling in `pages/ai_insights.py`."""

from tests import setup_path

setup_path()
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from dash.exceptions import PreventUpdate

from insights.models import (
    AnalysisSnapshot,
    EvidenceRef,
    HotspotCandidate,
    InsightReport,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class _StubNarrativeClient:
    def __init__(self, narrative_text: str) -> None:
        self._narrative_text = narrative_text

    def generate_narrative(self, prompt_payload):  # noqa: ANN001
        return self._narrative_text


@pytest.fixture
def ai_insights_module():
    with patch("dash.register_page"):
        import pages.ai_insights as module

        return module


def _report() -> InsightReport:
    return InsightReport(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T23:59:59+00:00",
        total_commits=4,
        hotspots=[
            HotspotCandidate(
                file_path="src/a.py",
                score=4.0,
                evidence=[
                    EvidenceRef(kind="file", value="src/a.py"),
                    EvidenceRef(kind="metric", value="commit_count=4"),
                ],
            )
        ],
    )


def test_strict_narrative_result_passes_with_valid_citations(
    ai_insights_module,
):
    narrative_text = (
        "src/a.py changed frequently " "[file:src/a.py] [metric:commit_count=4]"
    )
    with patch.object(
        ai_insights_module,
        "get_llm_client",
        return_value=_StubNarrativeClient(narrative_text),
    ):
        result = ai_insights_module._strict_narrative_result(_report())

    assert result["passed"] is True
    assert result["narrative_text"] == narrative_text
    assert result["invalid_claims"] == []


def test_strict_narrative_result_reports_invalid_claims(
    ai_insights_module,
):
    narrative_text = (
        "claim without citation\n" "claim with unknown [metric:commit_count=99]"
    )
    with patch.object(
        ai_insights_module,
        "get_llm_client",
        return_value=_StubNarrativeClient(narrative_text),
    ):
        result = ai_insights_module._strict_narrative_result(_report())

    assert result["passed"] is False
    assert result["narrative_text"] == ""
    assert len(result["invalid_claims"]) == 2
    assert result["invalid_claims"][0]["reason"] == "missing_citation"
    assert result["invalid_claims"][1]["reason"] == "unknown_citation"
    assert (
        "metric:commit_count=99"
        in result["invalid_claims"][1]["unknown_citations"]
    )


@patch("pages.ai_insights.repo_context.get_repo")
@patch("pages.ai_insights.build_analysis_snapshot")
@patch("pages.ai_insights.build_insight_report")
def test_populate_narrative_summary_empty_hotspots(
    mock_build_report,
    mock_build_snapshot,
    mock_get_repo,
    ai_insights_module,
):
    mock_get_repo.return_value = MagicMock()
    mock_build_snapshot.return_value = AnalysisSnapshot(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T23:59:59+00:00",
        total_commits=0,
        file_commit_counts={},
        file_recent_commits={},
    )
    mock_build_report.return_value = InsightReport(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T23:59:59+00:00",
        total_commits=0,
        hotspots=[],
    )
    store_data = {
        "period": "Last 30 days",
        "begin": "2026-01-01T00:00:00+00:00",
        "end": "2026-01-31T23:59:59+00:00",
    }

    status, narrative_text, invalid_claims = (
        ai_insights_module.populate_narrative_summary(store_data)
    )

    assert isinstance(status, str)
    assert narrative_text == ""
    assert invalid_claims == []


def test_populate_narrative_summary_missing_store_raises_prevent_update(
    ai_insights_module,
):
    with pytest.raises(PreventUpdate):
        ai_insights_module.populate_narrative_summary(None)
