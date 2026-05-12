"""Tests for `algorithms/commit_filter.py`."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

from algorithms.commit_filter import (
    _format_commit_data,
    _get_modified_files,
    get_commits_for_group_files,
)


def test_get_modified_files_uses_first_parent_and_collects_paths():
    parent = object()
    commit = SimpleNamespace(parents=[parent])
    commit.diff = Mock(
        return_value=[
            SimpleNamespace(a_path="src/a.py", b_path="src/b.py"),
        ]
    )

    modified_files = _get_modified_files(commit)

    assert modified_files == {"src/a.py", "src/b.py"}
    commit.diff.assert_called_once_with(parent)


def test_get_modified_files_keeps_b_path_when_a_path_attribute_missing():
    parent = object()
    commit = SimpleNamespace(parents=[parent])
    commit.diff = Mock(return_value=[SimpleNamespace(b_path="src/b.py")])

    modified_files = _get_modified_files(commit)

    assert modified_files == {"src/b.py"}


def test_get_modified_files_keeps_a_path_when_b_path_attribute_missing():
    parent = object()
    commit = SimpleNamespace(parents=[parent])
    commit.diff = Mock(return_value=[SimpleNamespace(a_path="src/a.py")])

    modified_files = _get_modified_files(commit)

    assert modified_files == {"src/a.py"}


def test_get_modified_files_never_adds_none_for_b_path():
    parent = object()
    commit = SimpleNamespace(parents=[parent])
    commit.diff = Mock(return_value=[SimpleNamespace(b_path="src/only_b.py")])

    modified_files = _get_modified_files(commit)

    assert modified_files == {"src/only_b.py"}
    assert None not in modified_files


def test_format_commit_data_joins_group_files_with_comma_space():
    commit = SimpleNamespace(
        hexsha="123456789abcdef",
        committed_datetime=datetime(2026, 5, 12, 10, 30, tzinfo=timezone.utc),
        message="feat: improve pipeline\n\nextra details",
    )

    row = _format_commit_data(commit, ["src/b.py", "src/a.py"])

    assert row["group_files"] == "src/a.py, src/b.py"


def test_get_commits_for_group_files_skips_bad_commit_and_continues():
    bad_commit = SimpleNamespace()  # Missing expected attributes -> skipped.
    parent = object()
    good_commit = SimpleNamespace(
        parents=[parent],
        hexsha="abcdef123456",
        committed_datetime=datetime(2026, 5, 11, 12, 0, tzinfo=timezone.utc),
        message="fix: handle edge case",
    )
    good_commit.diff = Mock(
        return_value=[SimpleNamespace(a_path="src/a.py", b_path="src/b.py")]
    )

    rows = get_commits_for_group_files(
        commits_in_period=[bad_commit, good_commit],
        group_files=["src/a.py", "src/b.py", "src/c.py"],
    )

    assert len(rows) == 1
    assert rows[0]["hash"] == "abcdef1"
    assert rows[0]["group_files"] == "src/a.py, src/b.py"
