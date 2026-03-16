"""AI Insights page for ranked, evidence-backed hotspots."""

from __future__ import annotations

import re

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
                        {
                            "name": "File",
                            "id": "file_link",
                            "presentation": "markdown",
                        },
                        {"name": "Risk Score", "id": "score"},
                        {"name": "Commit Count", "id": "commit_count"},
                        {
                            "name": "Latest Commit",
                            "id": "latest_commit_link",
                            "presentation": "markdown",
                        },
                        {"name": "Why this is risky", "id": "risk_reason"},
                        {
                            "name": "Suggested action",
                            "id": "suggested_action",
                        },
                    ],
                    tooltip_header=INSIGHTS_TABLE_TOOLTIPS,
                    style_table={"maxHeight": "500px", "overflowY": "auto"},
                    style_cell={"textAlign": "left", "padding": "8px"},
                    style_cell_conditional=[
                        {"if": {"column_id": "rank"}, "width": "8%"},
                        {"if": {"column_id": "file_link"}, "width": "24%"},
                        {"if": {"column_id": "score"}, "width": "10%"},
                        {"if": {"column_id": "commit_count"}, "width": "10%"},
                        {
                            "if": {"column_id": "latest_commit_link"},
                            "width": "12%",
                        },
                        {"if": {"column_id": "risk_reason"}, "width": "18%"},
                        {
                            "if": {"column_id": "suggested_action"},
                            "width": "14%",
                        },
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


def _commit_markdown_link(commit_ref: str, repo) -> str:
    if not commit_ref:
        return ""
    base_url = _repo_web_base_url(repo)
    if not base_url:
        return commit_ref
    return f"[`{commit_ref}`]({base_url}/commit/{commit_ref})"


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


def _row(rank: int, hotspot, repo, repo_path: str) -> dict[str, object]:
    file_path = hotspot.file_path
    score = round(hotspot.score, 2)
    evidence_refs = " | ".join(
        f"{item.kind}:{item.value}" for item in hotspot.evidence
    )
    commit_count = _parse_commit_count(_evidence_value(hotspot, "metric"))
    commit_ref = _evidence_value(hotspot, "commit")
    return {
        "rank": rank,
        "file_path": file_path,
        "file_link": _file_markdown_link(file_path, repo_path),
        "score": score,
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
        _row(
            rank=index,
            hotspot=item,
            repo=repo,
            repo_path=report.repo_path,
        )
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
