"""
Network Graph Visualization Module

This module provides functions for creating and visualizing file affinity networks.
It consolidates the best features from the original implementations in affinity_groups.py
and improved_affinity_network.py.
"""

from functools import lru_cache
from typing import Any

import networkx as nx
import plotly.express as px
import plotly.graph_objects as go

from algorithms.affinity_analysis import get_top_files_by_affinity
from algorithms.affinity_calculator import calculate_affinities
from algorithms.graph_statistics import (
    calculate_graph_statistics,
    count_files_in_commits,
    count_multi_file_commits,
    detect_and_assign_communities,
    filter_low_degree_nodes,
)
from utils.git import ensure_list
from visualization.common import create_empty_figure


def calculate_node_size(commit_count: int, degree: int) -> float:
    """Calculate node size based on commit count and degree."""
    base_size = 10
    commit_factor = min(commit_count * 0.5, 20)
    degree_factor = degree * 2
    return base_size + commit_factor + degree_factor


def create_node_tooltip(node: str, commit_count: int, degree: int) -> str:
    """Create informative tooltip text for a node."""
    return f"File: {node}<br>Commits: {commit_count}<br>Connections: {degree}"


def create_file_affinity_network(
    commits,
    min_affinity: float = 0.2,
    max_nodes: int = 50,
    min_edge_count: int = 1,
    precomputed_affinities: dict[tuple[str, str], float] | None = None,
) -> tuple[nx.Graph, list, dict[str, Any]]:
    """Create a network graph of file affinities based on commit history.

    Returns:
        A tuple of (networkx graph, communities list, stats dict)
    """
    stats: dict[str, Any] = {
        "total_commits": 0,
        "commits_with_multiple_files": 0,
        "unique_files": 0,
        "file_pairs": 0,
        "nodes_before_filtering": 0,
        "nodes_after_filtering": 0,
        "edges_before_filtering": 0,
        "edges_after_filtering": 0,
        "isolated_nodes": 0,
        "communities": 0,
        "avg_node_degree": 0,
        "avg_edge_weight": 0,
        "avg_community_size": 0,
    }

    if not commits:
        return nx.Graph(), [], {"error": "No commits provided"}

    commits = ensure_list(commits)
    stats["total_commits"] = len(commits)

    affinities = (
        precomputed_affinities
        if precomputed_affinities is not None
        else calculate_affinities(commits)
    )

    file_counts = count_files_in_commits(commits)
    stats["commits_with_multiple_files"] = count_multi_file_commits(commits)

    # Determine unique files from affinities (not just from commits) so we align with the graph.
    all_files: set[str] = set()
    for file_pair in affinities:
        all_files.update(file_pair)

    stats["unique_files"] = len(all_files)
    stats["file_pairs"] = len(affinities)

    # Build graph with nodes and edges
    G = nx.Graph()
    top_file_set = get_top_files_by_affinity(affinities, max_nodes)
    for file in top_file_set:
        G.add_node(file, commit_count=file_counts.get(file, 0))

    stats["nodes_before_filtering"] = len(G.nodes())

    for (file1, file2), affinity in affinities.items():
        if (
            file1 in top_file_set
            and file2 in top_file_set
            and affinity >= min_affinity
        ):
            G.add_edge(file1, file2, weight=affinity)

    stats["edges_before_filtering"] = len(G.edges())

    stats["isolated_nodes"] = filter_low_degree_nodes(G, min_edge_count)
    stats["nodes_after_filtering"] = len(G.nodes())
    stats["edges_after_filtering"] = len(G.edges())

    communities, community_stats = detect_and_assign_communities(G)
    stats.update(community_stats)

    graph_stats = calculate_graph_statistics(G)
    stats.update(graph_stats)

    return G, communities, stats


@lru_cache(maxsize=32)
def _cached_layout(hash_key: str) -> dict:
    """Cached spring layout positions based on a simple hash key.

    The hash key should uniquely represent the graph structure for layout
    purposes (e.g., sorted list of edges).
    """
    # This function will be populated by create_network_visualization, which
    # constructs the graph and then calls this helper with a derived key.
    # The actual implementation is filled in at call-time.
    raise RuntimeError("_cached_layout should not be called directly")


def _compute_layout(G: nx.Graph, iterations: int = 40) -> dict:
    """Compute a spring layout with tuned iteration count."""
    return nx.spring_layout(G, seed=42, iterations=iterations)


def create_network_visualization(
    # Default title is cosmetic; keep it out of mutation testing noise.
    G: nx.Graph,
    communities: list,
    title: str = "File Affinity Network",  # pragma: no mutate
) -> go.Figure:
    """
    Create a Plotly figure for visualizing the file affinity network.

    Combines best features from both implementations:
    - Better handling of empty graphs
    - Improved node sizing based on commit count and degree
    - More informative tooltips
    - Better color scheme for communities
    - Proper edge width scaling

    Args:
        G: NetworkX graph of file affinities
        communities: List of communities detected in the graph
        title: Title for the visualization

    Returns:
        A Plotly figure object
    """
    if len(G.nodes()) == 0:
        # Empty-graph message/title are cosmetic; avoid mutating their literals.
        return create_empty_figure(
            message="No data available for the selected time period",  # pragma: no mutate
            title=title,
        )

    # Use force-directed layout with tuned iterations.
    # For now we compute the layout directly with fewer iterations
    # to reduce render time. If we want to add true layout caching
    # keyed by edge structure, we can plug in _compute_layout and an
    # lru_cache-backed helper.
    pos = nx.spring_layout(G, seed=42, iterations=40)

    # Create edge traces
    edge_traces = _create_edge_traces(G, pos)

    # Create node traces
    node_traces = _create_node_traces(G, pos, communities)

    # Create figure
    fig = go.Figure(
        data=[*edge_traces, *node_traces],
        layout=go.Layout(
            # Title text and legend visibility are presentation-only concerns.
            title=title,  # pragma: no mutate
            title_font=dict(size=16),  # pragma: no mutate
            showlegend=True,  # pragma: no mutate
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )

    return fig


def _create_edge_traces(G: nx.Graph, pos: dict) -> list[go.Scatter]:
    """
    Create edge traces for the network visualization.

    Args:
        G: NetworkX graph
        pos: Node positions from layout algorithm

    Returns:
        List of Plotly Scatter traces for edges
    """
    edge_traces = []

    if len(G.edges()) == 0:
        # Return empty trace if no edges
        return [
            go.Scatter(
                x=[],
                y=[],
                line=dict(width=0, color="#888"),
                hoverinfo="none",
                mode="lines",
                showlegend=False,
            )
        ]

    # Collect edge data
    edge_x = []
    edge_y = []
    edge_weights = []
    edge_texts = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

        weight = G.edges[edge]["weight"]
        edge_weights.append(weight)
        edge_texts.append(f"{edge[0]} - {edge[1]}<br>Affinity: {weight:.2f}")

    # Normalize edge weights for width
    max_weight = max(edge_weights) if edge_weights else 1

    # Create separate trace for each edge with its own width
    for i in range(0, len(edge_x), 3):
        if i + 2 < len(edge_x):
            edge_idx = i // 3
            if edge_idx < len(edge_weights):
                width = 2 + (edge_weights[edge_idx] / max_weight) * 6
                text = (
                    edge_texts[edge_idx] if edge_idx < len(edge_texts) else ""
                )
            else:
                width = 2
                text = ""

            edge_trace = go.Scatter(
                x=edge_x[i : i + 3],
                y=edge_y[i : i + 3],
                line=dict(width=width, color="#888"),
                hoverinfo="text",
                text=text,
                mode="lines",
                showlegend=False,
            )
            edge_traces.append(edge_trace)

    return (
        edge_traces
        if edge_traces
        else [
            go.Scatter(
                x=[],
                y=[],
                line=dict(width=0, color="#888"),
                hoverinfo="none",
                mode="lines",
                showlegend=False,
            )
        ]
    )


def _create_node_traces(
    G: nx.Graph, pos: dict, communities: list
) -> list[go.Scatter]:
    """
    Create node traces for the network visualization.

    Args:
        G: NetworkX graph
        pos: Node positions from layout algorithm
        communities: List of communities

    Returns:
        List of Plotly Scatter traces for nodes
    """
    node_traces = []

    # Use distinct color palette
    community_colors = px.colors.qualitative.D3

    # Get community IDs from node attributes
    community_ids = set(nx.get_node_attributes(G, "community").values())

    # If no communities but nodes exist, create single community
    if not community_ids and len(G.nodes()) > 0:
        node_trace = _create_single_community_trace(G, pos, community_colors[0])
        node_traces.append(node_trace)
    else:
        # Process each community separately
        for community_id in community_ids:
            community_nodes = [
                node
                for node, data in G.nodes(data=True)
                if data.get("community") == community_id
            ]

            # Skip single-node communities
            if len(community_nodes) <= 1:
                continue

            color = community_colors[community_id % len(community_colors)]
            node_trace = _create_community_trace(
                G, pos, community_nodes, color, community_id
            )
            node_traces.append(node_trace)

    return node_traces


def _create_single_community_trace(
    G: nx.Graph, pos: dict, color: str
) -> go.Scatter:
    """Create a trace for all nodes in a single color."""
    node_x = []
    node_y = []
    node_text = []
    node_size = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        commit_count = G.nodes[node].get("commit_count", 0)
        degree = G.degree(node)
        node_text.append(create_node_tooltip(node, commit_count, degree))
        node_size.append(calculate_node_size(commit_count, degree))

    return go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(
            color=color, size=node_size, line=dict(width=1, color="#333")
        ),
        # Legend label is cosmetic; exclude from mutation testing.
        name="All Files",  # pragma: no mutate
    )


def _create_community_trace(
    G: nx.Graph, pos: dict, community_nodes: list, color: str, community_id: int
) -> go.Scatter:
    """Create a trace for a specific community."""
    node_x = []
    node_y = []
    node_text = []
    node_size = []

    for node in community_nodes:
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        commit_count = G.nodes[node].get("commit_count", 0)
        degree = G.degree(node)
        node_text.append(create_node_tooltip(node, commit_count, degree))
        node_size.append(calculate_node_size(commit_count, degree))

    return go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_text,
        marker=dict(
            color=color, size=node_size, line=dict(width=1, color="#333")
        ),
        # Community legend label is cosmetic; exclude from mutation testing.
        name=f"Group {community_id + 1}",  # pragma: no mutate
    )
