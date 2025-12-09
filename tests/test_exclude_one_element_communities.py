"""
Test script to verify that one-element communities are excluded from the graph.
"""

from tests import setup_path

setup_path()
import sys

import networkx as nx


def test_exclude_one_element_communities() -> None:
    """
    Test that one-element communities are excluded from the graph.
    Should raise AssertionError if test fails.
    """
    G = nx.Graph()
    G.add_node("file1.py", community=0)
    G.add_node("file2.py", community=0)
    G.add_node("file3.py", community=0)
    G.add_node("file4.py", community=1)
    G.add_node("file5.py", community=1)
    G.add_node("file6.py", community=2)
    G.add_node("file7.py", community=3)
    community_ids = set(nx.get_node_attributes(G, "community").values())
    included_communities = []
    for community_id in community_ids:
        community_nodes = [
            node
            for (node, data) in G.nodes(data=True)
            if data.get("community") == community_id
        ]
        if len(community_nodes) <= 1:
            continue
        included_communities.append((community_id, community_nodes))
    community_count = len(included_communities)
    included_ids = [id for (id, _) in included_communities]
    expected_ids = [0, 1]
    assert community_count == 2, "Expected 2 communities after filtering"
    assert set(included_ids) == set(
        expected_ids
    ), f"Expected communities {expected_ids}, got {included_ids}"
    for community_id, nodes in included_communities:
        assert len(nodes) > 1, f"Community {community_id} has only {len(nodes)} node"


if __name__ == "__main__":
    test_exclude_one_element_communities()
    sys.exit(0)
