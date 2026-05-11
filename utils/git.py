from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TypeVar

from git import Repo

# We intentionally delegate repository resolution to the data module
# to preserve single-source-of-truth for CLI arg handling.


def get_repo() -> Repo:
    from repository_context import (
        get_repo as _get_repo,
    )  # local import to avoid cycles

    return _get_repo()


T = TypeVar("T")


def ensure_list(items: Iterable[T] | Sequence[T] | None) -> list[T]:
    """Return a list from any iterable/sequence, handling None.
    - If items is already a list, it is returned as-is.
    - If items is None, returns an empty list.
    - Otherwise, constructs a list(items).
    """
    if items is None:
        return []
    if isinstance(items, list):
        return items
    return list(items)


def tree_entry_size(repo: Repo, commit_ref, path: str) -> int:
    """Safely fetch the size of a tree entry for a path at a commit.
    Returns 0 if the path does not exist or cannot be read.
    """
    try:
        entry = repo.commit(commit_ref).tree[path]
        return getattr(entry, "size", 0) or 0
    except Exception:
        return 0


def get_commit_messages_for_file(
    repo: Repo, filepath: str, start_date, end_date
):
    """Get all commit messages for a specific file during the specified period.

    Args:
        repo: Git repository object
        filepath: Path to the file
        start_date: Start of date range
        end_date: End of date range

    Yields:
        Commit messages (full text)
    """
    # Use GitPython's built-in filtering for efficiency
    for commit in repo.iter_commits(
        paths=filepath, since=start_date, until=end_date
    ):
        yield commit.message


def get_commits_for_file_pair(
    repo: Repo,
    first_file_path: str,
    second_file_path: str,
    period_start,
    period_end,
) -> list[dict[str, str]]:
    """Get commits that modified both files in a pairing during the specified period.

    Args:
        repo: Git repository object
        first_file_path: First file path
        second_file_path: Second file path
        period_start: Start of date range
        period_end: End of date range

    Returns:
        List of dicts with keys: hash, date, message
    """
    commits = []
    for commit in repo.iter_commits():
        commit_date = commit.committed_datetime
        if not (period_start <= commit_date <= period_end):
            continue

        # Check if both files were modified in this commit
        modified_files = (
            {item.a_path for item in commit.diff(commit.parents[0])}
            if commit.parents
            else set()
        )

        if (
            first_file_path in modified_files
            and second_file_path in modified_files
        ):
            commits.append(
                {
                    "hash": commit.hexsha[:7],
                    "date": commit_date.strftime("%Y-%m-%d %H:%M"),
                    "message": commit.message.split("\n")[0][
                        :80
                    ],  # First line, truncated
                }
            )

    return commits
