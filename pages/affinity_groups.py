from dash import Input, Output, State, callback, dcc, html, register_page
from dash.dash_table import DataTable
from dash.dcc import Slider, Store

import data
from algorithms.affinity_calculator import calculate_affinities
from algorithms.commit_filter import get_commits_for_group_files
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


def _get_cached_affinities(starting, ending, commits_data):
    """Get or compute affinities for date range."""
    cache_key = (starting.isoformat(), ending.isoformat())
    affinities = _AFFINITY_CACHE.get(cache_key)
    if affinities is None:
        affinities = calculate_affinities(commits_data)
        _AFFINITY_CACHE[cache_key] = affinities
    return affinities


def _build_graph_data_store(G, communities):
    """Transform graph into serializable store format."""
    graph_data = {"nodes": {}, "communities": {}}

    for node in G.nodes():
        node_community = G.nodes[node].get("community", 0)
        commit_count = G.nodes[node].get("commit_count", 0)
        degree = G.degree(node)

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

    for i, community in enumerate(communities):
        graph_data["communities"][i] = list(community)

    return graph_data


def _create_repo_error_figure():
    """Create figure for missing repository path."""
    return create_empty_figure(
        "No repository path provided. Please run the application with a repository path as a command-line argument.\n\nExample: python app.py /path/to/your/git/repository",
        title="File Affinity Network - Repository Path Required",
    )


def _create_error_figure(context: str, error_msg: str):
    """Create figure for general errors."""
    return create_empty_figure(
        f"{context}: {error_msg}", title="File Affinity Network - Error"
    )


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
                            marks={
                                i / 100: str(i / 100) for i in range(5, 51, 5)
                            },
                        ),
                    ],
                ),
            ],
        ),
        dcc.Loading(
            id="loading-file-affinity-graph",
            type="circle",
            children=[
                dcc.Graph(
                    id="id-file-affinity-graph", style={"height": "600px"}
                )
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
    except ValueError as e:
        return _create_error_figure("Invalid date range", str(e)), {}

    try:
        commits_data = ensure_list(data.commits_in_period(starting, ending))
    except ValueError as e:
        if "No repository path provided" in str(e):
            return _create_repo_error_figure(), {}
        raise

    affinities = _get_cached_affinities(starting, ending, commits_data)

    try:
        G, communities, stats = create_file_affinity_network(
            commits_data,
            min_affinity=min_affinity,
            max_nodes=max_nodes,
            precomputed_affinities=affinities,
        )
    except Exception as e:
        return _create_error_figure("Graph generation failed", str(e)), {}

    graph_data = _build_graph_data_store(G, communities)
    figure = create_network_visualization(G, communities)

    return figure, graph_data


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
    commits_in_period = data.commits_in_period(starting, ending)
    return get_commits_for_group_files(commits_in_period, group_files)
