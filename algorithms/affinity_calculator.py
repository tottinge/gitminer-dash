"""Core affinity calculation module.

This module provides the fundamental algorithm for calculating file affinities
based on commit history. Files that are modified together in the same commit
have affinity for each other.
"""

from collections import defaultdict
from collections.abc import Callable, Iterable
from itertools import combinations

from utils.git import ensure_list


def _calculate_affinities_from_commits(
    commits: Iterable,
    affinities: defaultdict[tuple[str, str], float],
    weight_fn: Callable[[int], float],
) -> None:
    """Core algorithm for calculating file affinities from commits.

    This is the inner loop logic extracted for reuse. Modifies the affinities
    dict in place.

    Args:
        commits: Iterable of commit objects with stats.files attribute
        affinities: A defaultdict(float) to accumulate affinity scores into
        weight_fn: Function mapping number of files in a commit to a per-pair weight
    """
    for commit in commits:
        files = list(commit.stats.files)
        files_in_commit = len(files)

        if files_in_commit < 2:
            continue

        weight = weight_fn(files_in_commit)
        for file1, file2 in combinations(files, 2):
            ordered_key = (file1, file2) if file1 <= file2 else (file2, file1)
            affinities[ordered_key] += weight


def _default_weight_fn(file_count: int) -> float:
    return 2 / (file_count * (file_count - 1))


def calculate_affinities(
    commits: Iterable,
    weight_fn: Callable[[int], float] | None = None,
) -> defaultdict[tuple[str, str], float]:
    """Calculate file affinities based on commit history.

    Files that are modified together in commits have "affinity" for each other.
    The default affinity score is normalized per commit: each commit contributes
    ~1 total "affinity mass" across all file pairs in that commit.

    With N files in a commit, there are C(N, 2) file pairs; each pair receives:
    1 / C(N, 2) = 2 / (N * (N - 1))

    This prevents large commits (like merges) from dominating the overall
    affinity scores.

    Args:
        commits: Iterable of commit objects with a stats.files attribute.
                 Automatically handles iterator consumption by converting to list.
        weight_fn: Optional function mapping the number of files in a commit to a
                   per-pair weight. Defaults to ``lambda n: 2 / (n * (n - 1))``.

    Returns:
        A defaultdict mapping (file1, file2) tuples to affinity scores.
        File pairs are always ordered alphabetically to ensure consistent keys.
        Returns empty defaultdict if commits is empty or None.

    Examples:
        >>> from unittest.mock import Mock
        >>> commit1 = Mock()
        >>> commit1.stats.files = {'a.py': {}, 'b.py': {}}
        >>> commit2 = Mock()
        >>> commit2.stats.files = {'b.py': {}, 'c.py': {}}
        >>> affinities = calculate_affinities([commit1, commit2])
        >>> affinities[('a.py', 'b.py')]
        1.0
        >>> affinities[('b.py', 'c.py')]
        1.0
    """
    affinities = defaultdict(float)

    if commits is None:
        return affinities

    if weight_fn is None:
        weight_fn = _default_weight_fn

    commits = ensure_list(commits)

    if not commits:
        return affinities

    _calculate_affinities_from_commits(commits, affinities, weight_fn)

    return affinities
