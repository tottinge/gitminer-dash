"""Tests for algorithms.analysis_context shared context builders."""

from datetime import datetime, timezone
from unittest.mock import Mock

from algorithms.analysis_context import (
    commit_range_context_from_store,
    date_range_context_from_store,
)


def test_date_range_context_from_store_uses_parser_result():
    period_start = datetime(2026, 1, 2, tzinfo=timezone.utc)
    period_end = datetime(2026, 1, 3, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(period_start, period_end))
    store_data = {"period": "Last 7 days"}

    context = date_range_context_from_store(
        store_data=store_data,
        parse_date_range_fn=parse_date_range_fn,
    )

    assert context.period_start == period_start
    assert context.period_end == period_end
    parse_date_range_fn.assert_called_once_with(store_data)


def test_commit_range_context_from_store_loads_commits_for_parsed_range():
    period_start = datetime(2026, 2, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 2, 2, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(period_start, period_end))
    commits = [{"sha": "abc123"}, {"sha": "def456"}]
    commits_in_period_fn = Mock(return_value=iter(commits))
    ensure_list_fn = list

    context = commit_range_context_from_store(
        store_data={"period": "Last 30 days"},
        parse_date_range_fn=parse_date_range_fn,
        commits_in_period_fn=commits_in_period_fn,
        ensure_list_fn=ensure_list_fn,
    )

    assert context.period_start == period_start
    assert context.period_end == period_end
    assert context.commits_data == commits
    commits_in_period_fn.assert_called_once_with(period_start, period_end)
