from collections import defaultdict

import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html, no_update, register_page
from dash.dash_table import DataTable
from dash.dcc import Slider, Store

import data
from algorithms.affinity_calculator import calculate_affinities
from utils import date_utils
from utils.git import ensure_list
from utils.plotly_utils import create_empty_figure
from visualization.network_graph import (
    create_file_affinity_network,
    create_network_visualization,
)

# Simple in-process cache of affinity maps keyed by date range.
# This avoids recomputing file-pair affinities for the same period when
# sliders change on the affinity-groups page.
_AFFINITY_CACHE: dict[tuple[str, str], dict[tuple[str, str], float]] = {}

register_page(__name__, title="Affinity Groups")

layout = html.Div(
    children=[
        html.H1("File Affinity Groups"),
        html.Div(
            style={
                "display": "flex",
                "justify-content": "space-between",
                "align-items": "center",
                "margin-bottom": "10px",
            },
            children=[
                html.Div(
                    style={"width": "45%"},
                    children=[
                        html.Label("Maximum Number of Nodes:"),
                        Slider(
                            id="id-affinity-node-slider",
                            min=10,
                            max=100,
                            step=10,
                            value=50,
                            marks={i: str(i) for i in range(10, 101, 10)},
                        ),
                    ],
                ),
                html.Div(
                    style={"width": "45%"},
                    children=[
                        html.Label("Minimum Affinity Factor:"),
                        Slider(
                            id="id-affinity-min-slider",
                            min=0.05,
                            max=0.5,
                            step=0.01,
                            value=0.2,
                            marks={i / 100: str(i / 100) for i in range(5, 51, 5)},
                        ),
                    ],
                ),
            ],
        ),
        dcc.Loading(
            id="loading-file-affinity-graph",
            type="circle",
            children=[
                dcc.Graph(id="id-file-affinity-graph", style={"height": "600px"})
            ],
        ),
        html.H3("Group Commits"),
        dcc.Loading(
            id="loading-node-details-table",
            type="circle",
            children=[
                DataTable(
                    id="id-node-details-table",
                    columns=[
                        {"name": "Hash", "id": "hash"},
                        {"name": "Timestamp", "id": "timestamp"},
                        {"name": "Message", "id": "message"},
                        {"name": "Group Files", "id": "group_files"},
                    ],
                    style_cell={"textAlign": "left"},
                    style_cell_conditional=[
                        {"if": {"column_id": "hash"}, "width": "10%"},
                        {"if": {"column_id": "timestamp"}, "width": "15%"},
                        {"if": {"column_id": "message"}, "width": "35%"},
                        {"if": {"column_id": "group_files"}, "width": "40%"},
                    ],
                    style_table={"maxHeight": "400px", "overflowY": "auto"},
                    data=[],
                )
            ],
        ),
        # Hidden store to keep graph data for click handling
        Store(id="id-graph-data-store", data={}),
    ]
)


@callback(
    Output("id-file-affinity-graph", "figure"),
    Output("id-graph-data-store", "data"),
    [
        Input("global-date-range", "data"),
        Input("id-affinity-node-slider", "value"),
        Input("id-affinity-min-slider", "value"),
    ],
)
def update_file_affinity_graph(store_data, max_nodes: int, min_affinity: float):
    try:
        starting, ending = date_utils.parse_date_range_from_store(store_data)
        # Convert commits_data to a list to prevent the iterator from being consumed
        commits_data = ensure_list(data.commits_in_period(starting, ending))

        # Cache affinities per date range so slider changes don't recompute
        cache_key = (starting.isoformat(), ending.isoformat())
        affinities = _AFFINITY_CACHE.get(cache_key)
        if affinities is None:
            affinities = calculate_affinities(commits_data)
            _AFFINITY_CACHE[cache_key] = affinities

        # Note: create_file_affinity_network returns (G, communities, stats)
        G, communities, stats = create_file_affinity_network(
            commits_data,
            min_affinity=min_affinity,
            max_nodes=max_nodes,
            precomputed_affinities=affinities,
        )

        # Store graph data for click handling
        graph_data = {"nodes": {}, "communities": {}}

        for node in G.nodes():
            node_community = G.nodes[node].get("community", 0)
            commit_count = G.nodes[node].get("commit_count", 0)
            degree = G.degree(node)

            # Find connected communities (for bridge detection)
            connected_communities = set()
            for neighbor in G.neighbors(node):
                neighbor_community = G.nodes[neighbor].get("community", 0)
                connected_communities.add(neighbor_community)

            graph_data["nodes"][node] = {
                "commit_count": commit_count,
                "degree": degree,
                "community": node_community,
                "connected_communities": sorted(list(connected_communities)),
            }

        # Store community information
        for i, community in enumerate(communities):
            graph_data["communities"][i] = list(community)

        return create_network_visualization(G, communities), graph_data
    except ValueError as e:
        # Check if this is the specific error about missing repository path
        if "No repository path provided" in str(e):
            # Create a figure with a helpful message about repository path
            fig = create_empty_figure(
                "No repository path provided. Please run the application with a repository path as a command-line argument.\n\nExample: python app.py /path/to/your/git/repository",
                title="File Affinity Network - Repository Path Required",
            )
            return fig, {}
        else:
            # Handle other ValueError exceptions
            fig = create_empty_figure(
                f"Error with input values: {str(e)}",
                title="File Affinity Network - Input Error",
            )
            return fig, {}
    except Exception as e:
        # Create a figure with a general error message
        fig = create_empty_figure(
            f"Error generating affinity graph: {str(e)}",
            title="File Affinity Network - Error",
        )
        return fig, {}


def get_commits_for_group_files(group_files: list[str], starting, ending) -> list[dict]:
    """
    Get commits that contain at least two files from the group.

    Args:
        group_files: List of file paths in the group
        starting: Start date for commit filtering
        ending: End date for commit filtering

    Returns:
        List of dicts with keys: hash, timestamp, message, group_files
    """
    commits_data = []
    group_files_set = set(group_files)

    for commit in data.commits_in_period(starting, ending):
        # Get modified files in this commit
        modified_files = set()
        if commit.parents:
            for item in commit.diff(commit.parents[0]):
                if hasattr(item, "a_path") and item.a_path:
                    modified_files.add(item.a_path)
                if hasattr(item, "b_path") and item.b_path:
                    modified_files.add(item.b_path)

        # Find which group files were modified
        group_files_in_commit = list(group_files_set & modified_files)

        # Only include commits with at least 2 group files
        if len(group_files_in_commit) >= 2:
            commits_data.append(
                {
                    "hash": commit.hexsha[:7],
                    "timestamp": commit.committed_datetime.strftime("%Y-%m-%d %H:%M"),
                    "message": commit.message.split("\n")[0][
                        :100
                    ],  # First line, truncated
                    "group_files": ", ".join(sorted(group_files_in_commit)),
                }
            )

    # Sort by timestamp (most recent first)
    commits_data.sort(key=lambda x: x["timestamp"], reverse=True)

    return commits_data


@callback(
    Output("id-node-details-table", "data"),
    [Input("id-file-affinity-graph", "clickData")],
    [State("id-graph-data-store", "data"), State("global-date-range", "data")],
)
def update_node_details_table(click_data, graph_data, date_range_data):
    """
    Handle node clicks and populate the table with commits containing multiple files from the group.

    Args:
        click_data: Click event data from the graph
        graph_data: Stored graph structure data
        date_range_data: Date range from global store

    Returns:
        List of dicts for the DataTable containing commits with group files
    """
    if not click_data or not graph_data or "nodes" not in graph_data:
        return []

    # Extract the clicked node name
    point = click_data.get("points", [{}])[0]
    node_name = point.get("text", "")

    # Parse the tooltip text to get the actual file name
    # Tooltip format: "File: {node}<br>Commits: {commit_count}<br>Connections: {degree}"
    if "<br>" in node_name:
        node_name = node_name.split("<br>")[0].replace("File: ", "")

    if not node_name or node_name not in graph_data["nodes"]:
        return []

    # Get the clicked node's community
    clicked_node_data = graph_data["nodes"][node_name]
    node_community = clicked_node_data.get("community", 0)

    # Find all files in the same community
    group_files = [
        node
        for node, node_info in graph_data["nodes"].items()
        if node_info.get("community", -1) == node_community
    ]

    # Get date range
    starting, ending = date_utils.parse_date_range_from_store(date_range_data)

    # Get commits for these files
    return get_commits_for_group_files(group_files, starting, ending)
