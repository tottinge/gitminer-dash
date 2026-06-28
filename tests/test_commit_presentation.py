"""Tests for `algorithms/commit_presentation.py`."""

from datetime import datetime, timezone
from types import SimpleNamespace

from algorithms.commit_presentation import present_commit


def test_present_commit_default_message_parsing_and_truncation():
    commit = SimpleNamespace(
        hexsha="abcdef1234567890",
        committed_datetime=datetime(2026, 6, 1, 9, 15, tzinfo=timezone.utc),
        author=SimpleNamespace(name="Alice"),
        message=("first line is long " + "x" * 120 + "\nsecond line"),
    )

    result = present_commit(
        commit,
        timestamp_format="%Y-%m-%d %H:%M",
        actor_attribute_name="author",
    )

    assert result.short_hash == "abcdef1"
    assert result.timestamp == "2026-06-01 09:15"
    assert result.actor == "Alice"
    assert "\n" not in result.message
    assert len(result.message) == 100


def test_present_commit_handles_missing_optional_fields():
    commit = SimpleNamespace(
        hexsha=None,
        committed_datetime=None,
        message=None,
    )

    result = present_commit(
        commit,
        timestamp_format="%Y-%m-%d %H:%M",
        actor_attribute_name="author",
    )

    assert result.short_hash == ""
    assert result.timestamp == ""
    assert result.actor == ""
    assert result.message == ""


def test_present_commit_supports_custom_message_selector_without_truncation():
    commit = SimpleNamespace(
        hexsha="1234567890",
        committed_datetime=datetime(2026, 6, 2, 10, 30, tzinfo=timezone.utc),
        committer=SimpleNamespace(name="Bob"),
        summary="summary text that should remain whole",
    )

    result = present_commit(
        commit,
        timestamp_format="%Y-%m-%d %H:%M:%S",
        actor_attribute_name="committer",
        message_selector=lambda current_commit: current_commit.summary,
        max_message_length=None,
    )

    assert result.short_hash == "1234567"
    assert result.timestamp == "2026-06-02 10:30:00"
    assert result.actor == "Bob"
    assert result.message == "summary text that should remain whole"
