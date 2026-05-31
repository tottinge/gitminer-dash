import inspect
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pandas as pd

from algorithms import conventional_commits
from algorithms.conventional_commits import (
    normalize_intent,
    prepare_changes_by_date,
)


def _commit(message: str, committed_datetime: datetime) -> SimpleNamespace:
    return SimpleNamespace(
        message=message,
        committed_datetime=committed_datetime,
    )


def test_prepare_changes_by_date_returns_expected_columns_with_empty_input():
    result = prepare_changes_by_date([])
    assert list(result.columns) == ["date", "reason", "count"]
    assert result.empty


def test_normalize_intent_exact_category_is_case_insensitive():
    assert normalize_intent("Fix") == "fix"


def test_normalize_intent_returns_unknown_for_unmatched_values():
    assert normalize_intent("definitely-not-a-category") == "unknown"


def test_normalize_intent_maps_partial_feature_label_to_feat(monkeypatch):
    monkeypatch.setattr(
        conventional_commits,
        "categories",
        (
            "build",
            "chore",
            "ci",
            "docs",
            "feat",
            "fix",
            "merge",
            "perf",
            "refactor",
            "revert",
            "style",
            "test",
        ),
    )
    assert normalize_intent("feature") == "feat"


def test_prepare_changes_by_date_aggregates_counts_by_date_and_reason():
    commits = [
        _commit(
            "feat(parser): add parser",
            datetime(2026, 1, 2, 13, 0, tzinfo=timezone.utc),
        ),
        _commit(
            "feat(ui): add UI",
            datetime(2026, 1, 2, 21, 0, tzinfo=timezone.utc),
        ),
        _commit(
            "FIX: repair bug",
            datetime(2026, 1, 3, 10, 0, tzinfo=timezone.utc),
        ),
        _commit(
            "this is not a conventional commit",
            datetime(2026, 1, 3, 11, 0, tzinfo=timezone.utc),
        ),
    ]

    result = prepare_changes_by_date(commits)

    assert list(result.columns) == ["date", "reason", "count"]
    assert len(result) == 2

    expected = pd.DataFrame(
        [
            [datetime(2026, 1, 2, tzinfo=timezone.utc).date(), "feat", 2],
            [datetime(2026, 1, 3, tzinfo=timezone.utc).date(), "fix", 1],
        ],
        columns=["date", "reason", "count"],
    )

    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected)


def test_prepare_changes_by_date_default_weeks_parameter_is_none():
    default_weeks = (
        inspect.signature(prepare_changes_by_date).parameters["weeks"].default
    )
    assert default_weeks is None


def test_prepare_changes_by_date_default_excludes_commit_older_than_twelve_weeks():
    latest = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
    older_than_default = latest - timedelta(weeks=13)

    commits = [
        _commit("feat(core): latest", latest),
        _commit("fix(core): old", older_than_default),
    ]

    result = prepare_changes_by_date(commits)

    assert list(result["date"]) == [latest.date()]
    assert list(result["reason"]) == ["feat"]
    assert list(result["count"]) == [1]


def test_prepare_changes_by_date_includes_commit_exactly_at_lookback_boundary():
    latest = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
    exactly_at_boundary = latest - timedelta(weeks=12)

    commits = [
        _commit("feat(core): latest", latest),
        _commit("fix(core): boundary", exactly_at_boundary),
    ]

    result = prepare_changes_by_date(commits)

    assert list(result["date"]) == [exactly_at_boundary.date(), latest.date()]
    assert list(result["reason"]) == ["fix", "feat"]
    assert list(result["count"]) == [1, 1]
