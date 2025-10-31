"""
Utility module for date-related operations used across the application.

This module provides common functionality for period selection and date calculations
used by various visualization pages.
"""

from datetime import datetime, timedelta
from typing import Tuple, List, Optional, Dict
from urllib.parse import parse_qs
from dateutil.relativedelta import relativedelta


# Common period options for dropdowns
PERIOD_OPTIONS: list[str] = [
    'Last 7 days',
    'Last 30 days',
    'Last 60 days',
    'Last 90 days',
    'Last 6 Months',
    'Last 1 Year',
    'Last 5 Years',
    'Ever'
]

# Default period used across the app when none is provided
DEFAULT_PERIOD: str = "Last 30 days"

def calculate_date_range(period: str) -> tuple[datetime, datetime]:
    """
    Calculate start and end datetimes for a period, normalized to full-day boundaries.

    - Start is set to 00:00:00 of the start date
    - End is set to 23:59:59 of the end date (today for relative ranges)

    Args:
        period: A string representing the time period (e.g., 'Last 30 days', 'Ever')
                If None or empty, defaults to "30 days"

    Returns:
        A tuple of (begin_date, end_date) as timezone-aware datetime objects

    Examples:
        >>> from datetime import datetime, timedelta
        >>> end = datetime(2025, 10, 22, 17, 59).astimezone()
        >>> begin, actual_end = calculate_date_range('Last 30 days')
        >>> actual_end.date() == datetime.today().date()
        True
        >>> (actual_end.date() - begin.date()).days
        30
    """
    now = datetime.today().astimezone()
    # Normalize "end" to end-of-day
    end = now.replace(hour=23, minute=59, second=59, microsecond=0)
    period = period or "30 days"

    lower = period.lower()
    if "last 7 " in lower:
        begin = (end - timedelta(days=7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif "30" in lower:
        begin = (end - timedelta(days=30)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif "60" in lower:
        begin = (end - timedelta(days=60)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif "90" in lower:
        begin = (end - timedelta(days=90)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif "6 months" in lower:
        begin = (end - relativedelta(months=6)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif "1 year" in lower:
        begin = (end - relativedelta(years=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif "5 years" in lower:
        begin = (end - relativedelta(years=5)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    else:
        # Ever
        begin = end.replace(
            year=1970, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        return begin, end

    return begin, end




def to_iso_range(begin: datetime, end: datetime) -> dict[str, str]:
    """Return JSON-serializable ISO strings for date range."""
    return {"begin": begin.isoformat(), "end": end.isoformat()}


def parse_date_range_from_store(store_data) -> tuple[datetime, datetime]:
    """
    Extract date range from global store data.

    Handles both period-based ranges (e.g., "Last 30 days") and explicit
    begin/end dates stored in the global-date-range store.

    Args:
        store_data: Dictionary from global-date-range store, or None

    Returns:
        A tuple of (start_date, end_date) as timezone-aware datetime objects

    Examples:
        >>> store = {"period": "Last 30 days"}
        >>> start, end = parse_date_range_from_store(store)
        >>> isinstance(start, datetime)
        True

        >>> store = {"begin": "2024-01-01T00:00:00+00:00", "end": "2024-01-31T23:59:59+00:00"}
        >>> start, end = parse_date_range_from_store(store)
        >>> start.day
        1
    """
    if isinstance(store_data, dict):
        period = store_data.get("period", DEFAULT_PERIOD)
    else:
        period = DEFAULT_PERIOD

    if isinstance(store_data, dict) and "begin" in store_data and "end" in store_data:
        start = datetime.fromisoformat(store_data["begin"])
        end = datetime.fromisoformat(store_data["end"])
    else:
        start, end = calculate_date_range(period)

    return start, end
