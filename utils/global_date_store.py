"""Helpers for app-level global date range store payloads."""

from __future__ import annotations

from utils import date_utils


def build_store_payload(period_label: str | None) -> dict[str, str]:
    """Build global-date-range store payload from period label."""
    period = period_label or date_utils.DEFAULT_PERIOD
    begin, end = date_utils.calculate_date_range(period)
    return {"period": period, **date_utils.to_iso_range(begin, end)}
