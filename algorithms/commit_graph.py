"""
Build NetworkX graphs from commit data.

This module provides pure functions for constructing commit graphs
that can be tested independently of git repositories.
"""

import networkx as nx
from typing import Any

def build_commit_graph(commits: list[Any]) -> nx.Graph:
    """
    Build a NetworkX graph from a list of commits.
    
    Creates nodes for each commit and its parents, with edges connecting
    parents to children. Merge commits (commits with multiple parents) are skipped.
    
    Args:
        commits: List of commit objects with attributes:
            - hexsha: commit hash
            - committed_datetime: timestamp of commit
            - parents: list of parent commit objects
            
    Returns:
        NetworkX graph where:
            - Nodes have attributes: 'committed' (datetime), 'sha' (str)
            - Edges connect parent commits to child commits
            - Merge commits are excluded
    """
    graph = nx.Graph()
    
    for commit in commits:
        # Skip merge commits (multiple parents)
        if len(commit.parents) > 1:
            continue
            
        for parent in commit.parents:
            # Store only the committed datetime; the node key itself is the SHA.
            graph.add_node(
                parent.hexsha,
                committed=parent.committed_datetime,
            )
            graph.add_node(
                commit.hexsha,
                committed=commit.committed_datetime,
            )
            graph.add_edge(parent.hexsha, commit.hexsha)
    
    return graph
