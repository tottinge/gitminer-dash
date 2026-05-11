"""
Tests for the date_utils module.

This module contains tests for the date_utils module using pytest.
"""

from tests import setup_path

setup_path()
from datetime import datetime

import pytest

from utils import date_utils

MOCK_DATE = datetime(2025, 10, 22, 17, 0)


@pytest.fixture
def mock_datetime(monkeypatch):
    """Fixture to mock datetime.today() to return a fixed date."""

    class MockDatetime:

        @classmethod
        def today(cls):
            return MOCK_DATE

        @staticmethod
        def astimezone(dt):
            return dt

    monkeypatch.setattr(date_utils, "datetime", MockDatetime)
    original_datetime = datetime

    class MockDatetimeWithConstructor(MockDatetime):

        def __new__(cls, *args, **kwargs):
            if args or kwargs:
                return original_datetime(*args, **kwargs)
            return super().__new__(cls)

    return MockDatetimeWithConstructor


def test_calculate_date_range_7_days(mock_datetime):
    """Test calculate_date_range with 'Last 7 days'."""
    (begin, end) = date_utils.calculate_date_range("Last 7 days")
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 10, 15).date()
    assert (end.date() - begin.date()).days == 7


def test_calculate_date_range_30_days(mock_datetime):
    """Test calculate_date_range with 'Last 30 days'."""
    (begin, end) = date_utils.calculate_date_range("Last 30 days")
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 9, 22).date()
    assert (end.date() - begin.date()).days == 30


def test_calculate_date_range_60_days(mock_datetime):
    """Test calculate_date_range with 'Last 60 days'."""
    (begin, end) = date_utils.calculate_date_range("Last 60 days")
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 8, 23).date()
    assert (end.date() - begin.date()).days == 60


def test_calculate_date_range_90_days(mock_datetime):
    """Test calculate_date_range with 'Last 90 days'."""
    (begin, end) = date_utils.calculate_date_range("Last 90 days")
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 7, 24).date()
    assert (end.date() - begin.date()).days == 90


def test_calculate_date_range_6_months(mock_datetime):
    """Test calculate_date_range with 'Last 6 Months'."""
    (begin, end) = date_utils.calculate_date_range("Last 6 Months")
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 4, 22).date()


@pytest.mark.parametrize(
    "period_label",
    [
        "Last 7 days",
        "Last 30 days",
        "Last 60 days",
        "Last 90 days",
        "Last 6 Months",
        "Last 1 Year",
        "Last 5 Years",
        "Ever",
    ],
)
def test_calculate_date_range_has_full_day_times(mock_datetime, period_label):
    """Start is at 00:00:00 and end is at 23:59:59 for all supported periods."""
    begin, end = date_utils.calculate_date_range(period_label)
    assert (begin.hour, begin.minute, begin.second, begin.microsecond) == (
        0,
        0,
        0,
        0,
    )
    assert (end.hour, end.minute, end.second, end.microsecond) == (
        23,
        59,
        59,
        0,
    )


def test_calculate_date_range_1_year(mock_datetime):
    """Test calculate_date_range with 'Last 1 Year'."""
    (begin, end) = date_utils.calculate_date_range("Last 1 Year")
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2024, 10, 22).date()
    assert begin.year == end.year - 1
    assert begin.month == end.month
    assert begin.day == end.day


def test_calculate_date_range_5_years(mock_datetime):
    """Test calculate_date_range with 'Last 5 Years'."""
    (begin, end) = date_utils.calculate_date_range("Last 5 Years")
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2020, 10, 22).date()
    assert begin.year == end.year - 5
    assert begin.month == end.month
    assert begin.day == end.day


def test_calculate_date_range_ever(monkeypatch):
    """Test calculate_date_range with 'Ever'."""

    class MockDatetime:

        @classmethod
        def today(cls):
            return MOCK_DATE

        @staticmethod
        def astimezone(dt):
            return dt

        def __call__(self, *args, **kwargs):
            return datetime(*args, **kwargs)

    mock_dt = MockDatetime()
    monkeypatch.setattr(date_utils, "datetime", mock_dt)
    (begin, end) = date_utils.calculate_date_range("Ever")
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(1970, 1, 1).date()


def test_calculate_date_range_default_none(mock_datetime):
    """Test calculate_date_range with None (default)."""
    (begin, end) = date_utils.calculate_date_range(None)
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 9, 22).date()
    assert (end.date() - begin.date()).days == 30


def test_calculate_date_range_default_empty(mock_datetime):
    """Test calculate_date_range with empty string (default)."""
    (begin, end) = date_utils.calculate_date_range("")
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 9, 22).date()
    assert (end.date() - begin.date()).days == 30


@pytest.mark.parametrize(
    "period_label",
    [
        "Last 7 days",
        "Last 30 days",
        "Last 60 days",
        "Last 90 days",
        "Last 6 Months",
        "Last 1 Year",
        "Last 5 Years",
        "Ever",
    ],
)
def test_calculate_date_range_clears_microseconds(monkeypatch, period_label):
    """Begin/end normalization should clear source microseconds."""

    class MockDatetime:

        @classmethod
        def today(cls):
            return datetime(2025, 10, 22, 17, 0, 0, 123456)

        @staticmethod
        def astimezone(dt):
            return dt

    monkeypatch.setattr(date_utils, "datetime", MockDatetime)

    begin, end = date_utils.calculate_date_range(period_label)

    assert begin.microsecond == 0
    assert end.microsecond == 0


def test_parse_date_range_from_store_uses_period_from_store(monkeypatch):
    """Stored period value is forwarded to calculate_date_range."""
    expected_begin = datetime(2025, 10, 1, 0, 0, 0)
    expected_end = datetime(2025, 10, 31, 23, 59, 59)
    captured_periods = []

    def fake_calculate(period):
        captured_periods.append(period)
        return expected_begin, expected_end

    monkeypatch.setattr(
        date_utils,
        "calculate_date_range",
        fake_calculate,
    )
    begin, end = date_utils.parse_date_range_from_store(
        {"period": "Last 7 days"}
    )
    assert begin == expected_begin
    assert end == expected_end
    assert captured_periods == ["Last 7 days"]


def test_parse_date_range_from_store_defaults_period_when_missing(monkeypatch):
    """Missing period key should fall back to DEFAULT_PERIOD."""
    captured_periods = []
    expected_begin = datetime(2025, 10, 1, 0, 0, 0)
    expected_end = datetime(2025, 10, 31, 23, 59, 59)

    def fake_calculate(period):
        captured_periods.append(period)
        return expected_begin, expected_end

    monkeypatch.setattr(date_utils, "calculate_date_range", fake_calculate)
    begin, end = date_utils.parse_date_range_from_store({})

    assert begin == expected_begin
    assert end == expected_end
    assert captured_periods == [date_utils.DEFAULT_PERIOD]


def test_parse_date_range_from_store_defaults_for_non_dict(monkeypatch):
    """Non-dict store_data should use DEFAULT_PERIOD."""
    captured_periods = []
    expected_begin = datetime(2025, 10, 1, 0, 0, 0)
    expected_end = datetime(2025, 10, 31, 23, 59, 59)

    def fake_calculate(period):
        captured_periods.append(period)
        return expected_begin, expected_end

    monkeypatch.setattr(date_utils, "calculate_date_range", fake_calculate)
    begin, end = date_utils.parse_date_range_from_store(None)

    assert begin == expected_begin
    assert end == expected_end
    assert captured_periods == [date_utils.DEFAULT_PERIOD]


def test_parse_date_range_from_store_uses_explicit_begin_end(monkeypatch):
    """Explicit begin/end values should bypass calculate_date_range."""
    explicit_begin = "2024-01-01T00:00:00+00:00"
    explicit_end = "2024-01-31T23:59:59+00:00"
    called = False

    def fake_calculate(_):
        nonlocal called
        called = True
        return datetime(2025, 1, 1), datetime(2025, 1, 31)

    monkeypatch.setattr(date_utils, "calculate_date_range", fake_calculate)
    begin, end = date_utils.parse_date_range_from_store(
        {"period": "Last 7 days", "begin": explicit_begin, "end": explicit_end}
    )

    assert begin == datetime.fromisoformat(explicit_begin)
    assert end == datetime.fromisoformat(explicit_end)
    assert called is False


def test_parse_date_range_from_store_requires_both_begin_and_end(monkeypatch):
    """Missing either begin or end should use period-based calculation."""
    captured_periods = []
    expected_begin = datetime(2025, 10, 1, 0, 0, 0)
    expected_end = datetime(2025, 10, 31, 23, 59, 59)

    def fake_calculate(period):
        captured_periods.append(period)
        return expected_begin, expected_end

    monkeypatch.setattr(date_utils, "calculate_date_range", fake_calculate)
    begin, end = date_utils.parse_date_range_from_store(
        {"period": "Last 7 days", "begin": "2024-01-01T00:00:00+00:00"}
    )

    assert begin == expected_begin
    assert end == expected_end
    assert captured_periods == ["Last 7 days"]


if __name__ == "__main__":
    import doctest

    doctest_results = doctest.testmod(date_utils)
    if doctest_results.failed != 0:
        exit(1)
    pytest.main([__file__])
