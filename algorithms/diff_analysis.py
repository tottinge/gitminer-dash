"""
Diff Analysis Module

This module provides functions for analyzing diffs and changes across commits.
"""

from collections import defaultdict
from collections.abc import Iterable
from datetime import date

import pandas as pd

POSSIBLE_MODIFICATIONS_KIND = "possible mods"
NET_INSERTIONS_KIND = "net inserts"
NET_DELETIONS_KIND = "net deletes"
RESULT_COLUMNS = ["date", "kind", "count"]


def _calculate_diff_breakdown(
    insertions: int, deletions: int
) -> tuple[int, int, int]:
    possible_modifications = min(insertions, deletions)
    net_insertions = max(insertions - possible_modifications, 0)
    net_deletions = max(deletions - possible_modifications, 0)
    return possible_modifications, net_insertions, net_deletions


def get_diffs_in_period(commits_data: Iterable[object]) -> pd.DataFrame:
    """
    Calculate daily diff statistics for a pre-filtered commit iterable.

    This function analyzes insertions and deletions to estimate:
    - Possible modifications (min of insertions and deletions)
    - Net insertions (insertions beyond possible modifications)
    - Net deletions (deletions beyond possible modifications)

    Args:
        commits_data: Iterable of commit objects

    Returns:
        A pandas DataFrame with columns: date, kind, count
    """
    diff_counts_by_day_and_kind: defaultdict[tuple[date, str], int] = (
        defaultdict(int)
    )
    for commit in commits_data:
        commit_day = commit.committed_datetime.date()
        insertions = commit.stats.total["insertions"]
        deletions = commit.stats.total["deletions"]

        (
            possible_modifications,
            net_insertions,
            net_deletions,
        ) = _calculate_diff_breakdown(insertions, deletions)
        diff_counts_by_day_and_kind[
            commit_day, POSSIBLE_MODIFICATIONS_KIND
        ] += possible_modifications
        diff_counts_by_day_and_kind[
            commit_day, NET_INSERTIONS_KIND
        ] += net_insertions
        diff_counts_by_day_and_kind[
            commit_day, NET_DELETIONS_KIND
        ] += net_deletions

    daily_kind_counts = sorted(
        (day, kind, count)
        for ((day, kind), count) in diff_counts_by_day_and_kind.items()
    )
    return pd.DataFrame(daily_kind_counts, columns=RESULT_COLUMNS)
