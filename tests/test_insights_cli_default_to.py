"""Tests default period behavior in `insights/cli.py`."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from insights.cli import main
from insights.models import InsightReport


def test_main_defaults_period_end_when_to_is_omitted(capsys):
    snapshot = MagicMock()
    report = InsightReport(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T23:59:59+00:00",
        total_commits=0,
        hotspots=[],
    )

    default_end = datetime(2026, 3, 14, 0, 0, 0, tzinfo=timezone.utc)

    with (
        patch("insights.cli.Repo"),
        patch(
            "insights.cli.build_analysis_snapshot",
            return_value=snapshot,
        ) as mock_build_snapshot,
        patch(
            "insights.cli.build_insight_report",
            return_value=report,
        ),
        patch("insights.cli._default_period_end", return_value=default_end),
    ):
        exit_code = main([".", "--from", "2026-01-01"])

    assert exit_code == 0
    assert capsys.readouterr().out
    called_kwargs = mock_build_snapshot.call_args.kwargs
    assert called_kwargs["period_end"] == default_end


def test_main_defaults_period_start_when_from_is_omitted(capsys):
    snapshot = MagicMock()
    report = InsightReport(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2025-03-13T00:00:00+00:00",
        period_end="2026-03-14T00:00:00+00:00",
        total_commits=0,
        hotspots=[],
    )

    default_start = datetime(2025, 3, 13, 0, 0, 0, tzinfo=timezone.utc)
    default_end = datetime(2026, 3, 14, 0, 0, 0, tzinfo=timezone.utc)

    with (
        patch("insights.cli.Repo"),
        patch(
            "insights.cli.build_analysis_snapshot",
            return_value=snapshot,
        ) as mock_build_snapshot,
        patch(
            "insights.cli.build_insight_report",
            return_value=report,
        ),
        patch("insights.cli._default_period_start", return_value=default_start),
        patch("insights.cli._default_period_end", return_value=default_end),
    ):
        exit_code = main(["."])

    assert exit_code == 0
    assert capsys.readouterr().out
    called_kwargs = mock_build_snapshot.call_args.kwargs
    assert called_kwargs["period_start"] == default_start
    assert called_kwargs["period_end"] == default_end
