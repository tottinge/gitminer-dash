"""CLI helpers for generating insights reports."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from git import Repo

from insights.prompt_builder import build_prompt_payload
from insights.report_builder import build_insight_report
from insights.snapshot_builder import build_analysis_snapshot
from insights.snapshot_store import load_snapshot, save_snapshot
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
    parser.add_argument("repo", help="Path to git repository.")
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
        default=5,
        help="Number of hotspots to return (default: 5).",
    )
    parser.add_argument(
        "--prompt-payload",
        action="store_true",
        help=(
            "Emit compact provider-agnostic payload based on deterministic "
            "report data and evidence refs."
        ),
    )
    parser.add_argument(
        "--save-snapshot",
        action="store_true",
        help=(
            "Persist and reuse a versioned snapshot artifact for identical "
            "repo/date/schema inputs."
        ),
    )
    parser.add_argument(
        "--snapshot-dir",
        help=(
            "Optional directory for snapshot artifacts. Defaults to "
            "<repo>/.gitminer-dash/snapshots."
        ),
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
    repo_path = repo.working_tree_dir or args.repo
    snapshot_dir = (
        Path(args.snapshot_dir)
        if args.snapshot_dir
        else Path(repo_path) / ".gitminer-dash" / "snapshots"
    )

    snapshot = None
    if args.save_snapshot:
        snapshot = load_snapshot(
            snapshot_dir=snapshot_dir,
            repo_path=repo_path,
            period_start=period_start,
            period_end=period_end,
        )

    if snapshot is None:
        snapshot = build_analysis_snapshot(
            repo=repo, period_start=period_start, period_end=period_end
        )
        if args.save_snapshot:
            save_snapshot(snapshot=snapshot, snapshot_dir=snapshot_dir)
    report = build_insight_report(snapshot=snapshot, top_n=args.top)
    payload = (
        build_prompt_payload(report=report)
        if args.prompt_payload
        else report.to_dict()
    )
    print(json.dumps(payload, indent=2))
    return 0
