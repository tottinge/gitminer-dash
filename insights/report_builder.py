"""Build structured insight reports from snapshots."""

from __future__ import annotations

from insights.hotspot_scoring import rank_hotspots
from insights.models import AnalysisSnapshot, InsightReport


def build_insight_report(
    snapshot: AnalysisSnapshot,
    top_n: int = 5,
    min_evidence_refs: int = 2,
) -> InsightReport:
    """Build deterministic report contract for delivery surfaces."""
    ranked_hotspots = rank_hotspots(snapshot=snapshot, top_n=top_n)
    vetted_hotspots = [
        hotspot
        for hotspot in ranked_hotspots
        if len(hotspot.evidence) >= min_evidence_refs
    ]
    return InsightReport(
        schema_version=snapshot.schema_version,
        repo_path=snapshot.repo_path,
        period_start=snapshot.period_start,
        period_end=snapshot.period_end,
        total_commits=snapshot.total_commits,
        hotspots=vetted_hotspots,
    )
