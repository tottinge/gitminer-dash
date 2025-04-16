import os
import re
import sys
from collections.abc import Iterable
from datetime import datetime
from functools import cache

from git import Repo, Commit


# Link this to any local repo, until we can make this
# a handy-dandy drag-n-drop or dir selection input field
def repository_path() -> str:
    return sys.argv[1]


def get_repo() -> Repo:
    return Repo(repository_path())


@cache
def get_repo_name():
    return re.sub(pattern=r'[_\.-]', repl=' ', string=os.path.split(repository_path())[-1]).title()


def commits_in_period(beginning: datetime, ending: datetime) -> Iterable[Commit]:
    for delta in get_repo().iter_commits():
        this_date = delta.committed_datetime
        if beginning <= this_date <= ending:
            yield delta
