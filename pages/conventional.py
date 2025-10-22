import re
from collections import Counter
from datetime import datetime, timedelta

import plotly.express as px
from dash import html, register_page, callback, Output, Input, dcc
from dash.dash_table import DataTable
from dash.dcc import Graph
from pandas import DataFrame

import data

register_page(__name__)

color_choices = {
    "feat": "rgb(141,211,199)",
    "ci": "rgb(255,255,179)",
    "fix": "rgb(251,128,114)",
    "chore": "rgb(190,186,218)",
    "build": "rgb(128,177,211)",
    "docs": "rgb(253,180,98)",
    "test": "rgb(179,222,105)",
    "refactor": "rgb(252,205,229)",
    "unknown": "rgb(188,128,189)",
}

layout = html.Div(
    [
        html.H2(
            id="id-conventional-h2",
            children="Change Type by Conventional Commit Messages"
        ),
        html.Button(
            id="id-conventional-refresh-button",
            children="Refresh"
        ),
        dcc.Loading(
            id="loading-conventional-graph",
            type="circle",
            children=[
                Graph(id="id-conventional-graph"),
            ]
        ),
        dcc.Loading(
            id="loading-conventional-table",
            type="circle",
            children=[
                DataTable(
                    id="id-conventional-table",
                    columns=[{"name": i, "id": i} for i in ["date", "message"]],
                    style_cell={'textAlign': 'left'},
                    data=[]
                ),
            ]
        ),
    ]
)


@callback(
    Output("id-conventional-graph", "figure"),
    Input("id-conventional-refresh-button", "n_clicks"),
)
def update_conventional_table(_):
    dataframe = prepare_changes_by_date()
    return make_figure(dataframe)  # , make_summary_figure(dataframe))


@callback(
    Output("id-conventional-table", "data"),
    Input("id-conventional-graph", "clickData"),
    prevent_initial_call=True
)
def handle_click_on_conventional_graph(click_data):
    if not click_data:
        return [dict(date=datetime.now(), message="No data at thsi time")]
    date_label = click_data["points"][0]['label']

    start = datetime.strptime(date_label, "%Y-%m-%d").astimezone()
    end = start + timedelta(hours=23, minutes=59, seconds=59)
    result_data = [
        dict(
            date=commit.committed_datetime.strftime('%b %d %H:%M'),
            message=commit.message
        )
        for commit in data.commits_in_period(start, end)
    ]
    return result_data


conventional_commit_match_pattern = re.compile(r'^(\w+)[!(:]')

categories = {"build", "chore", "ci", "docs", "feat", "fix", "merge", "perf", "refactor", "revert", "style", "test"}


def normalize_intent(intent: str):
    lower = intent.lower()
    if lower in categories:
        return lower
    for name in categories:
        if lower in name or name in lower:
            return name
    return "unknown"


def prepare_changes_by_date(weeks=12) -> DataFrame:
    today = datetime.today().astimezone()
    start = today - timedelta(weeks=weeks)

    daily_change_counter = Counter()
    for commit in data.commits_in_period(start, today):
        match = conventional_commit_match_pattern.match(commit.message)
        if match:
            intent = normalize_intent(match.group(1))
            daily_change_counter[(commit.committed_datetime.date(), intent)] += 1

    dataset = sorted(
        (date, intent, count)
        for ((date, intent), count) in daily_change_counter.items()
    )
    return DataFrame(dataset, columns=["date", "reason", "count"])


def make_figure(df: DataFrame):
    """
    we're not using this yet, but will when we have the data working
    as we want it.
    """
    return px.bar(
        df,
        height=500,
        x="date",
        y="count",
        color="reason",
        color_discrete_map=color_choices
    )
