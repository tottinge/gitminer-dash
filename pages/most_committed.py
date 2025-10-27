from collections import Counter

import plotly.express as px
from dash import html, register_page, dcc, callback, Output, Input
from dash.dash_table import DataTable
from dash.exceptions import PreventUpdate
from pandas import DataFrame

import data
import date_utils
from algorithms.file_changes import files_changes_over_period

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
                             options=date_utils.PERIOD_OPTIONS,
                             value=date_utils.PERIOD_OPTIONS[1],  # 'Last 30 days'
                             style={
                                 "display": "inline-block",
                                 "width": "100%",
                             }),
            ]
        ),
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
                #                 'filename': filename,
                #                 'count': count,
                #                 'avg_changes': 0.0,
                #                 'total_change': 0,
                #                 'percent_change': 0.0
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

def calculate_usages(period: str):
    # Use the shared date_utils module to calculate begin and end dates
    begin, end = date_utils.calculate_date_range(period)

    # Count file occurrences using Counter
    counter = Counter()
    for commit in data.commits_in_period(begin, end):
        try:
            files = commit.stats.files.keys()
            counter.update(files)
        except ValueError as e:
            print("Stop me if you've seen this one before")
            raise e

    # Get the 20 most common files
    most_common_files = counter.most_common(20)

    # Extract just the filenames
    filenames = [filename for filename, _ in most_common_files]

    # Get additional metrics for these files
    repo = data.get_repo()
    file_stats = files_changes_over_period(filenames, begin, end, repo)

    # Create a list of dictionaries with all metrics
    result = []
    for filename, count in most_common_files:
        if filename in file_stats:
            stats = file_stats[filename]
            result.append({
                'filename': filename,
                'count': count,
                'avg_changes': round(stats.avg_changes, 2),
                'total_change': stats.total_change,
                'percent_change': round(stats.percent_change, 2)
            })
        else:
            # If no stats available, use zeros for the additional metrics
            result.append({
                'filename': filename,
                'count': count,
                'avg_changes': 0.0,
                'total_change': 0,
                'percent_change': 0.0
            })

    return result


@callback(
    [
        Output('id-commit-graph', 'figure'),
        Output('table-data', 'data'),
        Output('id-most-committed-graph-holder', 'style')
    ],
    Input('id-period-dropdown', 'value'),
    running=[(Output('id-period-dropdown', 'disabled'), True, False)]
)
def populate_graph(period_input):
    if not period_input:
        raise PreventUpdate

    # Get file usage data with additional metrics
    usages = calculate_usages(period_input)

    # Create DataFrame with all metrics
    frame = DataFrame(data=usages)

    # Create bar chart using just filename and count
    figure = px.bar(data_frame=frame, x='filename', y='count')

    # Convert DataFrame to dict for table display
    table_data = frame.to_dict('records')

    style_show = {"display": "block"}
    return figure, table_data, style_show
