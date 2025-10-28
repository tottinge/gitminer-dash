"""
Tests for the date_utils module.

This module contains tests for the date_utils module using pytest.
"""

# Import from tests package to set up path
from tests import setup_path
setup_path()  # This ensures we can import modules from the project root
from datetime import datetime

import pytest

# Import date_utils module
from utils import date_utils

# Create a consistent mock date for all tests
MOCK_DATE = datetime(2025, 10, 22, 17, 59)


# Fixture to mock datetime in date_utils module
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

    # Apply the monkeypatch to replace datetime in date_utils
    monkeypatch.setattr(date_utils, 'datetime', MockDatetime)

    # For the 'Ever' test case, we need to handle datetime constructor
    original_datetime = datetime

    class MockDatetimeWithConstructor(MockDatetime):
        def __new__(cls, *args, **kwargs):
            if args or kwargs:
                return original_datetime(*args, **kwargs)
            return super().__new__(cls)

    # Return the mock for use in tests that need special handling
    return MockDatetimeWithConstructor


def test_calculate_date_range_7_days(mock_datetime):
    """Test calculate_date_range with 'Last 7 days'."""
    # Call function under test
    begin, end = date_utils.calculate_date_range('Last 7 days')

    # Assertions
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 10, 15).date()
    assert (end.date() - begin.date()).days == 7


def test_calculate_date_range_30_days(mock_datetime):
    """Test calculate_date_range with 'Last 30 days'."""
    # Call function under test
    begin, end = date_utils.calculate_date_range('Last 30 days')

    # Assertions
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 9, 22).date()
    assert (end.date() - begin.date()).days == 30


def test_calculate_date_range_60_days(mock_datetime):
    """Test calculate_date_range with 'Last 60 days'."""
    # Call function under test
    begin, end = date_utils.calculate_date_range('Last 60 days')

    # Assertions
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 8, 23).date()
    assert (end.date() - begin.date()).days == 60


def test_calculate_date_range_90_days(mock_datetime):
    """Test calculate_date_range with 'Last 90 days'."""
    # Call function under test
    begin, end = date_utils.calculate_date_range('Last 90 days')

    # Assertions
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 7, 24).date()
    assert (end.date() - begin.date()).days == 90


def test_calculate_date_range_6_months(mock_datetime):
    """Test calculate_date_range with 'Last 6 Months'."""
    # Call function under test
    begin, end = date_utils.calculate_date_range('Last 6 Months')

    # Assertions
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 4, 22).date()


def test_calculate_date_range_1_year(mock_datetime):
    """Test calculate_date_range with 'Last 1 Year'."""
    # Call function under test
    begin, end = date_utils.calculate_date_range('Last 1 Year')

    # Assertions
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2024, 10, 22).date()
    assert begin.year == end.year - 1
    assert begin.month == end.month
    assert begin.day == end.day


def test_calculate_date_range_5_years(mock_datetime):
    """Test calculate_date_range with 'Last 5 Years'."""
    # Call function under test
    begin, end = date_utils.calculate_date_range('Last 5 Years')

    # Assertions
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2020, 10, 22).date()
    assert begin.year == end.year - 5
    assert begin.month == end.month
    assert begin.day == end.day


def test_calculate_date_range_ever(monkeypatch):
    """Test calculate_date_range with 'Ever'."""

    # For this test, we need special handling for datetime constructor
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
    monkeypatch.setattr(date_utils, 'datetime', mock_dt)

    # Call function under test
    begin, end = date_utils.calculate_date_range('Ever')

    # Assertions
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(1970, 1, 1).date()


def test_calculate_date_range_default_none(mock_datetime):
    """Test calculate_date_range with None (default)."""
    # Call function under test
    begin, end = date_utils.calculate_date_range(None)

    # Assertions
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 9, 22).date()
    assert (end.date() - begin.date()).days == 30


def test_calculate_date_range_default_empty(mock_datetime):
    """Test calculate_date_range with empty string (default)."""
    # Call function under test
    begin, end = date_utils.calculate_date_range('')

    # Assertions
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 9, 22).date()
    assert (end.date() - begin.date()).days == 30


# Run doctests when file is executed directly
if __name__ == '__main__':
    import doctest

    doctest_results = doctest.testmod(date_utils)
    if doctest_results.failed == 0:
        print(f"All {doctest_results.attempted} doctests passed!")
    else:
        print(f"Failed {doctest_results.failed} out of {doctest_results.attempted} doctests.")
        exit(1)

    # Run pytest
    pytest.main([__file__])
