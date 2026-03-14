"""Tests for `insights/evidence_builder.py`."""

from insights.evidence_builder import attach_evidence_refs, build_file_evidence
from insights.models import (
    AnalysisSnapshot,
    EvidenceRef,
    HotspotCandidate,
)


def _snapshot() -> AnalysisSnapshot:
    return AnalysisSnapshot(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=3,
        file_commit_counts={"a.py": 3},
        file_recent_commits={"a.py": ["aaaaaaa", "bbbbbbb"]},
    )


def test_build_file_evidence_includes_file_metric_and_latest_commit():
    evidence = build_file_evidence(snapshot=_snapshot(), file_path="a.py")

    assert [item.kind for item in evidence] == ["file", "metric", "commit"]
    assert [item.value for item in evidence] == [
        "a.py",
        "commit_count=3",
        "aaaaaaa",
    ]


def test_build_file_evidence_for_unknown_file_returns_file_only():
    evidence = build_file_evidence(snapshot=_snapshot(), file_path="missing.py")

    assert [item.kind for item in evidence] == ["file"]
    assert [item.value for item in evidence] == ["missing.py"]


def test_attach_evidence_refs_populates_when_hotspot_has_no_evidence():
    hotspots = [HotspotCandidate(file_path="a.py", score=3.0, evidence=[])]

    enriched = attach_evidence_refs(snapshot=_snapshot(), hotspots=hotspots)

    assert len(enriched[0].evidence) == 3
    assert [item.kind for item in enriched[0].evidence] == [
        "file",
        "metric",
        "commit",
    ]


def test_attach_evidence_refs_preserves_existing_evidence():
    existing = [
        EvidenceRef(kind="file", value="a.py"),
        EvidenceRef(kind="metric", value="custom=1"),
    ]
    hotspots = [
        HotspotCandidate(file_path="a.py", score=3.0, evidence=existing)
    ]

    enriched = attach_evidence_refs(snapshot=_snapshot(), hotspots=hotspots)

    assert enriched[0].evidence == existing
