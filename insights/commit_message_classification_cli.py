"""CLI for previewing file-scoped commit-message classification payloads."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from git import Repo

from algorithms.commit_message_classifier import classify_commit_messages
from pages.most_committed_service import (
    collect_commit_messages_for_file,
    generate_file_commit_classification_payload,
)
from utils import date_utils
from utils.global_date_store import build_store_payload


def _parse_iso_datetime(
    parser: argparse.ArgumentParser, value: str, option_name: str
) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        parser.error(f"{option_name} must be a valid ISO datetime string.")
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _build_date_range_store_payload(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> dict[str, str]:
    has_period_start = args.period_start is not None
    has_period_end = args.period_end is not None

    if has_period_start != has_period_end:
        parser.error("--from and --to must be provided together.")

    if has_period_start and has_period_end:
        period_start = _parse_iso_datetime(parser, args.period_start, "--from")
        period_end = _parse_iso_datetime(parser, args.period_end, "--to")
        if period_start > period_end:
            parser.error("--from must be earlier than or equal to --to.")
        return {
            "period": "Custom",
            "begin": period_start.isoformat(),
            "end": period_end.isoformat(),
        }

    return build_store_payload(args.period)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Preview file-scoped commit-message classification payloads as JSON."
        )
    )
    parser.add_argument("repo", help="Path to git repository.")
    parser.add_argument(
        "--file-path",
        required=True,
        help="Repository-relative file path to classify commit messages for.",
    )
    parser.add_argument(
        "--period",
        default="Last 60 days",
        help=(
            "Named period label (for example: 'Last 60 days'). "
            "Ignored when --from/--to are provided."
        ),
    )
    parser.add_argument(
        "--from",
        dest="period_start",
        help=(
            "Period start in ISO format (for example: 2026-01-01 or "
            "2026-01-01T00:00:00+00:00). Must be paired with --to."
        ),
    )
    parser.add_argument(
        "--to",
        dest="period_end",
        help=(
            "Period end in ISO format (for example: 2026-01-31 or "
            "2026-01-31T23:59:59+00:00). Must be paired with --from."
        ),
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=25,
        help="Maximum number of commit messages to classify (default: 25).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.max_messages <= 0:
        parser.error("--max-messages must be greater than zero.")

    store_payload = _build_date_range_store_payload(parser=parser, args=args)

    def _get_repo() -> Repo:
        return Repo(args.repo)

    def _collect_messages(repo, filename, period_start, period_end):
        return collect_commit_messages_for_file(
            repo=repo,
            filename=filename,
            period_start=period_start,
            period_end=period_end,
        )[: args.max_messages]

    payload = generate_file_commit_classification_payload(
        filename=args.file_path,
        date_range_data=store_payload,
        parse_date_range_fn=date_utils.parse_date_range_from_store,
        get_repo_fn=_get_repo,
        collect_commit_messages_for_file_fn=_collect_messages,
        classify_commit_messages_fn=classify_commit_messages,
    )
    print(json.dumps(payload, indent=2))
    return 0
