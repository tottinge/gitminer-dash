from __future__ import annotations
from typing import Iterable, List, TypeVar, Sequence

from git import Repo

# We intentionally delegate repository resolution to the data module
# to preserve single-source-of-truth for CLI arg handling.

def get_repo() -> Repo:
    from data import get_repo as _get_repo  # local import to avoid cycles
    return _get_repo()


T = TypeVar("T")

def ensure_list(items: Iterable[T] | Sequence[T] | None) -> List[T]:
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


def tree_entry_size(repo: Repo, commitish, path: str) -> int:
    """Safely fetch the size of a tree entry for a path at a commit.
    Returns 0 if the path does not exist or cannot be read.
    """
    try:
        entry = repo.commit(commitish).tree[path]
        return getattr(entry, "size", 0) or 0
    except Exception:
        return 0
