"""Tests for the concurrent effort (code lines) page callbacks.

These tests focus on the ``update_chain_commits_table`` callback and its
internal branch resolution helper.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


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
@patch("pages.codelines.data.get_repo")
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


@patch("pages.codelines.commits_to_chain_rows")
@patch("pages.codelines.traverse_linear_chain")
@patch("pages.codelines.data.get_repo")
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
