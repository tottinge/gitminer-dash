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
