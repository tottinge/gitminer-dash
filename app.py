import sys

from dash import html, dcc, Dash, page_container, page_registry, callback, Output, Input

import data
from utils import date_utils

if len(sys.argv) < 2:
    print("Usage: app.py <repo_name>")
    exit(1)

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

app.layout = html.Div([
    # URL for reading query params and Store for session-scoped date range
    dcc.Location(id='url'),
    dcc.Store(id='global-date-range', storage_type='session'),

    html.H1(f"The Git Miner: {data.get_repo_name()}", style={"text-align": "center"}),
    html.Div([
        dcc.Link(page['name'], href=page['path'])
        for page in page_registry.values()
    ], style={
        "display": "flex",
        "justify-content": "space-between"
    }),
    page_container
])


@callback(
    Output('global-date-range', 'data'),
    Input('url', 'search')
)
def hydrate_global_date_range(search: str):
    # Determine period from query or fall back to default
    period = date_utils.parse_period_from_query(search) or date_utils.DEFAULT_PERIOD
    begin, end = date_utils.calculate_date_range(period)
    payload = {"period": period, **date_utils.to_iso_range(begin, end)}
    return payload


if __name__ == '__main__':
    app.run(debug=True)
