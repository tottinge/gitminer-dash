import os
import re
import sys
from collections.abc import Iterable
from datetime import datetime
from functools import cache, lru_cache
from typing import List

from git import Repo, Commit


# Link this to any local repo, until we can make this
# a handy-dandy drag-n-drop or dir selection input field
def repository_path() -> str:
    """
    Get the repository path from command-line arguments.

    Returns:
        The repository path as a string.

    Raises:
        ValueError: If no repository path is provided as a command-line argument.
    """
    if len(sys.argv) < 2:
        raise ValueError(
            "No repository path provided. Please run the application with a repository path as a command-line argument."
        )
    return sys.argv[1]


@cache
def get_repo() -> Repo:
    return Repo(repository_path())


@cache
def get_repo_name():
    return re.sub(
        pattern=r"[_\.-]", repl=" ", string=os.path.split(repository_path())[-1]
    ).title()


def _dt_key(dt: datetime) -> str:
    # Normalize to second precision and timezone-aware string for caching key
    return dt.astimezone().replace(microsecond=0).isoformat()


@lru_cache(maxsize=64)
def _cached_commits(repo_path: str, begin_key: str, end_key: str) -> List[Commit]:
    repo = Repo(repo_path)
    begin = datetime.fromisoformat(begin_key)
    end = datetime.fromisoformat(end_key)
    result: List[Commit] = []
    for delta in repo.iter_commits():
        this_date = delta.committed_datetime
        if begin <= this_date <= end:
            result.append(delta)
    return result


def commits_in_period(beginning: datetime, ending: datetime) -> Iterable[Commit]:
    """Return commits between beginning and ending, cached by repo and date range."""
    repo_path = repository_path()
    begin_key = _dt_key(beginning)
    end_key = _dt_key(ending)
    for commit in _cached_commits(repo_path, begin_key, end_key):
        yield commit


def clear_commit_cache() -> None:
    """Clear the cached commits (useful after switching repos)."""
    _cached_commits.cache_clear()
