"""
Tests for global date store helper utilities.
"""

# Ensure project imports work
from tests import setup_path
setup_path()

from datetime import datetime

import pytest

from utils import date_utils


def test_parse_period_from_query_with_period_label():
    assert date_utils.parse_period_from_query("?period=Last+60+days") == "Last 60 days"
    assert date_utils.parse_period_from_query("period=Last+7+days") == "Last 7 days"


def test_parse_period_from_query_with_from_to_returns_none():
    # We do not infer a label when explicit range provided
    assert date_utils.parse_period_from_query("?from=2024-01-01&to=2024-02-01") is None


def test_parse_period_from_query_with_unknown_label_returns_candidate():
    # Unknown labels are returned as-is so caller can still use them
    assert date_utils.parse_period_from_query("?period=Custom+Range") == "Custom Range"


@pytest.fixture
def mock_datetime(monkeypatch):
    class MockDatetime:
        @classmethod
        def today(cls):
            return datetime(2025, 10, 22, 17, 59)

        @staticmethod
        def astimezone(dt):
            return dt

    monkeypatch.setattr(date_utils, 'datetime', MockDatetime)


def test_to_iso_range_and_default_period(mock_datetime):
    begin, end = date_utils.calculate_date_range(date_utils.DEFAULT_PERIOD)
    payload = date_utils.to_iso_range(begin, end)
    assert set(payload.keys()) == {"begin", "end"}
    # Ensure ISO string formatting
    assert isinstance(payload["begin"], str) and isinstance(payload["end"], str)
