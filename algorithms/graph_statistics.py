"""
Graph Statistics Module

Functions for calculating graph metrics and processing graph structures.
"""

from collections import Counter
from collections.abc import Iterable

import networkx as nx


def count_files_in_commits(commits: Iterable) -> dict[str, int]:
    """Count how many commits each file appears in."""
    counter = Counter()
    for commit in commits:
        counter.update(commit.stats.files.keys())
    return dict(counter)


def count_multi_file_commits(commits: Iterable) -> int:
    """Count commits that modify 2 or more files."""
    return sum(1 for commit in commits if len(commit.stats.files) >= 2)


def calculate_graph_statistics(G: nx.Graph) -> dict[str, float]:
    """Calculate basic graph metrics: avg degree and edge weight."""
    stats = {"avg_node_degree": 0, "avg_edge_weight": 0}

    if len(G.nodes()) > 0:
        degrees = [degree for _, degree in G.degree()]
        stats["avg_node_degree"] = sum(degrees) / len(G.nodes())

    if len(G.edges()) > 0:
        weights = [data["weight"] for _, _, data in G.edges(data=True)]
        stats["avg_edge_weight"] = sum(weights) / len(G.edges())

    return stats


def detect_and_assign_communities(G: nx.Graph) -> tuple[list, dict[str, float]]:
    """Detect communities and assign IDs to nodes. Returns (communities, stats)."""
    communities = []
    stats = {"communities": 0, "avg_community_size": 0}

    if len(G.nodes()) > 0:
        communities = nx.community.louvain_communities(G)
        stats["communities"] = len(communities)

        if communities:
            community_sizes = [len(c) for c in communities]
            stats["avg_community_size"] = sum(community_sizes) / len(
                communities
            )

        for i, community in enumerate(communities):
            for node in community:
                G.nodes[node]["community"] = i

    return communities, stats


def filter_low_degree_nodes(G: nx.Graph, min_degree: int) -> int:
    """Remove nodes with fewer than min_degree connections. Returns count removed."""
    if min_degree <= 0:
        return 0

    nodes_to_remove = [
        node for node, degree in G.degree() if degree < min_degree
    ]
    G.remove_nodes_from(nodes_to_remove)
    return len(nodes_to_remove)
