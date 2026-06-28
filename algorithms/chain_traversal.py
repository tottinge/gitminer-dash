"""Linear commit chain traversal utilities.

This module provides pure, easily testable helpers for walking a linear
(commit-with-single-parent) chain between two commits and formatting the
results for display in Dash tables.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from algorithms.commit_presentation import present_commit


@runtime_checkable
class HasCommitFields(Protocol):
    """Protocol for the minimal commit API we rely on.

    This keeps the traversal logic decoupled from GitPython so tests can
    use simple mocks.
    """

    hexsha: str
    committed_datetime: datetime
    message: str

    @property
    def parents(
        self,
    ) -> Iterable[HasCommitFields]:  # pragma: no cover - attribute
        ...

    @property
    def author(self):  # pragma: no cover - attribute (object with .name)
        ...


class LinearChainTraversalError(Exception):
    """Raised when the requested commits do not form a linear chain."""


@dataclass(frozen=True, slots=True)
class ChainTableRow:
    """Row of data for the chain commits table."""

    hash: str
    date: str
    branch: str
    author: str
    message: str


CHAIN_COMMITS_TABLE_COLUMNS = [
    {"name": "Hash", "id": "hash"},
    {"name": "Date", "id": "date"},
    {"name": "Branch", "id": "branch"},
    {"name": "Author", "id": "author"},
    {"name": "Message", "id": "message"},
]


def traverse_linear_chain(
    latest_commit: HasCommitFields,
    earliest_sha: str,
    *,
    max_steps: int = 10_000,
) -> list[HasCommitFields]:
    """Walk a linear chain from ``latest_commit`` back to ``earliest_sha``.

    The chain is expected to be linear: every intermediate commit must have
    exactly one parent. Traversal stops once a commit with ``hexsha`` equal
    to ``earliest_sha`` is reached.

    Args:
        latest_commit: The newest commit in the chain (tail).
        earliest_sha: The oldest commit's hash in the chain (head).
        max_steps: Safety limit to avoid infinite traversal.

    Returns:
        List of commits ordered from earliest -> latest.

    Raises:
        LinearChainTraversalError: If the chain is not linear, the earliest
        commit is not reachable, or safety limits are exceeded.
    """

    if not latest_commit:
        raise LinearChainTraversalError("latest_commit is required")

    path: list[HasCommitFields] = [latest_commit]
    current = latest_commit
    steps = 0

    while current.hexsha != earliest_sha:
        steps += 1
        if steps > max_steps:
            raise LinearChainTraversalError(
                "Maximum traversal depth exceeded while walking commit chain"
            )

        parent_candidates = getattr(current, "parents", None)
        parents = [] if parent_candidates is None else list(parent_candidates)
        if not parents:
            raise LinearChainTraversalError(
                "Reached a commit with no parents before finding earliest_sha"
            )
        if len(parents) != 1:
            raise LinearChainTraversalError(
                "Encountered a non-linear commit (multiple parents) in chain traversal"
            )

        current = parents[0]
        path.append(current)

    # We walked from latest -> earliest; reverse for chronological order
    return list(reversed(path))


def commits_to_chain_rows(
    commits: Iterable[HasCommitFields],
    branch_getter: Callable[[HasCommitFields], str] | None = None,
) -> list[dict[str, str]]:
    """Convert commits into dictionaries suitable for a Dash DataTable.

    Each row contains:
    - ``hash``: short SHA (7 chars)
    - ``date``: ``YYYY-MM-DD HH:MM``
    - ``branch``: branch name (when available, else empty string)
    - ``author``: author name
    - ``message``: first line of the commit message (truncated to 100 chars)

    ``branch_getter`` is optional; when provided it is called with each commit
    to obtain a branch name for display.
    """

    rows: list[dict[str, str]] = []
    for commit in commits:
        presentation = present_commit(
            commit,
            timestamp_format="%Y-%m-%d %H:%M",
            actor_attribute_name="author",
        )
        branch = branch_getter(commit) if branch_getter is not None else ""
        row = ChainTableRow(
            hash=presentation.short_hash,
            date=presentation.timestamp,
            branch=branch,
            author=presentation.actor,
            message=presentation.message,
        )
        rows.append(asdict(row))
    return rows
