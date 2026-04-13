"""Build deterministic bridge-metrics reports from affinity networks."""

from __future__ import annotations

from datetime import datetime

import networkx as nx
from git import Repo

from algorithms.affinity_network import create_file_affinity_network
from insights.models import BridgeMetric, BridgeMetricsReport, EvidenceRef
from insights.schema_version import ANALYSIS_SCHEMA_VERSION
from insights.snapshot_builder import get_commits_for_period


def _rounded(value: float) -> float:
    return round(value, 6)


def _build_bridge_metric(file_path: str, graph: nx.Graph) -> BridgeMetric:
    community = int(graph.nodes[file_path].get("community", 0))
    commit_count = int(graph.nodes[file_path].get("commit_count", 0))
    total_edges = int(graph.degree(file_path))

    cross_community_edges = 0
    total_affinity = 0.0
    cross_community_affinity = 0.0
    connected_communities: set[int] = set()

    for neighbor in graph.neighbors(file_path):
        weight = float(graph.edges[file_path, neighbor].get("weight", 0.0))
        total_affinity += weight

        neighbor_community = int(graph.nodes[neighbor].get("community", 0))
        if neighbor_community != community:
            cross_community_edges += 1
            cross_community_affinity += weight
            connected_communities.add(neighbor_community)

    bridge_ratio = (
        cross_community_affinity / total_affinity if total_affinity else 0.0
    )
    bridge_score = cross_community_affinity * bridge_ratio

    rounded_bridge_score = _rounded(bridge_score)
    rounded_bridge_ratio = _rounded(bridge_ratio)
    rounded_cross_affinity = _rounded(cross_community_affinity)
    rounded_total_affinity = _rounded(total_affinity)

    evidence = [
        EvidenceRef(kind="file", value=file_path),
        EvidenceRef(
            kind="metric",
            value=f"bridge_score={rounded_bridge_score:.6f}",
        ),
        EvidenceRef(
            kind="metric",
            value=f"bridge_ratio={rounded_bridge_ratio:.6f}",
        ),
        EvidenceRef(
            kind="metric",
            value=f"cross_community_edges={cross_community_edges}",
        ),
    ]
    return BridgeMetric(
        file_path=file_path,
        bridge_score=rounded_bridge_score,
        bridge_ratio=rounded_bridge_ratio,
        cross_community_edges=cross_community_edges,
        total_edges=total_edges,
        cross_community_affinity=rounded_cross_affinity,
        total_affinity=rounded_total_affinity,
        community=community,
        connected_communities=sorted(connected_communities),
        commit_count=commit_count,
        evidence=evidence,
    )


def rank_bridge_metrics(graph: nx.Graph, top_n: int = 10) -> list[BridgeMetric]:
    """Rank files by cross-community bridge behavior."""
    if top_n <= 0 or len(graph.nodes()) == 0:
        return []

    bridge_metrics = [
        _build_bridge_metric(file_path=node, graph=graph)
        for node in graph.nodes()
    ]
    ranked = sorted(
        bridge_metrics,
        key=lambda item: (
            -item.bridge_score,
            -item.cross_community_affinity,
            -item.cross_community_edges,
            item.file_path,
        ),
    )
    return ranked[:top_n]


def build_bridge_metrics_report(
    repo: Repo,
    period_start: datetime,
    period_end: datetime,
    *,
    top_n: int = 10,
    min_affinity: float = 0.2,
    max_nodes: int = 50,
    min_edge_count: int = 1,
) -> BridgeMetricsReport:
    """Build bridge-metrics report from affinity graph structure."""
    commits = get_commits_for_period(
        repo=repo, period_start=period_start, period_end=period_end
    )
    graph, _, graph_stats = create_file_affinity_network(
        commits=commits,
        min_affinity=min_affinity,
        max_nodes=max_nodes,
        min_edge_count=min_edge_count,
    )
    bridges = rank_bridge_metrics(graph=graph, top_n=top_n)
    return BridgeMetricsReport(
        schema_version=ANALYSIS_SCHEMA_VERSION,
        repo_path=repo.working_tree_dir or "",
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        total_commits=len(commits),
        graph_stats=graph_stats,
        bridges=bridges,
    )
