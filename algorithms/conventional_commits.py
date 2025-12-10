"""
Conventional Commits Analysis Module

This module provides functions for analyzing conventional commit messages
and categorizing them by intent/type.
"""

import re
from collections import Counter

import pandas as pd

# Pattern to match conventional commit format
conventional_commit_match_pattern = re.compile(r"^(\w+)[!(:]")

# Standard conventional commit categories
categories = {
    "build",
    "chore",
    "ci",
    "docs",
    "feat",
    "fix",
    "merge",
    "perf",
    "refactor",
    "revert",
    "style",
    "test",
}


def normalize_intent(intent: str):
    """
    Normalize a commit intent/type string to a standard category.

    Args:
        intent: The raw intent string from a commit message

    Returns:
        A normalized intent string from the standard categories,
        or "unknown" if no match is found
    """
    lower = intent.lower()
    if lower in categories:
        return lower
    for name in categories:
        if lower in name or name in lower:
            return name
    return "unknown"


def prepare_changes_by_date(commits_data, weeks=12) -> pd.DataFrame:
    """
    Prepare a DataFrame of changes grouped by date and conventional commit type.

    Args:
        commits_data: Iterable of commit objects to analyze
        weeks: Number of weeks to look back (default: 12)

    Returns:
        A pandas DataFrame with columns: date, reason, count
    """
    daily_change_counter = Counter()
    for commit in commits_data:
        match = conventional_commit_match_pattern.match(commit.message)
        if match:
            intent = normalize_intent(match.group(1))
            daily_change_counter[(commit.committed_datetime.date(), intent)] += 1

    dataset = sorted(
        (date, intent, count)
        for ((date, intent), count) in daily_change_counter.items()
    )
    return pd.DataFrame(dataset, columns=["date", "reason", "count"])
