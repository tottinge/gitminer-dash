import plotly.express as px
from dash import Input, Output, callback, dcc, html, register_page
from dash.dash_table import DataTable
from dash.exceptions import PreventUpdate
from pandas import DataFrame

import repository_context as repo_context
from algorithms.commit_frequency import calculate_file_commit_frequency
from algorithms.commit_message_classifier import classify_commit_messages
from pages.most_committed_service import (
    collect_commit_messages_for_file,
    generate_table_selection_commit_classification_payload,
)
from utils import date_utils
from utils.plotly_utils import create_empty_figure

register_page(
    module=__name__,  # Where it's found
    path="/",  # this is the root page (for now)
    name="Most Committed",  # Menu item name
)

layout = html.Div(
    [
        html.H2("Most Often Committed Files", style={"margin": "10px 0"}),
        html.Div(
            id="id-most-committed-graph-holder",
            style={"display": "none"},
            children=[
                dcc.Loading(
                    id="loading-graph",
                    type="circle",
                    children=[
                        dcc.Graph(id="id-commit-graph", figure={"data": []}),
                    ],
                ),
            ],
        ),
        html.H3("Source Data", style={"margin": "10px 0"}),
        dcc.Loading(
            id="loading-table",
            type="circle",
            children=[
                DataTable(
                    id="table-data",
                    columns=[
                        {"name": "File", "id": "filename"},
                        {"name": "Commits", "id": "count"},
                        {
                            "name": "Avg Lines/Commit",
                            "id": "avg_changes",
                        },
                        {
                            "name": "Change (lines)",
                            "id": "total_change",
                        },
                        {
                            "name": "Change (percent)",
                            "id": "percent_change",
                        },
                    ],
                    style_table={
                        "maxHeight": "600px",
                        "overflowY": "auto",
                    },
                    style_cell_conditional=[
                        {
                            "if": {"column_id": "filename"},
                            "width": "20%",
                            "textAlign": "left",
                        },
                        {
                            "if": {"column_id": "count"},
                            "width": "10%",
                        },
                        {},
                    ],
                )
            ],
        ),
        html.H3(
            "Selected File Commit Message Classification",
            style={"margin": "10px 0"},
        ),
        html.Div(
            id="id-file-commit-classification-holder",
            style={"display": "none"},
            children=[
                dcc.Loading(
                    id="loading-file-commit-classification",
                    type="circle",
                    children=[
                        html.Div(
                            id="id-file-commit-classification-status",
                            style={"marginBottom": "8px"},
                        ),
                        DataTable(
                            id="id-file-commit-intent-counts-table",
                            columns=[
                                {"name": "Intent", "id": "intent"},
                                {"name": "Count", "id": "count"},
                            ],
                            style_table={
                                "maxHeight": "200px",
                                "overflowY": "auto",
                            },
                            style_cell={"textAlign": "left"},
                            data=[],
                        ),
                        html.H4(
                            "Classified Messages",
                            style={"margin": "12px 0 8px 0"},
                        ),
                        DataTable(
                            id="id-file-commit-classifications-table",
                            columns=[
                                {"name": "Intent", "id": "intent"},
                                {"name": "Message", "id": "message"},
                            ],
                            style_table={
                                "maxHeight": "400px",
                                "overflowY": "auto",
                            },
                            style_cell={"textAlign": "left"},
                            style_cell_conditional=[
                                {
                                    "if": {"column_id": "intent"},
                                    "width": "15%",
                                },
                                {
                                    "if": {"column_id": "message"},
                                    "width": "85%",
                                },
                            ],
                            data=[],
                        ),
                    ],
                )
            ],
        ),
    ]
)


@callback(
    [
        Output("id-commit-graph", "figure"),
        Output("table-data", "data"),
        Output("id-most-committed-graph-holder", "style"),
    ],
    Input("global-date-range", "data"),
)
def populate_graph(store_data):
    if not store_data or "period" not in store_data:
        raise PreventUpdate

    # Get file usage data with additional metrics
    begin, end = date_utils.parse_date_range_from_store(store_data)
    commits_data = repo_context.commits_in_period(begin, end)
    repo = repo_context.get_repo()
    usages = calculate_file_commit_frequency(
        commits_data, repo, begin, end, top_n=20
    )

    # Create DataFrame with all metrics (ensure columns even when no data)
    columns = [
        "filename",
        "count",
        "avg_changes",
        "total_change",
        "percent_change",
    ]
    frame = DataFrame(usages if usages else [], columns=columns)

    # Create bar chart using just filename and count
    figure = px.bar(data_frame=frame, x="filename", y="count")
    if frame.empty:
        figure = create_empty_figure("No data in selected period")

    # Convert DataFrame to dict for table display
    table_data = frame.to_dict("records")

    style_show = {"display": "block"}
    return figure, table_data, style_show


def _classification_status_text(classification_payload) -> str:
    status = classification_payload.get("status", "")
    status_detail = classification_payload.get("status_detail", "")
    filename = classification_payload.get("filename", "")
    message_count = classification_payload.get("message_count", 0)

    if status == "ok" and filename:
        return f"{filename}: classified {message_count} commit message(s)."
    if status_detail and filename:
        return f"{filename}: {status_detail}"
    if status_detail:
        return status_detail
    return "Classification unavailable."


@callback(
    [
        Output("id-file-commit-classification-status", "children"),
        Output("id-file-commit-intent-counts-table", "data"),
        Output("id-file-commit-classifications-table", "data"),
        Output("id-file-commit-classification-holder", "style"),
    ],
    [
        Input("table-data", "active_cell"),
        Input("table-data", "data"),
        Input("global-date-range", "data"),
    ],
)
def populate_selected_file_commit_classification(
    active_cell,
    table_data,
    date_range_data,
):
    if not date_range_data or "period" not in date_range_data:
        return (
            "Select a date range to classify commit messages.",
            [],
            [],
            {"display": "none"},
        )

    classification_payload = (
        generate_table_selection_commit_classification_payload(
            active_cell=active_cell,
            table_data=table_data or [],
            date_range_data=date_range_data,
            parse_date_range_fn=date_utils.parse_date_range_from_store,
            get_repo_fn=repo_context.get_repo,
            collect_commit_messages_for_file_fn=(
                collect_commit_messages_for_file
            ),
            classify_commit_messages_fn=classify_commit_messages,
        )
    )
    return (
        _classification_status_text(classification_payload),
        classification_payload["intent_counts"],
        classification_payload["classifications"],
        {"display": "block"},
    )
