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

    with pytest.raises(
        LinearChainTraversalError,
        match=(
            "^Reached a commit with no parents before finding " "earliest_sha$"
        ),
    ):
        traverse_linear_chain(c2, "missing")


def test_traverse_linear_chain_requires_latest_commit_with_exact_message():
    """Missing latest commit should raise a stable, explicit message."""
    with pytest.raises(
        LinearChainTraversalError,
        match="^latest_commit is required$",
    ):
        traverse_linear_chain(None, "anything")


def test_traverse_linear_chain_max_steps_boundary_allows_single_hop():
    """A one-hop chain should succeed when max_steps is exactly 1."""
    earliest = make_commit("earliest")
    latest = make_commit("latest", parent=earliest)

    chain = traverse_linear_chain(latest, "earliest", max_steps=1)

    assert [commit.hexsha for commit in chain] == ["earliest", "latest"]


def test_traverse_linear_chain_max_steps_boundary_raises_on_second_hop():
    """A two-hop chain should exceed max_steps=1 with a stable message."""
    earliest = make_commit("earliest")
    middle = make_commit("middle", parent=earliest)
    latest = make_commit("latest", parent=middle)

    with pytest.raises(
        LinearChainTraversalError,
        match=(
            "^Maximum traversal depth exceeded while walking commit " "chain$"
        ),
    ):
        traverse_linear_chain(latest, "earliest", max_steps=1)


def test_traverse_linear_chain_default_max_steps_stops_before_10001st_parent_read():
    """Default max_steps should trigger before the 10001st parent access."""

    class SelfLoopCommit:
        def __init__(self):
            self.hexsha = "loop"
            self.committed_datetime = datetime(2024, 1, 1, tzinfo=timezone.utc)
            self.message = "loop"
            self.author = Mock()
            self.author.name = "Looper"
            self.parent_reads = 0

        @property
        def parents(self):
            self.parent_reads += 1
            if self.parent_reads > 10_000:
                raise AssertionError(
                    "parents read exceeded default max_steps guard"
                )
            return [self]

    loop_commit = SelfLoopCommit()

    with pytest.raises(
        LinearChainTraversalError,
        match=(
            "^Maximum traversal depth exceeded while walking commit " "chain$"
        ),
    ):
        traverse_linear_chain(loop_commit, "missing-earliest")

    assert loop_commit.parent_reads == 10_000


def test_traverse_linear_chain_raises_on_merge_commit():
    """If an intermediate commit has multiple parents, treat as non-linear."""
    base = make_commit("base")
    p1 = make_commit("p1", parent=base)
    p2 = make_commit("p2", parent=base)

    merge = make_commit("merge")
    merge.parents = [p1, p2]  # Simulate merge

    with pytest.raises(
        LinearChainTraversalError,
        match=(
            "^Encountered a non-linear commit \\(multiple parents\\) in "
            "chain traversal$"
        ),
    ):
        traverse_linear_chain(merge, "base")


def test_traverse_linear_chain_raises_with_exact_message_on_missing_parent():
    """No-parent path should raise a stable, explicit message."""
    root = make_commit("root")
    latest = make_commit("latest", parent=root)
    root.parents = []

    with pytest.raises(
        LinearChainTraversalError,
        match=(
            "^Reached a commit with no parents before finding " "earliest_sha$"
        ),
    ):
        traverse_linear_chain(latest, "missing")


def test_traverse_linear_chain_treats_missing_parents_attribute_as_empty():
    """Commits without a `parents` attribute should behave like no-parent commits."""

    class ParentlessCommit:
        def __init__(self, sha: str):
            self.hexsha = sha
            self.committed_datetime = datetime(2024, 1, 1, tzinfo=timezone.utc)
            self.message = f"Commit {sha}"
            self.author = Mock()
            self.author.name = "NoParents"

    with pytest.raises(
        LinearChainTraversalError,
        match=(
            "^Reached a commit with no parents before finding " "earliest_sha$"
        ),
    ):
        traverse_linear_chain(ParentlessCommit("latest"), "earliest")


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


def test_commits_to_chain_rows_passes_commit_to_branch_getter():
    commit = make_commit("abcdef123456")

    def branch_getter(candidate):
        return "unexpected-none" if candidate is None else candidate.hexsha

    [row] = commits_to_chain_rows([commit], branch_getter=branch_getter)

    assert row["branch"] == "abcdef123456"


def test_commits_to_chain_rows_defaults_empty_for_missing_optional_fields():
    commit = make_commit("abcdef123456")
    commit.hexsha = None
    commit.message = None
    commit.author = None

    [row] = commits_to_chain_rows([commit])

    assert row["hash"] == ""
    assert row["author"] == ""
    assert row["message"] == ""


def test_commits_to_chain_rows_defaults_empty_for_author_without_name():
    commit = make_commit("abcdef123456")
    commit.author = object()

    [row] = commits_to_chain_rows([commit])

    assert row["author"] == ""


def test_commits_to_chain_rows_defaults_empty_when_author_missing():
    class CommitWithoutAuthor:
        def __init__(self):
            self.hexsha = "abcdef123456"
            self.committed_datetime = datetime(
                2024, 1, 1, 15, 30, tzinfo=timezone.utc
            )
            self.message = "Commit message"

    [row] = commits_to_chain_rows([CommitWithoutAuthor()])

    assert row["author"] == ""


def test_commits_to_chain_rows_uses_first_message_line_only():
    commit = make_commit("abcdef123456")
    commit.message = "first line\nsecond line\nthird line"

    [row] = commits_to_chain_rows([commit])

    assert row["message"] == "first line"


def test_commits_to_chain_rows_truncates_long_message():
    long_msg = "X" * 200
    commit = make_commit("c1")
    commit.message = long_msg

    [row] = commits_to_chain_rows([commit])

    assert len(row["message"]) == 100
