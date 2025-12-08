"""
Analyze commit chains from graph structure.

This module provides pure functions for analyzing connected components
in commit graphs and extracting chain metadata.
"""

import networkx as nx
from typing import List
from algorithms.chain_models import ChainData


def analyze_commit_chains(graph: nx.Graph) -> List[ChainData]:
    """
    Analyze connected components in a commit graph.
    
    Extracts metadata about each connected chain of commits including:
    - Time span (earliest to latest commit)
    - Number of commits
    - SHA hashes of boundary commits
    
    Args:
        graph: NetworkX graph with nodes having attributes:
            - 'committed': datetime of commit
            - 'sha': commit hash
            
    Returns:
        List of ChainData objects, one per connected component.
        Empty list if graph is empty or has no edges.
    """
    chains = []
    
    for chain in nx.connected_components(graph):
        # Collect (node_id, attrs) pairs for this connected component
        node_items = [(node_id, graph.nodes[node_id]) for node_id in chain]
        
        # Sort by commit timestamp
        ordered = sorted(node_items, key=lambda item: item[1]["committed"])
        
        # Get earliest and latest commits (by timestamp) and their SHAs (node IDs)
        earliest_id, earliest_attrs = ordered[0]
        latest_id, latest_attrs = ordered[-1]
        
        early_timestamp = earliest_attrs["committed"]
        late_timestamp = latest_attrs["committed"]
        duration = late_timestamp - early_timestamp
        commit_count = len(chain)
        
        chain_data = ChainData(
            early_timestamp=early_timestamp,
            late_timestamp=late_timestamp,
            commit_count=commit_count,
            duration=duration,
            earliest_sha=earliest_id,
            latest_sha=latest_id,
        )
        
        chains.append(chain_data)
    
    return chains
