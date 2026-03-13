"""AI Insights page for ranked, evidence-backed hotspots."""

from __future__ import annotations

from dash import Input, Output, callback, dcc, html, register_page
from dash.dash_table import DataTable
from dash.exceptions import PreventUpdate

import data
from insights.report_builder import build_insight_report
from insights.snapshot_builder import build_analysis_snapshot
from utils import date_utils

register_page(
    module=__name__,
    name="AI Insights",
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
