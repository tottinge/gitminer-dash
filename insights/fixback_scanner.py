"""Experimental scanner for short-term revisit and fixback patterns."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime
from statistics import median
from typing import Any

from dateutil.relativedelta import relativedelta
from git import Repo

from algorithms.conventional_commits import (
    conventional_commit_match_pattern,
    normalize_intent,
)
from insights.snapshot_builder import get_commits_for_period

FIXLIKE_INTENTS = {"fix", "revert"}
FIXLIKE_KEYWORDS = (
    "backout",
    "bug",
    "fix",
    "follow-up",
    "followup",
    "hotfix",
    "patch",
    "revert",
    "rollback",
)


def _period_from_months(
    months: int, now: datetime | None = None
) -> tuple[datetime, datetime]:
    """Return [period_start, period_end] for a months lookback."""
    period_end = now or datetime.now().astimezone()
    period_start = period_end - relativedelta(months=months)
    return period_start, period_end


def _commit_summary(commit: Any) -> str:
    """Extract a one-line summary from commit message text."""
    return commit.message.splitlines()[0].strip()


def _commit_intent(summary: str) -> str:
    """Classify intent from conventional commit prefixes when available."""
    match = conventional_commit_match_pattern.match(summary)
    if not match:
        return "unknown"
    return normalize_intent(match.group(1))


def _is_fixlike(summary: str, intent: str) -> bool:
    """Heuristic fix/revert classifier used by the experimental scan."""
    if intent in FIXLIKE_INTENTS:
        return True
    lower_summary = summary.lower()
    return any(keyword in lower_summary for keyword in FIXLIKE_KEYWORDS)


def _hunk_fingerprints_from_patch(patch_text: str) -> list[str]:
    """Extract deterministic fingerprints for each unified-diff hunk body."""
    if not patch_text:
        return []

    fingerprints: list[str] = []
    seen: set[str] = set()
    current_hunk_lines: list[str] = []

    def flush_hunk() -> None:
        if not current_hunk_lines:
            return
        hunk_body = "\n".join(current_hunk_lines).strip()
        current_hunk_lines.clear()
        if not hunk_body:
            return
        digest = hashlib.sha256(hunk_body.encode("utf-8")).hexdigest()[:16]
        if digest in seen:
            return
        seen.add(digest)
        fingerprints.append(digest)

    for line in patch_text.splitlines():
        if line.startswith("@@"):
            flush_hunk()
            continue
        if line.startswith(
            (
                "diff --git ",
                "index ",
                "--- ",
                "+++ ",
                "\\ No newline at end of file",
            )
        ):
            continue
        if not line.startswith((" ", "+", "-")):
            continue
        current_hunk_lines.append(line.rstrip())

    flush_hunk()
    return fingerprints


def _commit_hunk_fingerprints_by_file(commit: Any) -> dict[str, list[str]]:
    """Collect hunk fingerprints for each file modified in a commit."""
    if not commit.parents:
        return {}

    try:
        diff_items = commit.diff(commit.parents[0], create_patch=True)
    except Exception:
        return {}

    fingerprints_by_file: dict[str, list[str]] = {}
    for diff_item in diff_items:
        file_path = diff_item.b_path or diff_item.a_path
        if not file_path:
            continue
        patch_bytes = diff_item.diff or b""
        if isinstance(patch_bytes, bytes):
            patch_text = patch_bytes.decode("utf-8", errors="replace")
        else:
            patch_text = str(patch_bytes)
        hunk_fingerprints = _hunk_fingerprints_from_patch(patch_text)
        if hunk_fingerprints:
            fingerprints_by_file[file_path] = hunk_fingerprints

    return fingerprints_by_file


def _scored_candidate(
    file_path: str,
    touches: list[dict[str, Any]],
    revisit_days: int,
    max_episodes_per_file: int,
) -> dict[str, Any] | None:
    opportunities = max(len(touches) - 1, 0)
    if opportunities == 0:
        return None

    revisit_events = 0
    fixback_events = 0
    revisit_lags: list[float] = []
    episodes: list[dict[str, Any]] = []

    for index in range(opportunities):
        anchor = touches[index]
        followup = touches[index + 1]
        revisit_lag_days = (
            followup["timestamp"] - anchor["timestamp"]
        ).total_seconds() / 86400
        if revisit_lag_days > revisit_days:
            continue

        revisit_events += 1
        if followup["fixlike"]:
            fixback_events += 1
        revisit_lags.append(revisit_lag_days)
        anchor_hunk_fingerprints = list(anchor.get("hunk_fingerprints", []))
        followup_hunk_fingerprints = list(followup.get("hunk_fingerprints", []))
        shared_hunk_fingerprints = sorted(
            set(anchor_hunk_fingerprints) & set(followup_hunk_fingerprints)
        )

        episodes.append(
            {
                "file_path": file_path,
                "anchor_commit": anchor["sha"],
                "anchor_timestamp": anchor["timestamp"].isoformat(),
                "anchor_summary": anchor["summary"],
                "followup_commit": followup["sha"],
                "followup_timestamp": followup["timestamp"].isoformat(),
                "followup_summary": followup["summary"],
                "followup_intent": followup["intent"],
                "followup_fixlike": followup["fixlike"],
                "anchor_hunk_fingerprints": anchor_hunk_fingerprints,
                "followup_hunk_fingerprints": followup_hunk_fingerprints,
                "shared_hunk_fingerprints": shared_hunk_fingerprints,
                "shared_hunk_count": len(shared_hunk_fingerprints),
                "revisit_days": round(revisit_lag_days, 6),
            }
        )

    if revisit_events == 0:
        return None

    unique_pattern_commits = sorted(
        {episode["anchor_commit"] for episode in episodes}
        | {episode["followup_commit"] for episode in episodes}
    )
    revisit_rate = revisit_events / opportunities
    fixback_rate = fixback_events / revisit_events
    median_revisit_days = round(float(median(revisit_lags)), 6)
    avg_revisit_days = round(sum(revisit_lags) / len(revisit_lags), 6)
    score = round(
        (fixback_events * 3.0)
        + revisit_events
        + revisit_rate
        + ((revisit_days - median_revisit_days) / revisit_days),
        6,
    )

    return {
        "file_path": file_path,
        "score": score,
        "touch_count": len(touches),
        "revisit_events": revisit_events,
        "revisit_rate": round(revisit_rate, 6),
        "fixback_events": fixback_events,
        "fixback_rate": round(fixback_rate, 6),
        "median_revisit_days": median_revisit_days,
        "avg_revisit_days": avg_revisit_days,
        "pattern_commits": unique_pattern_commits,
        "episodes": episodes[:max_episodes_per_file],
    }


def build_fixback_scan_report(
    repo: Repo,
    period_start: datetime,
    period_end: datetime,
    *,
    months: int | None = None,
    revisit_days: int = 14,
    top_n: int = 20,
    include_merges: bool = False,
    max_episodes_per_file: int = 5,
) -> dict[str, Any]:
    """Build an experimental report of short-term revisit/fixback patterns."""
    commits = get_commits_for_period(
        repo=repo, period_start=period_start, period_end=period_end
    )
    ordered_commits = sorted(
        commits, key=lambda commit: (commit.committed_datetime, commit.hexsha)
    )

    merge_commits_skipped = 0
    commit_records: list[dict[str, Any]] = []

    for commit in ordered_commits:
        if not include_merges and len(commit.parents) > 1:
            merge_commits_skipped += 1
            continue
        file_paths = sorted(commit.stats.files)
        if not file_paths:
            continue

        summary = _commit_summary(commit)
        intent = _commit_intent(summary)
        hunk_fingerprints_by_file = _commit_hunk_fingerprints_by_file(commit)
        commit_records.append(
            {
                "sha": commit.hexsha[:7],
                "timestamp": commit.committed_datetime,
                "summary": summary,
                "intent": intent,
                "fixlike": _is_fixlike(summary=summary, intent=intent),
                "files": file_paths,
                "hunk_fingerprints_by_file": hunk_fingerprints_by_file,
            }
        )

    file_touches: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in commit_records:
        for file_path in record["files"]:
            file_touches[file_path].append(
                {
                    "sha": record["sha"],
                    "timestamp": record["timestamp"],
                    "summary": record["summary"],
                    "intent": record["intent"],
                    "fixlike": record["fixlike"],
                    "hunk_fingerprints": list(
                        record["hunk_fingerprints_by_file"].get(file_path, [])
                    ),
                }
            )

    candidates = []
    for file_path, touches in sorted(file_touches.items()):
        candidate = _scored_candidate(
            file_path=file_path,
            touches=touches,
            revisit_days=revisit_days,
            max_episodes_per_file=max_episodes_per_file,
        )
        if candidate is not None:
            candidates.append(candidate)

    ranked_candidates = sorted(
        candidates,
        key=lambda item: (
            -float(item["score"]),
            -int(item["fixback_events"]),
            -int(item["revisit_events"]),
            item["file_path"],
        ),
    )
    top_candidates = ranked_candidates[:top_n]

    episodes = sorted(
        [
            episode
            for candidate in top_candidates
            for episode in candidate["episodes"]
        ],
        key=lambda episode: (
            float(episode["revisit_days"]),
            episode["file_path"],
            episode["anchor_commit"],
            episode["followup_commit"],
        ),
    )

    total_revisit_events = sum(
        int(candidate["revisit_events"]) for candidate in candidates
    )
    total_fixback_events = sum(
        int(candidate["fixback_events"]) for candidate in candidates
    )

    return {
        "schema_version": "0.1.0",
        "report_type": "fixback-scan",
        "repo_path": repo.working_tree_dir or "",
        "period": {
            "start": period_start.isoformat(),
            "end": period_end.isoformat(),
            "months": months,
        },
        "parameters": {
            "revisit_days": revisit_days,
            "top": top_n,
            "include_merges": include_merges,
        },
        "summary": {
            "commits_scanned": len(ordered_commits),
            "commits_analyzed": len(commit_records),
            "merge_commits_skipped": merge_commits_skipped,
            "files_scanned": len(file_touches),
            "candidate_files": len(candidates),
            "revisit_events": total_revisit_events,
            "fixback_events": total_fixback_events,
        },
        "file_candidates": top_candidates,
        "episodes": episodes,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Experimental short-term revisit/fixback scanner from git "
            "maintenance history."
        )
    )
    parser.add_argument("repo", help="Path to git repository.")
    parser.add_argument(
        "--months",
        type=int,
        default=6,
        help="Months to look back from now (default: 6).",
    )
    parser.add_argument(
        "--revisit-days",
        type=int,
        default=14,
        help="Max days between sequential touches to count as revisit.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of top candidates to return.",
    )
    parser.add_argument(
        "--include-merges",
        action="store_true",
        help="Include merge commits in scan (off by default).",
    )
    return parser


def _validate_args(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    if args.months <= 0:
        parser.error("--months must be greater than zero.")
    if args.revisit_days <= 0:
        parser.error("--revisit-days must be greater than zero.")
    if args.top <= 0:
        parser.error("--top must be greater than zero.")


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    _validate_args(parser=parser, args=args)

    period_start, period_end = _period_from_months(args.months)
    repo = Repo(args.repo)
    payload = build_fixback_scan_report(
        repo=repo,
        period_start=period_start,
        period_end=period_end,
        months=args.months,
        revisit_days=args.revisit_days,
        top_n=args.top,
        include_merges=args.include_merges,
    )
    print(json.dumps(payload, indent=2))
    return 0
