"""Tests for `pages/conventional.py` figure helper behavior."""

from datetime import datetime, timezone
from unittest.mock import Mock

from pandas import DataFrame


def _sample_dataframe() -> DataFrame:
    return DataFrame(
        [
            {"date": "2026-01-01", "count": 3, "reason": "feat"},
            {"date": "2026-01-02", "count": 1, "reason": "fix"},
        ]
    )


def test_make_figure_passes_expected_px_bar_arguments(monkeypatch):
    monkeypatch.setattr("dash.register_page", lambda *args, **kwargs: None)
    from pages import conventional

    fake_figure = Mock()
    px_bar = Mock(return_value=fake_figure)
    monkeypatch.setattr(conventional.px, "bar", px_bar)

    dataframe = _sample_dataframe()

    result = conventional.make_figure(dataframe)

    assert result is fake_figure
    px_bar.assert_called_once_with(
        dataframe,
        height=500,
        x="date",
        y="count",
        color="reason",
        color_discrete_map=conventional.color_choices,
    )


def test_make_figure_updates_xaxis_range_when_dates_provided(monkeypatch):
    monkeypatch.setattr("dash.register_page", lambda *args, **kwargs: None)
    from pages import conventional

    fake_figure = Mock()
    px_bar = Mock(return_value=fake_figure)
    monkeypatch.setattr(conventional.px, "bar", px_bar)
    start_date = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2026, 1, 31, tzinfo=timezone.utc)

    conventional.make_figure(_sample_dataframe(), start_date, end_date)

    fake_figure.update_xaxes.assert_called_once_with(
        range=[start_date.date(), end_date.date()]
    )


def test_make_figure_does_not_update_xaxis_range_without_full_dates(
    monkeypatch,
):
    monkeypatch.setattr("dash.register_page", lambda *args, **kwargs: None)
    from pages import conventional

    fake_figure = Mock()
    px_bar = Mock(return_value=fake_figure)
    monkeypatch.setattr(conventional.px, "bar", px_bar)
    start_date = datetime(2026, 2, 1, tzinfo=timezone.utc)
    end_date = datetime(2026, 2, 28, tzinfo=timezone.utc)

    conventional.make_figure(_sample_dataframe(), start_date, None)
    conventional.make_figure(_sample_dataframe(), None, end_date)

    fake_figure.update_xaxes.assert_not_called()
