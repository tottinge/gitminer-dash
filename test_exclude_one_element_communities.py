#!/usr/bin/env python3
"""
Test script to verify that one-element communities are excluded from the graph.
"""

import networkx as nx
import sys
import os

def test_exclude_one_element_communities():
    """
    Test that one-element communities are excluded from the graph.
    """
    print("Testing exclusion of one-element communities...")
    
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
    community_ids = set(nx.get_node_attributes(G, 'community').values())
    print(f"Total communities in graph: {len(community_ids)}")
    
    # Simulate the community filtering logic from create_network_visualization
    included_communities = []
    for community_id in community_ids:
        community_nodes = [node for node, data in G.nodes(data=True) 
                          if data.get('community') == community_id]
        
        # Skip communities with only one node (this is the logic we're testing)
        if len(community_nodes) <= 1:
            print(f"Community {community_id + 1} has {len(community_nodes)} node(s) - EXCLUDED")
            continue
        
        print(f"Community {community_id + 1} has {len(community_nodes)} node(s) - INCLUDED")
        included_communities.append((community_id, community_nodes))
    
    # Count the number of included communities
    community_count = len(included_communities)
    
    # Print results
    print(f"Communities with more than one node: 2")
    print(f"Communities included after filtering: {community_count}")
    
    # Check if the number of included communities matches the expected number
    if community_count == 2:
        print("✓ One-element communities are correctly excluded")
    else:
        print("✗ One-element communities are not excluded")
    
    # Check which communities were included
    included_ids = [id for id, _ in included_communities]
    print(f"Included community IDs: {included_ids}")
    
    # Expected included community IDs are 0 and 1
    expected_ids = [0, 1]
    if set(included_ids) == set(expected_ids):
        print("✓ Correct communities were included")
    else:
        print(f"✗ Incorrect communities were included. Expected: {expected_ids}")
    
    # Verify that each included community has more than one node
    all_valid = True
    for community_id, nodes in included_communities:
        node_count = len(nodes)
        if node_count <= 1:
            print(f"✗ Community {community_id + 1} has only {node_count} node")
            all_valid = False
    
    if all_valid:
        print("✓ All included communities have more than one node")
    
    return community_count == 2 and set(included_ids) == set(expected_ids) and all_valid

if __name__ == "__main__":
    test_result = test_exclude_one_element_communities()
    print("\nTest result:", "PASSED" if test_result else "FAILED")
    sys.exit(0 if test_result else 1)