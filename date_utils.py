"""
Utility module for date-related operations used across the application.

This module provides common functionality for period selection and date calculations
used by various visualization pages.
"""
from datetime import datetime, timedelta
from typing import Tuple, List
import calendar
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

def calculate_date_range(period: str) -> Tuple[datetime, datetime]:
    """
    Calculate start and end dates based on the selected period.
    
    Args:
        period: A string representing the time period (e.g., 'Last 30 days', 'Ever')
                If None or empty, defaults to "30 days"
    
    Returns:
        A tuple of (begin_date, end_date) as datetime objects with timezone info
    
    Examples:
        >>> from datetime import datetime, timedelta
        >>> end = datetime(2025, 10, 22, 17, 59).astimezone()
        >>> begin, actual_end = calculate_date_range('Last 30 days')
        >>> actual_end.date() == datetime.today().date()
        True
        >>> (actual_end - begin).days
        30
    """
    end = datetime.today().astimezone()
    period = period or "30 days"
    
    match period.lower():
        case p if "7" in p:
            begin = end - timedelta(days=7)
        case p if "30" in p:
            begin = end - timedelta(days=30)
        case p if "60" in p:
            begin = end - timedelta(days=60)
        case p if "90" in p:
            begin = end - timedelta(days=90)
        case p if "6 months" in p:
            begin = end - relativedelta(months=6)
        case p if "1 year" in p:
            begin = end - relativedelta(years=1)
        case p if "5 years" in p:
            begin = end - relativedelta(years=5)
        case _:
            begin = datetime(1970, 1, 1, tzinfo=end.tzinfo)
    
    return begin, end