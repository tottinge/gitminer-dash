"""Tests for the concurrent effort (code lines) page callbacks.

These tests focus on the ``update_chain_commits_table`` callback and its
internal branch resolution helper.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _stub_dash_register_page(monkeypatch):
    """Prevent Dash page registration side effects during unit-test imports."""
    monkeypatch.setattr("dash.register_page", lambda *args, **kwargs: None)


@pytest.mark.parametrize(
    "click_data",
    [
        None,
        {},
        {"points": []},
    ],
)
def test_update_chain_commits_table_returns_empty_for_missing_points(
    click_data,
):
    """Return an empty list when clickData is missing or has no usable points.

    Covers:
    1. clickData is None.
    2. clickData does not contain "points".
    3. clickData has an empty "points" list.
    """
    from pages.codelines import update_chain_commits_table

    result = update_chain_commits_table(click_data)

    assert result == []


def test_update_chain_commits_table_returns_empty_for_insufficient_customdata():
    """Return an empty list when clickData's points lack sufficient customdata.

    The callback requires at least two values in ``customdata`` (head and tail
    SHAs). If fewer are provided, it should return an empty list.
    """
    from pages.codelines import update_chain_commits_table

    click_data = {
        "points": [
            {
                # Only one value provided instead of the required head & tail.
                "customdata": ["only_head_sha"],
            }
        ]
    }

    result = update_chain_commits_table(click_data)

    assert result == []


class DummyRef:
    """Simple reference object holding a name attribute."""

    def __init__(self, name: str) -> None:
        self.name = name


class DummyCommitWithRefs:
    """Commit mock that exposes refs for branch detection tests."""

    def __init__(self, ref_name: str) -> None:
        self.refs = [DummyRef(ref_name)]


class DummyCommitWithNameRev:
    """Commit mock that exposes name_rev for branch detection tests."""

    def __init__(self, name_rev: str) -> None:
        # No refs so that _branch_for_commit falls back to name_rev.
        self.refs = []
        self.name_rev = name_rev


@patch("pages.codelines.commits_to_chain_rows")
@patch("pages.codelines.traverse_linear_chain")
@patch("pages.codelines.repo_context.get_repo")
def test_branch_for_commit_uses_refs_to_extract_branch(
    mock_get_repo, mock_traverse_linear_chain, mock_commits_to_chain_rows
):
    """_branch_for_commit prefers commit.refs and strips prefixes like "origin/".

    Example: a ref named "origin/main" should yield "main".
    """
    from pages.codelines import update_chain_commits_table

    # Arrange a commit whose branch should be derived from its refs.
    commit = DummyCommitWithRefs("origin/main")

    class DummyRepo:
        def commit(self, _sha):  # pragma: no cover - trivial passthrough
            return commit

    mock_get_repo.return_value = DummyRepo()
    mock_traverse_linear_chain.return_value = [commit]

    def fake_commits_to_chain_rows(chain_commits, branch_getter):
        # Use the provided branch_getter to compute branch names for the chain.
        branches = [branch_getter(c) for c in chain_commits]
        return [{"branch": b} for b in branches]

    mock_commits_to_chain_rows.side_effect = fake_commits_to_chain_rows

    click_data = {"points": [{"customdata": ["earliest", "latest"]}]}

    rows = update_chain_commits_table(click_data)

    assert rows == [{"branch": "main"}]


def test_branch_for_commit_returns_empty_when_refs_and_name_rev_absent():
    """Missing refs/name_rev attributes should resolve to empty branch."""
    from pages.codelines import branch_for_commit

    class MinimalCommit:
        pass

    assert branch_for_commit(MinimalCommit()) == ""


def test_branch_for_commit_skips_blank_refs_and_uses_next_leaf_name():
    """Blank ref names should be skipped and later refs should still be considered."""
    from pages.codelines import branch_for_commit

    class CommitWithMixedRefs:
        def __init__(self):
            self.refs = [DummyRef(""), DummyRef("origin/feature/cool")]

    assert branch_for_commit(CommitWithMixedRefs()) == "cool"


def test_branch_for_commit_missing_ref_name_attribute_returns_empty():
    """Refs without `name` should not fabricate a branch name."""
    from pages.codelines import branch_for_commit

    class RefWithoutName:
        pass

    class CommitWithUnnamedRef:
        def __init__(self):
            self.refs = [RefWithoutName()]

    assert branch_for_commit(CommitWithUnnamedRef()) == ""


def test_branch_for_commit_name_rev_with_single_token_returns_empty():
    """A single-token name_rev cannot contain branch metadata and should return empty."""
    from pages.codelines import branch_for_commit

    class CommitWithSingleTokenNameRev:
        def __init__(self):
            self.refs = []
            self.name_rev = "deadbeef"

    assert branch_for_commit(CommitWithSingleTokenNameRev()) == ""


def test_branch_for_commit_name_rev_extracts_leaf_from_nested_path():
    """Fallback parsing should return the leaf branch component from nested refs."""
    from pages.codelines import branch_for_commit

    class CommitWithNestedNameRev:
        def __init__(self):
            self.refs = []
            self.name_rev = "deadbeef refs/remotes/origin/main"

    assert branch_for_commit(CommitWithNestedNameRev()) == "main"


def test_branch_for_commit_non_string_name_rev_is_ignored():
    """Non-string name_rev values should be ignored safely."""
    from pages.codelines import branch_for_commit

    class CommitWithNonStringNameRev:
        def __init__(self):
            self.refs = []
            self.name_rev = 123

    assert branch_for_commit(CommitWithNonStringNameRev()) == ""


def test_branch_for_commit_missing_name_rev_attr_with_empty_refs_returns_empty():
    """When refs exist but name_rev does not, branch lookup should still return empty."""
    from pages.codelines import branch_for_commit

    class CommitWithRefsOnly:
        def __init__(self):
            self.refs = []

    assert branch_for_commit(CommitWithRefsOnly()) == ""


@patch("pages.codelines.commits_to_chain_rows")
@patch("pages.codelines.traverse_linear_chain")
@patch("pages.codelines.repo_context.get_repo")
def test_branch_for_commit_uses_name_rev_when_refs_missing(
    mock_get_repo, mock_traverse_linear_chain, mock_commits_to_chain_rows
):
    """_branch_for_commit falls back to commit.name_rev when refs are absent.

    Example: a name_rev string "<sha> main" should yield "main".
    """
    from pages.codelines import update_chain_commits_table

    commit = DummyCommitWithNameRev("deadbeef main")

    class DummyRepo:
        def commit(self, _sha):  # pragma: no cover - trivial passthrough
            return commit

    mock_get_repo.return_value = DummyRepo()
    mock_traverse_linear_chain.return_value = [commit]

    def fake_commits_to_chain_rows(chain_commits, branch_getter):
        branches = [branch_getter(c) for c in chain_commits]
        return [{"branch": b} for b in branches]

    mock_commits_to_chain_rows.side_effect = fake_commits_to_chain_rows

    click_data = {"points": [{"customdata": ["earliest", "latest"]}]}

    rows = update_chain_commits_table(click_data)

    assert rows == [{"branch": "main"}]
