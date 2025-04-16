from functools import cache

import pandas as pd
import plotly.express as px
from dash import html, dcc, register_page, callback, Output, Input
from dash.dash_table import DataTable

# Note: PyCharm tags these as invalid imports, but we run
# the app from the parent dir and these are okay.
from algorithms.change_series import change_series, change_name
from algorithms.sorted_tags import get_most_recent_tags
from data import get_repo

register_page(
    module=__name__,  # Where it's found
    name="Change Types By Tag",  # Menu item name
)


@cache
def prepared_data_frame():
    repo = get_repo()
    last_20 = get_most_recent_tags(repo, 20)
    if not last_20:
        return pd.DataFrame(columns=['Name', 'Date'])
    # Get the Date, Name, and counters for the most recent commit diffs
    categorized_commits = change_series(start=last_20[0], commit_refs=last_20)
    change_df = pd.DataFrame(categorized_commits)
    return change_df


layout = html.Div(
    [
        html.P(
            id="id-no-data-message",
            children="No tags found in repository."
        ),
        html.Div(id="id-graph-container",
                 children=[dcc.Graph(id="id-local_graph")]
                 ),
        html.Hr(),
        html.H2("Source Data"),
        DataTable(id="id-data-table"),
    ]
)


@callback(
    [
        Output("id-local_graph", "figure"),
        Output("id-data-table", "data"),
        Output("id-graph-container", "style"),
        Output("id-no-data-message", "style")
    ],
    Input("id-graph-container", "n_clicks")
)
def update_graph(_):
    style_show = {"display": "block"}
    style_hide = {"display": "none"}
    data = prepared_data_frame()
    if data.empty:
        figure = {"data": []}
        table_data = []
        return figure, table_data, style_hide, style_show
    figure = px.bar(
        data,
        title="Change Types and Magnitudes Across Tags",
        x="Name",
        y=list(change_name.values()),
        labels=["Added", "Deleted", "Modified", "Removed"],
        hover_name="Name",
        hover_data=["Date"],
        text_auto='.2s'
    )
    table_data = data.to_dict('records')
    return figure, table_data, style_show, style_hide
