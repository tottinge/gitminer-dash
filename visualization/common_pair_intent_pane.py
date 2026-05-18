"""Compact right-pane component for common-pair intent and evidence drill-down."""

from __future__ import annotations

from typing import TypedDict

from dash import html
from dash.dash_table import DataTable

EMPTY_SELECTION_MESSAGE = (
    "Select a common pair to preview intent and supporting evidence."
)
DRILLDOWN_HELPER_MESSAGE = (
    "Hover preview rows for full messages. Expand drill-down for full "
    "evidence."
)
DEFAULT_PREVIEW_ROW_COUNT = 3
MAX_INTENT_CHIP_COUNT = 4

PANE_STYLE = {
    "backgroundColor": "#ffffff",
    "border": "1px solid #d9dee8",
    "borderRadius": "10px",
    "padding": "10px 12px",
    "boxShadow": "0 1px 2px rgba(15, 23, 42, 0.06)",
    "fontSize": "12px",
}
METRICS_ROW_STYLE = {
    "display": "flex",
    "gap": "6px",
    "flexWrap": "wrap",
    "margin": "6px 0 8px",
}
METRIC_CHIP_STYLE = {
    "backgroundColor": "#f8fafc",
    "border": "1px solid #e2e8f0",
    "borderRadius": "999px",
    "padding": "2px 8px",
    "fontWeight": "600",
}
INTENT_CHIP_STYLE = {
    "backgroundColor": "#f8fafc",
    "border": "1px solid #e2e8f0",
    "borderRadius": "999px",
    "padding": "2px 8px",
}
FOCUSED_INTENT_CHIP_STYLE = {
    "backgroundColor": "#dbeafe",
    "border": "1px solid #60a5fa",
}
PREVIEW_LIST_STYLE = {
    "margin": "6px 0 8px",
    "paddingLeft": "16px",
    "maxHeight": "130px",
    "overflowY": "auto",
}


class IntentCountRow(TypedDict):
    """Intent aggregate row."""

    intent: str
    count: int


class EvidenceRow(TypedDict):
    """One evidence row associated with a selected pair."""

    intent: str
    message: str
    hash: str
    date: str


class CommonPairIntentPanePayload(TypedDict):
    """Input payload for the common-pair intent pane."""

    pairing: str
    affinity: str
    message_count: int
    intent_counts: list[IntentCountRow]
    evidence_rows: list[EvidenceRow]


def _component_id(component_id_prefix: str, suffix: str) -> str:
    return f"{component_id_prefix}-{suffix}"


def _normalized_intent(intent_value: str) -> str:
    normalized = (intent_value or "").strip().lower()
    return normalized or "unknown"


def _format_affinity_label(affinity_value: str) -> str:
    try:
        return f"Affinity {float(affinity_value):.2f}"
    except (TypeError, ValueError):
        affinity_text = str(affinity_value).strip()
        if not affinity_text:
            return "Affinity n/a"
        return f"Affinity {affinity_text}"


def _intent_leader(intent_counts: list[IntentCountRow]) -> tuple[str, int]:
    if not intent_counts:
        return ("unknown", 0)
    first_row = intent_counts[0]
    return (_normalized_intent(first_row["intent"]), int(first_row["count"]))


def filter_evidence_rows_by_intent(
    evidence_rows: list[EvidenceRow], focused_intent: str | None = None
) -> list[EvidenceRow]:
    """Filter evidence rows by an optional focused intent."""
    normalized_focus = _normalized_intent(focused_intent or "")
    if not focused_intent or normalized_focus == "all":
        return evidence_rows
    return [
        evidence_row
        for evidence_row in evidence_rows
        if _normalized_intent(evidence_row.get("intent", ""))
        == normalized_focus
    ]


def build_intent_chips(
    intent_counts: list[IntentCountRow],
    message_count: int,
    focused_intent: str | None = None,
) -> list[html.Span]:
    """Create compact intent mix chips."""
    chips: list[html.Span] = []
    normalized_focus = _normalized_intent(focused_intent or "")
    for intent_count_row in intent_counts[:MAX_INTENT_CHIP_COUNT]:
        intent_name = _normalized_intent(intent_count_row["intent"])
        count = int(intent_count_row["count"])
        percent = round((count / message_count) * 100) if message_count else 0
        chip_style = dict(INTENT_CHIP_STYLE)
        if focused_intent and normalized_focus == intent_name:
            chip_style.update(FOCUSED_INTENT_CHIP_STYLE)
        chips.append(
            html.Span(
                f"{intent_name} {count} ({percent}%)",
                style=chip_style,
            )
        )
    return chips


def build_evidence_preview_items(
    evidence_rows: list[EvidenceRow],
    preview_row_count: int = DEFAULT_PREVIEW_ROW_COUNT,
) -> list[html.Li]:
    """Build compact preview rows with hover tooltips."""
    if not evidence_rows:
        return [html.Li("No evidence rows available for this focus.")]

    preview_rows: list[html.Li] = []
    for evidence_row in evidence_rows[:preview_row_count]:
        message_text = (evidence_row.get("message", "") or "").strip()
        if not message_text:
            message_text = "(empty commit message)"
        intent_name = _normalized_intent(evidence_row.get("intent", ""))
        hash_text = evidence_row.get("hash", "-")
        date_text = evidence_row.get("date", "-")
        preview_rows.append(
            html.Li(
                [
                    html.Span(
                        f"{intent_name} · {hash_text} · {date_text}",
                        style={"color": "#64748b", "marginRight": "6px"},
                    ),
                    html.Span(
                        message_text[:120],
                        title=message_text,
                    ),
                ]
            )
        )
    return preview_rows


def _drilldown_data(evidence_rows: list[EvidenceRow]) -> list[dict[str, str]]:
    return [
        {
            "intent": _normalized_intent(evidence_row.get("intent", "")),
            "hash": evidence_row.get("hash", "-"),
            "date": evidence_row.get("date", "-"),
            "message": evidence_row.get("message", ""),
        }
        for evidence_row in evidence_rows
    ]


def build_common_pair_intent_pane(
    payload: CommonPairIntentPanePayload | None,
    *,
    focused_intent: str | None = None,
    preview_row_count: int = DEFAULT_PREVIEW_ROW_COUNT,
    component_id_prefix: str = "id-common-pair-intent-pane",
    title_text: str = "Pair Intent Snapshot",
    empty_state_message: str = EMPTY_SELECTION_MESSAGE,
) -> html.Div:
    """Build a compact right-side pane for selected common-pair intent."""
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
    intent_counts = payload.get("intent_counts", [])
    filtered_evidence_rows = filter_evidence_rows_by_intent(
        payload.get("evidence_rows", []),
        focused_intent=focused_intent,
    )
    intent_leader, intent_leader_count = _intent_leader(intent_counts)
    leader_coverage = (
        round((intent_leader_count / message_count) * 100)
        if message_count
        else 0
    )
    intent_chips = build_intent_chips(
        intent_counts=intent_counts,
        message_count=message_count,
        focused_intent=focused_intent,
    )

    drilldown_data = _drilldown_data(filtered_evidence_rows)
    drilldown_summary_text = (
        f"Drill down into {len(drilldown_data)} evidence row(s)"
    )

    return html.Div(
        id=_component_id(component_id_prefix, "container"),
        style=PANE_STYLE,
        children=[
            html.H3(title_text, style={"margin": "0 0 6px"}),
            html.Div(
                str(payload.get("pairing", "")),
                id=_component_id(component_id_prefix, "pairing"),
                style={"fontWeight": "600"},
            ),
            html.Div(
                style=METRICS_ROW_STYLE,
                children=[
                    html.Span(
                        _format_affinity_label(payload.get("affinity", "")),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        f"Intent leader {intent_leader}",
                        id=_component_id(
                            component_id_prefix, "summary-intent-leader"
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        f"Leader coverage {leader_coverage}%",
                        id=_component_id(
                            component_id_prefix, "summary-leader-coverage"
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                    html.Span(
                        f"Evidence {message_count}",
                        id=_component_id(
                            component_id_prefix, "summary-evidence-count"
                        ),
                        style=METRIC_CHIP_STYLE,
                    ),
                ],
            ),
            html.Div(
                "Intent mix",
                style={"fontWeight": "600", "marginBottom": "4px"},
            ),
            html.Div(
                intent_chips or [html.Span("No intent data available.")],
                id=_component_id(component_id_prefix, "intent-chips"),
                style=METRICS_ROW_STYLE,
            ),
            html.P(
                DRILLDOWN_HELPER_MESSAGE,
                style={"margin": "0 0 4px", "color": "#64748b"},
            ),
            html.Ul(
                build_evidence_preview_items(
                    evidence_rows=filtered_evidence_rows,
                    preview_row_count=preview_row_count,
                ),
                id=_component_id(component_id_prefix, "evidence-preview"),
                style=PREVIEW_LIST_STYLE,
            ),
            html.Details(
                children=[
                    html.Summary(
                        drilldown_summary_text,
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
                            "maxHeight": "240px",
                            "overflowY": "auto",
                            "marginTop": "6px",
                        },
                    ),
                ]
            ),
        ],
    )
