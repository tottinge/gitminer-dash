"""Service helpers for the affinity groups page."""

from __future__ import annotations

from typing import Any

import networkx as nx
import plotly.graph_objects as go


def get_or_compute_affinities(
    cache: dict[tuple[str, str], dict[tuple[str, str], float]],
    starting,
    ending,
    commits_data,
    calculate_affinities_fn,
) -> dict[tuple[str, str], float]:
    """Get affinities from cache or compute and cache them."""
    cache_key = (starting.isoformat(), ending.isoformat())
    affinities = cache.get(cache_key)
    if affinities is None:
        affinities = calculate_affinities_fn(commits_data)
        cache[cache_key] = affinities
    return affinities


def build_graph_data_store(
    G: nx.Graph, communities: list[set[str]]
) -> dict[str, dict[Any, Any]]:
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


def build_affinity_graph_output(
    commits_data,
    min_affinity: float,
    max_nodes: int,
    affinities: dict[tuple[str, str], float],
    create_network_fn,
    create_visualization_fn,
) -> tuple[go.Figure, dict[str, dict[Any, Any]]]:
    """Build figure + serialized graph data for affinity groups page."""
    G, communities, _ = create_network_fn(
        commits_data,
        min_affinity=min_affinity,
        max_nodes=max_nodes,
        precomputed_affinities=affinities,
    )
    graph_data = build_graph_data_store(G, communities)
    figure = create_visualization_fn(G, communities)
    return figure, graph_data


def generate_affinity_graph_result(
    store_data,
    max_nodes: int,
    min_affinity: float,
    *,
    parse_date_range_fn,
    commits_in_period_fn,
    ensure_list_fn,
    get_cached_affinities_fn,
    create_network_fn,
    create_visualization_fn,
    create_repo_error_figure_fn,
    create_error_figure_fn,
) -> tuple[go.Figure, dict[str, dict[Any, Any]]]:
    """Generate affinity graph callback result using injected dependencies."""
    try:
        starting, ending = parse_date_range_fn(store_data)
    except ValueError as error:
        return create_error_figure_fn("Invalid date range", str(error)), {}

    try:
        commits_data = ensure_list_fn(commits_in_period_fn(starting, ending))
    except ValueError as error:
        if "No repository path provided" in str(error):
            return create_repo_error_figure_fn(), {}
        raise

    affinities = get_cached_affinities_fn(starting, ending, commits_data)

    try:
        return build_affinity_graph_output(
            commits_data=commits_data,
            min_affinity=min_affinity,
            max_nodes=max_nodes,
            affinities=affinities,
            create_network_fn=create_network_fn,
            create_visualization_fn=create_visualization_fn,
        )
    except Exception as error:
        return (
            create_error_figure_fn("Graph generation failed", str(error)),
            {},
        )


def extract_clicked_node_name(click_data) -> str:
    """Extract clicked node file path from click payload."""
    if not click_data:
        return ""
    point = click_data.get("points", [{}])[0]
    node_name = point.get("text", "")
    if "<br>" in node_name:
        return node_name.split("<br>")[0].replace("File: ", "")
    return node_name


def files_in_clicked_community(
    graph_data: dict[str, dict[Any, Any]], node_name: str
) -> list[str]:
    """Return files in the same community as the clicked node."""
    if not node_name or "nodes" not in graph_data:
        return []
    if node_name not in graph_data["nodes"]:
        return []

    clicked_node_data = graph_data["nodes"][node_name]
    node_community = clicked_node_data.get("community", 0)
    return [
        node
        for node, node_info in graph_data["nodes"].items()
        if node_info.get("community", -1) == node_community
    ]


def generate_node_details_rows(
    click_data,
    graph_data,
    date_range_data,
    *,
    extract_clicked_node_name_fn,
    files_in_clicked_community_fn,
    parse_date_range_fn,
    commits_in_period_fn,
    get_commits_for_group_files_fn,
) -> list[dict[str, str]]:
    """Generate group-commit table rows for a clicked affinity node."""
    if not click_data or not graph_data or "nodes" not in graph_data:
        return []

    node_name = extract_clicked_node_name_fn(click_data)
    group_files = files_in_clicked_community_fn(graph_data, node_name)
    if not group_files:
        return []

    starting, ending = parse_date_range_fn(date_range_data)
    commits_in_period = commits_in_period_fn(starting, ending)
    return get_commits_for_group_files_fn(commits_in_period, group_files)
