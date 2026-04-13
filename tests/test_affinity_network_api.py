"""Requirement-based API tests for algorithms.affinity_network."""

from unittest.mock import Mock, patch

import networkx as nx

from algorithms.affinity_network import (
    AFFINITY_STATS_KEYS,
    create_file_affinity_network,
)


def _commit(*files: str) -> Mock:
    """Create a lightweight commit mock with a stats.files mapping."""
    commit = Mock()
    commit.stats = Mock()
    commit.stats.files = {file_path: {} for file_path in files}
    return commit


def test_requirement_empty_input_returns_error_payload():
    """API requirement: empty input returns empty graph and error payload."""
    graph, communities, stats = create_file_affinity_network([])

    assert isinstance(graph, nx.Graph)
    assert len(graph.nodes()) == 0
    assert len(graph.edges()) == 0
    assert communities == []
    assert set(AFFINITY_STATS_KEYS).issubset(stats)
    assert stats["error"] == "No commits provided"

    for key in AFFINITY_STATS_KEYS:
        assert stats[key] == 0


def test_requirement_iterables_are_materialized_before_affinity_calculation():
    """API requirement: iterable commits are accepted and consumed once."""
    expected_affinities = {("a.py", "b.py"): 0.7}

    def commit_stream():
        yield _commit("a.py", "b.py")

    with patch(
        "algorithms.affinity_network.calculate_affinities",
        return_value=expected_affinities,
    ) as mock_calculate:
        graph, _communities, stats = create_file_affinity_network(
            commit_stream(),
            min_affinity=0.0,
        )

    mock_calculate.assert_called_once()
    passed_commits = mock_calculate.call_args.args[0]
    assert isinstance(passed_commits, list)
    assert len(passed_commits) == 1
    assert graph.edges["a.py", "b.py"]["weight"] == 0.7
    assert stats["total_commits"] == 1


def test_requirement_precomputed_affinities_skip_recalculation():
    """API requirement: supplied affinities must be used directly."""
    commit = _commit("a.py", "b.py")
    precomputed_affinities = {("a.py", "b.py"): 0.6}

    with patch("algorithms.affinity_network.calculate_affinities") as mock_calc:
        graph, _communities, stats = create_file_affinity_network(
            [commit],
            min_affinity=0.0,
            precomputed_affinities=precomputed_affinities,
        )

    mock_calc.assert_not_called()
    assert graph.has_edge("a.py", "b.py")
    assert graph.edges["a.py", "b.py"]["weight"] == 0.6
    assert stats["file_pairs"] == 1


def test_requirement_min_affinity_and_low_degree_filter_are_applied():
    """API requirement: threshold is inclusive and low-degree nodes are removed."""
    commit = _commit("a.py", "b.py", "c.py")
    precomputed_affinities = {
        ("a.py", "b.py"): 0.2,
        ("a.py", "c.py"): 0.19,
    }

    graph, _communities, stats = create_file_affinity_network(
        [commit],
        min_affinity=0.2,
        min_edge_count=1,
        precomputed_affinities=precomputed_affinities,
    )

    assert graph.has_edge("a.py", "b.py")
    assert not graph.has_edge("a.py", "c.py")
    assert set(graph.nodes()) == {"a.py", "b.py"}
    assert stats["nodes_before_filtering"] == 3
    assert stats["edges_before_filtering"] == 1
    assert stats["isolated_nodes"] == 1
    assert stats["nodes_after_filtering"] == 2
    assert stats["edges_after_filtering"] == 1


def test_requirement_graph_is_limited_to_top_files():
    """API requirement: only files from the selected top set appear in graph."""
    commit = _commit("a.py", "b.py", "c.py")
    precomputed_affinities = {
        ("a.py", "b.py"): 0.8,
        ("a.py", "c.py"): 0.7,
        ("b.py", "c.py"): 0.6,
    }

    with patch(
        "algorithms.affinity_network.get_top_files_by_affinity",
        return_value={"a.py", "b.py"},
    ):
        graph, _communities, _stats = create_file_affinity_network(
            [commit],
            min_affinity=0.0,
            max_nodes=2,
            precomputed_affinities=precomputed_affinities,
        )

    assert set(graph.nodes()) == {"a.py", "b.py"}
    assert len(graph.edges()) == 1
    assert graph.has_edge("a.py", "b.py")


def test_requirement_defaults_for_min_affinity_and_max_nodes_are_enforced():
    """API requirement: omitted optional args must use documented defaults."""
    commit = _commit("a.py", "b.py")
    precomputed_affinities = {("a.py", "b.py"): 0.5}

    with patch(
        "algorithms.affinity_network.get_top_files_by_affinity",
        return_value={"a.py", "b.py"},
    ) as mock_top_files:
        graph, _communities, _stats = create_file_affinity_network(
            [commit],
            precomputed_affinities=precomputed_affinities,
        )

    assert graph.has_edge("a.py", "b.py")
    assert mock_top_files.call_count == 1
    called_args = mock_top_files.call_args.args
    assert len(called_args) == 2
    assert called_args[1] == 50


def test_requirement_stats_include_multi_file_and_unique_file_counts():
    """API requirement: stats payload reports multi-file and unique-file counts."""
    commits = [
        _commit("a.py", "b.py"),
        _commit("b.py", "c.py"),
        _commit("d.py"),
    ]
    precomputed_affinities = {
        ("a.py", "b.py"): 0.4,
        ("b.py", "c.py"): 0.3,
    }

    _graph, _communities, stats = create_file_affinity_network(
        commits,
        min_affinity=0.0,
        precomputed_affinities=precomputed_affinities,
    )

    assert "commits_with_multiple_files" in stats
    assert "unique_files" in stats
    assert stats.get("commits_with_multiple_files") == 2
    assert stats.get("unique_files") == 3


def test_requirement_missing_file_commit_count_defaults_to_zero():
    """API requirement: selected top files missing from commits get commit_count=0."""
    commit = _commit("a.py", "b.py")
    precomputed_affinities = {
        ("ghost.py", "a.py"): 0.9,
        ("a.py", "b.py"): 0.8,
    }

    with patch(
        "algorithms.affinity_network.get_top_files_by_affinity",
        return_value={"ghost.py", "a.py"},
    ):
        graph, _communities, _stats = create_file_affinity_network(
            [commit],
            min_affinity=0.0,
            max_nodes=2,
            precomputed_affinities=precomputed_affinities,
        )

    assert "ghost.py" in graph.nodes
    assert "a.py" in graph.nodes

    ghost_node_data = graph.nodes.get("ghost.py", {})
    a_node_data = graph.nodes.get("a.py", {})

    assert "commit_count" in ghost_node_data
    assert "commit_count" in a_node_data
    assert ghost_node_data.get("commit_count") == 0
    assert a_node_data.get("commit_count") == 1
