"""Shared helpers for building page analysis contexts from date-range store data."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from utils.git import ensure_list

DateRangeParser = Callable[[Any], tuple[datetime, datetime]]
CommitsInPeriodLoader = Callable[[datetime, datetime], Iterable[Any]]


@dataclass(frozen=True)
class DateRangeContext:
    """Normalized date-range context used by page callbacks."""

    period_start: datetime
    period_end: datetime


@dataclass(frozen=True)
class CommitRangeContext(DateRangeContext):
    """Date-range context extended with loaded commits for that range."""

    commits_data: list[Any]


def date_range_context_from_store(
    store_data,
    *,
    parse_date_range_fn: DateRangeParser,
) -> DateRangeContext:
    """Build date-range context by parsing global store data."""
    period_start, period_end = parse_date_range_fn(store_data)
    return DateRangeContext(
        period_start=period_start,
        period_end=period_end,
    )


def commit_range_context_from_store(
    store_data,
    *,
    parse_date_range_fn: DateRangeParser,
    commits_in_period_fn: CommitsInPeriodLoader,
    ensure_list_fn: Callable[[Iterable[Any] | None], list[Any]] = ensure_list,
) -> CommitRangeContext:
    """Build date-range context and materialized commits for that range."""
    date_range_context = date_range_context_from_store(
        store_data=store_data,
        parse_date_range_fn=parse_date_range_fn,
    )
    commits_data = ensure_list_fn(
        commits_in_period_fn(
            date_range_context.period_start,
            date_range_context.period_end,
        )
    )
    return CommitRangeContext(
        period_start=date_range_context.period_start,
        period_end=date_range_context.period_end,
        commits_data=commits_data,
    )
