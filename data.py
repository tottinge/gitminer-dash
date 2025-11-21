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
def get_repo_name():
    reverse_split_path = reversed(repository_path().split(os.sep))
    rightmost_word = next(x for x in reverse_split_path if x)
    return re.sub(pattern=r"[_\.-]", repl=" ", string=rightmost_word).title()


def _dt_key(dt: datetime) -> str:
    return dt.astimezone().replace(microsecond=0).isoformat()


@lru_cache(maxsize=2)
def _cached_commits(repo_path: str, begin_key: str, end_key: str) -> list[Commit]:
    repo = Repo(repo_path)
    begin = datetime.fromisoformat(begin_key)
    end = datetime.fromisoformat(end_key)
    return list(repo.iter_commits("--all", since=begin, until=end))


def commits_in_period(beginning: datetime, ending: datetime) -> Iterable[
    Commit
]:
    repo_path = repository_path()
    begin_key = _dt_key(beginning)
    end_key = _dt_key(ending)
    yield from _cached_commits(repo_path, begin_key, end_key)
