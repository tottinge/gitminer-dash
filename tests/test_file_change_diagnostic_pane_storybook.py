"""Storybook-focused tests for file-change diagnostic pane component states."""

import pytest

from visualization.file_change_diagnostic_pane import (
    EMPTY_SELECTION_MESSAGE,
    build_file_change_diagnostic_pane,
)
from visualization.file_change_diagnostic_pane_storybook import (
    FILE_CHANGE_DIAGNOSTIC_PANE_STORIES,
    _feature_growth_payload,
    _thrash_leaning_payload,
    build_file_change_diagnostic_pane_storybook,
    story_empty_selection,
    story_feature_growth,
    story_thrash_leaning,
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


def test_storybook_registry_contains_expected_story_names():
    assert set(FILE_CHANGE_DIAGNOSTIC_PANE_STORIES) == {
        "empty-selection",
        "feature-growth",
        "thrash-leaning",
    }


def test_storybook_registry_order_and_targets_are_stable():
    assert list(FILE_CHANGE_DIAGNOSTIC_PANE_STORIES.items()) == [
        ("empty-selection", story_empty_selection),
        ("feature-growth", story_feature_growth),
        ("thrash-leaning", story_thrash_leaning),
    ]


@pytest.mark.parametrize(
    ("payload_builder", "expected_payload"),
    [
        (
            _feature_growth_payload,
            {
                "filename": "pages/most_committed.py",
                "message_count": 7,
                "filtered_message_count": 7,
                "focused_intent": "all",
                "intent_counts": [
                    {"intent": "feat", "count": 4},
                    {"intent": "test", "count": 2},
                    {"intent": "refactor", "count": 1},
                ],
                "evidence_rows": [
                    {
                        "intent": "feat",
                        "hash": "abc1111",
                        "date": "2026-05-10 09:15",
                        "message": (
                            "feat(most-committed): add ranked table "
                            "selection"
                        ),
                    },
                    {
                        "intent": "test",
                        "hash": "abc2222",
                        "date": "2026-05-10 11:50",
                        "message": (
                            "test(most-committed): add row-selection coverage"
                        ),
                    },
                    {
                        "intent": "feat",
                        "hash": "abc3333",
                        "date": "2026-05-12 13:40",
                        "message": (
                            "feat(most-committed): add diagnostic pane scaffold"
                        ),
                    },
                ],
                "advisory_labels": ["feature_growth"],
                "confidence_hint": (
                    "Medium confidence: trend based on 7 commits."
                ),
                "advisory_note": (
                    "Signals are advisory. Review commit evidence before "
                    "deciding whether to refactor."
                ),
                "intent_leader": "feat",
                "leader_coverage_percent": 57,
                "fixlike_ratio_percent": 0,
                "feature_ratio_percent": 57,
                "maintenance_ratio_percent": 43,
                "short_gap_followups": 1,
                "short_gap_shared_hunk_followups": 0,
                "median_revisit_days": 1.4,
                "unique_cochange_neighbors": 4,
                "cochange_commit_coverage_percent": 57,
                "average_neighbors_per_commit": 0.57,
                "coupling_signal_score": 1,
                "top_cochange_neighbors": [
                    {"path": "pages/most_committed.py", "count": 2},
                    {"path": "tests/test_most_committed.py", "count": 1},
                    {
                        "path": (
                            "visualization/file_change_diagnostic_pane.py"
                        ),
                        "count": 1,
                    },
                ],
                "rework_episode_count": 0,
                "rework_episodes": [],
            },
        ),
        (
            _thrash_leaning_payload,
            {
                "filename": "src/parser/core.py",
                "message_count": 9,
                "filtered_message_count": 9,
                "focused_intent": "all",
                "intent_counts": [
                    {"intent": "fix", "count": 5},
                    {"intent": "refactor", "count": 2},
                    {"intent": "feat", "count": 2},
                ],
                "evidence_rows": [
                    {
                        "intent": "fix",
                        "hash": "fix1111",
                        "date": "2026-05-02 10:10",
                        "message": ("fix(parser): stabilize fallback behavior"),
                    },
                    {
                        "intent": "fix",
                        "hash": "fix2222",
                        "date": "2026-05-03 09:32",
                        "message": ("fix(parser): address follow-up edge case"),
                    },
                    {
                        "intent": "refactor",
                        "hash": "fix3333",
                        "date": "2026-05-04 14:05",
                        "message": (
                            "refactor(parser): isolate line normalizer"
                        ),
                    },
                ],
                "advisory_labels": ["possible_thrash", "coupling_pressure"],
                "confidence_hint": (
                    "High confidence: trend based on 9 commits."
                ),
                "advisory_note": (
                    "Signals are advisory. Review commit evidence before "
                    "deciding whether to refactor."
                ),
                "intent_leader": "fix",
                "leader_coverage_percent": 56,
                "fixlike_ratio_percent": 56,
                "feature_ratio_percent": 22,
                "maintenance_ratio_percent": 22,
                "short_gap_followups": 3,
                "short_gap_shared_hunk_followups": 2,
                "median_revisit_days": 0.8,
                "unique_cochange_neighbors": 12,
                "cochange_commit_coverage_percent": 89,
                "average_neighbors_per_commit": 1.78,
                "coupling_signal_score": 3,
                "top_cochange_neighbors": [
                    {"path": "src/parser/tokenizer.py", "count": 4},
                    {"path": "src/parser/rules.py", "count": 3},
                    {"path": "src/parser/errors.py", "count": 2},
                    {"path": "src/core/config.py", "count": 1},
                ],
                "rework_episode_count": 1,
                "rework_episodes": [
                    {
                        "anchor_hash": "fix1111",
                        "followup_hash": "fix2222",
                        "revisit_days": 0.95,
                        "followup_intent": "fix",
                        "followup_fixlike": True,
                        "shared_hunk_count": 2,
                        "rework_signal_score": 3,
                    }
                ],
            },
        ),
    ],
    ids=["feature-growth", "thrash-leaning"],
)
def test_story_payloads_match_expected_contract(
    payload_builder, expected_payload
):
    assert payload_builder() == expected_payload


def test_empty_selection_story_renders_clear_guidance():
    story = story_empty_selection()
    empty_message = _find_by_id(
        story,
        "id-story-file-change-diagnostic-empty-empty-state-message",
    )
    assert empty_message.children == EMPTY_SELECTION_MESSAGE


def test_feature_growth_story_shows_advisory_label_and_preview():
    story = story_feature_growth()
    leader_chip = _find_by_id(
        story,
        "id-story-file-change-diagnostic-feature-growth-summary-intent-leader",
    )
    label_chips = _find_by_id(
        story,
        "id-story-file-change-diagnostic-feature-growth-advisory-label-chips",
    )
    label_help = _find_by_id(
        story,
        "id-story-file-change-diagnostic-feature-growth-advisory-label-help",
    )
    confidence_hint = _find_by_id(
        story,
        "id-story-file-change-diagnostic-feature-growth-confidence-hint",
    )
    evidence_preview = _find_by_id(
        story,
        "id-story-file-change-diagnostic-feature-growth-evidence-preview",
    )
    neighbors_summary = _find_by_id(
        story,
        "id-story-file-change-diagnostic-feature-growth-neighbors-summary",
    )
    neighbors_table = _find_by_id(
        story,
        "id-story-file-change-diagnostic-feature-growth-neighbors-table",
    )
    assert leader_chip.children == "Leader: 'feat' %57"
    assert len(label_chips.children) == 1
    assert label_chips.children[0].children == "feature growth"
    assert len(label_help.children) == 1
    assert "Feature growth" in label_help.children[0].children
    assert (
        confidence_hint.children
        == "Medium confidence: trend based on 7 commits."
    )
    assert len(evidence_preview.children) == 3
    assert (
        neighbors_summary.children
        == "Top co-change neighbors for all intents (3)"
    )
    assert len(neighbors_table.data) == 3


def test_thrash_story_shows_rework_and_drilldown_data():
    story = story_thrash_leaning()
    drilldown_table = _find_by_id(
        story,
        "id-story-file-change-diagnostic-thrash-drilldown-table",
    )
    rework_table = _find_by_id(
        story,
        "id-story-file-change-diagnostic-thrash-rework-table",
    )
    label_help = _find_by_id(
        story,
        "id-story-file-change-diagnostic-thrash-advisory-label-help",
    )
    neighbor_coverage_chip = _find_by_id(
        story,
        "id-story-file-change-diagnostic-thrash-summary-neighbor-coverage",
    )
    average_neighbors_chip = _find_by_id(
        story,
        "id-story-file-change-diagnostic-thrash-summary-average-neighbors",
    )
    coupling_score_chip = _find_by_id(
        story,
        "id-story-file-change-diagnostic-thrash-summary-coupling-score",
    )
    neighbors_summary = _find_by_id(
        story,
        "id-story-file-change-diagnostic-thrash-neighbors-summary",
    )
    neighbors_table = _find_by_id(
        story,
        "id-story-file-change-diagnostic-thrash-neighbors-table",
    )
    assert len(drilldown_table.data) == 3
    assert len(rework_table.data) == 1
    assert len(neighbors_table.data) == 4
    assert neighbors_table.data[0] == {
        "path": "src/parser/tokenizer.py",
        "count": 4,
    }
    assert rework_table.data[0]["followup_intent"] == "fix"
    assert len(label_help.children) == 2
    label_help_texts = [item.children for item in label_help.children]
    assert any("Possible thrash" in text for text in label_help_texts)
    assert any("Coupling pressure" in text for text in label_help_texts)
    assert neighbor_coverage_chip.children == "Neighbor coverage 89%"
    assert average_neighbors_chip.children == "Avg neighbors 1.78"
    assert coupling_score_chip.children == "Coupling score 3"
    assert (
        neighbors_summary.children
        == "Top co-change neighbors for all intents (4)"
    )


def test_storybook_layout_contains_one_section_per_story():
    storybook_layout = build_file_change_diagnostic_pane_storybook()
    assert storybook_layout.style == {"maxWidth": "620px", "padding": "8px"}
    assert len(storybook_layout.children) == 3

    expected_sections = [
        (
            "empty-selection",
            "id-story-file-change-diagnostic-empty-container",
        ),
        (
            "feature-growth",
            "id-story-file-change-diagnostic-feature-growth-container",
        ),
        ("thrash-leaning", "id-story-file-change-diagnostic-thrash-container"),
    ]
    for section, expected in zip(
        storybook_layout.children, expected_sections, strict=True
    ):
        expected_name, expected_container_id = expected
        assert section.style == {"marginBottom": "18px"}
        assert section.children[0].children == expected_name
        assert section.children[0].style == {"margin": "0 0 6px"}
        assert section.children[1].id == expected_container_id
    section_headers = [
        component.children
        for component in _walk_components(storybook_layout)
        if component.__class__.__name__ == "H4"
    ]
    assert section_headers == [
        "empty-selection",
        "feature-growth",
        "thrash-leaning",
    ]


def test_neighbors_summary_uses_non_all_focus_label():
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
                    "date": "2026-05-01 10:00",
                    "message": "fix(core): patch parser",
                }
            ],
            "advisory_labels": ["mixed_signal"],
            "confidence_hint": "Low confidence: trend based on only 3 commit(s).",
            "advisory_note": "Signals are advisory.",
            "intent_leader": "fix",
            "leader_coverage_percent": 67,
            "fixlike_ratio_percent": 67,
            "feature_ratio_percent": 0,
            "maintenance_ratio_percent": 33,
            "short_gap_followups": 1,
            "short_gap_shared_hunk_followups": 0,
            "median_revisit_days": 1.0,
            "unique_cochange_neighbors": 2,
            "cochange_commit_coverage_percent": 67,
            "average_neighbors_per_commit": 1.0,
            "coupling_signal_score": 1,
            "top_cochange_neighbors": [{"path": "src/fix.py", "count": 2}],
            "rework_episode_count": 0,
            "rework_episodes": [],
        },
        component_id_prefix="id-story-file-change-diagnostic-focus-fix",
    )
    neighbors_summary = _find_by_id(
        pane,
        "id-story-file-change-diagnostic-focus-fix-neighbors-summary",
    )
    focus_chip = _find_by_id(
        pane,
        "id-story-file-change-diagnostic-focus-fix-summary-focus",
    )
    assert focus_chip.children == "Focus fix-like"
    assert (
        neighbors_summary.children == "Top co-change neighbors for fix-like (1)"
    )
