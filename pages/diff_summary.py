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
        html.H2("Diff Summary"),
        html.Div(
            id="id-diff-summary-container",
            children=[
                html.P("This page shows summed net changes for a given day."),
                dcc.Loading(
                    id="loading-diff-summary-graph",
                    type="circle",
                    children=[
                        dcc.Graph(id="diff-summary-graph", figure={"data": []}),
                    ]
                ),
            ]
        ),
        html.P(id="id-diff-summary-description", children=[
            "This is a tad sketchy, but here is the idea: we assume if 100 lines were inserted and 100 deleted,"
            "then it is likely that all those lines were replacements -- all were modified. The leftover are "
            "net additions or net deletions, and we report them as such"
        ]),
        html.P("This must be taken with a grain of salt, as it can be misleading.")
    ]
)




@log
def make_figure(diffs_in_period):
    bar_chart = px.bar(
        data_frame=diffs_in_period,
        x="date",
        y="count",
        color="kind",
        color_discrete_sequence=plotly.colors.qualitative.Pastel
    )
    return bar_chart


@callback(
    Output("diff-summary-graph", "figure"),
    Input("id-diff-summary-container", "n_clicks"),
    Input("global-date-range", "data"),
)
def update_graph(_, store_data):
    if isinstance(store_data, dict):
        period = store_data.get('period', date_utils.DEFAULT_PERIOD)
    else:
        period = date_utils.DEFAULT_PERIOD
    ninety_days_ago, today = date_utils.calculate_date_range(period)
    commits_data = data.commits_in_period(ninety_days_ago, today)
    diffs_in_period = get_diffs_in_period(commits_data, ninety_days_ago, today)
    return make_figure(diffs_in_period)


if __name__ == "__main__":
    import doctest
    doctest.testmod()