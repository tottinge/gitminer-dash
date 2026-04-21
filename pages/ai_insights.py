"""AI Insights page for ranked, evidence-backed hotspots."""

from __future__ import annotations

import re
from urllib.parse import quote

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
INSIGHTS_TABLE_TOOLTIPS = {  # pragma: no mutate
    "commit_count": "Commits touching this file in selected period.",
    "latest_commit_link": "Most recent evidence commit for this hotspot.",
    "risk_reason": "Deterministic risk classification based on evidence.",
    "suggested_action": "Deterministic first action from risk class.",
}
FILTER_LABEL = "Filters"  # pragma: no mutate
TOP_N_LABEL = "Top N hotspots"  # pragma: no mutate
MIN_SCORE_LABEL = "Minimum score"  # pragma: no mutate
FILTER_EXCLUDE_CONFIG = "exclude_config"
FILTER_EXCLUDE_TESTS = "exclude_tests"
FILTER_OPTIONS = [  # pragma: no mutate
    {"label": "Exclude config/lock files", "value": FILTER_EXCLUDE_CONFIG},
    {"label": "Exclude test files", "value": FILTER_EXCLUDE_TESTS},
]
DRILLDOWN_SECTION_TITLE = "Hotspot Drill-down"  # pragma: no mutate
DRILLDOWN_EMPTY_STATUS = "No hotspot selected."  # pragma: no mutate
DRILLDOWN_SELECTED_STATUS = "Selected hotspot details."  # pragma: no mutate
DRILLDOWN_HELPER_TEXT = (  # pragma: no mutate
    "Select a hotspot row to inspect details and evidence."
)
NARRATIVE_HELPER_TEXT = (  # pragma: no mutate
    "Narrative is shown only when strict citations pass."
)
SECTION_CARD_STYLE = {  # pragma: no mutate
    "backgroundColor": "#ffffff",
    "border": "1px solid #d9dee8",
    "borderRadius": "10px",
    "padding": "12px",
    "marginBottom": "12px",
    "boxShadow": "0 1px 2px rgba(15, 23, 42, 0.06)",
}
HELPER_TEXT_STYLE = {  # pragma: no mutate
    "color": "#64748b",
    "margin": "0 0 8px",
}
TABLE_CELL_STYLE = {  # pragma: no mutate
    "textAlign": "left",
    "padding": "8px",
}
MAIN_TABLE_STYLE_TABLE = {  # pragma: no mutate
    "maxHeight": "480px",
    "overflowY": "auto",
    "overflowX": "auto",
}
DRILLDOWN_TABLE_STYLE_TABLE = {  # pragma: no mutate
    "maxHeight": "240px",
    "overflowY": "auto",
    "overflowX": "auto",
}
INVALID_CLAIMS_TABLE_STYLE_TABLE = {  # pragma: no mutate
    "maxHeight": "200px",
    "overflowY": "auto",
    "overflowX": "auto",
}
NARRATIVE_PRE_STYLE = {  # pragma: no mutate
    "whiteSpace": "pre-wrap",
    "padding": "8px",
    "backgroundColor": "#f8f9fa",
    "border": "1px solid #ddd",
    "borderRadius": "4px",
    "maxHeight": "220px",
    "overflowY": "auto",
}
MAIN_TABLE_HEADER_STYLE = {  # pragma: no mutate
    "backgroundColor": "#e8f1ff",
    "fontWeight": "600",
}
DRILLDOWN_TABLE_HEADER_STYLE = {  # pragma: no mutate
    "backgroundColor": "#eefbf3",
    "fontWeight": "600",
}
INVALID_CLAIMS_TABLE_HEADER_STYLE = {  # pragma: no mutate
    "backgroundColor": "#fff1f2",
    "fontWeight": "600",
}
TABLE_ZEBRA_STYLE_CONDITIONAL = [  # pragma: no mutate
    {"if": {"row_index": "odd"}, "backgroundColor": "#f8fafc"},
    {"if": {"row_index": "even"}, "backgroundColor": "#ffffff"},
]
MAIN_TABLE_STYLE_DATA_CONDITIONAL = [  # pragma: no mutate
    *TABLE_ZEBRA_STYLE_CONDITIONAL,
    {
        "if": {"filter_query": '{trend} = "rising"'},
        "backgroundColor": "#fff7e6",
    },
    {
        "if": {"filter_query": '{trend} = "falling"'},
        "backgroundColor": "#e6f7f1",
    },
    {
        "if": {"filter_query": '{trend} = "new"'},
        "backgroundColor": "#f3e8ff",
    },
    {
        "if": {"state": "selected"},
        "backgroundColor": "#dbeafe",
        "border": "1px solid #60a5fa",
    },
]

layout = html.Div(
    [
        html.H2("AI Insights", style={"margin": "10px 0"}),
        html.Div(
            [
                html.Div(
                    [
                        html.Label(TOP_N_LABEL),
                        dcc.Dropdown(
                            id="id-ai-insights-top-n",
                            options=[
                                {"label": "5", "value": 5},
                                {"label": "10", "value": 10},
                                {"label": "20", "value": 20},
                            ],
                            value=10,
                            clearable=False,
                        ),
                    ],
                    style={"width": "22%"},
                ),
                html.Div(
                    [
                        html.Label(MIN_SCORE_LABEL),
                        dcc.Input(
                            id="id-ai-insights-min-score",
                            type="number",
                            min=0,
                            step=1,
                            value=0,
                        ),
                    ],
                    style={"width": "22%"},
                ),
                html.Div(
                    [
                        html.Label(FILTER_LABEL),
                        dcc.Checklist(
                            id="id-ai-insights-filters",
                            options=FILTER_OPTIONS,
                            value=[],
                        ),
                    ],
                    style={"width": "50%"},
                ),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "flex-start",
                "gap": "12px",
                "margin": "8px 0 12px",
            },
        ),
        html.Div(
            [
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
                                {
                                    "name": "File",
                                    "id": "file_display_link",
                                    "type": "text",
                                    "presentation": "markdown",
                                },
                                {"name": "Risk Score", "id": "score"},
                                {"name": "Δ Score", "id": "score_delta"},
                                {"name": "Trend", "id": "trend"},
                                {
                                    "name": "Commit Count",
                                    "id": "commit_count",
                                },
                                {
                                    "name": "Latest Commit",
                                    "id": "latest_commit_link",
                                    "type": "text",
                                    "presentation": "markdown",
                                },
                                {
                                    "name": "Why this is risky",
                                    "id": "risk_reason",
                                },
                                {
                                    "name": "Suggested action",
                                    "id": "suggested_action",
                                },
                            ],
                            tooltip_header=INSIGHTS_TABLE_TOOLTIPS,
                            style_table=MAIN_TABLE_STYLE_TABLE,
                            style_cell=TABLE_CELL_STYLE,
                            style_header=MAIN_TABLE_HEADER_STYLE,
                            style_data_conditional=(
                                MAIN_TABLE_STYLE_DATA_CONDITIONAL
                            ),
                            fixed_rows={"headers": True},
                            cell_selectable=True,
                            style_cell_conditional=[
                                {"if": {"column_id": "rank"}, "width": "8%"},
                                {
                                    "if": {"column_id": "file_display_link"},
                                    "width": "24%",
                                },
                                {"if": {"column_id": "score"}, "width": "8%"},
                                {
                                    "if": {"column_id": "score_delta"},
                                    "width": "8%",
                                },
                                {"if": {"column_id": "trend"}, "width": "8%"},
                                {
                                    "if": {"column_id": "commit_count"},
                                    "width": "8%",
                                },
                                {
                                    "if": {"column_id": "latest_commit_link"},
                                    "width": "12%",
                                },
                                {
                                    "if": {"column_id": "risk_reason"},
                                    "width": "18%",
                                },
                                {
                                    "if": {"column_id": "suggested_action"},
                                    "width": "14%",
                                },
                            ],
                            data=[],
                        )
                    ],
                ),
            ],
            style=SECTION_CARD_STYLE,
        ),
        html.Div(
            [
                html.H3(
                    DRILLDOWN_SECTION_TITLE,
                    style={"margin": "0 0 8px"},
                ),
                html.P(DRILLDOWN_HELPER_TEXT, style=HELPER_TEXT_STYLE),
                html.P(
                    id="id-ai-insights-drilldown-status",
                    style={"fontStyle": "italic", "color": "#666"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                DataTable(
                                    id="id-ai-insights-drilldown-details",
                                    columns=[
                                        {"name": "Field", "id": "field"},
                                        {"name": "Value", "id": "value"},
                                    ],
                                    style_table=DRILLDOWN_TABLE_STYLE_TABLE,
                                    style_cell=TABLE_CELL_STYLE,
                                    style_header=DRILLDOWN_TABLE_HEADER_STYLE,
                                    style_data_conditional=(
                                        TABLE_ZEBRA_STYLE_CONDITIONAL
                                    ),
                                    fixed_rows={"headers": True},
                                    data=[],
                                )
                            ],
                            style={"flex": "1 1 320px"},
                        ),
                        html.Div(
                            [
                                DataTable(
                                    id="id-ai-insights-drilldown-evidence",
                                    columns=[
                                        {
                                            "name": "Evidence Kind",
                                            "id": "kind",
                                        },
                                        {
                                            "name": "Evidence Value",
                                            "id": "value",
                                        },
                                    ],
                                    style_table=DRILLDOWN_TABLE_STYLE_TABLE,
                                    style_cell=TABLE_CELL_STYLE,
                                    style_header=DRILLDOWN_TABLE_HEADER_STYLE,
                                    style_data_conditional=(
                                        TABLE_ZEBRA_STYLE_CONDITIONAL
                                    ),
                                    fixed_rows={"headers": True},
                                    data=[],
                                )
                            ],
                            style={"flex": "1 1 320px"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "gap": "12px",
                        "flexWrap": "wrap",
                    },
                ),
            ],
            style=SECTION_CARD_STYLE,
        ),
        html.Div(
            [
                html.H3(
                    NARRATIVE_SECTION_TITLE,
                    style={"margin": "0 0 8px"},
                ),
                html.P(NARRATIVE_HELPER_TEXT, style=HELPER_TEXT_STYLE),
                html.P(
                    id="id-ai-insights-narrative-status",
                    style={"fontStyle": "italic", "color": "#666"},
                ),
                html.Pre(
                    id="id-ai-insights-narrative-text",
                    style=NARRATIVE_PRE_STYLE,
                ),
                DataTable(
                    id="id-ai-insights-narrative-invalid-claims",
                    columns=[
                        {"name": "Line", "id": "line"},
                        {"name": "Reason", "id": "reason"},
                        {"name": "Claim", "id": "claim"},
                        {
                            "name": "Unknown Citations",
                            "id": "unknown_citations",
                        },
                    ],
                    style_table=INVALID_CLAIMS_TABLE_STYLE_TABLE,
                    style_cell=TABLE_CELL_STYLE,
                    style_header=INVALID_CLAIMS_TABLE_HEADER_STYLE,
                    style_data_conditional=TABLE_ZEBRA_STYLE_CONDITIONAL,
                    fixed_rows={"headers": True},
                    style_cell_conditional=[
                        {"if": {"column_id": "line"}, "width": "8%"},
                        {"if": {"column_id": "reason"}, "width": "18%"},
                        {"if": {"column_id": "claim"}, "width": "44%"},
                        {
                            "if": {"column_id": "unknown_citations"},
                            "width": "30%",
                        },
                    ],
                    data=[],
                ),
            ],
            style=SECTION_CARD_STYLE,
        ),
    ]
)


def _evidence_value(hotspot, kind: str) -> str:
    for item in hotspot.evidence:
        if item.kind == kind:
            return item.value
    return ""


def _parse_commit_count(metric_value: str) -> int:
    matched = re.fullmatch(r"commit_count=(\d+)", metric_value)
    if not matched:
        return 0
    return int(matched.group(1))


def _extract_remote_url(repo) -> str:
    remotes = getattr(repo, "remotes", None)
    if remotes is None:
        return ""
    for remote in remotes:
        if getattr(remote, "name", "") != "origin":
            continue
        urls = list(getattr(remote, "urls", []))
        for url in urls:
            if isinstance(url, str):
                return url
        fallback_url = getattr(remote, "url", "")
        if isinstance(fallback_url, str):
            return fallback_url
    return ""


def _repo_web_base_url(repo) -> str:
    origin_url = _extract_remote_url(repo)
    if origin_url.startswith("https://"):
        return origin_url.removesuffix(".git")
    matched = re.fullmatch(r"git@([^:]+):(.+?)(?:\.git)?", origin_url)
    if not matched:
        return ""
    host = matched.group(1)
    path = matched.group(2)
    return f"https://{host}/{path}"


def _file_markdown_link(file_path: str, repo_path: str) -> str:
    if not repo_path:
        return file_path
    return f"[`{file_path}`](file://{repo_path}/{file_path})"


def _file_display_markdown_link(file_path: str, repo) -> str:
    base_url = _repo_web_base_url(repo)
    if not base_url:
        return file_path
    encoded_file_path = quote(file_path, safe="/")
    return f"[{file_path}]({base_url}/blob/HEAD/{encoded_file_path})"


def _commit_markdown_link(commit_ref: str, repo) -> str:
    if not commit_ref:
        return ""
    base_url = _repo_web_base_url(repo)
    if not base_url:
        return commit_ref
    return f"[{commit_ref}]({base_url}/commit/{commit_ref})"


def _risk_reason(file_path: str, score: float, commit_count: int) -> str:
    reasons: list[str] = []
    if commit_count >= 20:
        reasons.append("high_churn")
    if file_path.startswith("pages/"):
        reasons.append("ui_orchestration_surface")
    if file_path.startswith("visualization/"):
        reasons.append("visualization_logic_surface")
    if file_path.endswith((".toml", ".lock")):
        reasons.append("dependency_or_config_touchpoint")
    if not reasons and score >= 10:
        reasons.append("elevated_score")
    return ", ".join(reasons)


def _suggested_action(file_path: str, score: float, commit_count: int) -> str:
    reason = _risk_reason(
        file_path=file_path, score=score, commit_count=commit_count
    )
    if "dependency_or_config_touchpoint" in reason:
        return "tighten_dependency_workflow"
    if "ui_orchestration_surface" in reason and commit_count >= 20:
        return "extract_service_boundary"
    if "visualization_logic_surface" in reason:
        return "split_layout_and_rendering"
    if "high_churn" in reason:
        return "reduce_change_surface_with_helpers"
    return "monitor_next_period"


def _normalize_top_n(top_n: int | None) -> int:
    if top_n is None or top_n <= 0:
        return 10
    return top_n


def _normalize_min_score(min_score: float | int | None) -> float:
    if min_score is None:
        return 0.0
    return max(float(min_score), 0.0)


def _is_config_or_lock_path(file_path: str) -> bool:
    return file_path.endswith(
        (".toml", ".lock", ".yaml", ".yml", ".ini", ".cfg")
    )


def _passes_filters(
    file_path: str,
    score: float,
    min_score: float,
    filter_tokens: list[str] | None,
) -> bool:
    filters = set(filter_tokens or [])
    if score < min_score:
        return False
    if FILTER_EXCLUDE_CONFIG in filters and _is_config_or_lock_path(file_path):
        return False
    return not (
        FILTER_EXCLUDE_TESTS in filters and file_path.startswith("tests/")
    )


def _previous_period_bounds(begin, end):
    duration = end - begin
    previous_end = begin
    previous_begin = begin - duration
    return previous_begin, previous_end


def _trend_bucket(current_score: float, previous_score: float) -> str:
    if previous_score == 0 and current_score > 0:
        return "new"
    delta = current_score - previous_score
    if delta > 0.5:
        return "rising"
    if delta < -0.5:
        return "falling"
    return "stable"


def _row(
    rank: int,
    hotspot,
    repo,
    repo_path: str,
    previous_scores: dict[str, float],
) -> dict[str, object]:
    file_path = hotspot.file_path
    score = round(hotspot.score, 2)
    previous_score = round(previous_scores.get(file_path, 0.0), 2)
    score_delta = round(score - previous_score, 2)
    evidence_refs = " | ".join(
        f"{item.kind}:{item.value}" for item in hotspot.evidence
    )
    commit_count = _parse_commit_count(_evidence_value(hotspot, "metric"))
    commit_ref = _evidence_value(hotspot, "commit")
    return {
        "rank": rank,
        "file_path": file_path,
        "file_link": _file_markdown_link(file_path, repo_path),
        "file_display_link": _file_display_markdown_link(file_path, repo),
        "score": score,
        "score_delta": score_delta,
        "trend": _trend_bucket(score, previous_score),
        "commit_count": commit_count,
        "latest_commit_link": _commit_markdown_link(commit_ref, repo),
        "risk_reason": _risk_reason(file_path, score, commit_count),
        "suggested_action": _suggested_action(file_path, score, commit_count),
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


def _evidence_rows_from_refs(evidence_refs: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not evidence_refs:
        return rows
    for token in evidence_refs.split(" | "):
        if ":" in token:
            kind, value = token.split(":", 1)
        else:
            kind, value = token, ""
        rows.append({"kind": kind, "value": value})
    return rows


def _row_highlight_style(active_cell, rows) -> list[dict[str, object]]:
    style = list(MAIN_TABLE_STYLE_DATA_CONDITIONAL)
    if not rows:
        return style
    selected_index = 0
    if isinstance(active_cell, dict):
        selected_index = int(active_cell.get("row", 0))
    if selected_index < 0 or selected_index >= len(rows):
        selected_index = 0
    style.append(
        {
            "if": {"row_index": selected_index},
            "backgroundColor": "#dbeafe",
            "border": "1px solid #60a5fa",
        }
    )
    return style


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
    [
        Input("global-date-range", "data"),
        Input("id-ai-insights-top-n", "value"),
        Input("id-ai-insights-min-score", "value"),
        Input("id-ai-insights-filters", "value"),
    ],
)
def populate_insights(
    store_data,
    top_n: int | None = 10,
    min_score: float | int | None = 0,
    filters: list[str] | None = None,
):
    """Populate ranked insights table for selected date range."""
    if not store_data or "period" not in store_data:
        raise PreventUpdate
    normalized_top_n = _normalize_top_n(top_n)
    normalized_min_score = _normalize_min_score(min_score)
    report_size = max(50, normalized_top_n * 5)

    begin, end = date_utils.parse_date_range_from_store(store_data)
    repo = data.get_repo()
    previous_begin, previous_end = _previous_period_bounds(begin, end)
    previous_snapshot = build_analysis_snapshot(
        repo=repo, period_start=previous_begin, period_end=previous_end
    )
    previous_report = build_insight_report(
        snapshot=previous_snapshot, top_n=report_size
    )
    previous_scores = {
        item.file_path: round(item.score, 2)
        for item in previous_report.hotspots
    }
    snapshot = build_analysis_snapshot(
        repo=repo, period_start=begin, period_end=end
    )
    report = build_insight_report(snapshot=snapshot, top_n=report_size)
    filtered_hotspots = [
        item
        for item in report.hotspots
        if _passes_filters(
            file_path=item.file_path,
            score=item.score,
            min_score=normalized_min_score,
            filter_tokens=filters,
        )
    ]
    limited_hotspots = filtered_hotspots[:normalized_top_n]

    rows = [
        _row(
            rank=index,
            hotspot=item,
            repo=repo,
            repo_path=report.repo_path,
            previous_scores=previous_scores,
        )
        for index, item in enumerate(limited_hotspots, start=1)
    ]
    if not rows:
        return [], "No evidence-backed hotspots in selected period."

    return rows, f"{len(rows)} evidence-backed hotspots in selected period."


@callback(
    [
        Output("id-ai-insights-drilldown-status", "children"),
        Output("id-ai-insights-drilldown-details", "data"),
        Output("id-ai-insights-drilldown-evidence", "data"),
    ],
    [
        Input("id-ai-insights-table", "active_cell"),
        Input("id-ai-insights-table", "data"),
    ],
)
def populate_hotspot_drilldown(active_cell, rows):
    """Populate drill-down detail rows for selected hotspot."""
    if not rows:
        return DRILLDOWN_EMPTY_STATUS, [], []
    if isinstance(active_cell, dict):
        selected_index = int(active_cell.get("row", 0))
    else:
        selected_index = 0
    if selected_index < 0 or selected_index >= len(rows):
        selected_index = 0
    selected_row = rows[selected_index]

    details = [
        {"field": "file_path", "value": selected_row.get("file_path", "")},
        {"field": "risk_score", "value": selected_row.get("score", 0)},
        {"field": "score_delta", "value": selected_row.get("score_delta", 0)},
        {"field": "trend", "value": selected_row.get("trend", "")},
        {"field": "commit_count", "value": selected_row.get("commit_count", 0)},
        {
            "field": "risk_reason",
            "value": selected_row.get("risk_reason", ""),
        },
        {
            "field": "suggested_action",
            "value": selected_row.get("suggested_action", ""),
        },
    ]
    evidence_rows = _evidence_rows_from_refs(
        selected_row.get("evidence_refs", "")
    )
    return DRILLDOWN_SELECTED_STATUS, details, evidence_rows


@callback(
    Output("id-ai-insights-table", "style_data_conditional"),
    [
        Input("id-ai-insights-table", "active_cell"),
        Input("id-ai-insights-table", "data"),
    ],
)
def populate_hotspot_row_highlight(active_cell, rows):
    """Keep main-table selection row-focused when a cell is clicked."""
    return _row_highlight_style(active_cell, rows)


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
