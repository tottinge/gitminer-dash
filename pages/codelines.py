from dash import Input, Output, callback, dcc, html, register_page
from dash.dash_table import DataTable

import repository_context as repo_context
from algorithms.branch_resolution import branch_for_commit
from algorithms.chain_analyzer import analyze_commit_chains
from algorithms.chain_clamper import clamp_chains_to_period
from algorithms.chain_layout import calculate_chain_layout
from algorithms.chain_traversal import (
    commits_to_chain_rows,
    traverse_linear_chain,
)
from algorithms.commit_graph import build_commit_graph
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
                html.H3("Chain Commits", style={"margin": "20px 0 10px 0"}),
                dcc.Loading(
                    id="loading-chain-commits-table",
                    type="circle",
                    children=[
                        DataTable(
                            id="id-chain-commits-table",
                            columns=[
                                {"name": "Hash", "id": "hash"},
                                {"name": "Date", "id": "date"},
                                {"name": "Branch", "id": "branch"},
                                {"name": "Author", "id": "author"},
                                {"name": "Message", "id": "message"},
                            ],
                            style_table={
                                "maxHeight": "400px",
                                "overflowY": "auto",
                            },
                            style_cell={
                                "textAlign": "left",
                                "padding": "3px 8px",
                                "whiteSpace": "normal",
                            },
                            data=[],
                        )
                    ],
                ),
            ],
        ),
    ]
)


@callback(
    [
        Output("code-lines-graph", "figure"),
        Output("id-code-lines-container", "style"),
    ],
    Input("code-lines-refresh-button", "n_clicks"),
    Input("global-date-range", "data"),
    running=[(Output("code-lines-refresh-button", "disabled"), True, False)],
)
def update_code_lines_graph(_: int, store_data):
    show = {"display": "block"}

    # Determine range from global store
    start_date, end_date = date_utils.parse_date_range_from_store(store_data)

    # Build commit graph
    commits = repo_context.commits_in_period(start_date, end_date)
    graph = build_commit_graph(commits)

    # Analyze chains
    chains = analyze_commit_chains(graph)

    # Clamp chains to the selected period
    clamped_chains = clamp_chains_to_period(chains, start_date, end_date)

    # Calculate layout for timeline visualization
    timeline_rows = calculate_chain_layout(clamped_chains)

    # Create DataFrame with proper datetime types
    df = create_timeline_dataframe(timeline_rows)

    # Create timeline figure (includes head/tail in custom_data for selection)
    figure = create_timeline_figure(df)

    return figure, show


@callback(
    Output("id-chain-commits-table", "data"),
    Input("code-lines-graph", "clickData"),
)
def update_chain_commits_table(click_data):
    """Populate the chain commits table when a timeline bar is clicked.

    The timeline figure attaches the earliest (head) and latest (tail)
    commit SHAs for each chain as Plotly ``custom_data``. When a bar is
    clicked, we recover those SHAs, traverse the linear chain in git, and
    format the commits for tabular display.
    """
    if not click_data or "points" not in click_data or not click_data["points"]:
        return []

    point = click_data["points"][0]
    custom_data = point.get("customdata") or []
    if len(custom_data) < 2:
        # If we don't have both head and tail SHAs, we cannot build the chain.
        return []

    earliest_sha = custom_data[0]
    latest_sha = custom_data[1]

    # Resolve commits from the repository and traverse the linear chain.
    repo = repo_context.get_repo()
    latest_commit = repo.commit(latest_sha)
    chain_commits = traverse_linear_chain(latest_commit, earliest_sha)

    # Format for DataTable consumption, including branch column.
    return commits_to_chain_rows(chain_commits, branch_getter=branch_for_commit)
