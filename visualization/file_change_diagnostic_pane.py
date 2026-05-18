"""Compact right-pane component for file change diagnostics and evidence."""

# pylint: disable=duplicate-code

from __future__ import annotations

from typing import TypedDict

from dash import html
from dash.dash_table import DataTable

from visualization.common_pair_intent_pane import (
    DEFAULT_PREVIEW_ROW_COUNT,
    METRIC_CHIP_STYLE,
    METRICS_ROW_STYLE,
    PANE_STYLE,
    PREVIEW_LIST_STYLE,
    _component_id,
    _normalized_intent,
    build_evidence_preview_items,
)

EMPTY_SELECTION_MESSAGE = (
    "Select a file row to preview diagnostics and supporting evidence."
)
ADVISORY_HELPER_MESSAGE = (
    "Signals are advisory. Review commit evidence before deciding whether "
    "to refactor."
)
LABEL_CHIP_STYLE = {
    "backgroundColor": "#ecfeff",
    "border": "1px solid #a5f3fc",
    "borderRadius": "999px",
    "padding": "2px 8px",
}
ADVISORY_LABEL_HELP = {
    "possible_thrash": (
        "Possible thrash: repeated short-gap follow-ups suggest rework on "
        "the same area."
    ),
    "feature_growth": (
        "Feature growth: commit history is dominated by new capability work."
    ),
    "maintenance_chore": (
        "Maintenance chore: commits trend toward upkeep tasks over net-new "
        "features."
    ),
    "coupling_pressure": (
        "Coupling pressure: this file changes with many neighbors and may be "
        "too central."
    ),
    "mixed_signal": (
        "Mixed signal: no single pattern dominates; inspect evidence rows for "
        "context."
    ),
}


class IntentCountRow(TypedDict):
    """Intent aggregate row."""

    intent: str
    count: int


class EvidenceRow(TypedDict):
    """One commit evidence row for a selected file."""

    intent: str
    hash: str
    date: str
    message: str


class ReworkEpisodeRow(TypedDict):
    """One short-gap revisit episode row."""

    anchor_hash: str
    followup_hash: str
    revisit_days: float
    followup_intent: str
    followup_fixlike: bool
    shared_hunk_count: int
    rework_signal_score: int


class FileChangeDiagnosticPanePayload(TypedDict):
    """Input payload for the file-change diagnostic pane."""

    filename: str
    message_count: int
    filtered_message_count: int
    focused_intent: str
    intent_counts: list[IntentCountRow]
    evidence_rows: list[EvidenceRow]
    advisory_labels: list[str]
    confidence_hint: str
    advisory_note: str
    intent_leader: str
    leader_coverage_percent: int
    fixlike_ratio_percent: int
    feature_ratio_percent: int
    maintenance_ratio_percent: int
    short_gap_followups: int
    short_gap_shared_hunk_followups: int
    median_revisit_days: float | None
    unique_cochange_neighbors: int
    cochange_commit_coverage_percent: int
    average_neighbors_per_commit: float
    coupling_signal_score: int
    rework_episode_count: int
    rework_episodes: list[ReworkEpisodeRow]


def _label_text(label_value: str) -> str:
    normalized = (label_value or "").strip()
    if not normalized:
        return "mixed signal"
    return normalized.replace("_", " ")


def build_label_chips(advisory_labels: list[str]) -> list[html.Span]:
    """Build advisory label chips."""
    if not advisory_labels:
        return [html.Span("mixed signal", style=LABEL_CHIP_STYLE)]
    return [
        html.Span(_label_text(label), style=LABEL_CHIP_STYLE)
        for label in advisory_labels
    ]


def _label_help_text(label_value: str) -> str:
    normalized_label = _normalized_intent(label_value)
    if normalized_label == "unknown":
        normalized_label = "mixed_signal"
    return ADVISORY_LABEL_HELP.get(
        normalized_label,
        ADVISORY_LABEL_HELP["mixed_signal"],
    )


def build_label_help_items(advisory_labels: list[str]) -> list[html.Li]:
    """Build concise helper-copy items for each advisory label."""
    label_values = advisory_labels or ["mixed_signal"]
    deduplicated_labels = list(
        dict.fromkeys(_normalized_intent(label) for label in label_values)
    )
    return [html.Li(_label_help_text(label)) for label in deduplicated_labels]


def _evidence_data(evidence_rows: list[EvidenceRow]) -> list[dict[str, str]]:
    return [
        {
            "intent": _normalized_intent(evidence_row.get("intent", "")),
            "hash": evidence_row.get("hash", "-"),
            "date": evidence_row.get("date", "-"),
            "message": evidence_row.get("message", ""),
        }
        for evidence_row in evidence_rows
    ]


def _rework_data(
    rework_episodes: list[ReworkEpisodeRow],
) -> list[dict[str, str | float]]:
    return [
        {
            "anchor_hash": rework_episode.get("anchor_hash", "-"),
            "followup_hash": rework_episode.get("followup_hash", "-"),
            "revisit_days": round(
                float(rework_episode.get("revisit_days", 0.0)),
                2,
            ),
            "followup_intent": _normalized_intent(
                rework_episode.get("followup_intent", "")
            ),
            "followup_fixlike": bool(
                rework_episode.get("followup_fixlike", False)
            ),
            "shared_hunk_count": int(
                rework_episode.get("shared_hunk_count", 0)
            ),
            "rework_signal_score": int(
                rework_episode.get("rework_signal_score", 0)
            ),
        }
        for rework_episode in rework_episodes
    ]


def _median_revisit_text(median_revisit_days: float | None) -> str:
    if median_revisit_days is None:
        return "Median revisit n/a"
    return f"Median revisit {median_revisit_days:.1f}d"


def build_file_change_diagnostic_pane(
    payload: FileChangeDiagnosticPanePayload | None,
    *,
    preview_row_count: int = DEFAULT_PREVIEW_ROW_COUNT,
    component_id_prefix: str = "id-file-change-diagnostic-pane",
    title_text: str = "File Change Diagnostic",
    empty_state_message: str = EMPTY_SELECTION_MESSAGE,
) -> html.Div:
    """Build a compact right-side pane for selected-file diagnostics."""
    if not payload:
        return html.Div(
            id=_component_id(component_id_prefix, "container"),
            style=PANE_STYLE,
            children=[
                html.H3(title_text, style={"margin": "0 0 6px"}),
                html.P(
                    empty_state_message,
                    id=_component_id(
                        component_id_prefix,
                        "empty-state-message",
                    ),
                    style={"margin": "0", "color": "#64748b"},
                ),
            ],
        )

    message_count = max(int(payload.get("message_count", 0)), 0)
    filtered_message_count = max(
        int(payload.get("filtered_message_count", message_count)),
        0,
    )
    evidence_rows = payload.get("evidence_rows", [])
    rework_episodes = payload.get("rework_episodes", [])
    focused_intent = _normalized_intent(payload.get("focused_intent", "all"))
    focus_label = "all intents" if focused_intent == "all" else focused_intent
    leader_intent = _normalized_intent(payload.get("intent_leader", ""))
    leader_coverage_percent = int(payload.get("leader_coverage_percent", 0))
    drilldown_data = _evidence_data(evidence_rows)
    rework_data = _rework_data(rework_episodes)

    return html.Div(
        id=_component_id(component_id_prefix, "container"),
        style=PANE_STYLE,
        children=[
            html.H3(title_text, style={"margin": "0 0 6px"}),
            html.Div(
                str(payload.get("filename", "")),
                id=_component_id(component_id_prefix, "filename"),
                style={"fontWeight": "600"},
            ),
            html.Div(
                style=METRICS_ROW_STYLE,
                children=[
                    html.Span(
                        f"Commits {message_count}",
                        id=_component_id(
                            component_id_prefix, "summary-commit-count"
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        f"Focus {focus_label}",
                        id=_component_id(component_id_prefix, "summary-focus"),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        f"Leader: '{leader_intent}' %{leader_coverage_percent}",
                        id=_component_id(
                            component_id_prefix, "summary-intent-leader"
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        f"Fix-like {int(payload.get('fixlike_ratio_percent', 0))}%",
                        id=_component_id(
                            component_id_prefix, "summary-fixlike-ratio"
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        f"Feature {int(payload.get('feature_ratio_percent', 0))}%",
                        id=_component_id(
                            component_id_prefix, "summary-feature-ratio"
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        (
                            "Maintenance "
                            f"{int(payload.get('maintenance_ratio_percent', 0))}%"
                        ),
                        id=_component_id(
                            component_id_prefix, "summary-maintenance-ratio"
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        (
                            "Short-gap follow-ups "
                            f"{int(payload.get('short_gap_followups', 0))}"
                        ),
                        id=_component_id(
                            component_id_prefix, "summary-short-gap-followups"
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        (
                            "Shared-hunk follow-ups "
                            f"{int(payload.get('short_gap_shared_hunk_followups', 0))}"
                        ),
                        id=_component_id(
                            component_id_prefix,
                            "summary-shared-hunk-followups",
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        _median_revisit_text(
                            payload.get("median_revisit_days")
                        ),
                        id=_component_id(
                            component_id_prefix, "summary-median-revisit"
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        (
                            "Co-change neighbors "
                            f"{int(payload.get('unique_cochange_neighbors', 0))}"
                        ),
                        id=_component_id(
                            component_id_prefix, "summary-neighbors"
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        (
                            "Neighbor coverage "
                            f"{int(payload.get('cochange_commit_coverage_percent', 0))}%"
                        ),
                        id=_component_id(
                            component_id_prefix,
                            "summary-neighbor-coverage",
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        (
                            "Avg neighbors "
                            f"{float(payload.get('average_neighbors_per_commit', 0.0)):.2f}"
                        ),
                        id=_component_id(
                            component_id_prefix,
                            "summary-average-neighbors",
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        (
                            "Coupling score "
                            f"{int(payload.get('coupling_signal_score', 0))}"
                        ),
                        id=_component_id(
                            component_id_prefix,
                            "summary-coupling-score",
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        (
                            "Rework episodes "
                            f"{int(payload.get('rework_episode_count', 0))}"
                        ),
                        id=_component_id(
                            component_id_prefix, "summary-rework-episodes"
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                ],
            ),
            html.Div(
                "Advisory labels",
                style={"fontWeight": "600", "marginBottom": "4px"},
            ),
            html.Div(
                build_label_chips(payload.get("advisory_labels", [])),
                id=_component_id(component_id_prefix, "advisory-label-chips"),
                style=METRICS_ROW_STYLE,
            ),
            html.Div(
                "How to read labels",
                style={"fontWeight": "600", "marginBottom": "2px"},
            ),
            html.Ul(
                build_label_help_items(payload.get("advisory_labels", [])),
                id=_component_id(component_id_prefix, "advisory-label-help"),
                style={"margin": "0 0 6px 18px", "padding": "0"},
            ),
            html.P(
                str(payload.get("confidence_hint", "")),
                id=_component_id(component_id_prefix, "confidence-hint"),
                style={"margin": "0 0 4px", "color": "#334155"},
            ),
            html.P(
                str(payload.get("advisory_note", ADVISORY_HELPER_MESSAGE)),
                style={"margin": "0 0 4px", "color": "#64748b"},
            ),
            html.P(
                f"Showing {filtered_message_count} evidence row(s).",
                id=_component_id(
                    component_id_prefix, "summary-filtered-evidence-count"
                ),
                style={"margin": "0 0 4px", "color": "#334155"},
            ),
            html.Ul(
                build_evidence_preview_items(
                    evidence_rows=evidence_rows,
                    preview_row_count=preview_row_count,
                ),
                id=_component_id(component_id_prefix, "evidence-preview"),
                style=PREVIEW_LIST_STYLE,
            ),
            html.Details(
                children=[
                    html.Summary(
                        (
                            "Drill down into "
                            f"{len(drilldown_data)} evidence row(s)"
                        ),
                        id=_component_id(
                            component_id_prefix, "drilldown-summary"
                        ),
                    ),
                    DataTable(
                        id=_component_id(
                            component_id_prefix, "drilldown-table"
                        ),
                        columns=[
                            {"name": "Intent", "id": "intent"},
                            {"name": "Hash", "id": "hash"},
                            {"name": "Date", "id": "date"},
                            {"name": "Message", "id": "message"},
                        ],
                        data=drilldown_data,
                        style_cell={
                            "textAlign": "left",
                            "padding": "4px 6px",
                            "fontSize": "12px",
                        },
                        style_table={
                            "maxHeight": "220px",
                            "overflowY": "auto",
                            "marginTop": "6px",
                        },
                    ),
                ]
            ),
            html.Details(
                children=[
                    html.Summary(
                        f"Rework episodes ({len(rework_data)})",
                        id=_component_id(component_id_prefix, "rework-summary"),
                    ),
                    DataTable(
                        id=_component_id(component_id_prefix, "rework-table"),
                        columns=[
                            {"name": "Anchor", "id": "anchor_hash"},
                            {"name": "Follow-up", "id": "followup_hash"},
                            {"name": "Days", "id": "revisit_days"},
                            {"name": "Intent", "id": "followup_intent"},
                            {"name": "Fix-like", "id": "followup_fixlike"},
                            {"name": "Shared Hunks", "id": "shared_hunk_count"},
                            {"name": "Signal", "id": "rework_signal_score"},
                        ],
                        data=rework_data,
                        style_cell={
                            "textAlign": "left",
                            "padding": "4px 6px",
                            "fontSize": "12px",
                        },
                        style_table={
                            "maxHeight": "170px",
                            "overflowY": "auto",
                            "marginTop": "6px",
                        },
                    ),
                ]
            ),
        ],
    )
