"""Service helpers for the affinity groups page."""

from __future__ import annotations

from typing import Any, TypedDict

import networkx as nx
import plotly.graph_objects as go


class GraphNodeData(TypedDict):
    """Serialized node metadata for affinity graph stores."""

    commit_count: int
    degree: int
    community: int
    connected_communities: list[int]


class GraphDataStore(TypedDict):
    """Serializable graph data used by affinity page callbacks."""

    nodes: dict[str, GraphNodeData]
    communities: dict[int, list[str]]


GraphDataPayload = GraphDataStore | dict[Any, Any]


def _empty_graph_payload() -> dict[Any, Any]:
    return {}


def _graph_error_result(create_error_figure_fn, title: str, error: Exception):
    return create_error_figure_fn(title, str(error)), _empty_graph_payload()


def _repo_error_result(create_repo_error_figure_fn):
    return create_repo_error_figure_fn(), _empty_graph_payload()


def _is_missing_repository_path_error(error: ValueError) -> bool:
    return "No repository path provided" in str(error)


def _affinity_cache_key(starting, ending) -> tuple[str, str]:
    return starting.isoformat(), ending.isoformat()


def _compute_and_cache_affinities(
    cache: dict[tuple[str, str], dict[tuple[str, str], float]],
    cache_key: tuple[str, str],
    commits_data,
    calculate_affinities_fn,
) -> dict[tuple[str, str], float]:
    computed_affinities = calculate_affinities_fn(commits_data)
    cache[cache_key] = computed_affinities
    return computed_affinities


def get_or_compute_affinities(
    cache: dict[tuple[str, str], dict[tuple[str, str], float]],
    starting,
    ending,
    commits_data,
    calculate_affinities_fn,
) -> dict[tuple[str, str], float]:
    """Get affinities from cache or compute and cache them."""
    cache_key = _affinity_cache_key(starting, ending)
    cached_affinities = cache.get(cache_key)
    if cached_affinities is not None:
        return cached_affinities
    return _compute_and_cache_affinities(
        cache=cache,
        cache_key=cache_key,
        commits_data=commits_data,
        calculate_affinities_fn=calculate_affinities_fn,
    )


def _connected_communities_for_node(
    graph: nx.Graph, node_name: str
) -> list[int]:
    connected_communities = {
        int(graph.nodes[neighbor].get("community", 0))
        for neighbor in graph.neighbors(node_name)
    }
    return sorted(connected_communities)


def _build_graph_node_data(graph: nx.Graph, node_name: str) -> GraphNodeData:
    node_data = graph.nodes[node_name]
    return {
        "commit_count": int(node_data.get("commit_count", 0)),
        "degree": int(graph.degree(node_name)),
        "community": int(node_data.get("community", 0)),
        "connected_communities": _connected_communities_for_node(
            graph, node_name
        ),
    }


def _serialized_graph_nodes(graph: nx.Graph) -> dict[str, GraphNodeData]:
    return {
        node_name: _build_graph_node_data(graph, node_name)
        for node_name in graph.nodes()
    }


def _serialized_communities(
    communities: list[set[str]],
) -> dict[int, list[str]]:
    return {
        community_id: list(community_files)
        for community_id, community_files in enumerate(communities)
    }


def build_graph_data_store(
    G: nx.Graph, communities: list[set[str]]
) -> GraphDataStore:
    """Transform graph into serializable store format."""
    return {
        "nodes": _serialized_graph_nodes(G),
        "communities": _serialized_communities(communities),
    }


def build_affinity_graph_output(
    commits_data,
    min_affinity: float,
    max_nodes: int,
    affinities: dict[tuple[str, str], float],
    create_network_fn,
    create_visualization_fn,
) -> tuple[go.Figure, GraphDataStore]:
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


def _load_commits_data(
    starting,
    ending,
    *,
    commits_in_period_fn,
    ensure_list_fn,
):
    return ensure_list_fn(commits_in_period_fn(starting, ending))


def _build_affinity_graph_output_or_error(
    *,
    commits_data,
    min_affinity: float,
    max_nodes: int,
    affinities: dict[tuple[str, str], float],
    create_network_fn,
    create_visualization_fn,
    create_error_figure_fn,
) -> tuple[go.Figure, GraphDataPayload]:
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
        return _graph_error_result(
            create_error_figure_fn, "Graph generation failed", error
        )


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
) -> tuple[go.Figure, GraphDataPayload]:
    """Generate affinity graph callback result using injected dependencies."""
    try:
        starting, ending = parse_date_range_fn(store_data)
    except ValueError as error:
        return _graph_error_result(
            create_error_figure_fn, "Invalid date range", error
        )

    try:
        commits_data = _load_commits_data(
            starting,
            ending,
            commits_in_period_fn=commits_in_period_fn,
            ensure_list_fn=ensure_list_fn,
        )
    except ValueError as error:
        if _is_missing_repository_path_error(error):
            return _repo_error_result(create_repo_error_figure_fn)
        raise

    affinities = get_cached_affinities_fn(starting, ending, commits_data)
    return _build_affinity_graph_output_or_error(
        commits_data=commits_data,
        min_affinity=min_affinity,
        max_nodes=max_nodes,
        affinities=affinities,
        create_network_fn=create_network_fn,
        create_visualization_fn=create_visualization_fn,
        create_error_figure_fn=create_error_figure_fn,
    )


def _first_click_point(click_data: dict[str, Any]) -> dict[str, Any]:
    return click_data.get("points", [{}])[0]


def _file_path_from_hover_text(node_text: str) -> str:
    return node_text.split("<br>")[0].replace("File: ", "")


def extract_clicked_node_name(click_data) -> str:
    """Extract clicked node file path from click payload."""
    if not click_data:
        return ""
    point = _first_click_point(click_data)
    node_name = point.get("text", "")
    if "<br>" in node_name:
        return _file_path_from_hover_text(node_name)
    return node_name


def _graph_nodes(
    graph_data: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    nodes = graph_data.get("nodes")
    if isinstance(nodes, dict):
        return nodes
    return {}


def _clicked_node_community(
    nodes_by_name: dict[str, dict[str, Any]], node_name: str
) -> Any:
    clicked_node_data = nodes_by_name[node_name]
    return clicked_node_data.get("community", 0)


def _contains_node(
    nodes_by_name: dict[str, dict[str, Any]], node_name: str
) -> bool:
    return node_name in nodes_by_name


def _files_in_same_community(
    nodes_by_name: dict[str, dict[str, Any]], node_community: Any
) -> list[str]:
    return [
        file_path
        for file_path, node_info in nodes_by_name.items()
        if node_info.get("community", -1) == node_community
    ]


def files_in_clicked_community(
    graph_data: dict[str, Any], node_name: str
) -> list[str]:
    """Return files in the same community as the clicked node."""
    if not node_name:
        return []
    nodes_by_name = _graph_nodes(graph_data)
    if not _contains_node(nodes_by_name, node_name):
        return []
    node_community = _clicked_node_community(nodes_by_name, node_name)
    return _files_in_same_community(nodes_by_name, node_community)


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
    if not _has_node_details_prerequisites(click_data, graph_data):
        return []

    group_files = _group_files_for_clicked_node(
        click_data,
        graph_data,
        extract_clicked_node_name_fn=extract_clicked_node_name_fn,
        files_in_clicked_community_fn=files_in_clicked_community_fn,
    )
    if not group_files:
        return []

    commits_in_period = _commits_for_date_range(
        date_range_data,
        parse_date_range_fn=parse_date_range_fn,
        commits_in_period_fn=commits_in_period_fn,
    )
    return get_commits_for_group_files_fn(commits_in_period, group_files)


def _has_node_details_prerequisites(
    click_data, graph_data: dict[str, Any] | None
) -> bool:
    return bool(click_data and graph_data and "nodes" in graph_data)


def _group_files_for_clicked_node(
    click_data,
    graph_data,
    *,
    extract_clicked_node_name_fn,
    files_in_clicked_community_fn,
) -> list[str]:
    node_name = extract_clicked_node_name_fn(click_data)
    return files_in_clicked_community_fn(graph_data, node_name)


def _commits_for_date_range(
    date_range_data, *, parse_date_range_fn, commits_in_period_fn
):
    starting, ending = parse_date_range_fn(date_range_data)
    return commits_in_period_fn(starting, ending)
