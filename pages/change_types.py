from functools import cache

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html, register_page
from dash.dash_table import DataTable
from plotly.graph_objs import Figure

# Note: PyCharm tags these as invalid imports, but we run
# the app from the parent dir and these are okay.
from algorithms.change_series import change_name, change_series
from algorithms.sorted_tags import get_most_recent_tags
from data import get_repo

register_page(
    module=__name__,  # Where it's found
    name="Change Types By Tag",  # Menu item name
)


@cache
def change_series_20day():
    repo = get_repo()
    last_20 = get_most_recent_tags(repo, 20)
    if not last_20:
        return pd.DataFrame(columns=["Name", "Date"])
    # Get the Date, Name, and counters for the most recent commit diffs
    categorized_commits = change_series(start=last_20[0], commit_refs=last_20)
    change_df = pd.DataFrame(categorized_commits)
    return change_df


layout = html.Div(
    [
        html.P(
            id="id-no-data-message", children="No tags found in repository."
        ),
        html.Div(
            id="id-graph-container",
            children=[
                dcc.Loading(
                    id="loading-change-types-graph",
                    type="circle",
                    children=[
                        dcc.Graph(
                            id="id-local_graph", style={"height": "500px"}
                        )
                    ],
                )
            ],
        ),
        html.H3("Source Data", style={"margin": "10px 0"}),
        dcc.Loading(
            id="loading-change-types-table",
            type="circle",
            children=[
                DataTable(
                    id="id-data-table",
                    style_table={"maxHeight": "400px", "overflowY": "auto"},
                )
            ],
        ),
    ]
)

StyleDict = dict[str, str]
style_show: StyleDict = {"display": "block"}
style_hide: StyleDict = {"display": "none"}

ChangeTypeCallbackResult = tuple[
    Figure,  # Graphic to draw
    list,  # same data as a list
    StyleDict,  # graphic container show/hide style
    StyleDict,  # no data show/hide style
]


@callback(
    [
        Output("id-local_graph", "figure"),
        Output("id-data-table", "data"),
        Output("id-graph-container", "style"),
        Output("id-no-data-message", "style"),
    ],
    Input("id-graph-container", "n_clicks"),
)
def update_graph(_) -> ChangeTypeCallbackResult:
    data = change_series_20day()
    if data.empty:
        figure = go.Figure()
        table_data = []
        return figure, table_data, style_hide, style_show
    figure = px.bar(
        data,
        title="Change Types and Magnitudes Across Tags",
        x="Name",
        y=list(change_name.values()),
        labels={
            "Name": "Tag",
            "Files Added": "Added",
            "Files Deleted": "Deleted",
            "Files Renamed": "Renamed",
            "Files Modified": "Modified",
        },
        hover_name="Name",
        hover_data=["Date"],
        text_auto=".2s",
    )
    table_data = data.to_dict("records")
    return figure, table_data, style_show, style_hide
