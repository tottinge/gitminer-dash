import plotly.express as px
from dash import Input, Output, State, callback, dcc, html, register_page
from dash.dash_table import DataTable
from dash.exceptions import PreventUpdate
from pandas import DataFrame

import data
from algorithms.commit_frequency import calculate_file_commit_frequency
from algorithms.word_frequency import calculate_word_frequency
from utils import date_utils
from utils.git import get_commit_messages_for_file
from utils.plotly_utils import create_empty_figure
from visualization.word_frequency import create_word_frequency_treemap

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
        html.Div(
            style={
                "display": "flex",
                "gap": "20px",
                "alignItems": "flex-start",
            },
            children=[
                # Left side: Table
                html.Div(
                    style={"flex": "1", "minWidth": "0"},
                    children=[
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
                                        {"if": {"column_id": "count"}, "width": "10%"},
                                        {},
                                    ],
                                )
                            ],
                        ),
                    ],
                ),
                # Right side: Word frequency
                html.Div(
                    style={"flex": "0 0 400px", "minWidth": "400px"},
                    children=[
                        html.H3(
                            "Commit Message Word Frequency", style={"margin": "10px 0"}
                        ),
                        dcc.Loading(
                            id="loading-word-frequency",
                            type="circle",
                            children=[
                                dcc.Graph(
                                    id="id-word-frequency-graph",
                                    figure=create_empty_figure(
                                        "Click on a file in the table to view word frequency"
                                    ),
                                    style={"height": "600px"},
                                ),
                            ],
                        ),
                    ],
                ),
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
    commits_data = data.commits_in_period(begin, end)
    repo = data.get_repo()
    usages = calculate_file_commit_frequency(commits_data, repo, begin, end, top_n=20)

    # Create DataFrame with all metrics (ensure columns even when no data)
    columns = ["filename", "count", "avg_changes", "total_change", "percent_change"]
    frame = DataFrame(usages if usages else [], columns=columns)

    # Create bar chart using just filename and count
    figure = px.bar(data_frame=frame, x="filename", y="count")
    if frame.empty:
        figure = create_empty_figure("No data in selected period")

    # Convert DataFrame to dict for table display
    table_data = frame.to_dict("records")

    style_show = {"display": "block"}
    return figure, table_data, style_show


@callback(
    Output("id-word-frequency-graph", "figure"),
    [
        Input("table-data", "active_cell"),
        Input("global-date-range", "data"),
    ],
    State("table-data", "data"),
)
def update_word_frequency(active_cell, store_data, table_data):
    """Update word frequency visualization when a file is clicked."""
    if not active_cell or not table_data or not store_data:
        return create_empty_figure(
            "Click on a file in the table to view word frequency"
        )

    # Get selected filename
    row_index = active_cell["row"]
    if row_index >= len(table_data):
        return create_empty_figure("Invalid selection")

    filename = table_data[row_index]["filename"]

    # Get date range
    begin, end = date_utils.parse_date_range_from_store(store_data)

    # Get commit messages for the file
    repo = data.get_repo()
    messages = list(get_commit_messages_for_file(repo, filename, begin, end))

    if not messages:
        return create_empty_figure(f"No commit messages found for {filename}")

    # Calculate word frequency
    word_counts = calculate_word_frequency(messages)

    # Create visualization
    return create_word_frequency_treemap(
        word_counts,
        title=f"Word Frequency for {filename} ({len(messages)} commits)",
        top_n=30,
    )
