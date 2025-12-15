"""Unit tests for graph statistics and graph processing helpers."""

from types import SimpleNamespace
from unittest.mock import patch

import networkx as nx

from algorithms.graph_statistics import (
    calculate_graph_statistics,
    count_files_in_commits,
    count_multi_file_commits,
    detect_and_assign_communities,
    filter_low_degree_nodes,
)


def _mock_commit(*files: str):
    """Create a minimal commit-like object with a stats.files mapping."""
    return SimpleNamespace(stats=SimpleNamespace(files={f: {} for f in files}))


def test_count_files_in_commits_counts_occurrences_across_commits():
    commits = [
        _mock_commit("a.py", "b.py"),
        _mock_commit("b.py", "c.py"),
        _mock_commit("a.py"),
    ]

    assert count_files_in_commits(commits) == {"a.py": 2, "b.py": 2, "c.py": 1}


def test_count_multi_file_commits_counts_commits_with_two_or_more_files():
    commits = [
        _mock_commit("a.py"),
        _mock_commit("a.py", "b.py"),
        _mock_commit("a.py", "b.py", "c.py"),
    ]

    assert count_multi_file_commits(commits) == 2


def test_filter_low_degree_nodes_removes_nodes_below_threshold_and_returns_count_removed():
    # A - B - C, where A and C have degree 1, B has degree 2.
    G = nx.Graph()
    G.add_edge("a", "b", weight=1.0)
    G.add_edge("b", "c", weight=1.0)

    removed = filter_low_degree_nodes(G, min_degree=2)

    assert removed == 2
    assert set(G.nodes()) == {"b"}
    assert len(G.edges()) == 0


def test_filter_low_degree_nodes_with_non_positive_min_degree_is_noop():
    G = nx.Graph()
    G.add_edge("a", "b", weight=1.0)

    removed = filter_low_degree_nodes(G, min_degree=0)

    assert removed == 0
    assert set(G.nodes()) == {"a", "b"}
    assert set(G.edges()) == {("a", "b")}


def test_detect_and_assign_communities_assigns_community_ids_to_nodes_and_returns_stats():
    G = nx.Graph()
    G.add_edge("a", "b", weight=1.0)
    G.add_node("c")

    expected_communities = [
        {"a", "b"},
        {"c"},
    ]

    with patch(
        "networkx.community.louvain_communities", return_value=expected_communities
    ):
        communities, stats = detect_and_assign_communities(G)

    assert communities == expected_communities
    assert stats["communities"] == 2
    assert stats["avg_community_size"] == 1.5

    # IDs come from enumeration order of communities
    assert G.nodes["a"]["community"] == 0
    assert G.nodes["b"]["community"] == 0
    assert G.nodes["c"]["community"] == 1


def test_detect_and_assign_communities_with_empty_graph_returns_no_communities_and_no_node_attrs():
    G = nx.Graph()

    communities, stats = detect_and_assign_communities(G)

    assert communities == []
    assert stats == {"communities": 0, "avg_community_size": 0}
    assert nx.get_node_attributes(G, "community") == {}


def test_calculate_graph_statistics_computes_avg_degree_and_avg_edge_weight():
    # A - B - C with weights 2 and 4
    G = nx.Graph()
    G.add_edge("a", "b", weight=2.0)
    G.add_edge("b", "c", weight=4.0)

    stats = calculate_graph_statistics(G)

    assert stats["avg_node_degree"] == 4 / 3
    assert stats["avg_edge_weight"] == 3.0


def test_calculate_graph_statistics_with_empty_graph_returns_zeros():
    stats = calculate_graph_statistics(nx.Graph())
    assert stats == {"avg_node_degree": 0, "avg_edge_weight": 0}
