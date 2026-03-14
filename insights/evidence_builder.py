"""Build deterministic evidence references for hotspot candidates."""

from __future__ import annotations

from insights.models import AnalysisSnapshot, EvidenceRef, HotspotCandidate


def build_file_evidence(
    snapshot: AnalysisSnapshot, file_path: str
) -> list[EvidenceRef]:
    """Build canonical evidence refs for a file from snapshot signals."""
    evidence: list[EvidenceRef] = [EvidenceRef(kind="file", value=file_path)]
    commit_count = snapshot.file_commit_counts.get(file_path)
    if commit_count is not None:
        evidence.append(
            EvidenceRef(kind="metric", value=f"commit_count={commit_count}")
        )

    recent_commits = snapshot.file_recent_commits.get(file_path, [])
    if recent_commits:
        evidence.append(EvidenceRef(kind="commit", value=recent_commits[0]))
    return evidence


def attach_evidence_refs(
    snapshot: AnalysisSnapshot, hotspots: list[HotspotCandidate]
) -> list[HotspotCandidate]:
    """Attach canonical evidence to candidates that currently have none."""
    enriched: list[HotspotCandidate] = []
    for hotspot in hotspots:
        evidence = (
            hotspot.evidence
            if hotspot.evidence
            else build_file_evidence(snapshot, hotspot.file_path)
        )
        enriched.append(
            HotspotCandidate(
                file_path=hotspot.file_path,
                score=hotspot.score,
                evidence=evidence,
            )
        )
    return enriched
