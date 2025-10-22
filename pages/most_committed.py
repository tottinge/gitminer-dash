from collections import Counter
from datetime import datetime, timedelta

import plotly.express as px
from dash import html, register_page, dcc, callback, Output, Input
from dash.dash_table import DataTable
from dash.exceptions import PreventUpdate
from pandas import DataFrame

import data

register_page(
    module=__name__,  # Where it's found
    path="/",  # this is the root page (for now)
    name="Most Committed",  # Menu item name
)

layout = html.Div(
    [
        html.H2("Most Often Committed Files"),
        html.Div(
            style={"align-items": "center", "display": "flex"},
            children=[
                html.Label(children=["Period:"],
                           htmlFor="id-period-dropdown",
                           style={"display": "inline-block"}),
                dcc.Dropdown(id='id-period-dropdown',
                             options=[
                                 'Last 30 days',
                                 'Last 60 days',
                                 'Last 90 days',
                                 'Last 1 Year',
                                 'Ever'
                             ],
                             value='Last 30 days',
                             style={
                                 "display": "inline-block",
                                 "width": "100%",
                             }),
            ]
        ),

        # html.Div(id='page-content', children=[]),
        html.Div(
            id='id-most-committed-graph-holder',
            style={"display": "none"},
            children=[
                dcc.Graph(id='id-commit-graph', figure={"data": []}),
            ]
        ),

        html.Hr(),
        html.H2("Source Data"),
        DataTable(id='table-data')
    ]

)


def calculate_usages(period: str):
    end = datetime.today().astimezone()
    period = period or "30 days"
    match period.lower():
        case p if "30" in p:
            begin = end - timedelta(days=30)
        case p if "60" in p:
            begin = end - timedelta(days=60)
        case p if "90" in p:
            begin = end - timedelta(days=90)
        case p if "1 year" in p:
            begin = end - timedelta(years=1)
        case _:
            begin = datetime(1970, 1, 1, tzinfo=end.tzinfo)

    counter = Counter()
    all_commits = list(data.commits_in_period(begin, end))
    for commit in all_commits:
        try:
            files = commit.stats.files.keys()
            counter.update(files)
        except ValueError as e:
            print("Stop me if you've seen this one before")
            raise e
    return counter.most_common(20)


@callback(
    [
        Output('id-commit-graph', 'figure'),
        Output('table-data', 'data'),
        Output('id-most-committed-graph-holder', 'style')
    ],
    Input('id-period-dropdown', 'value'),
    running=(Output('id-period-dropdown', 'disabled'), True, False)
)
def populate_graph(period_input):
    if not period_input:
        raise PreventUpdate
    usages = calculate_usages(period_input)
    frame = DataFrame(data=usages, columns=['filename', 'count'])
    figure = px.bar(data_frame=frame, x='filename', y='count')

    frame = DataFrame(data=usages, columns=['filename', 'count'])
    table_data = frame.to_dict('records')

    style_show = {"display": "block"}
    return figure, table_data, style_show
