import os
import re
import sys
from collections.abc import Iterable
from datetime import datetime
from functools import cache, lru_cache

from git import Commit, Repo


# Link this to any local repo, until we can make this
# a handy-dandy drag-n-drop or dir selection input field
def repository_path() -> str:
    if len(sys.argv) < 2:
        raise ValueError(
            "No repository path provided. Please run the application with a repository path as a command-line argument."
        )
    return sys.argv[1]


@cache
def get_repo() -> Repo:
    return Repo(repository_path())


@cache
def format_repository_display_name():
    reverse_split_path = reversed(repository_path().split(os.sep))
    repository_directory_name = next(
        path_segment for path_segment in reverse_split_path if path_segment
    )
    return re.sub(
        pattern=r"[_\.-]",
        repl=" ",
        string=repository_directory_name,
    ).title()


def _iso_datetime_key(dt: datetime) -> str:
    return dt.astimezone().replace(microsecond=0).isoformat()


@lru_cache(maxsize=2)
def _cached_commits(
    repo_path: str, period_start_key: str, period_end_key: str
) -> list[Commit]:
    repo = Repo(repo_path)
    period_start = datetime.fromisoformat(period_start_key)
    period_end = datetime.fromisoformat(period_end_key)
    return list(
        repo.iter_commits("--all", since=period_start, until=period_end)
    )


def commits_in_period(
    period_start: datetime, period_end: datetime
) -> Iterable[Commit]:
    repo_path = repository_path()
    yield from commits_in_period_for_repo_path(
        repo_path=repo_path,
        period_start=period_start,
        period_end=period_end,
    )


def commits_in_period_for_repo_path(
    repo_path: str, period_start: datetime, period_end: datetime
) -> Iterable[Commit]:
    period_start_key = _iso_datetime_key(period_start)
    period_end_key = _iso_datetime_key(period_end)
    yield from _cached_commits(repo_path, period_start_key, period_end_key)
