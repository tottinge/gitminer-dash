"""Storybook-focused tests for common-pair intent pane component states."""

from tests.dash_component_helpers import (
    find_component_by_id as _find_by_id,
)
from tests.dash_component_helpers import (
    walk_components as _walk_components,
)
from visualization.common_pair_intent_pane import EMPTY_SELECTION_MESSAGE
from visualization.common_pair_intent_pane_storybook import (
    COMMON_PAIR_INTENT_PANE_STORIES,
    build_common_pair_intent_pane_storybook,
    story_balanced_intent_mix,
    story_empty_selection,
    story_fix_focused_drilldown,
)


def test_storybook_registry_contains_expected_story_names():
    assert set(COMMON_PAIR_INTENT_PANE_STORIES) == {
        "empty-selection",
        "balanced-intent-mix",
        "fix-focused-drilldown",
    }


def test_empty_selection_story_renders_clear_guidance():
    story = story_empty_selection()
    empty_message = _find_by_id(
        story,
        "id-story-common-pair-empty-empty-state-message",
    )
    assert empty_message.children == EMPTY_SELECTION_MESSAGE


def test_balanced_story_shows_compact_chips_and_preview_rows():
    story = story_balanced_intent_mix()
    intent_chips = _find_by_id(
        story,
        "id-story-common-pair-balanced-intent-chips",
    )
    evidence_preview = _find_by_id(
        story,
        "id-story-common-pair-balanced-evidence-preview",
    )
    leader_coverage = _find_by_id(
        story,
        "id-story-common-pair-balanced-summary-leader-coverage",
    )
    assert len(intent_chips.children) == 4
    assert len(evidence_preview.children) == 3
    assert leader_coverage.children == "Leader coverage 33%"


def test_fix_focused_story_filters_drilldown_to_fix_evidence():
    story = story_fix_focused_drilldown()
    drilldown_table = _find_by_id(
        story,
        "id-story-common-pair-fix-focus-drilldown-table",
    )
    assert len(drilldown_table.data) == 3
    assert {row["intent"] for row in drilldown_table.data} == {"fix"}


def test_storybook_layout_contains_one_section_per_story():
    storybook_layout = build_common_pair_intent_pane_storybook()
    section_headers = [
        component.children
        for component in _walk_components(storybook_layout)
        if component.__class__.__name__ == "H4"
    ]
    assert section_headers == [
        "empty-selection",
        "balanced-intent-mix",
        "fix-focused-drilldown",
    ]
