"""
Commit filtering utilities for finding commits that modify specific file groups.
"""

from datetime import datetime


def get_commits_for_group_files(
    commits_in_period, group_files: list[str]
) -> list[dict]:
    """
    Get commits that contain at least two files from the group.

    Args:
        commits_in_period: Iterator of commit objects for the period
        group_files: List of file paths in the group

    Returns:
        List of dicts with keys: hash, timestamp, message, group_files
        Sorted by timestamp (most recent first)
    """
    commits_data = []
    group_files_set = set(group_files)

    for commit in commits_in_period:
        try:
            modified_files = _get_modified_files(commit)
            group_files_in_commit = list(group_files_set & modified_files)

            if len(group_files_in_commit) >= 2:
                commits_data.append(_format_commit_data(commit, group_files_in_commit))
        except (AttributeError, ValueError):
            # Skip commits that can't be processed (e.g., missing attributes)
            continue

    commits_data.sort(key=lambda x: x["timestamp"], reverse=True)
    return commits_data


def _get_modified_files(commit) -> set[str]:
    """Extract modified file paths from a commit."""
    modified_files = set()

    if not commit.parents:
        return modified_files

    try:
        for item in commit.diff(commit.parents[0]):
            if hasattr(item, "a_path") and item.a_path:
                modified_files.add(item.a_path)
            if hasattr(item, "b_path") and item.b_path:
                modified_files.add(item.b_path)
    except Exception:  # noqa: S110
        # Git diff operations can fail for various reasons (repo state, permissions, etc.)
        pass

    return modified_files


def _format_commit_data(commit, group_files_in_commit: list[str]) -> dict:
    """Format commit data for display."""
    return {
        "hash": commit.hexsha[:7],
        "timestamp": commit.committed_datetime.strftime("%Y-%m-%d %H:%M"),
        "message": commit.message.split("\n")[0][:100],  # First line, truncated
        "group_files": ", ".join(sorted(group_files_in_commit)),
    }
