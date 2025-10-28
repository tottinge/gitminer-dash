import plotly.express as px
from dash import html, register_page, dcc, callback, Output, Input
from dash.dash_table import DataTable
from dash.exceptions import PreventUpdate
from pandas import DataFrame

import data
from utils import date_utils
from algorithms.commit_frequency import calculate_file_commit_frequency

register_page(
    module=__name__,  # Where it's found
    path="/",  # this is the root page (for now)
    name="Most Committed",  # Menu item name
)

layout = html.Div(
    [
        html.H2("Most Often Committed Files"),
        html.Div(
            id='id-most-committed-graph-holder',
            style={"display": "none"},
            children=[
                dcc.Loading(
                    id="loading-graph",
                    type="circle",
                    children=[
                        dcc.Graph(id='id-commit-graph', figure={"data": []}),
                    ]
                ),
            ]
        ),
        html.Hr(),
        html.H2("Source Data"),
        dcc.Loading(
            id="loading-table",
            type="circle",
            children=[
                DataTable(
                    id='table-data',
                    columns = [
                        {"name":"File", "id":"filename"},
                        {"name":"Commits", "id":"count"},
                        {"name":"Avg Lines/Commit", "id":"avg_changes"},
                        {"name":"Change (lines)", "id":"total_change"},
                        {"name":"Change (percent)", "id":"percent_change"},
                    ],
                    style_cell_conditional=[
                        {
                            'if': {'column_id': 'filename'},
                            'width': '20%',
                            'textAlign': 'left'
                        },
                        {
                            'if': {'column_id': 'count'},
                            'width': '10%'
                        },
                        {}]
                )
            ]
        )
    ]
)



@callback(
    [
        Output('id-commit-graph', 'figure'),
        Output('table-data', 'data'),
        Output('id-most-committed-graph-holder', 'style')
    ],
    Input('global-date-range', 'data')
)
def populate_graph(store_data):
    if not store_data or 'period' not in store_data:
        raise PreventUpdate

    # Get file usage data with additional metrics
    period_input = store_data['period']
    if 'begin' in store_data and 'end' in store_data:
        from datetime import datetime as _dt
        begin = _dt.fromisoformat(store_data['begin'])
        end = _dt.fromisoformat(store_data['end'])
    else:
        begin, end = date_utils.calculate_date_range(period_input)
    commits_data = data.commits_in_period(begin, end)
    repo = data.get_repo()
    usages = calculate_file_commit_frequency(commits_data, repo, begin, end, top_n=20)

    # Create DataFrame with all metrics
    frame = DataFrame(data=usages)

    # Create bar chart using just filename and count
    figure = px.bar(data_frame=frame, x='filename', y='count')

    # Convert DataFrame to dict for table display
    table_data = frame.to_dict('records')

    style_show = {"display": "block"}
    return figure, table_data, style_show


