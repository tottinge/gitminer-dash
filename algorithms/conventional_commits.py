"""
Conventional Commits Analysis Module

This module provides functions for analyzing conventional commit messages
and categorizing them by intent/type.
"""

import re
from collections import Counter
from datetime import timedelta

import pandas as pd

# Pattern to match conventional commit format
conventional_commit_match_pattern = re.compile(r"^(\w+)[!(:]")
INTENT_BUILD = "build"
INTENT_CHORE = "chore"
INTENT_CI = "ci"
INTENT_DOCS = "docs"
INTENT_FEAT = "feat"
INTENT_FIX = "fix"
INTENT_MERGE = "merge"
INTENT_PERF = "perf"
INTENT_REFACTOR = "refactor"
INTENT_REVERT = "revert"
INTENT_STYLE = "style"
INTENT_TEST = "test"
INTENT_UNKNOWN = "unknown"

# Standard conventional commit categories (kept as `categories` for compatibility)
categories = {
    INTENT_BUILD,
    INTENT_CHORE,
    INTENT_CI,
    INTENT_DOCS,
    INTENT_FEAT,
    INTENT_FIX,
    INTENT_MERGE,
    INTENT_PERF,
    INTENT_REFACTOR,
    INTENT_REVERT,
    INTENT_STYLE,
    INTENT_TEST,
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
    return INTENT_UNKNOWN


def prepare_changes_by_date(
    commits_data, weeks: int | None = None
) -> pd.DataFrame:
    """
    Prepare a DataFrame of changes grouped by date and conventional commit type.

    Args:
        commits_data: Iterable of commit objects to analyze
        weeks: Number of weeks to look back (default behavior: 12)

    Returns:
        A pandas DataFrame with columns: date, reason, count
    """
    commits = list(commits_data)
    if commits:
        lookback_weeks = 12 if weeks is None else weeks
        latest_commit_date = max(
            commit.committed_datetime.date() for commit in commits
        )
        lookback_start_date = latest_commit_date - timedelta(
            weeks=lookback_weeks
        )
        commits = [
            commit
            for commit in commits
            if commit.committed_datetime.date() >= lookback_start_date
        ]
    daily_change_counter = Counter()
    for commit in commits:
        match = conventional_commit_match_pattern.match(commit.message)
        if match:
            intent = normalize_intent(match.group(1))
            daily_change_counter[
                (commit.committed_datetime.date(), intent)
            ] += 1

    dataset = sorted(
        (date, intent, count)
        for ((date, intent), count) in daily_change_counter.items()
    )
    return pd.DataFrame(dataset, columns=["date", "reason", "count"])
