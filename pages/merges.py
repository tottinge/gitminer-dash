import pandas as pd
import plotly.express as px
from dash import Input, Output, callback, dcc, html, register_page

import data
from utils import date_utils

register_page(__name__, title="Merge Sizes")

layout = html.Div(
    [
        html.H2("Merge Magnitudes", style={"margin": "10px 0"}),
        html.Button(id="merge-refresh-button", children="Refresh"),
        html.Div(id="merge-graph-container"),
    ]
)


# Doing this synchronously here (called in the layout)
# makes startup time very slow.
def prepare_dataframe(start_date, end_date):
    recent_merges = [
        commit
        for commit in data.commits_in_period(start_date, end_date)
        if len(commit.parents) > 1
    ]
    columns = ["hash", "date", "comment", "lines", "files"]
    source = (
        (
            commit.hexsha,
            commit.committed_datetime.date(),
            commit.message,
            commit.stats.total["lines"],
            commit.stats.total["files"],
        )
        for commit in recent_merges
    )
    result = pd.DataFrame(source, columns=columns).sort_values(by="date")
    return result


@callback(
    Output("merge-graph-container", "children"),
    Input("merge-refresh-button", "n_clicks"),
    Input("global-date-range", "data"),
    running=[(Output("merge-refresh-button", "disabled"), True, False)],
)
def update_merge_graph(n_clicks: int, store_data):
    start_date, end_date = date_utils.parse_date_range_from_store(store_data)
    data_frame = prepare_dataframe(start_date, end_date)
    if data_frame.empty:
        return html.H3("no merges found in the selected period")
    bar_chart_figure = px.bar(
        data_frame=data_frame,
        x="date",
        y="lines",
        color="files",
        hover_name="date",
        hover_data=["files", "lines", "comment"],
    )

    # Set x-axis range to span the full requested period
    bar_chart_figure.update_xaxes(range=[start_date.date(), end_date.date()])

    return [
        dcc.Loading(
            id="loading-merge-graph",
            type="circle",
            children=[dcc.Graph(figure=bar_chart_figure, style={"height": "500px"})],
        )
    ]
