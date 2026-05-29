from types import SimpleNamespace

import pytest

from algorithms.change_series import change_series
from tests import setup_path

setup_path()


def _build_tag_ref(name: str, committed_at, change_types: list[str]):
    diffs = [SimpleNamespace(change_type=change_type) for change_type in change_types]
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


if __name__ == "__main__":
    pytest.main(["-v", __file__])
