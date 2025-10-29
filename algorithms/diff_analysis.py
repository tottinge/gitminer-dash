"""
Diff Analysis Module

This module provides functions for analyzing diffs and changes across commits.
"""

from collections import defaultdict
from datetime import datetime
import pandas as pd


def get_diffs_in_period(commits_data, start: datetime, end: datetime) -> pd.DataFrame:
    """
    Calculate diff statistics for commits in a given time period.

    This function analyzes insertions and deletions to estimate:
    - Possible modifications (min of insertions and deletions)
    - Net insertions (insertions beyond possible modifications)
    - Net deletions (deletions beyond possible modifications)

    Args:
        commits_data: Iterable of commit objects
        start: Start datetime for the period
        end: End datetime for the period

    Returns:
        A pandas DataFrame with columns: date, kind, count
    """
    counts = defaultdict(int)
    for commit in commits_data:
        day = commit.committed_datetime.date()
        inserted = commit.stats.total["insertions"]
        deleted = commit.stats.total["deletions"]

        possible_mods = min(inserted, deleted)
        counts[day, "possible mods"] += possible_mods
        counts[day, "net inserts"] += max(inserted - possible_mods, 0)
        counts[day, "net deletes"] += max(deleted - possible_mods, 0)

    source_data = sorted((day, kind, count) for ((day, kind), count) in counts.items())
    result = pd.DataFrame(source_data, columns=["date", "kind", "count"])
    return result
