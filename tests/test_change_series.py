"""Unit tests for `algorithms/change_series.py`."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from tests import setup_path

setup_path()

from algorithms.change_series import _summarize_change_types, change_series


def _change(change_type: str) -> SimpleNamespace:
    return SimpleNamespace(change_type=change_type)


def _commit(committed_datetime: datetime) -> MagicMock:
    commit = MagicMock()
    commit.committed_datetime = committed_datetime
    return commit


def _commit_ref(name: str, commit: MagicMock) -> SimpleNamespace:
    return SimpleNamespace(name=name, commit=commit)


def _build_tag_ref(name: str, committed_at, change_types: list[str]):
    diffs = [
        SimpleNamespace(change_type=change_type) for change_type in change_types
    ]
    commit = SimpleNamespace(
        committed_datetime=committed_at,
        diff=lambda _other: diffs,
    )
    return SimpleNamespace(name=name, commit=commit)


def test_change_series_returns_empty_when_commit_refs_is_empty():
    start_commit = _commit(datetime(2026, 1, 1, tzinfo=timezone.utc))
    start_ref = _commit_ref(name="v1.0", commit=start_commit)

    rows = list(change_series(start=start_ref, commit_refs=[]))

    assert rows == []
    start_commit.diff.assert_not_called()


def test_change_series_yields_expected_summaries_and_diff_chain():
    start_commit = _commit(datetime(2026, 1, 1, tzinfo=timezone.utc))
    first_commit = _commit(datetime(2026, 1, 2, tzinfo=timezone.utc))
    second_commit = _commit(datetime(2026, 1, 3, tzinfo=timezone.utc))

    start_commit.diff.return_value = [_change("A"), _change("M")]
    first_commit.diff.return_value = [_change("D"), _change("R"), _change("R")]

    start_ref = _commit_ref(name="v1.0", commit=start_commit)
    first_ref = _commit_ref(name="v1.1", commit=first_commit)
    second_ref = _commit_ref(name="v1.2", commit=second_commit)

    rows = list(
        change_series(start=start_ref, commit_refs=[first_ref, second_ref])
    )

    assert len(rows) == 2

    first_row = rows[0]
    assert first_row["Date"] == first_commit.committed_datetime.date()
    assert first_row["Name"] == "v1.1"
    assert first_row["Files Added"] == 1
    assert first_row["Files Modified"] == 1
    assert first_row.get("Files Deleted", 0) == 0
    assert first_row.get("Files Renamed", 0) == 0

    second_row = rows[1]
    assert second_row["Date"] == second_commit.committed_datetime.date()
    assert second_row["Name"] == "v1.2"
    assert second_row["Files Deleted"] == 1
    assert second_row["Files Renamed"] == 2
    assert second_row.get("Files Added", 0) == 0
    assert second_row.get("Files Modified", 0) == 0

    # Guard key names against accidental drift.
    for row in rows:
        assert "Date" in row
        assert "Name" in row
        assert "XXDateXX" not in row
        assert "XXNameXX" not in row
        assert "date" not in row
        assert "DATE" not in row
        assert "name" not in row
        assert "NAME" not in row

    start_commit.diff.assert_called_once_with(first_commit)
    first_commit.diff.assert_called_once_with(second_commit)
    second_commit.diff.assert_not_called()


def test_change_series_groups_unknown_change_type_under_other():
    start = _build_tag_ref(
        name="v1.0.0",
        committed_at=None,
        change_types=["M", "T"],
    )
    next_ref = _build_tag_ref(
        name="v1.0.1",
        committed_at=SimpleNamespace(date=lambda: "2026-05-29"),
        change_types=[],
    )

    rows = list(change_series(start=start, commit_refs=[next_ref]))

    assert len(rows) == 1
    row = rows[0]
    assert row["Files Modified"] == 1
    assert row["Other"] == 1


def test_change_series_uses_expected_diff_targets_across_refs():
    start_commit = SimpleNamespace(committed_datetime=None)
    middle_commit = SimpleNamespace(
        committed_datetime=SimpleNamespace(date=lambda: "2026-05-29")
    )
    end_commit = SimpleNamespace(
        committed_datetime=SimpleNamespace(date=lambda: "2026-05-30")
    )

    diff_targets = []

    def start_diff(other):
        diff_targets.append(other)
        change_type = "A" if other is middle_commit else "D"
        return [SimpleNamespace(change_type=change_type)]

    def middle_diff(other):
        diff_targets.append(other)
        change_type = "M" if other is end_commit else "R"
        return [SimpleNamespace(change_type=change_type)]

    start_commit.diff = start_diff
    middle_commit.diff = middle_diff
    end_commit.diff = lambda _other: []

    start_ref = SimpleNamespace(name="v1.0.0", commit=start_commit)
    middle_ref = SimpleNamespace(name="v1.0.1", commit=middle_commit)
    end_ref = SimpleNamespace(name="v1.0.2", commit=end_commit)

    rows = list(
        change_series(start=start_ref, commit_refs=[middle_ref, end_ref])
    )

    assert len(rows) == 2
    assert diff_targets == [middle_commit, end_commit]
    assert rows[0]["Files Added"] == 1
    assert "Files Deleted" not in rows[0]
    assert rows[1]["Files Modified"] == 1
    assert "Files Renamed" not in rows[1]


def test_summarize_change_types_handles_missing_change_type_as_other():
    diffs = [SimpleNamespace(change_type="M"), SimpleNamespace()]

    counts = _summarize_change_types(diffs)

    assert counts["Files Modified"] == 1
    assert counts["Other"] == 1
    assert None not in counts
