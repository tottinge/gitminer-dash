from types import SimpleNamespace

import pytest

from algorithms.change_series import _summarize_change_types, change_series
from tests import setup_path

setup_path()


def _build_tag_ref(name: str, committed_at, change_types: list[str]):
    diffs = [
        SimpleNamespace(change_type=change_type) for change_type in change_types
    ]
    commit = SimpleNamespace(
        committed_datetime=committed_at,
        diff=lambda _other: diffs,
    )
    return SimpleNamespace(name=name, commit=commit)


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


if __name__ == "__main__":
    pytest.main(["-v", __file__])
