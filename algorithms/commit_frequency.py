"""
Commit Frequency Analysis Module

This module provides functions for analyzing which files are committed most frequently
and calculating statistics about those commits.
"""

import logging
from collections import Counter
from collections.abc import Iterable
from datetime import datetime

from git import Repo, Commit


def calculate_file_commit_frequency(
        commits_data: Iterable[Commit],
        repo: Repo,
        begin: datetime,
        end: datetime,
        top_n: int=20
) -> list[dict]:
    """
    Calculate commit frequency and change statistics for the most committed files.

    Returns:
        A list of dictionaries containing file statistics:
        - filename: Path to the file
        - count: Number of commits touching this file
        - avg_changes: Average lines changed per commit
        - total_change: Total lines changed
        - percent_change: Percentage change in file size
    """
    from algorithms.file_changes import files_changes_over_period

    counter = Counter()
    for commit in commits_data:
        try:
            files = commit.stats.files.keys()
            counter.update(files)
        except ValueError:
            logging.getLogger(__name__).exception("Error processing commit")
            raise
    most_common_files = counter.most_common(top_n)

    # Extract just the filenames
    filenames = [filename for filename, _ in most_common_files]

    # Get additional metrics for these files
    file_stats = files_changes_over_period(filenames, begin, end, repo)

    # Create a list of dictionaries with all metrics
    result = []
    for filename, count in most_common_files:
        if filename in file_stats:
            stats = file_stats[filename]
            result.append(
                {
                    "filename": filename,
                    "count": count,
                    "avg_changes": round(stats.avg_changes, 2),
                    "total_change": stats.total_change,
                    "percent_change": round(stats.percent_change, 2),
                }
            )
        else:
            # If no stats available, use zeros for the additional metrics
            result.append(
                {
                    "filename": filename,
                    "count": count,
                    "avg_changes": 0.0,
                    "total_change": 0,
                    "percent_change": 0.0,
                }
            )

    return result
