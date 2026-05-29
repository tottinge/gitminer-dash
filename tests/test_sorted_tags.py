import pytest

from algorithms.sorted_tags import get_most_recent_tags

# ... (existing tests)

"""Tests for `algorithms/sorted_tags.py`."""

from datetime import datetime, timezone
from types import SimpleNamespace

from tests import setup_path

setup_path()


def _build_tag(name: str, day: int):
    authored_datetime = datetime(2026, 1, day, tzinfo=timezone.utc)
    commit = SimpleNamespace(authored_datetime=authored_datetime)
    return SimpleNamespace(name=name, commit=commit)


def _build_repo_with_tags(tags):
    return SimpleNamespace(tags=list(tags))


def _tag_names(tags):
    return [tag.name for tag in tags]


def test_get_most_recent_tags_returns_empty_for_non_positive_desired():
    repo = _build_repo_with_tags([_build_tag("v1.0.0", 1)])

    assert get_most_recent_tags(repo, desired=0) == []
    assert get_most_recent_tags(repo, desired=-1) == []


def test_get_most_recent_tags_returns_latest_tag_when_desired_is_one():
    repo = _build_repo_with_tags(
        [
            _build_tag("v3.0.0", 3),
            _build_tag("v1.0.0", 1),
            _build_tag("v2.0.0", 2),
        ]
    )

    tags = get_most_recent_tags(repo, desired=1)

    assert _tag_names(tags) == ["v3.0.0"]


def test_get_most_recent_tags_returns_latest_n_tags_in_chronological_order():
    repo = _build_repo_with_tags(
        [
            _build_tag("v2.0.0", 2),
            _build_tag("v4.0.0", 4),
            _build_tag("v1.0.0", 1),
            _build_tag("v3.0.0", 3),
        ]
    )

    tags = get_most_recent_tags(repo, desired=2)

    assert _tag_names(tags) == ["v3.0.0", "v4.0.0"]


def test_get_most_recent_tags_returns_all_available_tags_when_desired_is_larger():
    repo = _build_repo_with_tags(
        [
            _build_tag("v2.0.0", 2),
            _build_tag("v1.0.0", 1),
        ]
    )

    tags = get_most_recent_tags(repo, desired=5)

    assert _tag_names(tags) == ["v1.0.0", "v2.0.0"]
