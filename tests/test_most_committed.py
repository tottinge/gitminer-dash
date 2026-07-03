"""Behavioral tests for the refactored Most Committed page."""

from tests import setup_path
from tests.dash_component_helpers import (
    find_component_by_id as _find_component_by_id,
)

setup_path()
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def most_committed_module():
    with patch("dash.register_page"):
        import pages.most_committed as module

        return module


@pytest.fixture
def mock_store_data():
    return {
        "period": "30",
        "begin": "2024-01-01T00:00:00",
        "end": "2024-01-31T23:59:59",
    }


@patch("pages.most_committed.repo_context.commits_in_period")
@patch("pages.most_committed.repo_context.get_repo")
@patch("pages.most_committed.calculate_file_commit_frequency")
def test_populate_ranked_table_returns_file_and_count_rows(
    mock_calc,
    mock_get_repo,
    mock_commits,
    mock_store_data,
    most_committed_module,
):
    mock_commits.return_value = [MagicMock()]
    mock_get_repo.return_value = MagicMock()
    mock_calc.return_value = [
        {"filename": "src/core.py", "count": 10},
        {"filename": "src/utils.py", "count": 7},
    ]

    table_data = most_committed_module.populate_ranked_table(mock_store_data)

    assert table_data == [
        {"filename": "src/core.py", "count": 10},
        {"filename": "src/utils.py", "count": 7},
    ]


def test_build_ranked_table_style_data_conditional_contains_bars_and_selection(
    most_committed_module,
):
    style_rules = (
        most_committed_module.build_ranked_table_style_data_conditional(
            active_cell={"row": 1, "column": 0},
            table_data=[
                {"filename": "src/core.py", "count": 10},
                {"filename": "src/utils.py", "count": 5},
            ],
        )
    )

    assert len(style_rules) == 3
    bar_rules = [
        rule
        for rule in style_rules
        if rule.get("if", {}).get("column_id") == "count"
    ]
    assert len(bar_rules) == 2
    selection_rule = next(
        (
            rule
            for rule in style_rules
            if rule.get("if", {}).get("row_index") == 1
            and "backgroundColor" in rule
        ),
        None,
    )
    assert selection_rule is not None
    assert selection_rule["backgroundColor"] == "#e6f3ff"


def test_selected_file_diagnostic_uses_empty_state_without_date_range(
    most_committed_module,
):
    status_text, pane = most_committed_module.populate_selected_file_diagnostic(
        active_cell={"row": 0},
        table_data=[{"filename": "src/core.py", "count": 5}],
        date_range_data=None,
        focused_intent="all",
    )

    assert status_text == "Select a date range to view file diagnostics."
    empty_message = _find_component_by_id(
        pane,
        "id-most-committed-file-change-diagnostic-pane-empty-state-message",
    )
    assert (
        empty_message.children
        == "Select a date range to view file diagnostics."
    )


@patch(
    "pages.most_committed.generate_table_selection_file_change_diagnostic_payload"
)
def test_selected_file_diagnostic_renders_success_payload(
    mock_generate_payload,
    mock_store_data,
    most_committed_module,
):
    mock_generate_payload.return_value = {
        "status": "ok",
        "status_detail": "Diagnostics completed.",
        "error_detail": "",
        "filename": "src/core.py",
        "message_count": 3,
        "filtered_message_count": 3,
        "focused_intent": "all",
        "intent_counts": [{"intent": "fix", "count": 2}],
        "classifications": [],
        "evidence_rows": [
            {
                "intent": "fix",
                "hash": "abc1234",
                "date": "2026-05-10 10:00",
                "message": "fix(core): patch regression",
            }
        ],
        "advisory_labels": ["possible_thrash"],
        "confidence_hint": "Medium confidence: trend based on 3 commits.",
        "advisory_note": "Signals are advisory.",
        "intent_leader": "fix",
        "leader_coverage_percent": 67,
        "fixlike_ratio_percent": 67,
        "feature_ratio_percent": 0,
        "maintenance_ratio_percent": 33,
        "short_gap_followups": 1,
        "median_revisit_days": 1.0,
        "unique_cochange_neighbors": 2,
        "rework_episodes": [],
    }

    status_text, pane = most_committed_module.populate_selected_file_diagnostic(
        active_cell={"row": 0},
        table_data=[{"filename": "src/core.py", "count": 3}],
        date_range_data=mock_store_data,
        focused_intent="all",
    )

    assert status_text == "src/core.py: analyzed 3 commit(s)."
    filename_label = _find_component_by_id(
        pane,
        "id-most-committed-file-change-diagnostic-pane-filename",
    )
    assert filename_label.children == "src/core.py"


@patch(
    "pages.most_committed.generate_table_selection_file_change_diagnostic_payload"
)
def test_selected_file_diagnostic_uses_focused_intent_status_text(
    mock_generate_payload,
    mock_store_data,
    most_committed_module,
):
    mock_generate_payload.return_value = {
        "status": "ok",
        "status_detail": "Diagnostics completed.",
        "error_detail": "",
        "filename": "src/core.py",
        "message_count": 5,
        "filtered_message_count": 2,
        "focused_intent": "fix",
        "intent_counts": [{"intent": "fix", "count": 2}],
        "classifications": [],
        "evidence_rows": [],
        "advisory_labels": ["mixed_signal"],
        "confidence_hint": "Medium confidence: trend based on 5 commits.",
        "advisory_note": "Signals are advisory.",
        "intent_leader": "fix",
        "leader_coverage_percent": 40,
        "fixlike_ratio_percent": 40,
        "feature_ratio_percent": 20,
        "maintenance_ratio_percent": 40,
        "short_gap_followups": 2,
        "median_revisit_days": 2.0,
        "unique_cochange_neighbors": 3,
        "rework_episodes": [],
    }

    status_text, _pane = (
        most_committed_module.populate_selected_file_diagnostic(
            active_cell={"row": 0},
            table_data=[{"filename": "src/core.py", "count": 5}],
            date_range_data=mock_store_data,
            focused_intent="fix",
        )
    )

    assert status_text == "src/core.py: showing 2 fix evidence row(s) out of 5."
