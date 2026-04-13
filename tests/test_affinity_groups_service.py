"""Requirement-based tests for pages.affinity_groups_service."""

import networkx as nx
import pytest

from pages.affinity_groups_service import build_graph_data_store


def test_build_graph_data_store_happy_path():
    """Happy path: output shape and key node/community fields are correct."""
    graph = nx.Graph()
    graph.add_node("api/a.py", community=0, commit_count=5)
    graph.add_node("api/b.py", community=0, commit_count=3)
    graph.add_node("ui/c.py", community=1, commit_count=8)
    graph.add_edge("api/a.py", "api/b.py")
    graph.add_edge("api/a.py", "ui/c.py")

    communities = [{"api/a.py", "api/b.py"}, {"ui/c.py"}]

    result = build_graph_data_store(graph, communities)

    assert set(result.keys()) == {"nodes", "communities"}
    assert set(result["nodes"]) == {"api/a.py", "api/b.py", "ui/c.py"}

    a_node = result["nodes"]["api/a.py"]
    assert a_node["commit_count"] == 5
    assert a_node["degree"] == 2
    assert a_node["community"] == 0
    assert a_node["connected_communities"] == [0, 1]

    assert set(result["communities"][0]) == {"api/a.py", "api/b.py"}
    assert set(result["communities"][1]) == {"ui/c.py"}


def test_build_graph_data_store_edge_cases():
    """Edge cases: defaults, deduped connected communities, and empty graph."""
    graph = nx.Graph()
    graph.add_node("no_attrs.py")
    graph.add_node("peer1.py", community=2)
    graph.add_node("peer2.py", community=2)
    graph.add_edge("no_attrs.py", "peer1.py")
    graph.add_edge("no_attrs.py", "peer2.py")

    result = build_graph_data_store(
        graph, [{"no_attrs.py", "peer1.py", "peer2.py"}]
    )

    node_data = result["nodes"]["no_attrs.py"]
    assert node_data["commit_count"] == 0
    assert node_data["community"] == 0
    assert node_data["degree"] == 2
    assert node_data["connected_communities"] == [2]

    empty_result = build_graph_data_store(nx.Graph(), [])
    assert empty_result == {"nodes": {}, "communities": {}}


@pytest.mark.parametrize(
    ("graph", "communities", "expected_exception"),
    [
        (None, [], AttributeError),
        (nx.Graph(), None, TypeError),
    ],
)
def test_build_graph_data_store_invalid_input(
    graph, communities, expected_exception
):
    """Invalid input: non-graph/invalid communities fail explicitly."""
    with pytest.raises(expected_exception):
        build_graph_data_store(graph, communities)
