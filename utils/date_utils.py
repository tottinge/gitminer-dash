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
PERIOD_OPTIONS: List[str] = [
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
DEFAULT_PERIOD: str = 'Last 30 days'

def calculate_date_range(period: str) -> Tuple[datetime, datetime]:
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
        begin = (end - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif "30" in lower:
        begin = (end - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif "60" in lower:
        begin = (end - timedelta(days=60)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif "90" in lower:
        begin = (end - timedelta(days=90)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif "6 months" in lower:
        begin = (end - relativedelta(months=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif "1 year" in lower:
        begin = (end - relativedelta(years=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif "5 years" in lower:
        begin = (end - relativedelta(years=5)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # Ever
        begin = end.replace(year=1970, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return begin, end

    return begin, end


def parse_period_from_query(search: Optional[str]) -> Optional[str]:
    """
    Parse a URL search string (e.g. "?period=Last+60+days") and return a period label
    matching PERIOD_OPTIONS when possible.

    Supports either:
      - period=Last+60+days (string label)
      - from=YYYY-MM-DD&to=YYYY-MM-DD (falls back to best-fitting label; if not exact, returns None)

    Returns a period string if detected, otherwise None.
    """
    if not search:
        return None
    s = search.lstrip('?')
    qs = parse_qs(s)
    period_vals = qs.get('period')
    if period_vals:
        # normalize spacing and case to match one of the PERIOD_OPTIONS
        candidate = period_vals[0].replace('+', ' ').strip()
        # Attempt loose matching by lowercase compare
        for option in PERIOD_OPTIONS:
            if option.lower() == candidate.lower():
                return option
        # If not an exact known option, return the original candidate
        return candidate

    frm = qs.get('from')
    to = qs.get('to')
    if frm and to:
        # If explicit range supplied, do not infer a label aggressively
        # Let caller decide default label; we just signal that custom range exists
        return None
    return None


def to_iso_range(begin: datetime, end: datetime) -> Dict[str, str]:
    """Return JSON-serializable ISO strings for date range."""
    return {"begin": begin.isoformat(), "end": end.isoformat()}
