"""Service helpers for Most Committed page selection and diagnostics."""

from __future__ import annotations

from statistics import median
from typing import Any

from insights.fixback_scanner import (
    _hunk_fingerprints_from_patch as hunk_fingerprints_from_patch,
)

FIXLIKE_INTENTS = {"fix", "revert"}
FEATURE_INTENTS = {"feat"}
MAINTENANCE_INTENTS = {
    "build",
    "chore",
    "ci",
    "docs",
    "refactor",
    "style",
    "test",
}
SHORT_GAP_DAYS_THRESHOLD = 7.0
REWORK_MIN_SHARED_HUNK_COUNT = 1
REWORK_SHARED_HUNK_WEIGHT = 2
REWORK_FIXLIKE_WEIGHT = 1
REWORK_MIN_SIGNAL_SCORE = 2
COUPLING_MIN_MESSAGES = 4
COUPLING_NEIGHBOR_FLOOR = 8
COUPLING_NEIGHBOR_COVERAGE_THRESHOLD = 60
COUPLING_AVERAGE_NEIGHBORS_THRESHOLD = 1.5
COUPLING_MIN_SIGNAL_SCORE = 2
DIAGNOSTIC_ADVISORY_NOTE = (
    "Signals are advisory. Review commit evidence before deciding whether "
    "to refactor."
)


def selected_filename_from_active_cell(active_cell, table_data) -> str:
    """Return selected filename from table selection payload."""
    if not active_cell or not table_data:
        return ""

    row_index = active_cell.get("row")
    if row_index is None:
        return ""
    if not isinstance(row_index, int) or row_index < 0:
        return ""
    if row_index >= len(table_data):
        return ""

    selected_row = table_data[row_index]
    selected_filename = selected_row.get("filename", "")
    if not isinstance(selected_filename, str):
        return ""
    return selected_filename


def collect_commit_messages_for_file(
    repo,
    filename: str,
    period_start,
    period_end,
) -> list[str]:
    """Collect commit messages for a specific file in the selected period."""
    return [
        commit.message
        for commit in repo.iter_commits(
            paths=filename,
            since=period_start,
            until=period_end,
        )
    ]


def _summary_line(commit_message: str) -> str:
    summary_line = str(commit_message).splitlines()[0].strip()
    if summary_line:
        return summary_line
    return "(empty commit message)"


def _patch_text_for_selected_file(commit, filename: str) -> str:
    if not commit.parents:
        return ""
    try:
        diff_items = commit.diff(commit.parents[0], create_patch=True)
    except Exception:
        return ""

    for diff_item in diff_items:
        diff_file_path = diff_item.b_path or diff_item.a_path
        if diff_file_path != filename:
            continue
        patch_bytes = diff_item.diff or b""
        if isinstance(patch_bytes, bytes):
            return patch_bytes.decode("utf-8", errors="replace")
        return str(patch_bytes)
    return ""


def collect_file_commit_evidence(
    repo,
    filename: str,
    period_start,
    period_end,
) -> list[dict[str, Any]]:
    """Collect commit evidence rows for a specific file in selected period."""
    evidence_rows = []
    for commit in repo.iter_commits(
        paths=filename,
        since=period_start,
        until=period_end,
    ):
        patch_text = _patch_text_for_selected_file(commit, filename)
        changed_files = sorted(str(path) for path in commit.stats.files)
        evidence_rows.append(
            {
                "hash": commit.hexsha[:7],
                "date": commit.committed_datetime.strftime("%Y-%m-%d %H:%M"),
                "message": _summary_line(commit.message),
                "committed_at": commit.committed_datetime,
                "cochanged_neighbors": [
                    changed_file
                    for changed_file in changed_files
                    if changed_file != filename
                ],
                "hunk_fingerprints": hunk_fingerprints_from_patch(patch_text),
            }
        )

    return sorted(
        evidence_rows,
        key=lambda row: (row["committed_at"], row["hash"]),
    )


def build_empty_classification_payload(
    *,
    status: str,
    filename: str = "",
    status_detail: str = "",
    error_detail: str = "",
) -> dict[str, Any]:
    """Build a consistent empty classification payload."""
    return {
        "status": status,
        "status_detail": status_detail,
        "error_detail": error_detail,
        "filename": filename,
        "message_count": 0,
        "intent_counts": [],
        "classifications": [],
    }


def generate_file_commit_classification_payload(
    filename: str,
    date_range_data,
    *,
    parse_date_range_fn,
    get_repo_fn,
    collect_commit_messages_for_file_fn,
    classify_commit_messages_fn,
) -> dict[str, Any]:
    """Generate file-scoped commit-message classification payload."""
    if not filename:
        return build_empty_classification_payload(
            status="no_file_selected",
            status_detail="Select a file to classify commit messages.",
        )

    try:
        period_start, period_end = parse_date_range_fn(date_range_data)
    except ValueError as error:
        return build_empty_classification_payload(
            status="invalid_date_range",
            filename=filename,
            status_detail="Date range could not be parsed.",
            error_detail=str(error),
        )

    try:
        repo = get_repo_fn()
        commit_messages = collect_commit_messages_for_file_fn(
            repo,
            filename,
            period_start,
            period_end,
        )
    except ValueError as error:
        if "No repository path provided" in str(error):
            return build_empty_classification_payload(
                status="repository_unavailable",
                filename=filename,
                status_detail="Repository selection is required.",
                error_detail=str(error),
            )
        raise

    if not commit_messages:
        return build_empty_classification_payload(
            status="no_messages",
            filename=filename,
            status_detail="No commit messages found for selected file.",
        )

    classification_result = classify_commit_messages_fn(commit_messages)

    return {
        "status": "ok",
        "status_detail": "Classification completed.",
        "error_detail": "",
        "filename": filename,
        "message_count": classification_result["message_count"],
        "intent_counts": classification_result["intent_counts"],
        "classifications": classification_result["classifications"],
    }


def generate_table_selection_commit_classification_payload(
    active_cell,
    table_data,
    date_range_data,
    *,
    parse_date_range_fn,
    get_repo_fn,
    collect_commit_messages_for_file_fn,
    classify_commit_messages_fn,
) -> dict[str, Any]:
    """Generate classification payload from table selection context."""
    selected_filename = selected_filename_from_active_cell(
        active_cell,
        table_data,
    )
    return generate_file_commit_classification_payload(
        selected_filename,
        date_range_data,
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_commit_messages_for_file_fn=collect_commit_messages_for_file_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )


def _normalize_intent(intent_value: str) -> str:
    normalized = str(intent_value or "").strip().lower()
    return normalized or "unknown"


def _intent_count(intent_counts, intents: set[str]) -> int:
    normalized_intents = {_normalize_intent(intent) for intent in intents}
    return sum(
        int(intent_count_row.get("count", 0))
        for intent_count_row in intent_counts
        if _normalize_intent(intent_count_row.get("intent", ""))
        in normalized_intents
    )


def _ratio_percent(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        return 0
    return int(round((numerator / denominator) * 100))


def _intent_leader(intent_counts) -> tuple[str, int]:
    if not intent_counts:
        return "unknown", 0
    first_intent_count = intent_counts[0]
    return (
        _normalize_intent(first_intent_count.get("intent", "unknown")),
        int(first_intent_count.get("count", 0)),
    )


def _revisit_signals(evidence_rows) -> dict[str, Any]:
    if len(evidence_rows) < 2:
        return {
            "short_gap_followups": 0,
            "short_gap_shared_hunk_followups": 0,
            "fixlike_followups": 0,
            "median_revisit_days": None,
            "rework_episode_count": 0,
            "rework_episodes": [],
        }

    revisit_day_gaps = []
    short_gap_followups = 0
    short_gap_shared_hunk_followups = 0
    fixlike_followups = 0
    rework_episodes = []

    for anchor_row, followup_row in zip(
        evidence_rows,
        evidence_rows[1:],
        strict=False,
    ):
        revisit_days = (
            followup_row["committed_at"] - anchor_row["committed_at"]
        ).total_seconds() / 86400
        revisit_day_gaps.append(revisit_days)

        if revisit_days > SHORT_GAP_DAYS_THRESHOLD:
            continue

        short_gap_followups += 1
        followup_intent = _normalize_intent(followup_row.get("intent", ""))
        followup_fixlike = followup_intent in FIXLIKE_INTENTS
        if followup_fixlike:
            fixlike_followups += 1
        anchor_hunk_fingerprints = set(
            anchor_row.get("hunk_fingerprints", []) or []
        )
        followup_hunk_fingerprints = set(
            followup_row.get("hunk_fingerprints", []) or []
        )
        shared_hunk_fingerprints = sorted(
            anchor_hunk_fingerprints & followup_hunk_fingerprints
        )
        shared_hunk_count = len(shared_hunk_fingerprints)
        if shared_hunk_count >= REWORK_MIN_SHARED_HUNK_COUNT:
            short_gap_shared_hunk_followups += 1
        rework_signal_score = 0
        if shared_hunk_count >= REWORK_MIN_SHARED_HUNK_COUNT:
            rework_signal_score += REWORK_SHARED_HUNK_WEIGHT
        if followup_fixlike:
            rework_signal_score += REWORK_FIXLIKE_WEIGHT
        if rework_signal_score < REWORK_MIN_SIGNAL_SCORE:
            continue

        rework_episodes.append(
            {
                "anchor_hash": anchor_row.get("hash", "-"),
                "followup_hash": followup_row.get("hash", "-"),
                "revisit_days": round(revisit_days, 2),
                "followup_intent": followup_intent,
                "followup_fixlike": followup_fixlike,
                "shared_hunk_count": shared_hunk_count,
                "shared_hunk_fingerprints": shared_hunk_fingerprints,
                "rework_signal_score": rework_signal_score,
            }
        )

    return {
        "short_gap_followups": short_gap_followups,
        "short_gap_shared_hunk_followups": short_gap_shared_hunk_followups,
        "fixlike_followups": fixlike_followups,
        "median_revisit_days": round(float(median(revisit_day_gaps)), 2),
        "rework_episode_count": len(rework_episodes),
        "rework_episodes": rework_episodes,
    }


def _coupling_signals(
    evidence_rows: list[dict[str, Any]],
    message_count: int,
) -> dict[str, Any]:
    if message_count <= 0:
        return {
            "unique_cochange_neighbors": 0,
            "cochange_commit_coverage_percent": 0,
            "average_neighbors_per_commit": 0.0,
            "coupling_signal_score": 0,
        }

    unique_cochange_neighbors = len(
        {
            neighbor_path
            for evidence_row in evidence_rows
            for neighbor_path in evidence_row.get("cochanged_neighbors", [])
        }
    )
    commits_with_neighbors = sum(
        1
        for evidence_row in evidence_rows
        if evidence_row.get("cochanged_neighbors", [])
    )
    total_neighbor_events = sum(
        len(evidence_row.get("cochanged_neighbors", []))
        for evidence_row in evidence_rows
    )
    cochange_commit_coverage_percent = _ratio_percent(
        commits_with_neighbors, message_count
    )
    average_neighbors_per_commit = round(
        total_neighbor_events / message_count,
        2,
    )

    coupling_signal_score = 0
    if unique_cochange_neighbors >= max(COUPLING_NEIGHBOR_FLOOR, message_count):
        coupling_signal_score += 1
    if cochange_commit_coverage_percent >= COUPLING_NEIGHBOR_COVERAGE_THRESHOLD:
        coupling_signal_score += 1
    if average_neighbors_per_commit >= COUPLING_AVERAGE_NEIGHBORS_THRESHOLD:
        coupling_signal_score += 1
    if message_count < COUPLING_MIN_MESSAGES:
        coupling_signal_score = 0

    return {
        "unique_cochange_neighbors": unique_cochange_neighbors,
        "cochange_commit_coverage_percent": cochange_commit_coverage_percent,
        "average_neighbors_per_commit": average_neighbors_per_commit,
        "coupling_signal_score": coupling_signal_score,
    }


def _diagnostic_labels(
    *,
    message_count: int,
    fixlike_ratio_percent: int,
    feature_ratio_percent: int,
    maintenance_ratio_percent: int,
    short_gap_followups: int,
    short_gap_shared_hunk_followups: int,
    fixlike_followups: int,
    rework_episode_count: int,
    coupling_signal_score: int,
) -> list[str]:
    labels = []
    if message_count >= 4 and (
        rework_episode_count >= 2
        or (
            rework_episode_count >= 1
            and (fixlike_ratio_percent >= 35 or fixlike_followups >= 2)
        )
        or (
            short_gap_shared_hunk_followups >= 2 and fixlike_ratio_percent >= 30
        )
        or (
            short_gap_followups >= 3
            and fixlike_followups >= 2
            and short_gap_shared_hunk_followups >= 1
        )
    ):
        labels.append("possible_thrash")
    if feature_ratio_percent >= 40 and fixlike_ratio_percent < 35:
        labels.append("feature_growth")
    if maintenance_ratio_percent >= 45 and feature_ratio_percent < 40:
        labels.append("maintenance_chore")
    if (
        message_count >= COUPLING_MIN_MESSAGES
        and coupling_signal_score >= COUPLING_MIN_SIGNAL_SCORE
    ):
        labels.append("coupling_pressure")
    if not labels:
        labels.append("mixed_signal")
    return labels


def _confidence_hint(message_count: int) -> str:
    if message_count < 4:
        return f"Low confidence: trend based on only {message_count} commit(s)."
    if message_count < 8:
        return f"Medium confidence: trend based on {message_count} commits."
    return f"High confidence: trend based on {message_count} commits."


def _normalize_focused_intent(focused_intent: str | None) -> str:
    normalized = _normalize_intent(focused_intent or "all")
    if normalized in {"*", "all"}:
        return "all"
    return normalized


def _filtered_evidence_rows(
    evidence_rows: list[dict[str, Any]],
    focused_intent: str,
) -> list[dict[str, Any]]:
    normalized_focus = _normalize_focused_intent(focused_intent)
    if normalized_focus == "all":
        return evidence_rows
    return [
        evidence_row
        for evidence_row in evidence_rows
        if _normalize_intent(evidence_row.get("intent", "")) == normalized_focus
    ]


def build_empty_file_change_diagnostic_payload(
    *,
    status: str,
    filename: str = "",
    status_detail: str = "",
    error_detail: str = "",
    focused_intent: str = "all",
) -> dict[str, Any]:
    """Build a consistent empty diagnostic payload."""
    normalized_focus = _normalize_focused_intent(focused_intent)
    return {
        "status": status,
        "status_detail": status_detail,
        "error_detail": error_detail,
        "filename": filename,
        "message_count": 0,
        "filtered_message_count": 0,
        "focused_intent": normalized_focus,
        "intent_counts": [],
        "classifications": [],
        "evidence_rows": [],
        "advisory_labels": [],
        "confidence_hint": "",
        "advisory_note": DIAGNOSTIC_ADVISORY_NOTE,
        "intent_leader": "unknown",
        "leader_coverage_percent": 0,
        "fixlike_ratio_percent": 0,
        "feature_ratio_percent": 0,
        "maintenance_ratio_percent": 0,
        "short_gap_followups": 0,
        "short_gap_shared_hunk_followups": 0,
        "median_revisit_days": None,
        "unique_cochange_neighbors": 0,
        "cochange_commit_coverage_percent": 0,
        "average_neighbors_per_commit": 0.0,
        "coupling_signal_score": 0,
        "rework_episode_count": 0,
        "rework_episodes": [],
    }


def generate_file_change_diagnostic_payload(
    filename: str,
    date_range_data,
    *,
    focused_intent: str = "all",
    parse_date_range_fn,
    get_repo_fn,
    collect_file_commit_evidence_fn,
    classify_commit_messages_fn,
) -> dict[str, Any]:
    """Generate file-scoped diagnostics payload with evidence and labels."""
    normalized_focus = _normalize_focused_intent(focused_intent)
    if not filename:
        return build_empty_file_change_diagnostic_payload(
            status="no_file_selected",
            status_detail="Select a file row to view diagnostics.",
            focused_intent=normalized_focus,
        )

    try:
        period_start, period_end = parse_date_range_fn(date_range_data)
    except ValueError as error:
        return build_empty_file_change_diagnostic_payload(
            status="invalid_date_range",
            filename=filename,
            status_detail="Date range could not be parsed.",
            error_detail=str(error),
            focused_intent=normalized_focus,
        )

    try:
        repo = get_repo_fn()
        file_commit_evidence = collect_file_commit_evidence_fn(
            repo,
            filename,
            period_start,
            period_end,
        )
    except ValueError as error:
        if "No repository path provided" in str(error):
            return build_empty_file_change_diagnostic_payload(
                status="repository_unavailable",
                filename=filename,
                status_detail="Repository selection is required.",
                error_detail=str(error),
                focused_intent=normalized_focus,
            )
        raise

    if not file_commit_evidence:
        return build_empty_file_change_diagnostic_payload(
            status="no_messages",
            filename=filename,
            status_detail="No commit evidence found for selected file.",
            focused_intent=normalized_focus,
        )

    commit_messages = [
        file_commit_row.get("message", "")
        for file_commit_row in file_commit_evidence
    ]
    classification_result = classify_commit_messages_fn(commit_messages)
    classifications = classification_result.get("classifications", [])

    evidence_rows_with_intent: list[dict[str, Any]] = []
    for file_commit_row, classification in zip(
        file_commit_evidence,
        classifications,
        strict=True,
    ):
        evidence_rows_with_intent.append(
            {
                **file_commit_row,
                "intent": _normalize_intent(classification.get("intent", "")),
            }
        )

    message_count = int(classification_result.get("message_count", 0))
    intent_counts = classification_result.get("intent_counts", [])
    intent_leader, intent_leader_count = _intent_leader(intent_counts)
    leader_coverage_percent = _ratio_percent(intent_leader_count, message_count)
    fixlike_count = _intent_count(intent_counts, FIXLIKE_INTENTS)
    feature_count = _intent_count(intent_counts, FEATURE_INTENTS)
    maintenance_count = _intent_count(intent_counts, MAINTENANCE_INTENTS)
    fixlike_ratio_percent = _ratio_percent(fixlike_count, message_count)
    feature_ratio_percent = _ratio_percent(feature_count, message_count)
    maintenance_ratio_percent = _ratio_percent(maintenance_count, message_count)

    revisit_signals = _revisit_signals(evidence_rows_with_intent)
    coupling_signals = _coupling_signals(
        evidence_rows=evidence_rows_with_intent,
        message_count=message_count,
    )
    advisory_labels = _diagnostic_labels(
        message_count=message_count,
        fixlike_ratio_percent=fixlike_ratio_percent,
        feature_ratio_percent=feature_ratio_percent,
        maintenance_ratio_percent=maintenance_ratio_percent,
        short_gap_followups=revisit_signals["short_gap_followups"],
        short_gap_shared_hunk_followups=revisit_signals[
            "short_gap_shared_hunk_followups"
        ],
        fixlike_followups=revisit_signals["fixlike_followups"],
        rework_episode_count=revisit_signals["rework_episode_count"],
        coupling_signal_score=coupling_signals["coupling_signal_score"],
    )

    filtered_evidence_rows = _filtered_evidence_rows(
        evidence_rows_with_intent,
        normalized_focus,
    )
    filtered_classifications = [
        {
            "intent": _normalize_intent(evidence_row.get("intent", "")),
            "message": evidence_row.get("message", ""),
        }
        for evidence_row in filtered_evidence_rows
    ]

    return {
        "status": "ok",
        "status_detail": "Diagnostics completed.",
        "error_detail": "",
        "filename": filename,
        "message_count": message_count,
        "filtered_message_count": len(filtered_evidence_rows),
        "focused_intent": normalized_focus,
        "intent_counts": intent_counts,
        "classifications": filtered_classifications,
        "evidence_rows": [
            {
                "intent": _normalize_intent(evidence_row.get("intent", "")),
                "hash": evidence_row.get("hash", "-"),
                "date": evidence_row.get("date", "-"),
                "message": evidence_row.get("message", ""),
            }
            for evidence_row in filtered_evidence_rows
        ],
        "advisory_labels": advisory_labels,
        "confidence_hint": _confidence_hint(message_count),
        "advisory_note": DIAGNOSTIC_ADVISORY_NOTE,
        "intent_leader": intent_leader,
        "leader_coverage_percent": leader_coverage_percent,
        "fixlike_ratio_percent": fixlike_ratio_percent,
        "feature_ratio_percent": feature_ratio_percent,
        "maintenance_ratio_percent": maintenance_ratio_percent,
        "short_gap_followups": revisit_signals["short_gap_followups"],
        "short_gap_shared_hunk_followups": revisit_signals[
            "short_gap_shared_hunk_followups"
        ],
        "median_revisit_days": revisit_signals["median_revisit_days"],
        "unique_cochange_neighbors": coupling_signals[
            "unique_cochange_neighbors"
        ],
        "cochange_commit_coverage_percent": coupling_signals[
            "cochange_commit_coverage_percent"
        ],
        "average_neighbors_per_commit": coupling_signals[
            "average_neighbors_per_commit"
        ],
        "coupling_signal_score": coupling_signals["coupling_signal_score"],
        "rework_episode_count": revisit_signals["rework_episode_count"],
        "rework_episodes": revisit_signals["rework_episodes"],
    }


def generate_table_selection_file_change_diagnostic_payload(
    active_cell,
    table_data,
    date_range_data,
    *,
    focused_intent: str = "all",
    parse_date_range_fn,
    get_repo_fn,
    collect_file_commit_evidence_fn,
    classify_commit_messages_fn,
) -> dict[str, Any]:
    """Generate diagnostics payload from ranked-table row selection context."""
    selected_filename = selected_filename_from_active_cell(
        active_cell,
        table_data,
    )
    return generate_file_change_diagnostic_payload(
        selected_filename,
        date_range_data,
        focused_intent=focused_intent,
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_file_commit_evidence_fn=collect_file_commit_evidence_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )
