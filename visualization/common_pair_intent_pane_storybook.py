"""Standalone stories for the common-pair intent pane component."""

from __future__ import annotations

from dash import html

from visualization.common_pair_intent_pane import (
    CommonPairIntentPanePayload,
    build_common_pair_intent_pane,
)


def _balanced_pair_payload() -> CommonPairIntentPanePayload:
    return {
        "pairing": "pages/strongest_pairings.py ↔ utils/git.py",
        "affinity": "0.58",
        "message_count": 6,
        "intent_counts": [
            {"intent": "refactor", "count": 2},
            {"intent": "fix", "count": 2},
            {"intent": "feat", "count": 1},
            {"intent": "test", "count": 1},
        ],
        "evidence_rows": [
            {
                "intent": "refactor",
                "hash": "a1b2c3d",
                "date": "2026-05-10",
                "message": "refactor(pairings): split row parser from callback",
            },
            {
                "intent": "fix",
                "hash": "b2c3d4e",
                "date": "2026-05-11",
                "message": "fix(pairings): keep empty selections stable",
            },
            {
                "intent": "feat",
                "hash": "c3d4e5f",
                "date": "2026-05-12",
                "message": "feat(pairings): add intent summary badges",
            },
            {
                "intent": "test",
                "hash": "d4e5f6a",
                "date": "2026-05-12",
                "message": "test(pairings): add edge-case callback coverage",
            },
        ],
    }


def _fix_dominant_payload() -> CommonPairIntentPanePayload:
    return {
        "pairing": "pages/affinity_groups.py ↔ algorithms/affinity_calculator.py",
        "affinity": "0.74",
        "message_count": 7,
        "intent_counts": [
            {"intent": "fix", "count": 5},
            {"intent": "refactor", "count": 1},
            {"intent": "test", "count": 1},
        ],
        "evidence_rows": [
            {
                "intent": "fix",
                "hash": "f6a7b8c",
                "date": "2026-05-08",
                "message": "fix(affinity): avoid divide-by-zero for sparse ranges",
            },
            {
                "intent": "fix",
                "hash": "a7b8c9d",
                "date": "2026-05-09",
                "message": "fix(affinity): guard null nodes in click handling",
            },
            {
                "intent": "fix",
                "hash": "b8c9d0e",
                "date": "2026-05-09",
                "message": "fix(affinity): normalize missing edge weight values",
            },
            {
                "intent": "refactor",
                "hash": "c9d0e1f",
                "date": "2026-05-10",
                "message": "refactor(affinity): isolate date-range parsing helper",
            },
        ],
    }


def story_empty_selection() -> html.Div:
    return build_common_pair_intent_pane(
        payload=None,
        component_id_prefix="id-story-common-pair-empty",
    )


def story_balanced_intent_mix() -> html.Div:
    return build_common_pair_intent_pane(
        payload=_balanced_pair_payload(),
        component_id_prefix="id-story-common-pair-balanced",
    )


def story_fix_focused_drilldown() -> html.Div:
    return build_common_pair_intent_pane(
        payload=_fix_dominant_payload(),
        focused_intent="fix",
        component_id_prefix="id-story-common-pair-fix-focus",
    )


COMMON_PAIR_INTENT_PANE_STORIES = {
    "empty-selection": story_empty_selection,
    "balanced-intent-mix": story_balanced_intent_mix,
    "fix-focused-drilldown": story_fix_focused_drilldown,
}


def build_common_pair_intent_pane_storybook() -> html.Div:
    """Build a standalone, inspectable storybook layout."""
    story_sections = []
    for story_name, story_fn in COMMON_PAIR_INTENT_PANE_STORIES.items():
        story_sections.append(
            html.Div(
                children=[
                    html.H4(story_name, style={"margin": "0 0 6px"}),
                    story_fn(),
                ],
                style={"marginBottom": "18px"},
            )
        )
    return html.Div(
        children=story_sections,
        style={"maxWidth": "560px", "padding": "8px"},
    )
