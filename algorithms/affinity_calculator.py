"""
Core affinity calculation module.

This module provides the fundamental algorithm for calculating file affinities
based on commit history. Files that are modified together in the same commit
have affinity for each other.
"""
from collections import defaultdict
from itertools import combinations
from typing import Iterable, Dict, Tuple
from utils.git import ensure_list


def _calculate_affinities_from_commits(commits, affinities):
    """
    Core algorithm for calculating file affinities from commits.

    This is the inner loop logic extracted for reuse. Modifies the affinities
    dict in place.

    Args:
        commits: Iterable of commit objects with stats.files attribute
        affinities: A defaultdict(float) to accumulate affinity scores into
    """
    for commit in commits:
        files_in_commit = len(commit.stats.files)

        if files_in_commit < 2:
            continue

        for combo in combinations(commit.stats.files, 2):
            ordered_key = tuple(sorted(combo))
            affinities[ordered_key] += 1 / files_in_commit


def calculate_affinities(commits: Iterable) -> Dict[Tuple[str, str], float]:
    """
    Calculate file affinities based on commit history.

    Files that are modified together in commits have "affinity" for each other.
    The affinity score is weighted by the number of files in each commit:
    - A commit with 2 files contributes 1/2 = 0.5 to each pair's affinity
    - A commit with 10 files contributes 1/10 = 0.1 to each pair's affinity

    This weighting prevents large commits (like merges) from dominating the
    affinity scores.

    Args:
        commits: Iterable of commit objects with a stats.files attribute.
                 Automatically handles iterator consumption by converting to list.

    Returns:
        A defaultdict mapping (file1, file2) tuples to affinity scores.
        File pairs are always sorted alphabetically to ensure consistent keys.
        Returns empty defaultdict if commits is empty or None.

    Examples:
        >>> from unittest.mock import Mock
        >>> commit1 = Mock()
        >>> commit1.stats.files = {'a.py': {}, 'b.py': {}}
        >>> commit2 = Mock()
        >>> commit2.stats.files = {'b.py': {}, 'c.py': {}}
        >>> affinities = calculate_affinities([commit1, commit2])
        >>> affinities[('a.py', 'b.py')]
        0.5
        >>> affinities[('b.py', 'c.py')]
        0.5
    """
    affinities = defaultdict(float)

    if commits is None:
        return affinities

    commits = ensure_list(commits)

    if not commits:
        return affinities

    _calculate_affinities_from_commits(commits, affinities)

    return affinities
