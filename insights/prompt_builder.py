"""Build compact prompt payloads from deterministic insight reports."""

from __future__ import annotations

from insights.models import InsightReport


def _payload_hotspot(rank: int, hotspot) -> dict[str, object]:
    return {
        "rank": rank,
        "file_path": hotspot.file_path,
        "score": hotspot.score,
        "evidence": [item.to_dict() for item in hotspot.evidence],
    }


def build_prompt_payload(report: InsightReport) -> dict[str, object]:
    """Build provider-agnostic prompt payload from a deterministic report."""
    return {
        "prompt_payload_version": "1.0.0",
        "schema_version": report.schema_version,
        "repo_path": report.repo_path,
        "period_start": report.period_start,
        "period_end": report.period_end,
        "total_commits": report.total_commits,
        "hotspots": [
            _payload_hotspot(rank=index, hotspot=hotspot)
            for index, hotspot in enumerate(report.hotspots, start=1)
        ],
        "constraints": {
            "citation_required": True,
            "use_only_report_evidence_refs": True,
        },
    }
