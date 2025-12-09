"""
Tests for global date store helper utilities.
"""

from tests import setup_path

setup_path()
from datetime import datetime

import pytest

from utils import date_utils


@pytest.fixture
def mock_datetime(monkeypatch):

    class MockDatetime:

        @classmethod
        def today(cls):
            return datetime(2025, 10, 22, 17, 59)

        @staticmethod
        def astimezone(dt):
            return dt

    monkeypatch.setattr(date_utils, "datetime", MockDatetime)


def test_to_iso_range_and_default_period(mock_datetime):
    (begin, end) = date_utils.calculate_date_range(date_utils.DEFAULT_PERIOD)
    payload = date_utils.to_iso_range(begin, end)
    assert set(payload.keys()) == {"begin", "end"}
    assert isinstance(payload["begin"], str) and isinstance(payload["end"], str)
