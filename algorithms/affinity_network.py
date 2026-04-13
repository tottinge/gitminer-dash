"""Affinity-network graph construction and statistics assembly."""

from __future__ import annotations

from typing import Any

import networkx as nx

from algorithms.affinity_analysis import get_top_files_by_affinity
from algorithms.affinity_calculator import calculate_affinities
from algorithms.graph_statistics import (
    calculate_graph_statistics,
    count_files_in_commits,
    count_multi_file_commits,
    detect_and_assign_communities,
    filter_low_degree_nodes,
)
from utils.git import ensure_list

AFFINITY_STATS_KEYS = (
    "total_commits",
    "commits_with_multiple_files",
    "unique_files",
    "file_pairs",
    "nodes_before_filtering",
    "nodes_after_filtering",
    "edges_before_filtering",
    "edges_after_filtering",
    "isolated_nodes",
    "communities",
    "avg_node_degree",
    "avg_edge_weight",
    "avg_community_size",
)


def _initial_affinity_stats() -> dict[str, Any]:
    """Create default stats payload for affinity-network analysis."""
    return {key: 0 for key in AFFINITY_STATS_KEYS}


def _resolve_affinities(
    commits, precomputed_affinities: dict[tuple[str, str], float] | None
) -> dict[tuple[str, str], float]:
    """Return provided affinities or compute them from commits."""
    if precomputed_affinities is not None:
        return precomputed_affinities
    return calculate_affinities(commits)


def _unique_files_from_affinities(
    affinities: dict[tuple[str, str], float],
) -> set[str]:
    """Return distinct file paths present in affinity pairs."""
    files: set[str] = set()
    for file_pair in affinities:
        files.update(file_pair)
    return files


def _add_affinity_edges(
    G: nx.Graph,
    affinities: dict[tuple[str, str], float],
    top_file_set: set[str],
    min_affinity: float,
) -> None:
    """Add weighted edges for affinity pairs that pass filters."""
    for (file1, file2), affinity in affinities.items():
        if (
            file1 in top_file_set
            and file2 in top_file_set
            and affinity >= min_affinity
        ):
            G.add_edge(file1, file2, weight=affinity)


def _add_nodes_from_top_files(
    G: nx.Graph, top_file_set: set[str], file_counts: dict[str, int]
) -> None:
    """Add graph nodes for selected top files with commit-count attributes."""
    for file in top_file_set:
        G.add_node(file, commit_count=file_counts.get(file, 0))


def _update_post_filter_stats(
    stats: dict[str, Any], G: nx.Graph, min_edge_count: int
) -> None:
    """Apply low-degree filtering and update post-filter graph size stats."""
    stats["isolated_nodes"] = filter_low_degree_nodes(G, min_edge_count)
    stats["nodes_after_filtering"] = len(G.nodes())
    stats["edges_after_filtering"] = len(G.edges())


def create_file_affinity_network(
    commits,
    min_affinity: float = 0.2,
    max_nodes: int = 50,
    min_edge_count: int = 1,
    precomputed_affinities: dict[tuple[str, str], float] | None = None,
) -> tuple[nx.Graph, list, dict[str, Any]]:
    """Create a network graph of file affinities based on commit history."""
    stats: dict[str, Any] = _initial_affinity_stats()
    if not commits:
        return nx.Graph(), [], {**stats, "error": "No commits provided"}

    commits = ensure_list(commits)
    stats["total_commits"] = len(commits)

    affinities = _resolve_affinities(
        commits=commits, precomputed_affinities=precomputed_affinities
    )
    file_counts = count_files_in_commits(commits)
    stats["commits_with_multiple_files"] = count_multi_file_commits(commits)

    all_files = _unique_files_from_affinities(affinities)
    stats["unique_files"] = len(all_files)
    stats["file_pairs"] = len(affinities)

    G = nx.Graph()
    top_file_set = get_top_files_by_affinity(affinities, max_nodes)
    _add_nodes_from_top_files(
        G=G, top_file_set=top_file_set, file_counts=file_counts
    )

    stats["nodes_before_filtering"] = len(G.nodes())
    _add_affinity_edges(
        G=G,
        affinities=affinities,
        top_file_set=top_file_set,
        min_affinity=min_affinity,
    )
    stats["edges_before_filtering"] = len(G.edges())
    _update_post_filter_stats(stats=stats, G=G, min_edge_count=min_edge_count)

    communities, community_stats = detect_and_assign_communities(G)
    stats.update(community_stats)
    graph_stats = calculate_graph_statistics(G)
    stats.update(graph_stats)

    return G, communities, stats
