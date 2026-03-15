"""Tests for `insights/prompt_builder.py`."""

from insights.models import EvidenceRef, HotspotCandidate, InsightReport
from insights.prompt_builder import build_prompt_payload


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
            ),
            HotspotCandidate(
                file_path="src/b.py",
                score=2.0,
                evidence=[
                    EvidenceRef(kind="file", value="src/b.py"),
                    EvidenceRef(kind="metric", value="commit_count=2"),
                ],
            ),
        ],
    )


def test_build_prompt_payload_contains_ranked_hotspots_and_evidence_refs():
    payload = build_prompt_payload(_report())

    assert payload["prompt_payload_version"] == "1.0.0"
    assert payload["schema_version"] == "1.0.0"
    assert payload["repo_path"] == "/example/repo"
    assert payload["period_start"] == "2026-01-01T00:00:00+00:00"
    assert payload["period_end"] == "2026-01-31T00:00:00+00:00"
    assert payload["total_commits"] == 3

    first_hotspot = payload["hotspots"][0]
    assert first_hotspot["rank"] == 1
    assert first_hotspot["file_path"] == "src/a.py"
    assert first_hotspot["score"] == 3.0
    assert first_hotspot["evidence"] == [
        {"kind": "file", "value": "src/a.py"},
        {"kind": "metric", "value": "commit_count=3"},
        {"kind": "commit", "value": "aaaaaaa"},
    ]

    second_hotspot = payload["hotspots"][1]
    assert second_hotspot["rank"] == 2
    assert second_hotspot["file_path"] == "src/b.py"

    assert payload["constraints"] == {
        "citation_required": True,
        "use_only_report_evidence_refs": True,
    }


def test_build_prompt_payload_is_deterministic():
    report = _report()

    first_payload = build_prompt_payload(report)
    second_payload = build_prompt_payload(report)

    assert first_payload == second_payload
