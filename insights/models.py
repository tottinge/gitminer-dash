"""Typed contracts for insights snapshot and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidenceRef:
    """Concrete evidence reference for a hotspot claim."""

    kind: str
    value: str

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "value": self.value}


@dataclass(frozen=True)
class HotspotCandidate:
    """Deterministic hotspot ranking candidate."""

    file_path: str
    score: float
    evidence: list[EvidenceRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "file_path": self.file_path,
            "score": self.score,
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True)
class AnalysisSnapshot:
    """Versioned and normalized analysis data for a repository period."""

    schema_version: str
    repo_path: str
    period_start: str
    period_end: str
    total_commits: int
    file_commit_counts: dict[str, int]
    file_recent_commits: dict[str, list[str]]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "repo_path": self.repo_path,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "total_commits": self.total_commits,
            "file_commit_counts": self.file_commit_counts,
            "file_recent_commits": self.file_recent_commits,
        }


@dataclass(frozen=True)
class InsightReport:
    """Report contract consumed by delivery surfaces (CLI/Dash)."""

    schema_version: str
    repo_path: str
    period_start: str
    period_end: str
    total_commits: int
    hotspots: list[HotspotCandidate]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "repo_path": self.repo_path,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "total_commits": self.total_commits,
            "hotspots": [hotspot.to_dict() for hotspot in self.hotspots],
        }


@dataclass(frozen=True)
class BridgeMetric:
    """Bridge metric for files that connect affinity communities."""

    file_path: str
    bridge_score: float
    bridge_ratio: float
    cross_community_edges: int
    total_edges: int
    cross_community_affinity: float
    total_affinity: float
    community: int
    connected_communities: list[int]
    commit_count: int
    evidence: list[EvidenceRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "file_path": self.file_path,
            "bridge_score": self.bridge_score,
            "bridge_ratio": self.bridge_ratio,
            "cross_community_edges": self.cross_community_edges,
            "total_edges": self.total_edges,
            "cross_community_affinity": self.cross_community_affinity,
            "total_affinity": self.total_affinity,
            "community": self.community,
            "connected_communities": self.connected_communities,
            "commit_count": self.commit_count,
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True)
class BridgeMetricsReport:
    """Report contract for deterministic bridge-metrics output."""

    schema_version: str
    repo_path: str
    period_start: str
    period_end: str
    total_commits: int
    graph_stats: dict[str, Any]
    bridges: list[BridgeMetric]
    report_type: str = "bridge-metrics"

    def to_dict(self) -> dict[str, object]:
        return {
            "report_type": self.report_type,
            "schema_version": self.schema_version,
            "repo_path": self.repo_path,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "total_commits": self.total_commits,
            "graph_stats": self.graph_stats,
            "bridges": [bridge.to_dict() for bridge in self.bridges],
        }
