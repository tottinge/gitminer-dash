"""Storybook-focused tests for file-change diagnostic pane component states."""

from visualization.file_change_diagnostic_pane import EMPTY_SELECTION_MESSAGE
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
    assert len(drilldown_table.data) == 3
    assert len(rework_table.data) == 1
    assert rework_table.data[0]["followup_intent"] == "fix"
    assert len(label_help.children) == 2
    label_help_texts = [item.children for item in label_help.children]
    assert any("Possible thrash" in text for text in label_help_texts)
    assert any("Coupling pressure" in text for text in label_help_texts)
    assert neighbor_coverage_chip.children == "Neighbor coverage 89%"
    assert average_neighbors_chip.children == "Avg neighbors 1.78"
    assert coupling_score_chip.children == "Coupling score 3"


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
