"""CLI helpers for generating insights reports."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

from git import Repo

from insights.report_builder import build_insight_report
from insights.snapshot_builder import build_analysis_snapshot
from utils import date_utils


def _parse_period(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _default_period_end() -> datetime:
    _, end_of_today = date_utils.calculate_date_range(date_utils.DEFAULT_PERIOD)
    return end_of_today + timedelta(seconds=1)


def _default_period_start() -> datetime:
    start, _ = date_utils.calculate_date_range("Last 1 Year")
    return start


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate deterministic, evidence-backed repo hotspots."
    )
    parser.add_argument("--repo", default=".", help="Path to git repository.")
    parser.add_argument(
        "--from",
        dest="period_start",
        help=(
            "Period start in ISO format (example: 2026-01-01). "
            "Defaults to one year ago today at 00:00:00 when omitted."
        ),
    )
    parser.add_argument(
        "--to",
        dest="period_end",
        help=(
            "Period end in ISO format (example: 2026-01-31). "
            "Defaults to midnight tonight when omitted."
        ),
    )
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="Number of hotspots to return (default: 3).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    period_start = (
        _parse_period(args.period_start)
        if args.period_start is not None
        else _default_period_start()
    )
    period_end = (
        _parse_period(args.period_end)
        if args.period_end is not None
        else _default_period_end()
    )
    if period_start > period_end:
        parser.error("--from must be earlier than or equal to --to.")

    repo = Repo(args.repo)
    snapshot = build_analysis_snapshot(
        repo=repo, period_start=period_start, period_end=period_end
    )
    report = build_insight_report(snapshot=snapshot, top_n=args.top)
    print(json.dumps(report.to_dict(), indent=2))
    return 0
