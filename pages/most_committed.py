# pylint: disable=duplicate-code
from dash import Input, Output, callback, dcc, html, register_page
from dash.dash_table import DataTable
from dash.exceptions import PreventUpdate

import repository_context as repo_context
from algorithms.commit_frequency import calculate_file_commit_frequency
from algorithms.commit_message_classifier import classify_commit_messages
from pages.most_committed_service import (
    collect_file_commit_evidence,
    generate_table_selection_file_change_diagnostic_payload,
)
from utils import date_utils
from visualization.file_change_diagnostic_pane import (
    EMPTY_SELECTION_MESSAGE,
    build_file_change_diagnostic_pane,
)

TABLE_ID = "table-data"
FILE_CHANGE_DIAGNOSTIC_PANE_PREFIX = (
    "id-most-committed-file-change-diagnostic-pane"
)
INTENT_FOCUS_OPTIONS = [
    {"label": "All intents", "value": "all"},
    {"label": "Feature", "value": "feat"},
    {"label": "Fix-like", "value": "fix"},
    {"label": "Refactor", "value": "refactor"},
    {"label": "Chore", "value": "chore"},
    {"label": "Test", "value": "test"},
]

register_page(
    module=__name__,
    path="/",
    name="Most Committed",
)

layout = html.Div(
    [
        html.H2("Most Often Committed Files", style={"margin": "10px 0"}),
        html.Div(
            style={
                "display": "flex",
                "gap": "20px",
                "alignItems": "flex-start",
                "flexWrap": "wrap",
            },
            children=[
                html.Div(
                    style={"flex": "1", "minWidth": "420px"},
                    children=[
                        html.H3("Ranked Files", style={"margin": "10px 0"}),
                        dcc.Loading(
                            id="loading-table",
                            type="circle",
                            children=[
                                DataTable(
                                    id=TABLE_ID,
                                    columns=[
                                        {"name": "Commits", "id": "count"},
                                        {"name": "File", "id": "filename"},
                                    ],
                                    style_table={
                                        "maxHeight": "720px",
                                        "overflowY": "auto",
                                    },
                                    style_cell={
                                        "textAlign": "left",
                                        "padding": "4px 8px",
                                        "fontSize": "12px",
                                        "whiteSpace": "normal",
                                        "height": "auto",
                                    },
                                    style_cell_conditional=[
                                        {
                                            "if": {"column_id": "count"},
                                            "width": "34%",
                                        },
                                        {
                                            "if": {"column_id": "filename"},
                                            "width": "66%",
                                        },
                                    ],
                                    style_data_conditional=[],
                                    cell_selectable=True,
                                    data=[],
                                )
                            ],
                        ),
                    ],
                ),
                html.Div(
                    style={"flex": "1", "minWidth": "420px"},
                    children=[
                        html.H3(
                            "File Change Diagnostics",
                            style={"margin": "10px 0"},
                        ),
                        html.P(
                            "Click a row's commit bar or filename to select a file.",
                            style={"margin": "0 0 8px", "color": "#64748b"},
                        ),
                        dcc.Dropdown(
                            id="id-most-committed-intent-focus",
                            options=INTENT_FOCUS_OPTIONS,
                            value="all",
                            clearable=False,
                            style={
                                "maxWidth": "260px",
                                "marginBottom": "10px",
                            },
                        ),
                        html.P(
                            id="id-file-change-diagnostic-status",
                            style={"fontStyle": "italic", "color": "#475569"},
                        ),
                        dcc.Loading(
                            id="loading-file-change-diagnostic",
                            type="circle",
                            children=[
                                html.Div(
                                    id="id-file-change-diagnostic-pane-holder",
                                    children=build_file_change_diagnostic_pane(
                                        payload=None,
                                        component_id_prefix=(
                                            FILE_CHANGE_DIAGNOSTIC_PANE_PREFIX
                                        ),
                                    ),
                                )
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ]
)


@callback(
    Output(TABLE_ID, "data"),
    Input("global-date-range", "data"),
)
def populate_ranked_table(store_data):
    if not store_data or "period" not in store_data:
        raise PreventUpdate

    begin, end = date_utils.parse_date_range_from_store(store_data)
    commits_data = repo_context.commits_in_period(begin, end)
    repo = repo_context.get_repo()
    usages = calculate_file_commit_frequency(
        commits_data,
        repo,
        begin,
        end,
        top_n=20,
    )
    return [
        {
            "filename": str(usage.get("filename", "")),
            "count": int(usage.get("count", 0)),
        }
        for usage in usages
    ]


def populate_graph(store_data):
    """Compatibility wrapper retained for legacy tests/contracts."""
    return populate_ranked_table(store_data)


def _selected_row_index(active_cell, table_data) -> int | None:
    if not active_cell or not table_data:
        return None
    row_index = active_cell.get("row")
    if not isinstance(row_index, int) or row_index < 0:
        return None
    if row_index >= len(table_data):
        return None
    return row_index


def _data_bar_rules(table_data) -> list[dict]:
    counts = [
        int(row.get("count", 0))
        for row in table_data
        if int(row.get("count", 0)) > 0
    ]
    if not counts:
        return []
    max_count = max(counts)
    rules = []
    for row_index, row in enumerate(table_data):
        count = int(row.get("count", 0))
        bar_percent = int(round((count / max_count) * 100)) if max_count else 0
        rules.append(
            {
                "if": {"row_index": row_index, "column_id": "count"},
                "background": (
                    "linear-gradient(90deg, #dbeafe 0%, "
                    f"#dbeafe {bar_percent}%, transparent {bar_percent}%, "
                    "transparent 100%)"
                ),
                "fontWeight": "600",
            }
        )
    return rules


def build_ranked_table_style_data_conditional(
    active_cell,
    table_data,
) -> list[dict]:
    style_rules = _data_bar_rules(table_data)
    selected_row = _selected_row_index(active_cell, table_data)
    if selected_row is not None:
        style_rules.append(
            {
                "if": {"row_index": selected_row},
                "backgroundColor": "#e6f3ff",
                "border": "1px solid #60a5fa",
            }
        )
    return style_rules


@callback(
    Output(TABLE_ID, "style_data_conditional"),
    [
        Input(TABLE_ID, "active_cell"),
        Input(TABLE_ID, "data"),
    ],
)
def populate_ranked_table_styles(active_cell, table_data):
    return build_ranked_table_style_data_conditional(
        active_cell,
        table_data or [],
    )


def _diagnostic_status_text(diagnostic_payload) -> str:
    status = diagnostic_payload.get("status", "")
    status_detail = diagnostic_payload.get("status_detail", "")
    filename = diagnostic_payload.get("filename", "")
    message_count = int(diagnostic_payload.get("message_count", 0))
    filtered_message_count = int(
        diagnostic_payload.get("filtered_message_count", message_count)
    )
    focused_intent = str(diagnostic_payload.get("focused_intent", "all"))

    if status == "ok" and filename:
        if focused_intent and focused_intent != "all":
            return (
                f"{filename}: showing {filtered_message_count} "
                f"{focused_intent} evidence row(s) out of {message_count}."
            )
        return f"{filename}: analyzed {message_count} commit(s)."
    if status_detail and filename:
        return f"{filename}: {status_detail}"
    if status_detail:
        return status_detail
    return "Diagnostics unavailable."


@callback(
    [
        Output("id-file-change-diagnostic-status", "children"),
        Output("id-file-change-diagnostic-pane-holder", "children"),
    ],
    [
        Input(TABLE_ID, "active_cell"),
        Input(TABLE_ID, "data"),
        Input("global-date-range", "data"),
        Input("id-most-committed-intent-focus", "value"),
    ],
)
def populate_selected_file_diagnostic(
    active_cell,
    table_data,
    date_range_data,
    focused_intent,
):
    if not date_range_data or "period" not in date_range_data:
        status_message = "Select a date range to view file diagnostics."
        return (
            status_message,
            build_file_change_diagnostic_pane(
                payload=None,
                component_id_prefix=FILE_CHANGE_DIAGNOSTIC_PANE_PREFIX,
                empty_state_message=status_message,
            ),
        )

    diagnostic_payload = (
        generate_table_selection_file_change_diagnostic_payload(
            active_cell=active_cell,
            table_data=table_data or [],
            date_range_data=date_range_data,
            focused_intent=focused_intent or "all",
            parse_date_range_fn=date_utils.parse_date_range_from_store,
            get_repo_fn=repo_context.get_repo,
            collect_file_commit_evidence_fn=collect_file_commit_evidence,
            classify_commit_messages_fn=classify_commit_messages,
        )
    )

    if diagnostic_payload.get("status") != "ok":
        empty_state_message = (
            diagnostic_payload.get("status_detail", "")
            or EMPTY_SELECTION_MESSAGE
        )
        pane_children = build_file_change_diagnostic_pane(
            payload=None,
            component_id_prefix=FILE_CHANGE_DIAGNOSTIC_PANE_PREFIX,
            empty_state_message=empty_state_message,
        )
        return _diagnostic_status_text(diagnostic_payload), pane_children

    pane_children = build_file_change_diagnostic_pane(
        payload=diagnostic_payload,
        component_id_prefix=FILE_CHANGE_DIAGNOSTIC_PANE_PREFIX,
    )
    return (
        _diagnostic_status_text(diagnostic_payload),
        pane_children,
    )
