"""CLI helpers for generating insights reports."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from git import Repo

from insights.citation_guard import validate_narrative_citations
from insights.llm_client import get_llm_client
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


def _read_narrative_text(
    parser: argparse.ArgumentParser, narrative_file: str
) -> str:
    try:
        return Path(narrative_file).read_text(encoding="utf-8")
    except OSError as exc:
        parser.error(f"--narrative-file could not be read: {exc}")


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
        "--narrative",
        action="store_true",
        help=(
            "Generate narrative summary using provider-agnostic llm_client "
            "interface."
        ),
    )
    parser.add_argument(
        "--strict-citations",
        action="store_true",
        help=(
            "Require generated narrative citations to validate against "
            "report-backed evidence refs."
        ),
    )
    parser.add_argument(
        "--narrative-file",
        help=(
            "Path to narrative text where each non-empty line is a claim and "
            "citations use [kind:value] tokens."
        ),
    )
    parser.add_argument(
        "--validate-citations",
        action="store_true",
        help=(
            "Validate narrative-file claims against report-backed evidence refs."
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


def _validate_args(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    period_start: datetime,
    period_end: datetime,
) -> None:
    if period_start > period_end:
        parser.error("--from must be earlier than or equal to --to.")
    if args.narrative_file and not args.validate_citations:
        parser.error("--narrative-file requires --validate-citations.")
    if args.validate_citations and not args.narrative_file:
        parser.error("--validate-citations requires --narrative-file.")
    if args.validate_citations and args.narrative:
        parser.error(
            "--validate-citations cannot be combined with --narrative."
        )
    if args.strict_citations and not args.narrative:
        parser.error("--strict-citations requires --narrative.")


def _load_or_build_snapshot(
    repo: Repo,
    repo_path: str,
    snapshot_dir: Path,
    period_start: datetime,
    period_end: datetime,
    save_snapshot_enabled: bool,
):
    snapshot = None
    if save_snapshot_enabled:
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
        if save_snapshot_enabled:
            save_snapshot(snapshot=snapshot, snapshot_dir=snapshot_dir)
    return snapshot


def _citation_validation_payload(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    report,
) -> dict[str, object]:
    narrative_text = _read_narrative_text(
        parser=parser, narrative_file=args.narrative_file
    )
    return {
        "schema_version": report.schema_version,
        "repo_path": report.repo_path,
        "period_start": report.period_start,
        "period_end": report.period_end,
        "total_commits": report.total_commits,
        "citation_validation": validate_narrative_citations(
            report=report, narrative_text=narrative_text
        ),
    }


def _narrative_output_payload(
    report, strict_citations: bool
) -> dict[str, object]:
    prompt_payload = build_prompt_payload(report=report)
    narrative_text = get_llm_client().generate_narrative(
        prompt_payload=prompt_payload
    )
    if strict_citations:
        citation_validation = validate_narrative_citations(
            report=report, narrative_text=narrative_text
        )
        narrative_payload: dict[str, object] = {
            "status": ("passed" if citation_validation["passed"] else "failed"),
            "citation_validation": citation_validation,
        }
        if citation_validation["passed"]:
            narrative_payload["text"] = narrative_text
    else:
        narrative_payload = {
            "status": "generated",
            "text": narrative_text,
        }
    return {
        "report": report.to_dict(),
        "narrative": narrative_payload,
    }


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
    _validate_args(
        parser=parser,
        args=args,
        period_start=period_start,
        period_end=period_end,
    )

    repo = Repo(args.repo)
    repo_path = repo.working_tree_dir or args.repo
    snapshot_dir = (
        Path(args.snapshot_dir)
        if args.snapshot_dir
        else Path(repo_path) / ".gitminer-dash" / "snapshots"
    )
    snapshot = _load_or_build_snapshot(
        repo=repo,
        repo_path=repo_path,
        snapshot_dir=snapshot_dir,
        period_start=period_start,
        period_end=period_end,
        save_snapshot_enabled=args.save_snapshot,
    )
    report = build_insight_report(snapshot=snapshot, top_n=args.top)

    if args.validate_citations:
        payload = _citation_validation_payload(
            parser=parser, args=args, report=report
        )
    elif args.narrative:
        payload = _narrative_output_payload(
            report=report, strict_citations=args.strict_citations
        )
    elif args.prompt_payload:
        payload = build_prompt_payload(report=report)
    else:
        payload = report.to_dict()

    print(json.dumps(payload, indent=2))
    return 0
