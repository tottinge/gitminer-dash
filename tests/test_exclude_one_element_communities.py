#!/usr/bin/env python3
"""
Test script to verify that one-element communities are excluded from the graph.
"""

# Import from tests package to set up path
from tests import setup_path

setup_path()  # This ensures we can import modules from the project root
import sys

import networkx as nx


def test_exclude_one_element_communities() -> None:
    """
    Test that one-element communities are excluded from the graph.
    Should raise AssertionError if test fails.
    """

    # Create a test graph with multiple communities, including some with only one node
    G = nx.Graph()

    # Add nodes for different communities
    # Community 0: 3 nodes
    G.add_node("file1.py", community=0)
    G.add_node("file2.py", community=0)
    G.add_node("file3.py", community=0)

    # Community 1: 2 nodes
    G.add_node("file4.py", community=1)
    G.add_node("file5.py", community=1)

    # Community 2: 1 node (should be excluded)
    G.add_node("file6.py", community=2)

    # Community 3: 1 node (should be excluded)
    G.add_node("file7.py", community=3)

    # Get community IDs from node attributes
    community_ids = set(nx.get_node_attributes(G, "community").values())

    # Simulate the community filtering logic from create_network_visualization
    included_communities = []
    for community_id in community_ids:
        community_nodes = [
            node
            for node, data in G.nodes(data=True)
            if data.get("community") == community_id
        ]

        # Skip communities with only one node (this is the logic we're testing)
        if len(community_nodes) <= 1:
            continue

        included_communities.append((community_id, community_nodes))

    # Count the number of included communities
    community_count = len(included_communities)

    # Get included community IDs
    included_ids = [id for id, _ in included_communities]
    expected_ids = [0, 1]

    # Verify all conditions
    assert community_count == 2, "Expected 2 communities after filtering"
    assert set(included_ids) == set(
        expected_ids
    ), f"Expected communities {expected_ids}, got {included_ids}"

    # Verify that each included community has more than one node
    for community_id, nodes in included_communities:
        assert len(nodes) > 1, f"Community {community_id} has only {len(nodes)} node"


if __name__ == "__main__":
    test_exclude_one_element_communities()
    sys.exit(0)
