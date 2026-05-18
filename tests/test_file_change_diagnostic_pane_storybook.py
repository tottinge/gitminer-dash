"""Storybook-focused tests for file-change diagnostic pane component states."""

from visualization.file_change_diagnostic_pane import (
    EMPTY_SELECTION_MESSAGE,
    build_file_change_diagnostic_pane,
)
from visualization.file_change_diagnostic_pane_storybook import (
    FILE_CHANGE_DIAGNOSTIC_PANE_STORIES,
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
