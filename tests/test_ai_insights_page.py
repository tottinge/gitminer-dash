"""Tests for `pages/ai_insights.py`."""

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


@pytest.fixture
def populate_insights():
    """Import and return the AI insights callback with register_page mocked."""
    with patch("dash.register_page"):
        from pages.ai_insights import populate_insights as callback_fn

        return callback_fn


@pytest.fixture
def store_data():
    return {
        "period": "Last 30 days",
        "begin": "2026-01-01T00:00:00+00:00",
        "end": "2026-01-31T23:59:59+00:00",
    }


@patch("pages.ai_insights.repo_context.get_repo")
@patch("pages.ai_insights.build_analysis_snapshot")
@patch("pages.ai_insights.build_insight_report")
def test_populate_insights_returns_rows_and_status(
    mock_build_report,
    mock_build_snapshot,
    mock_get_repo,
    store_data,
    populate_insights,
):
    mock_repo = MagicMock()
    mock_get_repo.return_value = mock_repo
    snapshot = AnalysisSnapshot(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T23:59:59+00:00",
        total_commits=4,
        file_commit_counts={"src/a.py": 4},
        file_recent_commits={"src/a.py": ["aaaaaaa"]},
    )
    mock_build_snapshot.return_value = snapshot
    mock_build_report.return_value = InsightReport(
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

    rows, status = populate_insights(store_data)

    assert len(rows) == 1
    assert rows[0]["rank"] == 1
    assert rows[0]["file_path"] == "src/a.py"
    assert "file:src/a.py" in rows[0]["evidence_refs"]
    assert status == "1 evidence-backed hotspots in selected period."
    called = mock_build_snapshot.call_args.kwargs
    assert called["period_start"].isoformat() == store_data["begin"]
    assert called["period_end"].isoformat() == store_data["end"]


@patch("pages.ai_insights.repo_context.get_repo")
@patch("pages.ai_insights.build_analysis_snapshot")
@patch("pages.ai_insights.build_insight_report")
def test_populate_insights_empty_state(
    mock_build_report,
    mock_build_snapshot,
    mock_get_repo,
    store_data,
    populate_insights,
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

    rows, status = populate_insights(store_data)

    assert rows == []
    assert status == "No evidence-backed hotspots in selected period."


def test_populate_insights_prevent_update_for_missing_store(populate_insights):
    with pytest.raises(PreventUpdate):
        populate_insights(None)
