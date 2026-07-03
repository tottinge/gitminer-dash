"""Behavioral tests for the strongest-pairings right sidebar."""

from datetime import datetime, timezone
from importlib import import_module
from unittest.mock import patch

from tests import setup_path
from tests.dash_component_helpers import (
    find_component_by_id as _find_component_by_id,
)
from visualization.common_pair_intent_pane import EMPTY_SELECTION_MESSAGE

setup_path()


def _strongest_pairings_module():
    with patch("dash.register_page"):
        return import_module("pages.strongest_pairings")


def test_sidebar_requires_selected_pair_before_showing_intent_snapshot():
    module = _strongest_pairings_module()

    pane = module.show_pair_intent_sidebar(
        active_cell=None,
        store_data={"period": "Last 30 days"},
        table_data=[],
    )

    empty_state_message = _find_component_by_id(
        pane,
        f"{module.COMMON_PAIR_INTENT_PANE_PREFIX}-empty-state-message",
    )
    assert empty_state_message.children == EMPTY_SELECTION_MESSAGE


def test_sidebar_treats_non_pair_rows_as_unselected():
    module = _strongest_pairings_module()

    pane = module.show_pair_intent_sidebar(
        active_cell={"row": 0},
        store_data={"period": "Last 30 days"},
        table_data=[{"Affinity": "0.44", "Pairing": "src/one_file_only.py"}],
    )

    empty_state_message = _find_component_by_id(
        pane,
        f"{module.COMMON_PAIR_INTENT_PANE_PREFIX}-empty-state-message",
    )
    assert empty_state_message.children == EMPTY_SELECTION_MESSAGE


def test_sidebar_falls_back_to_empty_state_when_repository_unavailable(
    monkeypatch,
):
    module = _strongest_pairings_module()
    monkeypatch.setattr(
        module.repo_context,
        "get_repo",
        lambda: (_ for _ in ()).throw(
            ValueError("No repository path provided")
        ),
    )

    pane = module.show_pair_intent_sidebar(
        active_cell={"row": 0},
        store_data={"period": "Last 30 days"},
        table_data=[
            {"Affinity": "0.44", "Pairing": "src/alpha.py\nsrc/beta.py"}
        ],
    )

    empty_state_message = _find_component_by_id(
        pane,
        f"{module.COMMON_PAIR_INTENT_PANE_PREFIX}-empty-state-message",
    )
    assert empty_state_message.children == EMPTY_SELECTION_MESSAGE


def test_sidebar_renders_pair_intent_snapshot_for_selected_pair(monkeypatch):
    module = _strongest_pairings_module()
    pair_table_data = [
        {"Affinity": "0.80", "Pairing": "src/alpha.py\nsrc/beta.py"}
    ]
    store_data = {
        "period": "Last 30 days",
        "begin": "2026-05-01T00:00:00+00:00",
        "end": "2026-05-18T23:59:59+00:00",
    }
    expected_period_start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    expected_period_end = datetime(2026, 5, 18, 23, 59, 59, tzinfo=timezone.utc)
    captured = {}
    sentinel_repo = object()
    pair_commits = [
        {
            "hash": "abc1234",
            "date": "2026-05-11 09:15",
            "message": "feat(core): add pair summary",
        },
        {
            "hash": "def5678",
            "date": "2026-05-12 14:30",
            "message": "fix(core): stabilize pair filtering",
        },
    ]

    monkeypatch.setattr(
        module.date_utils,
        "parse_date_range_from_store",
        lambda payload: (expected_period_start, expected_period_end),
    )
    monkeypatch.setattr(module.repo_context, "get_repo", lambda: sentinel_repo)

    def _capture_pair_commits(
        repo, first_path, second_path, period_start, period_end
    ):
        captured["repo"] = repo
        captured["first_path"] = first_path
        captured["second_path"] = second_path
        captured["period_start"] = period_start
        captured["period_end"] = period_end
        return pair_commits

    monkeypatch.setattr(
        module,
        "get_commits_for_file_pair",
        _capture_pair_commits,
    )

    def _capture_classification(messages):
        captured["messages"] = list(messages)
        return {
            "message_count": 2,
            "intent_counts": [
                {"intent": "feat", "count": 1},
                {"intent": "fix", "count": 1},
            ],
            "classifications": [
                {
                    "intent": "feat",
                    "message": "feat(core): add pair summary",
                },
                {
                    "intent": "fix",
                    "message": "fix(core): stabilize pair filtering",
                },
            ],
        }

    monkeypatch.setattr(
        module,
        "classify_commit_messages",
        _capture_classification,
    )

    pane = module.show_pair_intent_sidebar(
        active_cell={"row": 0},
        store_data=store_data,
        table_data=pair_table_data,
    )

    assert captured == {
        "repo": sentinel_repo,
        "first_path": "src/alpha.py",
        "second_path": "src/beta.py",
        "period_start": expected_period_start,
        "period_end": expected_period_end,
        "messages": [
            "feat(core): add pair summary",
            "fix(core): stabilize pair filtering",
        ],
    }

    pairing_label = _find_component_by_id(
        pane,
        f"{module.COMMON_PAIR_INTENT_PANE_PREFIX}-pairing",
    )
    evidence_count_label = _find_component_by_id(
        pane,
        f"{module.COMMON_PAIR_INTENT_PANE_PREFIX}-summary-evidence-count",
    )
    drilldown_table = _find_component_by_id(
        pane,
        f"{module.COMMON_PAIR_INTENT_PANE_PREFIX}-drilldown-table",
    )

    assert pairing_label.children == "src/alpha.py ↔ src/beta.py"
    assert evidence_count_label.children == "Evidence 2"
    assert drilldown_table.data == [
        {
            "intent": "feat",
            "hash": "abc1234",
            "date": "2026-05-11 09:15",
            "message": "feat(core): add pair summary",
        },
        {
            "intent": "fix",
            "hash": "def5678",
            "date": "2026-05-12 14:30",
            "message": "fix(core): stabilize pair filtering",
        },
    ]
