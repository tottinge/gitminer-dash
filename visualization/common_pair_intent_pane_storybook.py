"""Standalone stories for the common-pair intent pane component."""

from __future__ import annotations

from dash import html

from visualization.common_pair_intent_pane import (
    CommonPairIntentPanePayload,
    build_common_pair_intent_pane,
)


def _balanced_pair_payload() -> CommonPairIntentPanePayload:
    return {
        "pairing": "pages/strongest_pairings.py ↔ utils/git.py",  # pragma: no mutate
        "affinity": "0.58",  # pragma: no mutate
        "message_count": 6,
        "intent_counts": [
            {"intent": "refactor", "count": 2},  # pragma: no mutate
            {"intent": "fix", "count": 2},  # pragma: no mutate
            {"intent": "feat", "count": 1},  # pragma: no mutate
            {"intent": "test", "count": 1},  # pragma: no mutate
        ],
        "evidence_rows": [
            {
                "intent": "refactor",  # pragma: no mutate
                "hash": "a1b2c3d",  # pragma: no mutate
                "date": "2026-05-10",  # pragma: no mutate
                "message": "refactor(pairings): split row parser from callback",  # pragma: no mutate
            },
            {
                "intent": "fix",  # pragma: no mutate
                "hash": "b2c3d4e",  # pragma: no mutate
                "date": "2026-05-11",  # pragma: no mutate
                "message": "fix(pairings): keep empty selections stable",  # pragma: no mutate
            },
            {
                "intent": "feat",  # pragma: no mutate
                "hash": "c3d4e5f",  # pragma: no mutate
                "date": "2026-05-12",  # pragma: no mutate
                "message": "feat(pairings): add intent summary badges",  # pragma: no mutate
            },
            {
                "intent": "test",  # pragma: no mutate
                "hash": "d4e5f6a",  # pragma: no mutate
                "date": "2026-05-12",  # pragma: no mutate
                "message": "test(pairings): add edge-case callback coverage",  # pragma: no mutate
            },
        ],
    }


def _fix_dominant_payload() -> CommonPairIntentPanePayload:
    return {
        "pairing": "pages/affinity_groups.py ↔ algorithms/affinity_calculator.py",  # pragma: no mutate
        "affinity": "0.74",  # pragma: no mutate
        "message_count": 7,
        "intent_counts": [
            {"intent": "fix", "count": 5},  # pragma: no mutate
            {"intent": "refactor", "count": 1},  # pragma: no mutate
            {"intent": "test", "count": 1},  # pragma: no mutate
        ],
        "evidence_rows": [
            {
                "intent": "fix",  # pragma: no mutate
                "hash": "f6a7b8c",  # pragma: no mutate
                "date": "2026-05-08",  # pragma: no mutate
                "message": "fix(affinity): avoid divide-by-zero for sparse ranges",  # pragma: no mutate
            },
            {
                "intent": "fix",  # pragma: no mutate
                "hash": "a7b8c9d",  # pragma: no mutate
                "date": "2026-05-09",  # pragma: no mutate
                "message": "fix(affinity): guard null nodes in click handling",  # pragma: no mutate
            },
            {
                "intent": "fix",  # pragma: no mutate
                "hash": "b8c9d0e",  # pragma: no mutate
                "date": "2026-05-09",  # pragma: no mutate
                "message": "fix(affinity): normalize missing edge weight values",  # pragma: no mutate
            },
            {
                "intent": "refactor",  # pragma: no mutate
                "hash": "c9d0e1f",  # pragma: no mutate
                "date": "2026-05-10",  # pragma: no mutate
                "message": "refactor(affinity): isolate date-range parsing helper",  # pragma: no mutate
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
                    html.H4(
                        story_name, style={"margin": "0 0 6px"}
                    ),  # pragma: no mutate
                    story_fn(),
                ],
                style={"marginBottom": "18px"},  # pragma: no mutate
            )
        )
    return html.Div(
        children=story_sections,
        style={"maxWidth": "560px", "padding": "8px"},  # pragma: no mutate
    )
