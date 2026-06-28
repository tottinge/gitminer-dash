"""Compact right-pane component for common-pair intent and evidence drill-down."""

from __future__ import annotations

from typing import TypedDict

from dash import html
from dash.dash_table import DataTable

EMPTY_SELECTION_MESSAGE = "Select a common pair to preview intent and supporting evidence."  # pragma: no mutate
DRILLDOWN_HELPER_MESSAGE = (
    "Hover preview rows for full messages. Expand drill-down for full "  # pragma: no mutate
    "evidence."  # pragma: no mutate
)
DEFAULT_PREVIEW_ROW_COUNT = 3
MAX_INTENT_CHIP_COUNT = 4

PANE_STYLE = {
    "backgroundColor": "#ffffff",  # pragma: no mutate
    "border": "1px solid #d9dee8",  # pragma: no mutate
    "borderRadius": "10px",  # pragma: no mutate
    "padding": "10px 12px",  # pragma: no mutate
    "boxShadow": "0 1px 2px rgba(15, 23, 42, 0.06)",  # pragma: no mutate
    "fontSize": "12px",  # pragma: no mutate
}
METRICS_ROW_STYLE = {
    "display": "flex",  # pragma: no mutate
    "gap": "6px",  # pragma: no mutate
    "flexWrap": "wrap",  # pragma: no mutate
    "margin": "6px 0 8px",  # pragma: no mutate
}
METRIC_CHIP_STYLE = {
    "backgroundColor": "#f8fafc",  # pragma: no mutate
    "border": "1px solid #e2e8f0",  # pragma: no mutate
    "borderRadius": "999px",  # pragma: no mutate
    "padding": "2px 8px",  # pragma: no mutate
    "fontWeight": "600",  # pragma: no mutate
}
INTENT_CHIP_STYLE = {
    "backgroundColor": "#f8fafc",  # pragma: no mutate
    "border": "1px solid #e2e8f0",  # pragma: no mutate
    "borderRadius": "999px",  # pragma: no mutate
    "padding": "2px 8px",  # pragma: no mutate
}
FOCUSED_INTENT_CHIP_STYLE = {
    "backgroundColor": "#dbeafe",  # pragma: no mutate
    "border": "1px solid #60a5fa",  # pragma: no mutate
}
PREVIEW_LIST_STYLE = {
    "margin": "6px 0 8px",  # pragma: no mutate
    "paddingLeft": "16px",  # pragma: no mutate
    "maxHeight": "130px",  # pragma: no mutate
    "overflowY": "auto",  # pragma: no mutate
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
        return f"Affinity {float(affinity_value):.2f}"  # pragma: no mutate
    except (TypeError, ValueError):
        affinity_text = str(affinity_value).strip()  # pragma: no mutate
        if not affinity_text:
            return "Affinity n/a"  # pragma: no mutate
        return f"Affinity {affinity_text}"  # pragma: no mutate


def _intent_leader(intent_counts: list[IntentCountRow]) -> tuple[str, int]:
    if not intent_counts:
        return ("unknown", 0)
    first_row = intent_counts[0]
    return (_normalized_intent(first_row["intent"]), int(first_row["count"]))


def filter_evidence_rows_by_intent(
    evidence_rows: list[EvidenceRow], focused_intent: str | None = None
) -> list[EvidenceRow]:
    """Filter evidence rows by an optional focused intent."""
    normalized_focus = _normalized_intent(
        focused_intent or ""
    )  # pragma: no mutate
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
        chip_style = dict(INTENT_CHIP_STYLE)  # pragma: no mutate
        if focused_intent and normalized_focus == intent_name:
            chip_style.update(FOCUSED_INTENT_CHIP_STYLE)  # pragma: no mutate
        chips.append(
            html.Span(
                f"{intent_name} {count} ({percent}%)",  # pragma: no mutate
                style=chip_style,  # pragma: no mutate
            )
        )
    return chips


def build_evidence_preview_items(
    evidence_rows: list[EvidenceRow],
    preview_row_count: int = DEFAULT_PREVIEW_ROW_COUNT,
) -> list[html.Li]:
    """Build compact preview rows with hover tooltips."""
    if not evidence_rows:
        return [
            html.Li("No evidence rows available for this focus.")
        ]  # pragma: no mutate

    preview_rows: list[html.Li] = []
    for evidence_row in evidence_rows[:preview_row_count]:
        message_text = (evidence_row.get("message", "") or "").strip()
        if not message_text:
            message_text = "(empty commit message)"  # pragma: no mutate
        intent_name = _normalized_intent(evidence_row.get("intent", ""))
        hash_text = evidence_row.get("hash", "-")
        date_text = evidence_row.get("date", "-")
        preview_rows.append(
            html.Li(
                [
                    html.Span(
                        f"{intent_name} · {hash_text} · {date_text}",  # pragma: no mutate
                        style={
                            "color": "#64748b",
                            "marginRight": "6px",
                        },  # pragma: no mutate
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
    title_text: str = "Pair Intent Snapshot",  # pragma: no mutate
    empty_state_message: str = EMPTY_SELECTION_MESSAGE,
) -> html.Div:
    """Build a compact right-side pane for selected common-pair intent."""
    if not payload:
        return html.Div(
            id=_component_id(component_id_prefix, "container"),
            style=PANE_STYLE,  # pragma: no mutate
            children=[
                html.H3(
                    title_text, style={"margin": "0 0 6px"}
                ),  # pragma: no mutate
                html.P(
                    empty_state_message,
                    id=_component_id(
                        component_id_prefix,
                        "empty-state-message",
                    ),
                    style={
                        "margin": "0",
                        "color": "#64748b",
                    },  # pragma: no mutate
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
    drilldown_summary_text = f"Drill down into {len(drilldown_data)} evidence row(s)"  # pragma: no mutate

    return html.Div(
        id=_component_id(component_id_prefix, "container"),
        style=PANE_STYLE,  # pragma: no mutate
        children=[
            html.H3(
                title_text, style={"margin": "0 0 6px"}
            ),  # pragma: no mutate
            html.Div(
                str(payload.get("pairing", "")),
                id=_component_id(component_id_prefix, "pairing"),
                style={"fontWeight": "600"},  # pragma: no mutate
            ),
            html.Div(
                style=METRICS_ROW_STYLE,  # pragma: no mutate
                children=[
                    html.Span(
                        _format_affinity_label(payload.get("affinity", "")),
                        style=METRIC_CHIP_STYLE,  # pragma: no mutate
                    ),
                    html.Span(
                        f"Intent leader {intent_leader}",  # pragma: no mutate
                        id=_component_id(
                            component_id_prefix, "summary-intent-leader"
                        ),
                        style=METRIC_CHIP_STYLE,  # pragma: no mutate
                    ),
                    html.Span(
                        f"Leader coverage {leader_coverage}%",  # pragma: no mutate
                        id=_component_id(
                            component_id_prefix, "summary-leader-coverage"
                        ),
                        style=METRIC_CHIP_STYLE,  # pragma: no mutate
                    ),
                    html.Span(
                        f"Evidence {message_count}",  # pragma: no mutate
                        id=_component_id(
                            component_id_prefix, "summary-evidence-count"
                        ),
                        style=METRIC_CHIP_STYLE,  # pragma: no mutate
                    ),
                ],
            ),
            html.Div(
                "Intent mix",  # pragma: no mutate
                style={
                    "fontWeight": "600",
                    "marginBottom": "4px",
                },  # pragma: no mutate
            ),
            html.Div(
                intent_chips
                or [
                    html.Span("No intent data available.")
                ],  # pragma: no mutate
                id=_component_id(component_id_prefix, "intent-chips"),
                style=METRICS_ROW_STYLE,  # pragma: no mutate
            ),
            html.P(
                DRILLDOWN_HELPER_MESSAGE,
                style={
                    "margin": "0 0 4px",
                    "color": "#64748b",
                },  # pragma: no mutate
            ),
            html.Ul(
                build_evidence_preview_items(
                    evidence_rows=filtered_evidence_rows,
                    preview_row_count=preview_row_count,
                ),
                id=_component_id(component_id_prefix, "evidence-preview"),
                style=PREVIEW_LIST_STYLE,  # pragma: no mutate
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
                            {
                                "name": "Intent",
                                "id": "intent",
                            },  # pragma: no mutate
                            {"name": "Hash", "id": "hash"},  # pragma: no mutate
                            {"name": "Date", "id": "date"},  # pragma: no mutate
                            {
                                "name": "Message",
                                "id": "message",
                            },  # pragma: no mutate
                        ],
                        data=drilldown_data,
                        style_cell={
                            "textAlign": "left",
                            "padding": "4px 6px",  # pragma: no mutate
                            "fontSize": "12px",  # pragma: no mutate
                        },
                        style_table={
                            "maxHeight": "240px",  # pragma: no mutate
                            "overflowY": "auto",  # pragma: no mutate
                            "marginTop": "6px",  # pragma: no mutate
                        },
                    ),
                ]
            ),
        ],
    )
