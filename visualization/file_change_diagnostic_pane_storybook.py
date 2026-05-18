"""Standalone stories for the file-change diagnostic pane component."""

# pylint: disable=duplicate-code

from __future__ import annotations

from dash import html

from visualization.file_change_diagnostic_pane import (
    FileChangeDiagnosticPanePayload,
    build_file_change_diagnostic_pane,
)


def _feature_growth_payload() -> FileChangeDiagnosticPanePayload:
    return {
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
                "message": "feat(most-committed): add ranked table selection",
            },
            {
                "intent": "test",
                "hash": "abc2222",
                "date": "2026-05-10 11:50",
                "message": "test(most-committed): add row-selection coverage",
            },
            {
                "intent": "feat",
                "hash": "abc3333",
                "date": "2026-05-12 13:40",
                "message": "feat(most-committed): add diagnostic pane scaffold",
            },
        ],
        "advisory_labels": ["feature_growth"],
        "confidence_hint": "Medium confidence: trend based on 7 commits.",
        "advisory_note": (
            "Signals are advisory. Review commit evidence before deciding "
            "whether to refactor."
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
        "rework_episode_count": 0,
        "rework_episodes": [],
    }


def _thrash_leaning_payload() -> FileChangeDiagnosticPanePayload:
    return {
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
                "message": "fix(parser): stabilize fallback behavior",
            },
            {
                "intent": "fix",
                "hash": "fix2222",
                "date": "2026-05-03 09:32",
                "message": "fix(parser): address follow-up edge case",
            },
            {
                "intent": "refactor",
                "hash": "fix3333",
                "date": "2026-05-04 14:05",
                "message": "refactor(parser): isolate line normalizer",
            },
        ],
        "advisory_labels": ["possible_thrash", "coupling_pressure"],
        "confidence_hint": "High confidence: trend based on 9 commits.",
        "advisory_note": (
            "Signals are advisory. Review commit evidence before deciding "
            "whether to refactor."
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
    }


def story_empty_selection() -> html.Div:
    return build_file_change_diagnostic_pane(
        payload=None,
        component_id_prefix="id-story-file-change-diagnostic-empty",
    )


def story_feature_growth() -> html.Div:
    return build_file_change_diagnostic_pane(
        payload=_feature_growth_payload(),
        component_id_prefix="id-story-file-change-diagnostic-feature-growth",
    )


def story_thrash_leaning() -> html.Div:
    return build_file_change_diagnostic_pane(
        payload=_thrash_leaning_payload(),
        component_id_prefix="id-story-file-change-diagnostic-thrash",
    )


FILE_CHANGE_DIAGNOSTIC_PANE_STORIES = {
    "empty-selection": story_empty_selection,
    "feature-growth": story_feature_growth,
    "thrash-leaning": story_thrash_leaning,
}


def build_file_change_diagnostic_pane_storybook() -> html.Div:
    """Build a standalone, inspectable storybook layout."""
    story_sections = []
    for story_name, story_fn in FILE_CHANGE_DIAGNOSTIC_PANE_STORIES.items():
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
        style={"maxWidth": "620px", "padding": "8px"},
    )
