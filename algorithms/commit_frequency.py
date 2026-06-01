"""
Commit Frequency Analysis Module

This module provides functions for analyzing which files are committed most frequently
and calculating statistics about those commits.
"""

import logging
from collections import Counter
from collections.abc import Iterable
from datetime import datetime
from typing import Protocol, TypedDict

from git import Commit, Repo

from algorithms import file_changes


class FileChangeMetrics(Protocol):
    avg_changes: float
    total_change: int
    percent_change: float


class FileCommitFrequencyRow(TypedDict):
    filename: str
    count: int
    avg_changes: float
    total_change: int
    percent_change: float


def _file_change_metrics_for(
    file_stats_by_file: dict[str, FileChangeMetrics], file_path: str
) -> FileChangeMetrics:
    return file_stats_by_file.get(
        file_path, file_changes.zero_file_change_stats(file_path)
    )


def _build_commit_frequency_row(
    file_path: str, commit_count: int, change_metrics: FileChangeMetrics
) -> FileCommitFrequencyRow:
    return {
        "filename": file_path,
        "count": commit_count,
        "avg_changes": round(change_metrics.avg_changes, 2),
        "total_change": change_metrics.total_change,
        "percent_change": round(change_metrics.percent_change, 2),
    }


def count_file_commits(commits_data: Iterable[Commit]) -> Counter[str]:
    """Count how many commits touched each file path."""
    counter = Counter()
    for commit in commits_data:
        try:
            counter.update(commit.stats.files.keys())
        except ValueError:
            logging.getLogger(__name__).exception("Error processing commit")
            raise
    return counter


def calculate_file_commit_frequency(
    commits_data: Iterable[Commit],
    repo: Repo,
    begin: datetime,
    end: datetime,
    top_n: int = 20,
) -> list[FileCommitFrequencyRow]:
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

    counter = count_file_commits(commits_data)
    most_common_files = counter.most_common(top_n)

    # Extract just the filenames
    filenames = [filename for filename, _ in most_common_files]

    # Get additional metrics for these files
    file_stats = file_changes.files_changes_over_period(
        filenames, begin, end, repo
    )

    # Create a list of dictionaries with all metrics
    return [
        _build_commit_frequency_row(
            file_path=filename,
            commit_count=count,
            change_metrics=_file_change_metrics_for(
                file_stats_by_file=file_stats, file_path=filename
            ),
        )
        for filename, count in most_common_files
    ]
