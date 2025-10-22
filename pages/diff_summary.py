import doctest
from collections import defaultdict
from datetime import datetime, timedelta

import pandas as pd
import plotly
import plotly.express as px
from dash import register_page, html, dcc, callback, Output, Input

import data
from logging_wrapper import log

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
def get_diffs_in_period(start: datetime, end: datetime) -> pd.DataFrame:
    counts = defaultdict(int)
    for commit in data.commits_in_period(start, end):
        day = commit.committed_datetime.date()
        inserted = commit.stats.total["insertions"]
        deleted = commit.stats.total["deletions"]

        possible_mods = min(inserted, deleted)
        counts[day, "possible mods"] += possible_mods
        counts[day, "net inserts"] += max(inserted - possible_mods, 0)
        counts[day, "net deletes"] += max(deleted - possible_mods, 0)

    source_data = sorted(
        (day, kind, count)
        for ((day, kind), count) in counts.items()
    )
    result = pd.DataFrame(source_data, columns=["date", "kind", "count"])
    return result


@log
def make_figure(diffs_in_period: pd.DataFrame):
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
    Input("id-diff-summary-container", "n_clicks")
)
def update_graph(_):
    today = datetime.today().astimezone()
    ninety_days_ago = today - timedelta(days=90)
    diffs_in_period = get_diffs_in_period(ninety_days_ago, today)
    return make_figure(diffs_in_period)


if __name__ == "__main__":
    import doctest
    doctest.testmod()