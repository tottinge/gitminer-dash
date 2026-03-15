"""Tests for `utils/global_date_store.py`."""

from datetime import datetime
from unittest.mock import patch

from utils.global_date_store import build_store_payload


@patch("utils.global_date_store.date_utils.to_iso_range")
@patch("utils.global_date_store.date_utils.calculate_date_range")
def test_build_store_payload_uses_given_period(mock_calculate, mock_iso):
    begin = datetime(2026, 1, 1)
    end = datetime(2026, 1, 31)
    mock_calculate.return_value = (begin, end)
    mock_iso.return_value = {"begin": "B", "end": "E"}

    payload = build_store_payload("Last 7 days")

    mock_calculate.assert_called_once_with("Last 7 days")
    mock_iso.assert_called_once_with(begin, end)
    assert payload == {"period": "Last 7 days", "begin": "B", "end": "E"}


@patch("utils.global_date_store.date_utils.to_iso_range")
@patch("utils.global_date_store.date_utils.calculate_date_range")
def test_build_store_payload_defaults_period(mock_calculate, mock_iso):
    begin = datetime(2026, 2, 1)
    end = datetime(2026, 2, 28)
    mock_calculate.return_value = (begin, end)
    mock_iso.return_value = {"begin": "B2", "end": "E2"}

    payload = build_store_payload(None)

    mock_calculate.assert_called_once()
    passed_period = mock_calculate.call_args.args[0]
    assert isinstance(passed_period, str)
    assert payload["period"] == passed_period
    assert payload == {"period": passed_period, "begin": "B2", "end": "E2"}
