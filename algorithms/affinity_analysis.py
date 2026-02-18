"""
Affinity Analysis Module

This module provides advanced analysis functions for file affinity calculations,
including finding optimal affinity thresholds and analyzing affinity ranges.
"""

from collections import defaultdict

from algorithms.affinity_calculator import calculate_affinities
from utils.git import ensure_list


def get_file_total_affinities(affinities: dict) -> dict[str, float]:
    """Calculate total affinity for each file across all pairs.

    Args:
        affinities: Dictionary of file pair affinities {(file1, file2): affinity}

    Returns:
        Dictionary mapping file names to their total affinity scores

    Example:
        >>> affinities = {('a.py', 'b.py'): 0.5, ('b.py', 'c.py'): 0.3}
        >>> totals = get_file_total_affinities(affinities)
        >>> totals['b.py']
        0.8
    """
    file_total_affinity = defaultdict(float)
    for (file1, file2), affinity in affinities.items():
        file_total_affinity[file1] += affinity
        file_total_affinity[file2] += affinity
    return dict(file_total_affinity)


def get_top_files_by_affinity(affinities: dict, max_nodes: int) -> set[str]:
    """Get the top N files by total affinity score.

    Args:
        affinities: Dictionary of file pair affinities {(file1, file2): affinity}
        max_nodes: Maximum number of files to return

    Returns:
        Set of top file names by affinity

    Example:
        >>> affinities = {('a.py', 'b.py'): 0.5, ('b.py', 'c.py'): 0.3}
        >>> top = get_top_files_by_affinity(affinities, 2)
        >>> 'b.py' in top
        True
    """
    file_total_affinity = get_file_total_affinities(affinities)
    top_files = sorted(
        file_total_affinity.items(), key=lambda x: x[1], reverse=True
    )[:max_nodes]
    return {file for file, _ in top_files}


def get_top_files_and_affinities(commits, affinities, max_nodes):
    """Get top files by affinity and their relevant affinity values.

    Args:
        commits: Iterable of commit objects
        affinities: Dictionary of file pair affinities
        max_nodes: Maximum number of nodes to consider

    Returns:
        A tuple of (top_file_set, relevant_affinities)
    """
    top_file_set = get_top_files_by_affinity(affinities, max_nodes)

    relevant_affinities = [
        affinity
        for (file1, file2), affinity in affinities.items()
        if file1 in top_file_set and file2 in top_file_set
    ]

    return top_file_set, relevant_affinities


def calculate_ideal_affinity(commits, target_node_count=15, max_nodes=50):
    """
    Calculate an ideal minimum affinity threshold that will result in approximately
    the target number of connected nodes.

    Args:
        commits: Iterable of commit objects
        target_node_count: Target number of nodes in the final graph (default: 15)
        max_nodes: Maximum number of nodes to consider (default: 50)

    Returns:
        A tuple of (ideal_min_affinity, estimated_node_count, estimated_edge_count)
    """
    if not commits:
        return 0.2, 0, 0  # Default values if no commits

    # Normalize to list for safe reuse
    commits = ensure_list(commits)

    affinities = calculate_affinities(commits)

    top_file_set, relevant_affinities = get_top_files_and_affinities(
        commits, affinities, max_nodes
    )

    if not relevant_affinities:
        return 0.2, 0, 0  # Default if no relevant affinities

    # Try different thresholds to find one that gives us the target node count
    thresholds = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
    best_threshold = 0.2  # Default if we can't find a better one
    best_node_count = 0
    best_edge_count = 0

    for threshold in thresholds:
        # Count edges that would be included with this threshold
        edge_count = sum(1 for a in relevant_affinities if a >= threshold)

        # Estimate connected nodes (this is an approximation)
        connected_nodes = set()
        for (file1, file2), affinity in affinities.items():
            if (
                file1 in top_file_set
                and file2 in top_file_set
                and affinity >= threshold
            ):
                connected_nodes.add(file1)
                connected_nodes.add(file2)

        node_count = len(connected_nodes)

        # If this threshold gives us a node count in our target range, use it
        if 5 <= node_count <= 20:
            best_threshold = threshold
            best_node_count = node_count
            best_edge_count = edge_count
            break

        # If we're below the target range but better than our current best, update
        if node_count > 0 and abs(node_count - target_node_count) < abs(
            best_node_count - target_node_count
        ):
            best_threshold = threshold
            best_node_count = node_count
            best_edge_count = edge_count

    return best_threshold, best_node_count, best_edge_count
