"""Temporary service helpers for file-scoped commit-message classification."""

from __future__ import annotations

from typing import Any


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
