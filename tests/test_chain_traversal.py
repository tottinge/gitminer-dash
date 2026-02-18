"""Tests for linear commit chain traversal utilities."""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from algorithms.chain_traversal import (
    LinearChainTraversalError,
    commits_to_chain_rows,
    traverse_linear_chain,
)


def make_commit(
    sha: str,
    *,
    parent=None,
    when: datetime | None = None,
    author_name: str = "Alice",
):
    """Create a minimal mock commit object for testing."""
    commit = Mock()
    commit.hexsha = sha
    commit.parents = [parent] if parent is not None else []
    commit.committed_datetime = when or datetime(
        2024, 1, 1, tzinfo=timezone.utc
    )
    commit.message = f"Commit {sha} message"

    author = Mock()
    author.name = author_name
    commit.author = author

    return commit


def test_traverse_linear_chain_simple_chain():
    """Walks from latest back to earliest and returns commits oldest->newest."""
    c1 = make_commit(
        "c1", when=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    )
    c2 = make_commit(
        "c2", parent=c1, when=datetime(2024, 1, 2, 12, 0, tzinfo=timezone.utc)
    )
    c3 = make_commit(
        "c3", parent=c2, when=datetime(2024, 1, 3, 12, 0, tzinfo=timezone.utc)
    )

    chain = traverse_linear_chain(c3, "c1")

    assert [c.hexsha for c in chain] == ["c1", "c2", "c3"]


def test_traverse_linear_chain_single_commit():
    """When earliest and latest are the same, returns a single-element list."""
    c1 = make_commit(
        "only", when=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    )

    chain = traverse_linear_chain(c1, "only")

    assert [c.hexsha for c in chain] == ["only"]


def test_traverse_linear_chain_raises_when_earliest_not_reachable():
    """If earliest_sha is not an ancestor of latest, raise an error."""
    c1 = make_commit("c1")
    c2 = make_commit("c2", parent=c1)

    with pytest.raises(LinearChainTraversalError):
        traverse_linear_chain(c2, "missing")


def test_traverse_linear_chain_raises_on_merge_commit():
    """If an intermediate commit has multiple parents, treat as non-linear."""
    base = make_commit("base")
    p1 = make_commit("p1", parent=base)
    p2 = make_commit("p2", parent=base)

    merge = make_commit("merge")
    merge.parents = [p1, p2]  # Simulate merge

    with pytest.raises(LinearChainTraversalError):
        traverse_linear_chain(merge, "base")


def test_commits_to_chain_rows_basic_fields_without_branch():
    """Formatting helper produces expected values without branch_getter."""
    when = datetime(2024, 1, 1, 15, 30, tzinfo=timezone.utc)
    c1 = make_commit("abcdef123456", when=when, author_name="Bob")

    rows = commits_to_chain_rows([c1])

    assert len(rows) == 1
    row = rows[0]
    assert row["hash"] == "abcdef1"  # short hash
    assert row["date"] == "2024-01-01 15:30"
    assert row["branch"] == ""
    assert row["author"] == "Bob"
    assert row["message"].startswith("Commit abcdef123456 message")


def test_commits_to_chain_rows_includes_branch_when_given_getter():
    when = datetime(2024, 1, 1, 15, 30, tzinfo=timezone.utc)
    c1 = make_commit("abcdef123456", when=when, author_name="Bob")

    rows = commits_to_chain_rows([c1], branch_getter=lambda c: "main")

    assert len(rows) == 1
    row = rows[0]
    assert row["branch"] == "main"


def test_commits_to_chain_rows_truncates_long_message():
    long_msg = "X" * 200
    commit = make_commit("c1")
    commit.message = long_msg

    [row] = commits_to_chain_rows([commit])

    assert len(row["message"]) == 100
