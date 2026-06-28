"""Unit tests for `algorithms/sorted_tags.py`."""

from datetime import datetime, timezone
from types import SimpleNamespace

from tests import setup_path

setup_path()

from algorithms.sorted_tags import get_most_recent_tags


def _tag(name: str, year: int, month: int, day: int) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        commit=SimpleNamespace(
            authored_datetime=datetime(year, month, day, tzinfo=timezone.utc)
        ),
    )


def _repo_with_unsorted_tags() -> SimpleNamespace:
    v10 = _tag("v1.0", 2026, 1, 1)
    v11 = _tag("v1.1", 2026, 1, 2)
    v12 = _tag("v1.2", 2026, 1, 3)
    v13 = _tag("v1.3", 2026, 1, 4)
    # Intentionally unsorted by authored_datetime.
    return SimpleNamespace(tags=[v12, v10, v13, v11])


def test_get_most_recent_tags_returns_latest_in_datetime_order():
    repo = _repo_with_unsorted_tags()

    tags = get_most_recent_tags(repo, desired=2)

    assert [tag.name for tag in tags] == ["v1.2", "v1.3"]


def test_get_most_recent_tags_desired_one_returns_single_latest_tag():
    repo = _repo_with_unsorted_tags()

    tags = get_most_recent_tags(repo, desired=1)

    assert [tag.name for tag in tags] == ["v1.3"]


def test_get_most_recent_tags_desired_larger_than_available_returns_all():
    repo = _repo_with_unsorted_tags()

    tags = get_most_recent_tags(repo, desired=10)

    assert [tag.name for tag in tags] == ["v1.0", "v1.1", "v1.2", "v1.3"]


def test_get_most_recent_tags_non_positive_desired_returns_empty():
    repo = _repo_with_unsorted_tags()

    assert get_most_recent_tags(repo, desired=0) == []
    assert get_most_recent_tags(repo, desired=-1) == []
