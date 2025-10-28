from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
from dash import register_page, html, dcc, callback, Output, Input

import data

register_page(__name__, title="Merge Sizes")

layout = html.Div(
    [
        html.H2("Merge Magnitudes"),
        html.Button(id="merge-refresh-button", children="Refresh"),
        html.Div(id="merge-graph-container"),
    ]
)


# Doing this synchronously here (called in the layout)
# makes startup time very slow.
def prepare_dataframe():
    today = datetime.today().astimezone()
    start_date = today - timedelta(days=30)
    recent_merges = [
        commit for commit in data.commits_in_period(start_date, today)
        if len(commit.parents) > 1
    ]
    columns = [
        "hash",
        "date",
        "comment",
        "lines",
        "files"
    ]
    source = (
        (commit.hexsha,
         commit.committed_datetime.date(),
         commit.message,
         commit.stats.total["lines"],
         commit.stats.total["files"])
        for commit in recent_merges
    )
    result = pd.DataFrame(source, columns=columns).sort_values(by="date")
    return result


@callback(
    Output("merge-graph-container", "children"),
    Input("merge-refresh-button", "n_clicks"),
    running=[(Output("merge-refresh-button", "disabled"), True, False)],
)
def update_merge_graph(n_clicks: int):
    data_frame = prepare_dataframe()
    if data_frame.empty:
        return html.H3("no merges found in the last 30 days")
    bar_chart_figure = px.bar(
        data_frame=data_frame,
        x="date",
        y="lines",
        color="files",
        hover_name="date",
        hover_data=["files", "lines", "comment"]
    )
    return [
        dcc.Loading(
            id="loading-merge-graph",
            type="circle",
            children=[
                dcc.Graph(figure=bar_chart_figure)
            ]
        )
    ]
