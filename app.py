import sys

from dash import html, dcc, Dash, page_container, page_registry, callback, Output, Input

import data
from utils import date_utils

if len(sys.argv) < 2:
    print("Usage: app.py <repo_name>")
    exit(1)

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

app.layout = html.Div(
    [
        # Memory-scoped date range store (cleared on page refresh)
        dcc.Store(id="global-date-range", storage_type="memory"),
        html.H1(
            f"The Git Miner: {data.get_repo_name()}",
            style={"text-align": "center", "margin": "10px 0"},
        ),
        # Global period selector
        html.Div(
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "10px",
                "margin": "5px 0",
            },
            children=[
                html.Label("Period:"),
                dcc.Dropdown(
                    id="global-period-dropdown",
                    options=date_utils.PERIOD_OPTIONS,
                    value=date_utils.DEFAULT_PERIOD,
                    style={"minWidth": "240px"},
                ),
            ],
        ),
        # Navigation
        html.Div(
            [
                dcc.Link(page["name"], href=page["path"])
                for page in page_registry.values()
            ],
            style={
                "display": "flex",
                "justify-content": "space-between",
                "margin": "5px 0",
            },
        ),
        page_container,
    ]
)


# Compute store from dropdown only (no URL syncing)
@callback(Output("global-date-range", "data"), Input("global-period-dropdown", "value"))
def compute_store(period_label: str):
    period = period_label or date_utils.DEFAULT_PERIOD
    begin, end = date_utils.calculate_date_range(period)
    payload = {"period": period, **date_utils.to_iso_range(begin, end)}
    return payload


if __name__ == "__main__":
    import os
    # Disable debug mode when running under coverage to avoid reloader issues
    debug_mode = os.environ.get("COVERAGE_RUN") != "true"
    app.run(debug=debug_mode)
