"""Unit tests for file-change diagnostic pane view-model and rendering helpers."""

from visualization.file_change_diagnostic_pane import (
    ADVISORY_HELPER_MESSAGE,
    _build_file_change_diagnostic_view_model,
    _summary_metric_chip_specs,
    build_file_change_diagnostic_pane,
)


def _walk_components(component):
    if component is None:
        return
    yield component
    children = getattr(component, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            yield from _walk_components(child)
        return
    if children is None or isinstance(children, str):
        return
    yield from _walk_components(children)


def _find_by_id(component, component_id: str):
    for item in _walk_components(component):
        if getattr(item, "id", None) == component_id:
            return item
    msg = f"Component not found for id={component_id}"
    raise AssertionError(msg)


def test_build_file_change_diagnostic_view_model_normalizes_values():
    view_model = _build_file_change_diagnostic_view_model(
        {
            "filename": "src/core.py",
            "message_count": -4,
            "filtered_message_count": -2,
            "focused_intent": "REVERT",
            "intent_counts": [],
            "evidence_rows": [
                {
                    "intent": "FIX",
                    "hash": "abc1234",
                    "date": "2026-06-01 09:00",
                    "message": "fix(core): patch edge case",
                }
            ],
            "advisory_labels": ["possible_thrash"],
            "confidence_hint": "Medium confidence",
            "intent_leader": "FIX",
            "leader_coverage_percent": "57",
            "fixlike_ratio_percent": "67",
            "feature_ratio_percent": "11",
            "maintenance_ratio_percent": "22",
            "short_gap_followups": "3",
            "short_gap_shared_hunk_followups": "2",
            "median_revisit_days": 1.49,
            "unique_cochange_neighbors": "5",
            "cochange_commit_coverage_percent": "89",
            "average_neighbors_per_commit": "1.567",
            "coupling_signal_score": "4",
            "top_cochange_neighbors": [{"path": "src/utils.py", "count": "3"}],
            "rework_episode_count": "2",
            "rework_episodes": [
                {
                    "anchor_hash": "abc1234",
                    "followup_hash": "def5678",
                    "revisit_days": "1.234",
                    "followup_intent": "ReVert",
                    "followup_fixlike": "",
                    "shared_hunk_count": "2",
                    "rework_signal_score": "3",
                }
            ],
        }
    )

    assert view_model["message_count"] == 0
    assert view_model["filtered_message_count"] == 0
    assert view_model["focus_label"] == "fix-like"
    assert view_model["advisory_note"] == ADVISORY_HELPER_MESSAGE
    assert view_model["drilldown_data"] == [
        {
            "intent": "fix",
            "hash": "abc1234",
            "date": "2026-06-01 09:00",
            "message": "fix(core): patch edge case",
        }
    ]
    assert view_model["rework_data"] == [
        {
            "anchor_hash": "abc1234",
            "followup_hash": "def5678",
            "revisit_days": 1.23,
            "followup_intent": "revert",
            "followup_fixlike": False,
            "shared_hunk_count": 2,
            "rework_signal_score": 3,
        }
    ]
    assert view_model["cochange_neighbor_data"] == [
        {"path": "src/utils.py", "count": 3}
    ]
    assert view_model["summary_metric_chips"][0] == {
        "id_suffix": "summary-commit-count",
        "text": "Commits 0",
    }
    assert view_model["summary_metric_chips"][-1] == {
        "id_suffix": "summary-rework-episodes",
        "text": "Rework episodes 2",
    }


def test_summary_metric_chip_specs_match_existing_contract():
    summary_metric_chips = _summary_metric_chip_specs(
        message_count=7,
        focus_label="all intents",
        leader_intent="feat",
        leader_coverage_percent=57,
        fixlike_ratio_percent=22,
        feature_ratio_percent=57,
        maintenance_ratio_percent=21,
        short_gap_followups=3,
        short_gap_shared_hunk_followups=1,
        median_revisit_text="Median revisit 1.4d",
        unique_cochange_neighbors=4,
        cochange_commit_coverage_percent=89,
        average_neighbors_per_commit=1.234,
        coupling_signal_score=2,
        rework_episode_count=1,
    )

    assert [chip["id_suffix"] for chip in summary_metric_chips] == [
        "summary-commit-count",
        "summary-focus",
        "summary-intent-leader",
        "summary-fixlike-ratio",
        "summary-feature-ratio",
        "summary-maintenance-ratio",
        "summary-short-gap-followups",
        "summary-shared-hunk-followups",
        "summary-median-revisit",
        "summary-neighbors",
        "summary-neighbor-coverage",
        "summary-average-neighbors",
        "summary-coupling-score",
        "summary-rework-episodes",
    ]
    assert [chip["text"] for chip in summary_metric_chips] == [
        "Commits 7",
        "Focus all intents",
        "Leader: 'feat' %57",
        "Fix-like 22%",
        "Feature 57%",
        "Maintenance 21%",
        "Short-gap follow-ups 3",
        "Shared-hunk follow-ups 1",
        "Median revisit 1.4d",
        "Co-change neighbors 4",
        "Neighbor coverage 89%",
        "Avg neighbors 1.23",
        "Coupling score 2",
        "Rework episodes 1",
    ]


def test_build_file_change_diagnostic_pane_renders_summary_from_view_model():
    pane = build_file_change_diagnostic_pane(
        payload={
            "filename": "src/core.py",
            "message_count": 3,
            "filtered_message_count": 2,
            "focused_intent": "fix",
            "intent_counts": [{"intent": "fix", "count": 2}],
            "evidence_rows": [
                {
                    "intent": "fix",
                    "hash": "abc1111",
                    "date": "2026-06-01 10:00",
                    "message": "fix(core): stabilize parser",
                }
            ],
            "advisory_labels": ["mixed_signal"],
            "confidence_hint": "Low confidence",
            "advisory_note": "Signals are advisory.",
            "intent_leader": "fix",
            "leader_coverage_percent": 67,
            "fixlike_ratio_percent": 67,
            "feature_ratio_percent": 0,
            "maintenance_ratio_percent": 33,
            "short_gap_followups": 1,
            "short_gap_shared_hunk_followups": 0,
            "median_revisit_days": 1.0,
            "unique_cochange_neighbors": 1,
            "cochange_commit_coverage_percent": 67,
            "average_neighbors_per_commit": 1.5,
            "coupling_signal_score": 1,
            "top_cochange_neighbors": [{"path": "src/fix.py", "count": 2}],
            "rework_episode_count": 0,
            "rework_episodes": [],
        },
        component_id_prefix="id-unit-file-change-pane",
    )

    assert (
        _find_by_id(
            pane,
            "id-unit-file-change-pane-summary-commit-count",
        ).children
        == "Commits 3"
    )
    assert (
        _find_by_id(
            pane,
            "id-unit-file-change-pane-summary-focus",
        ).children
        == "Focus fix-like"
    )
    assert (
        _find_by_id(
            pane,
            "id-unit-file-change-pane-summary-average-neighbors",
        ).children
        == "Avg neighbors 1.50"
    )
    assert (
        _find_by_id(
            pane,
            "id-unit-file-change-pane-summary-filtered-evidence-count",
        ).children
        == "Showing 2 evidence row(s)."
    )
    assert (
        _find_by_id(
            pane,
            "id-unit-file-change-pane-neighbors-summary",
        ).children
        == "Top co-change neighbors for fix-like (1)"
    )

    drilldown_table = _find_by_id(
        pane,
        "id-unit-file-change-pane-drilldown-table",
    )
    assert drilldown_table.data == [
        {
            "intent": "fix",
            "hash": "abc1111",
            "date": "2026-06-01 10:00",
            "message": "fix(core): stabilize parser",
        }
    ]
