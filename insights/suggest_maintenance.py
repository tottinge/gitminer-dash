"""Generate a compact maintenance recommendation report for a repository."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from dateutil.relativedelta import relativedelta
from git import Repo

from insights.bridge_metrics_report import build_bridge_metrics_report
from insights.fixback_scanner import build_fixback_scan_report
from insights.report_builder import build_insight_report
from insights.snapshot_builder import build_analysis_snapshot

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load_mutant_common():
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    return importlib.import_module("mutant_common")


def _parse_period(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.astimezone()
    return parsed


def _period_from_months(
    months: int, period_end: datetime | None = None
) -> tuple[datetime, datetime]:
    end = period_end or datetime.now().astimezone()
    start = end - relativedelta(months=months)
    return start, end


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_metric_value(evidence: list[dict[str, Any]], key: str) -> int | None:
    pattern = re.compile(rf"^{re.escape(key)}=(\d+)$")
    for item in evidence:
        if item.get("kind") != "metric":
            continue
        value = str(item.get("value", ""))
        match = pattern.match(value)
        if match:
            return int(match.group(1))
    return None


def _hotspot_rows(payload: dict[str, Any], top_n: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for hotspot in payload.get("hotspots", [])[:top_n]:
        evidence = hotspot.get("evidence", [])
        rows.append(
            {
                "file_path": hotspot["file_path"],
                "score": float(hotspot["score"]),
                "commit_count": _parse_metric_value(evidence, "commit_count"),
                "latest_commit": next(
                    (
                        entry["value"]
                        for entry in evidence
                        if entry.get("kind") == "commit"
                    ),
                    None,
                ),
            }
        )
    return rows


def _bridge_rows(payload: dict[str, Any], top_n: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bridge in payload.get("bridges", [])[:top_n]:
        rows.append(
            {
                "file_path": bridge["file_path"],
                "bridge_score": float(bridge["bridge_score"]),
                "bridge_ratio": float(bridge["bridge_ratio"]),
                "commit_count": int(bridge["commit_count"]),
                "connected_communities": list(
                    bridge.get("connected_communities", [])
                ),
            }
        )
    return rows


def _fixback_rows(payload: dict[str, Any], top_n: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in payload.get("file_candidates", [])[:top_n]:
        rows.append(
            {
                "file_path": candidate["file_path"],
                "score": float(candidate["score"]),
                "touch_count": int(candidate["touch_count"]),
                "revisit_events": int(candidate["revisit_events"]),
                "fixback_events": int(candidate["fixback_events"]),
                "revisit_rate": float(candidate["revisit_rate"]),
                "fixback_rate": float(candidate["fixback_rate"]),
            }
        )
    return rows


def _mutation_summary(root: Path, top_n: int) -> dict[str, Any]:
    mutant_common = _load_mutant_common()
    collect_mutants = mutant_common.collect_mutants
    summarize_statuses = mutant_common.summarize_statuses
    relative_path_str = mutant_common.relative_path_str
    records = collect_mutants(root)
    status_counts = summarize_statuses(records)
    module_counts = Counter(record.module for record in records)
    survived_source_counts = Counter(
        relative_path_str(record.source_path, root)
        for record in records
        if record.status == "survived"
    )
    return {
        "mutant_count": len(records),
        "status_counts": dict(status_counts),
        "top_modules": [
            {"module": module, "count": count}
            for module, count in module_counts.most_common(top_n)
        ],
        "top_survived_source_files": [
            {"file_path": file_path, "survived_mutants": count}
            for file_path, count in survived_source_counts.most_common(top_n)
        ],
    }


def _recommendations(
    *,
    fixbacks: list[dict[str, Any]],
    hotspots: list[dict[str, Any]],
    bridges: list[dict[str, Any]],
    mutation: dict[str, Any],
) -> list[dict[str, Any]]:
    signal_counts: defaultdict[str, int] = defaultdict(int)
    for row in fixbacks:
        signal_counts[row["file_path"]] += 1
    for row in hotspots:
        signal_counts[row["file_path"]] += 1
    for row in bridges:
        signal_counts[row["file_path"]] += 1
    for row in mutation.get("top_survived_source_files", []):
        signal_counts[row["file_path"]] += 1

    multi_signal = sorted(
        (
            {"file_path": file_path, "signal_count": count}
            for file_path, count in signal_counts.items()
            if count >= 2
        ),
        key=lambda item: (-item["signal_count"], item["file_path"]),
    )

    recommendations: list[dict[str, Any]] = []
    if multi_signal:
        recommendations.append(
            {
                "priority": "high",
                "title": "Stabilize files that are high-risk across signals",
                "targets": multi_signal[:5],
                "rationale": (
                    "These files are repeatedly flagged by churn/fixback, "
                    "hotspot, bridge, or mutation indicators."
                ),
            }
        )

    top_bridge = bridges[0] if bridges else None
    if top_bridge is not None:
        recommendations.append(
            {
                "priority": "high",
                "title": "Reduce cross-community coupling in top bridge file",
                "targets": [top_bridge["file_path"]],
                "rationale": (
                    "High bridge score suggests change ripples across "
                    "concerns, increasing maintenance cost."
                ),
                "evidence": {
                    "bridge_score": top_bridge["bridge_score"],
                    "connected_communities": top_bridge[
                        "connected_communities"
                    ],
                },
            }
        )

    top_mutation = mutation.get("top_survived_source_files", [])
    if top_mutation:
        recommendations.append(
            {
                "priority": "medium",
                "title": "Strengthen assertions in surviving-mutant hotspots",
                "targets": top_mutation[:5],
                "rationale": (
                    "Surviving mutants indicate behavior that tests do not "
                    "currently constrain."
                ),
            }
        )

    rapid_fixbacks = [
        row
        for row in fixbacks
        if row["fixback_events"] > 0 and row["touch_count"]
    ]
    if rapid_fixbacks:
        recommendations.append(
            {
                "priority": "medium",
                "title": "Add regression tests for rapid revisit files",
                "targets": [
                    {
                        "file_path": row["file_path"],
                        "fixback_rate": row["fixback_rate"],
                    }
                    for row in rapid_fixbacks[:5]
                ],
                "rationale": (
                    "Files with frequent short-lag fixbacks benefit from "
                    "targeted regression coverage around recent changes."
                ),
            }
        )

    recommendations.append(
        {
            "priority": "low",
            "title": "Diff this report between runs to track maintenance trend",
            "rationale": (
                "Stable JSON output makes it easy for humans and agents to "
                "detect churn/coupling/test-gap movement over time."
            ),
        }
    )

    return recommendations


def _build_payload(
    *,
    repo: Repo,
    period_start: datetime,
    period_end: datetime,
    months: int,
    top_n: int,
    revisit_days: int,
    mutation_top_n: int,
    include_merges: bool,
    workspace: Path,
) -> dict[str, Any]:
    fixback_payload = build_fixback_scan_report(
        repo=repo,
        period_start=period_start,
        period_end=period_end,
        months=months,
        revisit_days=revisit_days,
        top_n=top_n,
        include_merges=include_merges,
    )
    _write_json(workspace / "fixbacks.json", fixback_payload)

    snapshot = build_analysis_snapshot(
        repo=repo,
        period_start=period_start,
        period_end=period_end,
    )
    hotspot_payload = build_insight_report(
        snapshot=snapshot, top_n=top_n
    ).to_dict()
    _write_json(workspace / "hotspots.json", hotspot_payload)

    bridge_payload = build_bridge_metrics_report(
        repo=repo,
        period_start=period_start,
        period_end=period_end,
        top_n=top_n,
    ).to_dict()
    _write_json(workspace / "bridges.json", bridge_payload)

    repo_root = Path(repo.working_tree_dir or repo.git_dir or ".").resolve()
    mutation_payload = _mutation_summary(root=repo_root, top_n=mutation_top_n)
    _write_json(workspace / "mutation.json", mutation_payload)

    fixbacks = _fixback_rows(
        _read_json(workspace / "fixbacks.json"), top_n=top_n
    )
    hotspots = _hotspot_rows(
        _read_json(workspace / "hotspots.json"), top_n=top_n
    )
    bridges = _bridge_rows(_read_json(workspace / "bridges.json"), top_n=top_n)
    mutation = _read_json(workspace / "mutation.json")

    return {
        "schema_version": "0.1.0",
        "report_type": "maintenance-suggestions",
        "repo_path": str(repo_root),
        "period": {
            "start": period_start.isoformat(),
            "end": period_end.isoformat(),
            "months": months,
        },
        "parameters": {
            "top": top_n,
            "revisit_days": revisit_days,
            "mutation_top": mutation_top_n,
            "include_merges": include_merges,
        },
        "summary": {
            "commits_analyzed": int(
                fixback_payload["summary"]["commits_analyzed"]
            ),
            "files_scanned": int(fixback_payload["summary"]["files_scanned"]),
            "revisit_events": int(fixback_payload["summary"]["revisit_events"]),
            "fixback_events": int(fixback_payload["summary"]["fixback_events"]),
            "hotspots_returned": len(hotspots),
            "bridges_returned": len(bridges),
            "mutants_total": int(mutation["mutant_count"]),
            "mutants_survived": int(
                mutation["status_counts"].get("survived", 0)
            ),
            "mutants_no_tests": int(
                mutation["status_counts"].get("no_tests", 0)
            ),
        },
        "signals": {
            "fixbacks": fixbacks,
            "hotspots": hotspots,
            "bridges": bridges,
            "mutation": mutation,
        },
        "recommendations": _recommendations(
            fixbacks=fixbacks,
            hotspots=hotspots,
            bridges=bridges,
            mutation=mutation,
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a temporary-workspace maintenance suggestion report "
            "combining fixbacks, hotspots, bridge metrics, and mutation data."
        )
    )
    parser.add_argument("repo", help="Path to git repository.")
    parser.add_argument(
        "--months",
        type=int,
        default=6,
        help="Months to look back from period end (default: 6).",
    )
    parser.add_argument(
        "--as-of",
        dest="period_end",
        help=(
            "Optional period end in ISO format. "
            "Defaults to current local time."
        ),
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top files to include for each signal section.",
    )
    parser.add_argument(
        "--revisit-days",
        type=int,
        default=14,
        help="Max days between touches to count as revisit/fixback.",
    )
    parser.add_argument(
        "--mutation-top",
        type=int,
        default=10,
        help="Number of top mutation modules/files to include.",
    )
    parser.add_argument(
        "--include-merges",
        action="store_true",
        help="Include merge commits in fixback scan.",
    )
    return parser


def _validate_args(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    if args.months <= 0:
        parser.error("--months must be greater than zero.")
    if args.top <= 0:
        parser.error("--top must be greater than zero.")
    if args.revisit_days <= 0:
        parser.error("--revisit-days must be greater than zero.")
    if args.mutation_top <= 0:
        parser.error("--mutation-top must be greater than zero.")


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    _validate_args(parser=parser, args=args)
    period_end = (
        _parse_period(args.period_end)
        if args.period_end is not None
        else datetime.now().astimezone()
    )
    period_start, period_end = _period_from_months(
        args.months, period_end=period_end
    )
    repo = Repo(args.repo)

    with tempfile.TemporaryDirectory(prefix="suggest_maintenance_") as tmp_dir:
        payload = _build_payload(
            repo=repo,
            period_start=period_start,
            period_end=period_end,
            months=args.months,
            top_n=args.top,
            revisit_days=args.revisit_days,
            mutation_top_n=args.mutation_top,
            include_merges=args.include_merges,
            workspace=Path(tmp_dir),
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
