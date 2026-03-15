"""Tests for `insights/citation_guard.py`."""

from insights.citation_guard import validate_narrative_citations
from insights.models import EvidenceRef, HotspotCandidate, InsightReport


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


def test_validate_narrative_citations_passes_for_report_backed_claims():
    narrative_text = (
        "src/a.py changed frequently "
        "[file:src/a.py] [metric:commit_count=3]\n"
        "recent commit confirms activity [commit:aaaaaaa]"
    )

    result = validate_narrative_citations(
        report=_report(), narrative_text=narrative_text
    )

    assert result["passed"] is True
    assert result["claims_checked"] == 2
    assert result["invalid_claims"] == []


def test_validate_narrative_citations_reports_missing_citation_claim():
    result = validate_narrative_citations(
        report=_report(), narrative_text="src/a.py changed frequently."
    )

    assert result["passed"] is False
    assert result["invalid_claims"] == [
        {
            "line": 1,
            "reason": "missing_citation",
            "claim": "src/a.py changed frequently.",
        }
    ]


def test_validate_narrative_citations_reports_unknown_citations():
    narrative_text = (
        "src/a.py changed frequently "
        "[file:src/a.py] [metric:commit_count=99]"
    )

    result = validate_narrative_citations(
        report=_report(), narrative_text=narrative_text
    )

    assert result["passed"] is False
    assert result["invalid_claims"] == [
        {
            "line": 1,
            "reason": "unknown_citation",
            "claim": narrative_text,
            "unknown_citations": ["metric:commit_count=99"],
        }
    ]
    assert "metric:commit_count=99" not in result["allowed_evidence_refs"]
