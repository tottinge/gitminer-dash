"""Unit tests for graph statistics and graph processing helpers."""

from types import SimpleNamespace
from unittest.mock import patch

import networkx as nx

from algorithms.graph_statistics import (
    LOUVAIN_COMMUNITY_SEED,
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


def test_filter_low_degree_nodes_with_zero_min_degree_does_not_attempt_removal():
    G = nx.Graph()
    G.add_edge("a", "b", weight=1.0)

    with patch.object(G, "remove_nodes_from") as mock_remove_nodes:
        removed = filter_low_degree_nodes(G, min_degree=0)

    assert removed == 0
    mock_remove_nodes.assert_not_called()


def test_detect_and_assign_communities_assigns_community_ids_to_nodes_and_returns_stats():
    G = nx.Graph()
    G.add_edge("a", "b", weight=1.0)
    G.add_node("c")

    expected_communities = [
        {"a", "b"},
        {"c"},
    ]

    with patch(
        "networkx.community.louvain_communities",
        return_value=expected_communities,
    ) as mock_louvain:
        communities, stats = detect_and_assign_communities(G)

    assert communities == expected_communities
    assert stats["communities"] == 2
    assert stats["avg_community_size"] == 1.5
    mock_louvain.assert_called_once_with(G, seed=LOUVAIN_COMMUNITY_SEED)

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


def test_detect_and_assign_communities_empty_graph_does_not_call_louvain():
    G = nx.Graph()

    with patch("networkx.community.louvain_communities") as mock_louvain:
        communities, stats = detect_and_assign_communities(G)

    assert communities == []
    assert stats == {"communities": 0, "avg_community_size": 0}
    mock_louvain.assert_not_called()


def test_detect_and_assign_communities_single_node_still_runs_louvain():
    G = nx.Graph()
    G.add_node("solo")

    with patch(
        "networkx.community.louvain_communities",
        return_value=[{"solo"}],
    ) as mock_louvain:
        communities, stats = detect_and_assign_communities(G)
    mock_louvain.assert_called_once_with(G, seed=LOUVAIN_COMMUNITY_SEED)
    assert communities == [{"solo"}]
    assert stats == {"communities": 1, "avg_community_size": 1.0}
    assert G.nodes["solo"]["community"] == 0


def test_detect_and_assign_communities_is_stable_across_repeated_runs():
    G = nx.Graph()
    # Two clear clusters with one light bridge edge.
    G.add_edge("a", "b", weight=3.0)
    G.add_edge("b", "c", weight=3.0)
    G.add_edge("x", "y", weight=3.0)
    G.add_edge("y", "z", weight=3.0)
    G.add_edge("c", "x", weight=0.2)

    communities_one, _stats_one = detect_and_assign_communities(G.copy())
    communities_two, _stats_two = detect_and_assign_communities(G.copy())

    normalized_one = {frozenset(community) for community in communities_one}
    normalized_two = {frozenset(community) for community in communities_two}
    assert normalized_one == normalized_two


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


def test_calculate_graph_statistics_with_single_node_self_loop():
    G = nx.Graph()
    G.add_edge("solo", "solo", weight=2.5)

    stats = calculate_graph_statistics(G)

    assert stats == {"avg_node_degree": 2.0, "avg_edge_weight": 2.5}
