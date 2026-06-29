"""Unit tests for file-change diagnostic pane view-model and rendering helpers."""

from visualization.file_change_diagnostic_pane import (
    ADVISORY_HELPER_MESSAGE,
    _build_file_change_diagnostic_view_model,
    _build_summary_metric_chip_components,
    _cochange_neighbor_data,
    _evidence_data,
    _focus_label_text,
    _rework_data,
    _summary_metric_chip_specs,
    build_file_change_diagnostic_pane,
    build_label_chips,
    build_label_help_items,
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


def test_build_file_change_diagnostic_view_model_handles_sparse_payload_defaults():
    view_model = _build_file_change_diagnostic_view_model(
        {
            "filename": "src/empty.py",
            "message_count": 2,
            "focused_intent": "custom-intent",
            "advisory_labels": None,
            "evidence_rows": None,
            "rework_episodes": None,
            "top_cochange_neighbors": None,
            "intent_leader": "",
            "median_revisit_days": None,
        }
    )

    assert view_model["filename"] == "src/empty.py"
    assert view_model["message_count"] == 2
    assert view_model["filtered_message_count"] == 2
    assert view_model["focus_label"] == "custom-intent"
    assert view_model["advisory_labels"] == []
    assert view_model["advisory_note"] == ADVISORY_HELPER_MESSAGE
    assert view_model["evidence_rows"] == []
    assert view_model["drilldown_data"] == []
    assert view_model["rework_data"] == []
    assert view_model["cochange_neighbor_data"] == []
    assert view_model["summary_metric_chips"][8] == {
        "id_suffix": "summary-median-revisit",
        "text": "Median revisit n/a",
    }
    assert view_model["summary_metric_chips"][11] == {
        "id_suffix": "summary-average-neighbors",
        "text": "Avg neighbors 0.00",
    }


def test_build_file_change_diagnostic_view_model_builds_full_summary_chip_contract():
    view_model = _build_file_change_diagnostic_view_model(
        {
            "filename": "src/full.py",
            "message_count": "10",
            "filtered_message_count": "7",
            "focused_intent": "feat",
            "advisory_labels": ["feature_growth"],
            "confidence_hint": "Medium confidence",
            "advisory_note": "Review commit evidence.",
            "intent_leader": "feat",
            "leader_coverage_percent": "60",
            "fixlike_ratio_percent": "20",
            "feature_ratio_percent": "60",
            "maintenance_ratio_percent": "20",
            "short_gap_followups": "3",
            "short_gap_shared_hunk_followups": "1",
            "median_revisit_days": 2.0,
            "unique_cochange_neighbors": "4",
            "cochange_commit_coverage_percent": "70",
            "average_neighbors_per_commit": "1.2",
            "coupling_signal_score": "2",
            "top_cochange_neighbors": [],
            "rework_episode_count": "1",
            "rework_episodes": [],
            "evidence_rows": [],
            "intent_counts": [],
        }
    )

    assert [
        chip["id_suffix"] for chip in view_model["summary_metric_chips"]
    ] == [
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
    assert [chip["text"] for chip in view_model["summary_metric_chips"]] == [
        "Commits 10",
        "Focus feature",
        "Leader: 'feat' %60",
        "Fix-like 20%",
        "Feature 60%",
        "Maintenance 20%",
        "Short-gap follow-ups 3",
        "Shared-hunk follow-ups 1",
        "Median revisit 2.0d",
        "Co-change neighbors 4",
        "Neighbor coverage 70%",
        "Avg neighbors 1.20",
        "Coupling score 2",
        "Rework episodes 1",
    ]


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


def test_build_summary_metric_chip_components_uses_prefix_and_ids():
    chip_components = _build_summary_metric_chip_components(
        "id-unit-file-change-pane",
        [
            {"id_suffix": "summary-commit-count", "text": "Commits 2"},
            {"id_suffix": "summary-focus", "text": "Focus all intents"},
        ],
    )

    assert len(chip_components) == 2
    assert (
        chip_components[0].id == "id-unit-file-change-pane-summary-commit-count"
    )
    assert chip_components[0].children == "Commits 2"
    assert chip_components[1].id == "id-unit-file-change-pane-summary-focus"
    assert chip_components[1].children == "Focus all intents"


def test_helper_mappers_apply_default_values():
    assert _evidence_data([{}]) == [
        {"intent": "unknown", "hash": "-", "date": "-", "message": ""}
    ]
    assert _rework_data([{}]) == [
        {
            "anchor_hash": "-",
            "followup_hash": "-",
            "revisit_days": 0.0,
            "followup_intent": "unknown",
            "followup_fixlike": False,
            "shared_hunk_count": 0,
            "rework_signal_score": 0,
        }
    ]
    assert _cochange_neighbor_data([{}]) == [{"path": "-", "count": 0}]
    assert _focus_label_text("REVERT") == "fix-like"
    assert _focus_label_text("custom-intent") == "custom-intent"


def test_build_label_chips_and_help_items_cover_defaults_and_deduplication():
    default_chips = build_label_chips([])
    assert len(default_chips) == 1
    assert default_chips[0].children == "mixed signal"

    named_chips = build_label_chips(["possible_thrash", "feature_growth"])
    assert [chip.children for chip in named_chips] == [
        "possible thrash",
        "feature growth",
    ]

    help_items = build_label_help_items(
        ["possible_thrash", "possible_thrash", ""]
    )
    assert len(help_items) == 2
    assert "Possible thrash" in help_items[0].children
    assert "Mixed signal" in help_items[1].children


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


def test_build_file_change_diagnostic_pane_empty_payload_uses_empty_state_message():
    pane = build_file_change_diagnostic_pane(
        payload=None,
        component_id_prefix="id-unit-file-change-pane-empty",
        empty_state_message="Pick a file to inspect.",
    )

    assert (
        _find_by_id(
            pane,
            "id-unit-file-change-pane-empty-empty-state-message",
        ).children
        == "Pick a file to inspect."
    )


def test_build_file_change_diagnostic_pane_renders_rework_and_label_details():
    pane = build_file_change_diagnostic_pane(
        payload={
            "filename": "src/parser.py",
            "message_count": 4,
            "filtered_message_count": 4,
            "focused_intent": "all",
            "intent_counts": [{"intent": "fix", "count": 2}],
            "evidence_rows": [
                {
                    "intent": "feat",
                    "hash": "abc0001",
                    "date": "2026-06-01 11:00",
                    "message": "feat(parser): expand support",
                }
            ],
            "advisory_labels": ["possible_thrash", "coupling_pressure"],
            "confidence_hint": "High confidence",
            "advisory_note": "Inspect evidence first.",
            "intent_leader": "fix",
            "leader_coverage_percent": 50,
            "fixlike_ratio_percent": 50,
            "feature_ratio_percent": 25,
            "maintenance_ratio_percent": 25,
            "short_gap_followups": 2,
            "short_gap_shared_hunk_followups": 1,
            "median_revisit_days": 0.8,
            "unique_cochange_neighbors": 2,
            "cochange_commit_coverage_percent": 75,
            "average_neighbors_per_commit": 1.25,
            "coupling_signal_score": 2,
            "top_cochange_neighbors": [
                {"path": "src/tokenizer.py", "count": 3},
                {"path": "src/rules.py", "count": 2},
            ],
            "rework_episode_count": 1,
            "rework_episodes": [
                {
                    "anchor_hash": "abc0001",
                    "followup_hash": "abc0002",
                    "revisit_days": 0.75,
                    "followup_intent": "fix",
                    "followup_fixlike": True,
                    "shared_hunk_count": 1,
                    "rework_signal_score": 2,
                }
            ],
        },
        component_id_prefix="id-unit-file-change-pane-details",
    )

    label_help = _find_by_id(
        pane,
        "id-unit-file-change-pane-details-advisory-label-help",
    )
    assert len(label_help.children) == 2
    assert "Possible thrash" in label_help.children[0].children
    assert "Coupling pressure" in label_help.children[1].children

    rework_table = _find_by_id(
        pane,
        "id-unit-file-change-pane-details-rework-table",
    )
    assert rework_table.data == [
        {
            "anchor_hash": "abc0001",
            "followup_hash": "abc0002",
            "revisit_days": 0.75,
            "followup_intent": "fix",
            "followup_fixlike": True,
            "shared_hunk_count": 1,
            "rework_signal_score": 2,
        }
    ]

    neighbors_table = _find_by_id(
        pane,
        "id-unit-file-change-pane-details-neighbors-table",
    )
    assert neighbors_table.data == [
        {"path": "src/tokenizer.py", "count": 3},
        {"path": "src/rules.py", "count": 2},
    ]

    drilldown_table = _find_by_id(
        pane,
        "id-unit-file-change-pane-details-drilldown-table",
    )
    assert drilldown_table.columns == [
        {"name": "Intent", "id": "intent"},
        {"name": "Hash", "id": "hash"},
        {"name": "Date", "id": "date"},
        {"name": "Message", "id": "message"},
    ]

    rework_table_columns = rework_table.columns
    assert rework_table_columns == [
        {"name": "Anchor", "id": "anchor_hash"},
        {"name": "Follow-up", "id": "followup_hash"},
        {"name": "Days", "id": "revisit_days"},
        {"name": "Intent", "id": "followup_intent"},
        {"name": "Fix-like", "id": "followup_fixlike"},
        {"name": "Shared Hunks", "id": "shared_hunk_count"},
        {"name": "Signal", "id": "rework_signal_score"},
    ]

    assert neighbors_table.columns == [
        {"name": "Path", "id": "path"},
        {"name": "Count", "id": "count"},
    ]
