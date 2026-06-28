"""
Weekly Commits Analysis Module

This module provides functions for grouping commits by week and calculating
weekly commit statistics.
"""

from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import TypedDict

from git import Commit

from algorithms.commit_presentation import present_commit

WEEK_STEP_DAYS = 7


class WeekSummary(TypedDict):
    """Statistics for a single calendar week of commits."""

    week_ending: datetime
    commits: list[Commit]
    count: int


class WeeklyCommitsResult(TypedDict):
    """Typed result structure for weekly commits aggregation."""

    weeks: list[WeekSummary]
    min_commits: int
    max_commits: int
    avg_commits: float


class CommitDetails(TypedDict):
    """Typed dictionary for details extracted from a single commit."""

    date: str
    committer: str
    description: str
    lines_added: int
    lines_removed: int
    lines_modified: int


WEEKLY_COMMIT_DETAILS_TABLE_COLUMNS: list[dict[str, str]] = [
    {"name": "Date", "id": "date"},
    {"name": "Committer", "id": "committer"},
    {"name": "Description", "id": "description"},
    {"name": "Lines Added", "id": "lines_added"},
    {"name": "Lines Removed", "id": "lines_removed"},
    {"name": "Lines Modified", "id": "lines_modified"},
]


def get_week_ending(dt: datetime) -> datetime:
    """
    Get the Sunday (end of week) for a given date.

    Weeks run Monday-Sunday, so the weekend counts toward the prior workweek.

    Args:
        dt: A datetime object

    Returns:
        A datetime representing the Sunday ending that week (23:59:59)
    """
    days_until_sunday = 6 - dt.weekday()
    sunday = (
        dt if days_until_sunday == 0 else dt + timedelta(days=days_until_sunday)
    )

    return sunday.replace(hour=23, minute=59, second=59, microsecond=0)


def _normalize_datetime(dt: datetime) -> datetime:
    """Normalize datetime to timezone-aware UTC or timezone-naive."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone()


def _week_key(week_ending: datetime) -> datetime:
    """Normalize week-ending keys for dictionary lookup consistency."""
    if week_ending.tzinfo:
        return week_ending.replace(tzinfo=None)
    return week_ending


def _group_commits_by_week(
    commits_data: Iterable[Commit],
) -> dict[datetime, list[Commit]]:
    """Group commits by normalized week-ending key."""
    weeks_map: dict[datetime, list[Commit]] = defaultdict(list)
    for commit in commits_data:
        commit_date = _normalize_datetime(commit.committed_datetime)
        week_ending = get_week_ending(commit_date)
        weeks_map[_week_key(week_ending)].append(commit)
    return weeks_map


def _week_endings_in_period(begin: datetime, end: datetime) -> list[datetime]:
    """Return all normalized week-ending datetimes in [begin, end]."""
    week_endings: list[datetime] = []
    current = _week_key(get_week_ending(begin))
    final = _week_key(get_week_ending(end))
    while current <= final:
        week_endings.append(current)
        current += timedelta(days=WEEK_STEP_DAYS)
    return week_endings


def _build_week_summaries(
    week_endings: list[datetime],
    weeks_map: dict[datetime, list[Commit]],
) -> list[WeekSummary]:
    """Build week summary rows including explicit empty weeks."""
    summaries: list[WeekSummary] = []
    for week_ending in week_endings:
        commits_in_week = weeks_map.get(week_ending, [])
        summaries.append(
            {
                "week_ending": week_ending,
                "commits": commits_in_week,
                "count": len(commits_in_week),
            }
        )
    return summaries


def _commit_count_stats(weeks: list[WeekSummary]) -> tuple[int, int, float]:
    """Calculate min, max, and average commit counts across week rows."""
    counts = [week["count"] for week in weeks]
    if not counts:
        return 0, 0, 0.0
    return min(counts), max(counts), sum(counts) / len(counts)


def calculate_weekly_commits(
    commits_data: Iterable[Commit], begin: datetime, end: datetime
) -> WeeklyCommitsResult:
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

    weeks_map = _group_commits_by_week(commits_data)
    week_endings = _week_endings_in_period(begin, end)
    weeks_list = _build_week_summaries(week_endings, weeks_map)
    min_commits, max_commits, avg_commits = _commit_count_stats(weeks_list)

    return {
        "weeks": weeks_list,
        "min_commits": min_commits,
        "max_commits": max_commits,
        "avg_commits": avg_commits,
    }


def extract_commit_details(commit: Commit) -> CommitDetails:
    """
    Extract details from a commit for display.

    Args:
        commit: A git Commit object

    Returns:
        Dictionary with commit details including date, committer, description,
        and line change statistics
    """
    presentation = present_commit(
        commit,
        timestamp_format="%Y-%m-%d %H:%M:%S",
        actor_attribute_name="committer",
        message_selector=lambda current_commit: current_commit.summary,
        max_message_length=None,
    )
    stats = commit.stats.total

    return {
        "date": presentation.timestamp,
        "committer": presentation.actor,
        "description": presentation.message,
        "lines_added": stats.get("insertions", 0),
        "lines_removed": stats.get("deletions", 0),
        "lines_modified": stats.get("lines", 0),
    }
