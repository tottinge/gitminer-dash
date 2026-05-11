"""Behavior tests for actionable evidence rows in `pages/ai_insights.py`."""

from tests import setup_path

setup_path()
import os
import sys
from unittest.mock import patch

import pytest

from insights.models import (
    AnalysisSnapshot,
    EvidenceRef,
    HotspotCandidate,
    InsightReport,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class _Remote:
    def __init__(self, name: str, url: str) -> None:
        self.name = name
        self.urls = [url]
        self.url = url


class _Repo:
    def __init__(self, remotes) -> None:
        self.remotes = remotes


def _hotspot(
    file_path: str, score: float, commit_count: int, commit_ref: str
) -> HotspotCandidate:
    return HotspotCandidate(
        file_path=file_path,
        score=score,
        evidence=[
            EvidenceRef(kind="file", value=file_path),
            EvidenceRef(kind="metric", value=f"commit_count={commit_count}"),
            EvidenceRef(kind="commit", value=commit_ref),
        ],
    )


@patch("dash.register_page")
def test_row_generates_actionable_links_and_structural_fields(_):
    import pages.ai_insights as module

    repo = _Repo(
        remotes=[_Remote("origin", "https://github.com/acme/example.git")]
    )
    row = module._row(
        rank=1,
        hotspot=_hotspot(
            file_path="pages/affinity_groups.py",
            score=27.0,
            commit_count=27,
            commit_ref="fadaacb",
        ),
        repo=repo,
        repo_path="/example/repo",
        previous_scores={"pages/affinity_groups.py": 20.0},
    )

    assert row["rank"] == 1
    assert row["file_path"] == "pages/affinity_groups.py"
    assert "file:///example/repo/pages/affinity_groups.py" in row["file_link"]
    assert row["commit_count"] == 27
    assert "github.com/acme/example/commit/fadaacb" in row["latest_commit_link"]
    assert row["score_delta"] == 7.0
    assert row["trend"] == "rising"
    assert "high_churn" in row["risk_reason"]
    assert "ui_orchestration_surface" in row["risk_reason"]
    assert row["suggested_action"] == "extract_service_boundary"


@patch("dash.register_page")
def test_row_uses_dependency_workflow_action_for_config_hotspot(_):
    import pages.ai_insights as module

    row = module._row(
        rank=1,
        hotspot=_hotspot(
            file_path="pyproject.toml",
            score=25.0,
            commit_count=25,
            commit_ref="2e15897",
        ),
        repo=_Repo(remotes=[]),
        repo_path="/example/repo",
        previous_scores={},
    )

    assert row["commit_count"] == 25
    assert "dependency_or_config_touchpoint" in row["risk_reason"]
    assert row["suggested_action"] == "tighten_dependency_workflow"


@patch("dash.register_page")
def test_trend_bucket_classifies_new_stable_and_falling(_):
    import pages.ai_insights as module

    assert module._trend_bucket(3.0, 0.0) == "new"
    assert module._trend_bucket(10.2, 10.0) == "stable"
    assert module._trend_bucket(3.0, 5.0) == "falling"


@pytest.fixture
def ai_insights_module():
    with patch("dash.register_page"):
        import pages.ai_insights as module

        return module


def test_populate_insights_includes_actionable_columns(ai_insights_module):
    module = ai_insights_module
    current_report = InsightReport(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T23:59:59+00:00",
        total_commits=4,
        hotspots=[
            _hotspot(
                file_path="src/a.py",
                score=4.0,
                commit_count=4,
                commit_ref="aaaaaaa",
            )
        ],
    )
    previous_report = InsightReport(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2025-12-01T00:00:00+00:00",
        period_end="2025-12-31T23:59:59+00:00",
        total_commits=2,
        hotspots=[],
    )

    with (
        patch.object(
            module.repo_context, "get_repo", return_value=_Repo(remotes=[])
        ),
        patch.object(
            module,
            "build_analysis_snapshot",
            return_value=AnalysisSnapshot(
                schema_version="1.0.0",
                repo_path="/example/repo",
                period_start="2026-01-01T00:00:00+00:00",
                period_end="2026-01-31T23:59:59+00:00",
                total_commits=4,
                file_commit_counts={"src/a.py": 4},
                file_recent_commits={"src/a.py": ["aaaaaaa"]},
            ),
        ),
        patch.object(
            module,
            "build_insight_report",
            side_effect=[previous_report, current_report],
        ),
    ):
        rows, _status = module.populate_insights(
            {
                "period": "Last 30 days",
                "begin": "2026-01-01T00:00:00+00:00",
                "end": "2026-01-31T23:59:59+00:00",
            }
        )

    assert len(rows) == 1
    row = rows[0]
    assert row["commit_count"] == 4
    assert row["latest_commit_link"] == "aaaaaaa"
    assert row["score_delta"] == 4.0
    assert row["trend"] == "new"
    assert "risk_reason" in row
    assert "suggested_action" in row
