from dash import html, register_page, callback, Output, Input, dcc

from data import commits_in_period
from algorithms.commit_graph import build_commit_graph
from algorithms.chain_analyzer import analyze_commit_chains
from algorithms.chain_clamper import clamp_chains_to_period
from algorithms.chain_layout import calculate_chain_layout
from algorithms.dataframe_builder import create_timeline_dataframe
from algorithms.figure_builder import create_timeline_figure
from utils import date_utils

register_page(module=__name__, title="Concurrent Efforts")

layout = html.Div(
    [
        html.H2("Concurrent Effort", style={"margin": "10px 0"}),
        html.Button(id="code-lines-refresh-button", children=["Refresh"]),
        html.Div(
            id="id-code-lines-container",
            style={"display": "none"},
            children=[
                dcc.Loading(
                    id="loading-code-lines-graph",
                    type="circle",
                    children=[
                        dcc.Graph(
                            id="code-lines-graph",
                            figure={"data": []},
                            style={"height": "500px"},
                        ),
                    ],
                ),
            ],
        ),
    ]
)


@callback(
    [Output("code-lines-graph", "figure"), Output("id-code-lines-container", "style")],
    Input("code-lines-refresh-button", "n_clicks"),
    Input("global-date-range", "data"),
    running=[(Output("code-lines-refresh-button", "disabled"), True, False)],
)
def update_code_lines_graph(_: int, store_data):
    show = {"display": "block"}

    # Determine range from global store
    start_date, end_date = date_utils.parse_date_range_from_store(store_data)

    # Build commit graph
    commits = commits_in_period(start_date, end_date)
    graph = build_commit_graph(commits)

    # Analyze chains
    chains = analyze_commit_chains(graph)

    # Clamp chains to the selected period
    clamped_chains = clamp_chains_to_period(chains, start_date, end_date)

    # Calculate layout for timeline visualization
    timeline_rows = calculate_chain_layout(clamped_chains)

    # Create DataFrame with proper datetime types
    df = create_timeline_dataframe(timeline_rows)
    
    # Create timeline figure
    figure = create_timeline_figure(df)
    
    return figure, show
