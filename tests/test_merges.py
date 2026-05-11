"""Tests for merge page data preparation."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest

from tests import setup_path

setup_path()


@pytest.fixture(autouse=True)
def _stub_dash_register_page(monkeypatch):
    """Prevent Dash page registration side effects during imports."""
    monkeypatch.setattr("dash.register_page", lambda *args, **kwargs: None)


def _make_commit(
    *,
    sha: str,
    when: datetime,
    message: str,
    parent_count: int,
    lines: int,
    files: int,
):
    return SimpleNamespace(
        hexsha=sha,
        committed_datetime=when,
        message=message,
        parents=[object() for _ in range(parent_count)],
        stats=SimpleNamespace(total={"lines": lines, "files": files}),
    )


def test_prepare_dataframe_filters_only_merges_and_preserves_schema(
    monkeypatch,
):
    """Only commits with >1 parent should be returned with exact schema."""
    from pages import merges

    non_merge_commit = _make_commit(
        sha="non-merge",
        when=datetime(2025, 1, 2, 12, 0, 0),
        message="normal commit",
        parent_count=1,
        lines=999,
        files=999,
    )
    merge_commit = _make_commit(
        sha="merge-2-parents",
        when=datetime(2025, 1, 1, 12, 0, 0),
        message="merge commit",
        parent_count=2,
        lines=30,
        files=4,
    )

    monkeypatch.setattr(
        merges.repo_context,
        "commits_in_period",
        lambda _start, _end: [non_merge_commit, merge_commit],
    )

    data_frame = merges.prepare_dataframe(
        datetime(2025, 1, 1, 0, 0, 0),
        datetime(2025, 1, 31, 0, 0, 0),
    )

    assert list(data_frame.columns) == [
        "hash",
        "date",
        "comment",
        "lines",
        "files",
    ]
    assert len(data_frame) == 1
    row = data_frame.iloc[0]
    assert row["hash"] == "merge-2-parents"
    assert row["comment"] == "merge commit"
    assert row["lines"] == 30
    assert row["files"] == 4


def test_prepare_dataframe_sorts_rows_by_commit_date(monkeypatch):
    """Returned merge rows should be sorted ascending by date."""
    from pages import merges

    newer_merge = _make_commit(
        sha="newer",
        when=datetime(2025, 2, 3, 8, 0, 0),
        message="newer merge",
        parent_count=2,
        lines=10,
        files=1,
    )
    older_merge = _make_commit(
        sha="older",
        when=datetime(2025, 1, 3, 8, 0, 0),
        message="older merge",
        parent_count=2,
        lines=20,
        files=2,
    )

    monkeypatch.setattr(
        merges.repo_context,
        "commits_in_period",
        lambda _start, _end: [newer_merge, older_merge],
    )

    data_frame = merges.prepare_dataframe(
        datetime(2025, 1, 1, 0, 0, 0),
        datetime(2025, 2, 28, 0, 0, 0),
    )

    assert list(data_frame["hash"]) == ["older", "newer"]
    assert list(data_frame["date"]) == [
        datetime(2025, 1, 3, 8, 0, 0).date(),
        datetime(2025, 2, 3, 8, 0, 0).date(),
    ]
