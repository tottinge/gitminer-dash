"""Validate narrative claims against report-backed evidence references."""

from __future__ import annotations

import re

from insights.models import InsightReport

_CITATION_PATTERN = re.compile(r"\[([a-z_]+:[^\[\]]+)\]")


def _allowed_evidence_refs(report: InsightReport) -> set[str]:
    return {
        f"{item.kind}:{item.value}"
        for hotspot in report.hotspots
        for item in hotspot.evidence
    }


def _claim_lines(narrative_text: str) -> list[tuple[int, str]]:
    return [
        (line_number, line.strip())
        for line_number, line in enumerate(narrative_text.splitlines(), start=1)
        if line.strip()
    ]


def validate_narrative_citations(
    report: InsightReport, narrative_text: str
) -> dict[str, object]:
    """Validate narrative claim citations against report-backed evidence."""
    allowed_refs = _allowed_evidence_refs(report)
    invalid_claims: list[dict[str, object]] = []

    claims = _claim_lines(narrative_text=narrative_text)
    for line_number, claim in claims:
        citations = _CITATION_PATTERN.findall(claim)
        if not citations:
            invalid_claims.append(
                {
                    "line": line_number,
                    "reason": "missing_citation",
                    "claim": claim,
                }
            )
            continue

        unknown_citations = [
            citation for citation in citations if citation not in allowed_refs
        ]
        if unknown_citations:
            invalid_claims.append(
                {
                    "line": line_number,
                    "reason": "unknown_citation",
                    "claim": claim,
                    "unknown_citations": unknown_citations,
                }
            )

    return {
        "passed": not invalid_claims,
        "claims_checked": len(claims),
        "invalid_claims": invalid_claims,
        "allowed_evidence_refs": sorted(allowed_refs),
    }
