"""Tests for `algorithms/community_flow.py`."""

import networkx as nx

from algorithms.community_flow import (
    community_flow_rows,
    count_nodes_by_community,
)


def _graph_with_communities() -> nx.Graph:
    graph = nx.Graph()
    graph.add_node("a.py", community=0)
    graph.add_node("b.py", community=0)
    graph.add_node("c.py", community=1)
    graph.add_node("d.py", community=2)
    graph.add_edge("a.py", "b.py", weight=0.3)  # same community
    graph.add_edge("a.py", "c.py", weight=0.6)  # 0-1
    graph.add_edge("b.py", "c.py", weight=0.4)  # 0-1
    graph.add_edge("c.py", "d.py", weight=0.2)  # 1-2
    return graph


def test_count_nodes_by_community_returns_sorted_counts():
    assert count_nodes_by_community(_graph_with_communities()) == {
        0: 2,
        1: 1,
        2: 1,
    }


def test_community_flow_rows_aggregates_only_cross_community_edges():
    rows = community_flow_rows(_graph_with_communities())

    assert rows == [
        {
            "source_community": 0,
            "target_community": 1,
            "coupling_strength": 1.0,
            "edge_count": 2,
        },
        {
            "source_community": 1,
            "target_community": 2,
            "coupling_strength": 0.2,
            "edge_count": 1,
        },
    ]


def test_community_flow_rows_defaults_missing_community_to_zero():
    graph = nx.Graph()
    graph.add_node("a.py")
    graph.add_node("b.py", community=1)
    graph.add_edge("a.py", "b.py", weight=0.5)

    rows = community_flow_rows(graph)

    assert rows == [
        {
            "source_community": 0,
            "target_community": 1,
            "coupling_strength": 0.5,
            "edge_count": 1,
        }
    ]


def test_community_flow_rows_returns_empty_when_no_cross_community_edges():
    graph = nx.Graph()
    graph.add_node("a.py", community=0)
    graph.add_node("b.py", community=0)
    graph.add_edge("a.py", "b.py", weight=0.5)

    assert community_flow_rows(graph) == []
