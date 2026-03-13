"""Deterministic hotspot scoring from snapshot signals."""

from __future__ import annotations

from insights.models import AnalysisSnapshot, EvidenceRef, HotspotCandidate


def rank_hotspots(
    snapshot: AnalysisSnapshot, top_n: int = 3
) -> list[HotspotCandidate]:
    """Rank hotspot candidates from commit-frequency signal."""
    if top_n <= 0:
        return []

    candidates: list[HotspotCandidate] = []
    for file_path, commit_count in snapshot.file_commit_counts.items():
        evidence = [
            EvidenceRef(kind="file", value=file_path),
            EvidenceRef(kind="metric", value=f"commit_count={commit_count}"),
        ]
        commit_refs = snapshot.file_recent_commits.get(file_path, [])
        if commit_refs:
            evidence.append(EvidenceRef(kind="commit", value=commit_refs[0]))

        candidates.append(
            HotspotCandidate(
                file_path=file_path,
                score=float(commit_count),
                evidence=evidence,
            )
        )

    ranked = sorted(
        candidates,
        key=lambda candidate: (-candidate.score, candidate.file_path),
    )
    return ranked[:top_n]
