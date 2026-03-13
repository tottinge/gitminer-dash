"""Tests for `insights/report_builder.py`."""

from unittest.mock import patch

from insights.models import (
    AnalysisSnapshot,
    EvidenceRef,
    HotspotCandidate,
)
from insights.report_builder import build_insight_report


def _snapshot() -> AnalysisSnapshot:
    return AnalysisSnapshot(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=3,
        file_commit_counts={"a.py": 3},
        file_recent_commits={"a.py": ["aaaaaaa"]},
    )


def test_build_insight_report_filters_hotspots_with_insufficient_evidence():
    low_evidence = HotspotCandidate(
        file_path="a.py",
        score=9.0,
        evidence=[EvidenceRef(kind="file", value="a.py")],
    )
    enough_evidence = HotspotCandidate(
        file_path="b.py",
        score=8.0,
        evidence=[
            EvidenceRef(kind="file", value="b.py"),
            EvidenceRef(kind="metric", value="commit_count=8"),
        ],
    )

    with patch(
        "insights.report_builder.rank_hotspots",
        return_value=[low_evidence, enough_evidence],
    ):
        report = build_insight_report(snapshot=_snapshot(), top_n=5)

    assert [item.file_path for item in report.hotspots] == ["b.py"]


def test_build_insight_report_allows_configured_minimum_evidence_refs():
    candidate = HotspotCandidate(
        file_path="a.py",
        score=5.0,
        evidence=[EvidenceRef(kind="file", value="a.py")],
    )

    with patch(
        "insights.report_builder.rank_hotspots", return_value=[candidate]
    ):
        report = build_insight_report(
            snapshot=_snapshot(), top_n=5, min_evidence_refs=1
        )

    assert [item.file_path for item in report.hotspots] == ["a.py"]
