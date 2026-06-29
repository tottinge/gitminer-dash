"""Tests for pages.most_committed_service."""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from pages.most_committed_service import (
    generate_file_commit_classification_payload,
    generate_table_selection_commit_classification_payload,
    selected_filename_from_active_cell,
)


def test_selected_filename_from_active_cell_handles_missing_selection_data():
    assert selected_filename_from_active_cell(None, []) == ""
    assert selected_filename_from_active_cell({}, [{"filename": "a.py"}]) == ""
    assert (
        selected_filename_from_active_cell({"row": 0}, [{"name": "oops"}]) == ""
    )


def test_selected_filename_from_active_cell_returns_selected_filename():
    table_data = [
        {"filename": "src/alpha.py"},
        {"filename": "src/beta.py"},
    ]
    active_cell = {"row": 1, "column": 0}

    assert (
        selected_filename_from_active_cell(active_cell, table_data)
        == "src/beta.py"
    )


def test_selected_filename_from_active_cell_rejects_invalid_row_indexes():
    table_data = [{"filename": "src/alpha.py"}]

    assert selected_filename_from_active_cell({"row": -1}, table_data) == ""
    assert selected_filename_from_active_cell({"row": 1}, table_data) == ""
    assert selected_filename_from_active_cell({"row": "0"}, table_data) == ""
    assert selected_filename_from_active_cell({"row": 0.0}, table_data) == ""


def test_selected_filename_from_active_cell_rejects_non_string_filename():
    assert (
        selected_filename_from_active_cell({"row": 0}, [{"filename": None}])
        == ""
    )
    assert (
        selected_filename_from_active_cell({"row": 0}, [{"filename": 123}])
        == ""
    )


def test_generate_table_selection_payload_returns_no_selection_contract():
    parse_date_range_fn = Mock()
    get_repo_fn = Mock()
    collect_commit_messages_for_file_fn = Mock()
    classify_commit_messages_fn = Mock()

    payload = generate_table_selection_commit_classification_payload(
        active_cell=None,
        table_data=[],
        date_range_data={"period": "Last 30 days"},
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_commit_messages_for_file_fn=collect_commit_messages_for_file_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )

    assert payload["status"] == "no_file_selected"
    assert payload["message_count"] == 0
    assert payload["intent_counts"] == []
    assert payload["classifications"] == []
    parse_date_range_fn.assert_not_called()
    get_repo_fn.assert_not_called()
    collect_commit_messages_for_file_fn.assert_not_called()
    classify_commit_messages_fn.assert_not_called()


def test_generate_file_payload_returns_invalid_date_range_contract():
    parse_date_range_fn = Mock(side_effect=ValueError("Bad date range"))
    get_repo_fn = Mock()
    collect_commit_messages_for_file_fn = Mock()
    classify_commit_messages_fn = Mock()

    payload = generate_file_commit_classification_payload(
        filename="src/core.py",
        date_range_data={"period": "Broken"},
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_commit_messages_for_file_fn=collect_commit_messages_for_file_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )

    assert payload["status"] == "invalid_date_range"
    assert payload["filename"] == "src/core.py"
    assert payload["error_detail"] == "Bad date range"
    get_repo_fn.assert_not_called()
    collect_commit_messages_for_file_fn.assert_not_called()
    classify_commit_messages_fn.assert_not_called()


def test_generate_file_payload_returns_no_messages_contract():
    period_start = datetime(2026, 4, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 4, 7, tzinfo=timezone.utc)
    repo = Mock()
    parse_date_range_fn = Mock(return_value=(period_start, period_end))
    get_repo_fn = Mock(return_value=repo)
    collect_commit_messages_for_file_fn = Mock(return_value=[])
    classify_commit_messages_fn = Mock()

    payload = generate_file_commit_classification_payload(
        filename="src/core.py",
        date_range_data={"period": "Last 7 days"},
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_commit_messages_for_file_fn=collect_commit_messages_for_file_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )

    assert payload["status"] == "no_messages"
    assert payload["filename"] == "src/core.py"
    assert payload["message_count"] == 0
    classify_commit_messages_fn.assert_not_called()


def test_generate_file_payload_handles_missing_repository_path_error():
    period_start = datetime(2026, 4, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 4, 7, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(period_start, period_end))
    get_repo_fn = Mock(side_effect=ValueError("No repository path provided"))
    collect_commit_messages_for_file_fn = Mock()
    classify_commit_messages_fn = Mock()

    payload = generate_file_commit_classification_payload(
        filename="src/core.py",
        date_range_data={"period": "Last 7 days"},
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_commit_messages_for_file_fn=collect_commit_messages_for_file_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )

    assert payload["status"] == "repository_unavailable"
    assert payload["filename"] == "src/core.py"
    collect_commit_messages_for_file_fn.assert_not_called()
    classify_commit_messages_fn.assert_not_called()


def test_generate_file_payload_happy_path():
    period_start = datetime(2026, 4, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 4, 7, tzinfo=timezone.utc)
    repo = Mock()
    parse_date_range_fn = Mock(return_value=(period_start, period_end))
    get_repo_fn = Mock(return_value=repo)
    collect_commit_messages_for_file_fn = Mock(
        return_value=[
            "feat(parser): add parser",
            "fix(parser): repair crash",
        ]
    )
    classify_commit_messages_fn = Mock(
        return_value={
            "message_count": 2,
            "intent_counts": [
                {"intent": "feat", "count": 1},
                {"intent": "fix", "count": 1},
            ],
            "classifications": [
                {
                    "message": "feat(parser): add parser",
                    "intent": "feat",
                },
                {
                    "message": "fix(parser): repair crash",
                    "intent": "fix",
                },
            ],
        }
    )

    payload = generate_file_commit_classification_payload(
        filename="src/core.py",
        date_range_data={"period": "Last 7 days"},
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_commit_messages_for_file_fn=collect_commit_messages_for_file_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )

    assert payload == {
        "status": "ok",
        "status_detail": "Classification completed.",
        "error_detail": "",
        "filename": "src/core.py",
        "message_count": 2,
        "intent_counts": [
            {"intent": "feat", "count": 1},
            {"intent": "fix", "count": 1},
        ],
        "classifications": [
            {
                "message": "feat(parser): add parser",
                "intent": "feat",
            },
            {
                "message": "fix(parser): repair crash",
                "intent": "fix",
            },
        ],
    }
    parse_date_range_fn.assert_called_once()
    get_repo_fn.assert_called_once_with()
    collect_commit_messages_for_file_fn.assert_called_once_with(
        repo,
        "src/core.py",
        period_start,
        period_end,
    )
    classify_commit_messages_fn.assert_called_once_with(
        [
            "feat(parser): add parser",
            "fix(parser): repair crash",
        ]
    )


def test_generate_file_payload_reraises_unrelated_value_error():
    period_start = datetime(2026, 4, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 4, 7, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(period_start, period_end))
    get_repo_fn = Mock(side_effect=ValueError("Unexpected repo failure"))
    collect_commit_messages_for_file_fn = Mock()
    classify_commit_messages_fn = Mock()

    with pytest.raises(ValueError, match="Unexpected repo failure"):
        generate_file_commit_classification_payload(
            filename="src/core.py",
            date_range_data={"period": "Last 7 days"},
            parse_date_range_fn=parse_date_range_fn,
            get_repo_fn=get_repo_fn,
            collect_commit_messages_for_file_fn=(
                collect_commit_messages_for_file_fn
            ),
            classify_commit_messages_fn=classify_commit_messages_fn,
        )
