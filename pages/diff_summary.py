from datetime import datetime, timedelta

import plotly
import plotly.express as px
from dash import register_page, html, dcc, callback, Output, Input

import data
from algorithms.diff_analysis import get_diffs_in_period
from utils.logging_wrapper import log
from utils import date_utils

register_page(
    module=__name__,  # Where it's found
    name="Diff Summary",  # Menu item name
)

layout = html.Div(
    [
        html.H2("Diff Summary", style={"margin": "10px 0"}),
        html.Div(
            id="id-diff-summary-container",
            children=[
                dcc.Loading(
                    id="loading-diff-summary-graph",
                    type="circle",
                    children=[
                        dcc.Graph(
                            id="diff-summary-graph",
                            figure={"data": []},
                            style={"height": "500px"},
                        ),
                    ],
                ),
            ],
        ),
    ]
)


@log
def make_figure(diffs_in_period):
    bar_chart = px.bar(
        data_frame=diffs_in_period,
        x="date",
        y="count",
        color="kind",
        color_discrete_sequence=plotly.colors.qualitative.Pastel,
    )
    return bar_chart


@callback(
    Output("diff-summary-graph", "figure"),
    Input("id-diff-summary-container", "n_clicks"),
    Input("global-date-range", "data"),
)
def update_graph(_, store_data):
    start, end = date_utils.parse_date_range_from_store(store_data)
    commits_data = data.commits_in_period(start, end)
    diffs_in_period = get_diffs_in_period(commits_data, start, end)
    return make_figure(diffs_in_period)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
