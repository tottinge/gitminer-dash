"""Behavior tests for AI insights controls and drill-down interactions."""

from tests import setup_path

setup_path()
import os
import sys
from unittest.mock import patch

import pytest

from insights.models import InsightReport

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def ai_insights_module():
    with patch("dash.register_page"):
        import pages.ai_insights as module

        return module


@pytest.fixture
def store_data():
    return {
        "period": "Last 30 days",
        "begin": "2026-01-01T00:00:00+00:00",
        "end": "2026-01-31T23:59:59+00:00",
    }


def _report_from_rows(rows):
    hotspots = []
    for row in rows:
        hotspots.append(
            type(
                "Hotspot",
                (),
                {
                    "file_path": row["file_path"],
                    "score": row["score"],
                    "evidence": row["evidence"],
                },
            )()
        )
    return InsightReport(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T23:59:59+00:00",
        total_commits=10,
        hotspots=hotspots,
    )


def _ev(kind: str, value: str):
    return type("Evidence", (), {"kind": kind, "value": value})()


def test_populate_insights_applies_score_and_path_filters(
    ai_insights_module, store_data
):
    module = ai_insights_module
    current_report = _report_from_rows(
        [
            {
                "file_path": "src/core.py",
                "score": 12.0,
                "evidence": [
                    _ev("file", "src/core.py"),
                    _ev("metric", "commit_count=12"),
                    _ev("commit", "ccccccc"),
                ],
            },
            {
                "file_path": "tests/test_core.py",
                "score": 11.0,
                "evidence": [
                    _ev("file", "tests/test_core.py"),
                    _ev("metric", "commit_count=11"),
                    _ev("commit", "ttttttt"),
                ],
            },
            {
                "file_path": "pyproject.toml",
                "score": 10.0,
                "evidence": [
                    _ev("file", "pyproject.toml"),
                    _ev("metric", "commit_count=10"),
                    _ev("commit", "ppppppp"),
                ],
            },
            {
                "file_path": "src/low.py",
                "score": 3.0,
                "evidence": [
                    _ev("file", "src/low.py"),
                    _ev("metric", "commit_count=3"),
                    _ev("commit", "lllllll"),
                ],
            },
        ]
    )
    previous_report = _report_from_rows([])

    with (
        patch.object(
            module.repo_context,
            "get_repo",
            return_value=type("Repo", (), {"remotes": []})(),
        ),
        patch.object(module, "build_analysis_snapshot"),
        patch.object(
            module,
            "build_insight_report",
            side_effect=[previous_report, current_report],
        ),
    ):
        rows, _status = module.populate_insights(
            store_data,
            top_n=10,
            min_score=5,
            filters=[
                module.FILTER_EXCLUDE_CONFIG,
                module.FILTER_EXCLUDE_TESTS,
            ],
        )

    assert len(rows) == 1
    assert rows[0]["file_path"] == "src/core.py"


def test_populate_insights_applies_top_n_limit(ai_insights_module, store_data):
    module = ai_insights_module
    current_report = _report_from_rows(
        [
            {
                "file_path": "src/a.py",
                "score": 12.0,
                "evidence": [
                    _ev("file", "src/a.py"),
                    _ev("metric", "commit_count=12"),
                    _ev("commit", "aaaaaaa"),
                ],
            },
            {
                "file_path": "src/b.py",
                "score": 11.0,
                "evidence": [
                    _ev("file", "src/b.py"),
                    _ev("metric", "commit_count=11"),
                    _ev("commit", "bbbbbbb"),
                ],
            },
            {
                "file_path": "src/c.py",
                "score": 10.0,
                "evidence": [
                    _ev("file", "src/c.py"),
                    _ev("metric", "commit_count=10"),
                    _ev("commit", "ccccccc"),
                ],
            },
        ]
    )
    previous_report = _report_from_rows([])

    with (
        patch.object(
            module.repo_context,
            "get_repo",
            return_value=type("Repo", (), {"remotes": []})(),
        ),
        patch.object(module, "build_analysis_snapshot"),
        patch.object(
            module,
            "build_insight_report",
            side_effect=[previous_report, current_report],
        ),
    ):
        rows, _status = module.populate_insights(
            store_data,
            top_n=2,
            min_score=0,
            filters=[],
        )

    assert len(rows) == 2
    assert rows[0]["file_path"] == "src/a.py"
    assert rows[1]["file_path"] == "src/b.py"


def test_populate_hotspot_drilldown_parses_selected_row(ai_insights_module):
    module = ai_insights_module
    rows = [
        {
            "file_path": "src/a.py",
            "score": 10.0,
            "score_delta": 2.0,
            "trend": "rising",
            "commit_count": 10,
            "risk_reason": "high_churn",
            "suggested_action": "reduce_change_surface_with_helpers",
            "evidence_refs": "file:src/a.py | metric:commit_count=10 | commit:aaaaaaa",
        }
    ]

    status, details, evidence = module.populate_hotspot_drilldown(
        {"row": 0}, rows
    )

    assert isinstance(status, str)
    assert any(item["field"] == "file_path" for item in details)
    assert len(evidence) == 3
    assert evidence[0]["kind"] == "file"


def test_populate_hotspot_drilldown_handles_empty_rows(ai_insights_module):
    module = ai_insights_module
    status, details, evidence = module.populate_hotspot_drilldown(None, [])

    assert isinstance(status, str)
    assert details == []
    assert evidence == []
