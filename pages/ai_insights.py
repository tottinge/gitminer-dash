"""AI Insights page for ranked, evidence-backed hotspots."""

from __future__ import annotations

from dash import Input, Output, callback, dcc, html, register_page
from dash.dash_table import DataTable
from dash.exceptions import PreventUpdate

import data
from insights.citation_guard import validate_narrative_citations
from insights.llm_client import get_llm_client
from insights.prompt_builder import build_prompt_payload
from insights.report_builder import build_insight_report
from insights.snapshot_builder import build_analysis_snapshot
from utils import date_utils

register_page(
    module=__name__,
    name="AI Insights",
)
NARRATIVE_SECTION_TITLE = (  # pragma: no mutate
    "Narrative Summary (strict citations)"
)
NARRATIVE_EMPTY_STATUS = (  # pragma: no mutate
    "No evidence-backed hotspots in selected period."
)
NARRATIVE_PASSED_STATUS = "Citation validation passed."  # pragma: no mutate
NARRATIVE_FAILED_STATUS = (  # pragma: no mutate
    "Citation validation failed. Narrative hidden."
)

layout = html.Div(
    [
        html.H2("AI Insights", style={"margin": "10px 0"}),
        html.P(
            id="id-ai-insights-status",
            style={"fontStyle": "italic", "color": "#666"},
        ),
        dcc.Loading(
            id="loading-ai-insights-table",
            type="circle",
            children=[
                DataTable(
                    id="id-ai-insights-table",
                    columns=[
                        {"name": "Rank", "id": "rank"},
                        {"name": "File", "id": "file_path"},
                        {"name": "Risk Score", "id": "score"},
                        {"name": "Evidence", "id": "evidence_refs"},
                    ],
                    style_table={"maxHeight": "500px", "overflowY": "auto"},
                    style_cell={"textAlign": "left", "padding": "8px"},
                    style_cell_conditional=[
                        {"if": {"column_id": "rank"}, "width": "8%"},
                        {"if": {"column_id": "file_path"}, "width": "35%"},
                        {"if": {"column_id": "score"}, "width": "12%"},
                        {"if": {"column_id": "evidence_refs"}, "width": "45%"},
                    ],
                    data=[],
                )
            ],
        ),
        html.H3(
            NARRATIVE_SECTION_TITLE,
            style={"margin": "16px 0 8px"},
        ),
        html.P(
            id="id-ai-insights-narrative-status",
            style={"fontStyle": "italic", "color": "#666"},
        ),
        html.Pre(
            id="id-ai-insights-narrative-text",
            style={
                "whiteSpace": "pre-wrap",
                "padding": "8px",
                "backgroundColor": "#f8f9fa",
                "border": "1px solid #ddd",
                "borderRadius": "4px",
            },
        ),
        DataTable(
            id="id-ai-insights-narrative-invalid-claims",
            columns=[
                {"name": "Line", "id": "line"},
                {"name": "Reason", "id": "reason"},
                {"name": "Claim", "id": "claim"},
                {"name": "Unknown Citations", "id": "unknown_citations"},
            ],
            style_table={"maxHeight": "240px", "overflowY": "auto"},
            style_cell={"textAlign": "left", "padding": "8px"},
            style_cell_conditional=[
                {"if": {"column_id": "line"}, "width": "8%"},
                {"if": {"column_id": "reason"}, "width": "18%"},
                {"if": {"column_id": "claim"}, "width": "44%"},
                {"if": {"column_id": "unknown_citations"}, "width": "30%"},
            ],
            data=[],
        ),
    ]
)


def _row(rank: int, hotspot) -> dict[str, object]:
    evidence_refs = " | ".join(
        f"{item.kind}:{item.value}" for item in hotspot.evidence
    )
    return {
        "rank": rank,
        "file_path": hotspot.file_path,
        "score": round(hotspot.score, 2),
        "evidence_refs": evidence_refs,
    }


def _invalid_claim_row(claim: dict[str, object]) -> dict[str, object]:
    unknown_citations = claim.get("unknown_citations", [])
    citations = (
        " | ".join(unknown_citations)
        if isinstance(unknown_citations, list)
        else ""
    )
    return {
        "line": claim.get("line"),
        "reason": claim.get("reason"),
        "claim": claim.get("claim"),
        "unknown_citations": citations,
    }


def _strict_narrative_result(report) -> dict[str, object]:
    prompt_payload = build_prompt_payload(report=report)
    narrative_text = get_llm_client().generate_narrative(
        prompt_payload=prompt_payload
    )
    citation_validation = validate_narrative_citations(
        report=report, narrative_text=narrative_text
    )
    if citation_validation["passed"]:
        return {
            "passed": True,
            "narrative_text": narrative_text,
            "invalid_claims": [],
        }
    return {
        "passed": False,
        "narrative_text": "",
        "invalid_claims": [
            _invalid_claim_row(item)
            for item in citation_validation["invalid_claims"]
        ],
    }


@callback(
    [
        Output("id-ai-insights-table", "data"),
        Output("id-ai-insights-status", "children"),
    ],
    Input("global-date-range", "data"),
)
def populate_insights(store_data):
    """Populate ranked insights table for selected date range."""
    if not store_data or "period" not in store_data:
        raise PreventUpdate

    begin, end = date_utils.parse_date_range_from_store(store_data)
    repo = data.get_repo()
    snapshot = build_analysis_snapshot(
        repo=repo, period_start=begin, period_end=end
    )
    report = build_insight_report(snapshot=snapshot)

    rows = [
        _row(rank=index, hotspot=item)
        for index, item in enumerate(report.hotspots, start=1)
    ]
    if not rows:
        return [], "No evidence-backed hotspots in selected period."

    return rows, f"{len(rows)} evidence-backed hotspots in selected period."


@callback(
    [
        Output("id-ai-insights-narrative-status", "children"),
        Output("id-ai-insights-narrative-text", "children"),
        Output("id-ai-insights-narrative-invalid-claims", "data"),
    ],
    Input("global-date-range", "data"),
)
def populate_narrative_summary(store_data):
    """Populate strict-citation narrative summary for selected date range."""
    if not store_data or "period" not in store_data:
        raise PreventUpdate

    begin, end = date_utils.parse_date_range_from_store(store_data)
    repo = data.get_repo()
    snapshot = build_analysis_snapshot(
        repo=repo, period_start=begin, period_end=end
    )
    report = build_insight_report(snapshot=snapshot)
    if not report.hotspots:
        return NARRATIVE_EMPTY_STATUS, "", []

    narrative_result = _strict_narrative_result(report)
    if narrative_result["passed"]:
        return (
            NARRATIVE_PASSED_STATUS,
            narrative_result["narrative_text"],
            [],
        )
    return (
        NARRATIVE_FAILED_STATUS,
        "",
        narrative_result["invalid_claims"],
    )
