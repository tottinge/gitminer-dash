"""
Weekly Commits Analysis Module

This module provides functions for grouping commits by week and calculating
weekly commit statistics.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
from collections.abc import Iterable
from git import Commit


def get_week_ending(dt: datetime) -> datetime:
    """
    Get the Sunday (end of week) for a given date.

    Weeks run Monday-Sunday, so the weekend counts toward the prior workweek.

    Args:
        dt: A datetime object

    Returns:
        A datetime representing the Sunday ending that week (23:59:59)
    """
    days_until_sunday = (6 - dt.weekday()) % 7
    if days_until_sunday == 0:
        sunday = dt
    else:
        sunday = dt + timedelta(days=days_until_sunday)

    return sunday.replace(hour=23, minute=59, second=59, microsecond=0)


def _normalize_datetime(dt: datetime) -> datetime:
    """Normalize datetime to timezone-aware UTC or timezone-naive."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone()


def calculate_weekly_commits(
    commits_data: Iterable[Commit], begin: datetime, end: datetime
) -> dict[str, any]:
    """
    Group commits by week and calculate statistics.

    Args:
        commits_data: Iterable of commit objects
        begin: Start datetime for the analysis
        end: End datetime for the analysis

    Returns:
        A dictionary containing:
        - weeks: List of week data, each with week_ending, commits, and count
        - min_commits: Minimum commits in any week
        - max_commits: Maximum commits in any week
        - avg_commits: Average commits per week
    """
    # Normalize begin and end to have timezone info
    begin = _normalize_datetime(begin)
    end = _normalize_datetime(end)

    # Group commits by week ending date
    weeks_map: dict[datetime, list[Commit]] = defaultdict(list)

    for commit in commits_data:
        commit_date = _normalize_datetime(commit.committed_datetime)
        week_ending = get_week_ending(commit_date)
        # Normalize the key for consistent lookup
        week_key = (
            week_ending.replace(tzinfo=None) if week_ending.tzinfo else week_ending
        )
        weeks_map[week_key].append(commit)

    # Generate all weeks in the period (including empty weeks)
    all_weeks: list[datetime] = []
    current = get_week_ending(begin)
    final = get_week_ending(end)

    # Normalize to naive datetime for dictionary keys
    current = current.replace(tzinfo=None) if current.tzinfo else current
    final = final.replace(tzinfo=None) if final.tzinfo else final

    while current <= final:
        all_weeks.append(current)
        current += timedelta(days=7)

    # Build week data structures
    weeks_list = []
    for week_ending in all_weeks:
        commits_in_week = weeks_map.get(week_ending, [])
        weeks_list.append(
            {
                "week_ending": week_ending,
                "commits": commits_in_week,
                "count": len(commits_in_week),
            }
        )

    # Calculate statistics
    counts = [w["count"] for w in weeks_list]
    min_commits = min(counts) if counts else 0
    max_commits = max(counts) if counts else 0
    avg_commits = sum(counts) / len(counts) if counts else 0.0

    return {
        "weeks": weeks_list,
        "min_commits": min_commits,
        "max_commits": max_commits,
        "avg_commits": avg_commits,
    }


def extract_commit_details(commit: Commit) -> dict[str, any]:
    """
    Extract details from a commit for display.

    Args:
        commit: A git Commit object

    Returns:
        Dictionary with commit details including date, committer, description,
        and line change statistics
    """
    stats = commit.stats.total

    return {
        "date": commit.committed_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "committer": commit.committer.name,
        "description": commit.summary,
        "lines_added": stats.get("insertions", 0),
        "lines_removed": stats.get("deletions", 0),
        "lines_modified": stats.get("lines", 0),
    }
