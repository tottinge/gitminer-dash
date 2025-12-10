"""
Network Graph Visualization Module

This module provides functions for creating and visualizing file affinity networks.
It consolidates the best features from the original implementations in affinity_groups.py
and improved_affinity_network.py.
"""

from collections import defaultdict
from functools import lru_cache
from typing import Any

import networkx as nx
import plotly.express as px
import plotly.graph_objects as go

from algorithms.affinity_analysis import (
    get_top_files_by_affinity,
)
from algorithms.affinity_calculator import calculate_affinities
from utils.git import ensure_list


def _count_file_occurrences(commits) -> tuple[dict[str, int], int]:
    """Count file occurrences and commits with multiple files.

    Returns:
        Tuple of (file_counts dict, multi_file_commit_count)
    """
    file_counts = defaultdict(int)
    multi_file_commits = 0

    for commit in commits:
        files_in_commit = len(commit.stats.files)
        for file in commit.stats.files:
            file_counts[file] += 1
        if files_in_commit >= 2:
            multi_file_commits += 1

    return file_counts, multi_file_commits


def _build_graph_with_edges(
    affinities: dict[tuple[str, str], float],
    file_counts: dict[str, int],
    top_file_set: set[str],
    min_affinity: float,
) -> nx.Graph:
    """Build graph with nodes and edges from affinity data.

    Args:
        affinities: File pair affinity scores
        file_counts: Commit counts per file
        top_file_set: Set of files to include as nodes
        min_affinity: Minimum affinity threshold for edges

    Returns:
        NetworkX graph with nodes and edges
    """
    G = nx.Graph()

    # Add nodes for top files with commit count attribute
    for file in top_file_set:
        G.add_node(file, commit_count=file_counts[file])

    # Add edges with weights based on affinity
    for (file1, file2), affinity in affinities.items():
        if file1 in top_file_set and file2 in top_file_set and affinity >= min_affinity:
            G.add_edge(file1, file2, weight=affinity)

    return G


def _assign_communities(G: nx.Graph) -> list:
    """Detect communities and assign them to graph nodes.

    Args:
        G: NetworkX graph

    Returns:
        List of communities
    """
    communities = nx.community.louvain_communities(G)

    # Assign community ID to each node
    for i, community in enumerate(communities):
        for node in community:
            G.nodes[node]["community"] = i

    return communities


def _calculate_graph_stats(
    G: nx.Graph,
    commits_count: int,
    multi_file_commits: int,
    unique_files_count: int,
    file_pairs_count: int,
    nodes_before: int,
    edges_before: int,
    isolated_count: int,
    communities: list,
) -> dict[str, Any]:
    """Calculate network statistics.

    Args:
        G: NetworkX graph after filtering
        commits_count: Total number of commits
        multi_file_commits: Number of commits with multiple files
        unique_files_count: Number of unique files
        file_pairs_count: Number of file pairs
        nodes_before: Node count before filtering
        edges_before: Edge count before filtering
        isolated_count: Number of removed isolated nodes
        communities: List of detected communities

    Returns:
        Dictionary of statistics
    """
    stats = {
        "total_commits": commits_count,
        "commits_with_multiple_files": multi_file_commits,
        "unique_files": unique_files_count,
        "file_pairs": file_pairs_count,
        "nodes_before_filtering": nodes_before,
        "nodes_after_filtering": len(G.nodes()),
        "edges_before_filtering": edges_before,
        "edges_after_filtering": len(G.edges()),
        "isolated_nodes": isolated_count,
        "communities": len(communities),
        "avg_node_degree": 0,
        "avg_edge_weight": 0,
        "avg_community_size": 0,
    }

    # Calculate average community size
    if communities:
        community_sizes = [len(community) for community in communities]
        stats["avg_community_size"] = sum(community_sizes) / len(communities)

    # Calculate average node degree
    if len(G.nodes()) > 0:
        degrees = [degree for _, degree in G.degree()]
        stats["avg_node_degree"] = sum(degrees) / len(G.nodes())

    # Calculate average edge weight
    if len(G.edges()) > 0:
        weights = [data["weight"] for _, _, data in G.edges(data=True)]
        stats["avg_edge_weight"] = sum(weights) / len(G.edges())

    return stats


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
    """
    Create a network graph of file affinities based on commit history.

    Combines best features from both implementations:
    - Lower default min_affinity threshold (0.2)
    - min_edge_count parameter to filter isolated nodes
    - Detailed statistics tracking
    - Better handling of empty inputs

    Args:
        commits: Iterable of commit objects
        min_affinity: Minimum affinity threshold for including edges (default: 0.2)
        max_nodes: Maximum number of nodes to include in the graph (default: 50)
        min_edge_count: Minimum number of edges a node must have to be included (default: 1)

    Returns:
        A tuple of (networkx graph, communities list, stats dict)
    """
    if not commits:
        return nx.Graph(), [], {"error": "No commits provided"}

    # Convert to list to handle iterator consumption
    commits = ensure_list(commits)

    # Calculate affinities using shared function, unless precomputed values are provided
    affinities = (
        precomputed_affinities
        if precomputed_affinities is not None
        else calculate_affinities(commits)
    )

    # Early return if no affinities found
    if not affinities:
        return nx.Graph(), [], {"error": "No file affinities found"}

    # Count file occurrences and commits with multiple files
    file_counts, multi_file_commits = _count_file_occurrences(commits)

    # Get unique files from affinities
    all_files = set()
    for file_pair in affinities:
        all_files.update(file_pair)

    # Get top files by total affinity
    top_file_set = get_top_files_by_affinity(affinities, max_nodes)

    # Early return if no files selected
    if not top_file_set:
        return nx.Graph(), [], {"error": "No files meet criteria"}

    # Build graph with nodes and edges
    G = _build_graph_with_edges(affinities, file_counts, top_file_set, min_affinity)

    nodes_before = len(G.nodes())
    edges_before = len(G.edges())

    # Remove nodes with too few connections
    isolated_count = 0
    if min_edge_count > 0:
        nodes_to_remove = [
            node for node, degree in G.degree() if degree < min_edge_count
        ]
        G.remove_nodes_from(nodes_to_remove)
        isolated_count = len(nodes_to_remove)

    # Early return if all nodes were filtered out
    if len(G.nodes()) == 0:
        stats = _calculate_graph_stats(
            G,
            len(commits),
            multi_file_commits,
            len(all_files),
            len(affinities),
            nodes_before,
            edges_before,
            isolated_count,
            [],
        )
        return G, [], stats

    # Find communities and assign to nodes
    communities = _assign_communities(G)

    # Calculate final statistics
    stats = _calculate_graph_stats(
        G,
        len(commits),
        multi_file_commits,
        len(all_files),
        len(affinities),
        nodes_before,
        edges_before,
        isolated_count,
        communities,
    )

    return G, communities, stats


def create_no_data_figure(
    message: str = "No data available", title: str = "File Affinity Network"
) -> go.Figure:
    """
    Create a Plotly figure with a 'no data' message.

    Args:
        message: Message to display
        title: Title for the figure

    Returns:
        A Plotly figure object with the message
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=20),
    )
    fig.update_layout(
        title=f"{title} - No Data",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
    return fig


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
    G: nx.Graph, communities: list, title: str = "File Affinity Network"
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
        return create_no_data_figure(
            message="No data available for the selected time period", title=title
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
            title=title,
            title_font=dict(size=16),
            showlegend=True,
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
                text = edge_texts[edge_idx] if edge_idx < len(edge_texts) else ""
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


def _create_node_traces(G: nx.Graph, pos: dict, communities: list) -> list[go.Scatter]:
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


def _create_single_community_trace(G: nx.Graph, pos: dict, color: str) -> go.Scatter:
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
        marker=dict(color=color, size=node_size, line=dict(width=1, color="#333")),
        name="All Files",
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
        marker=dict(color=color, size=node_size, line=dict(width=1, color="#333")),
        name=f"Group {community_id + 1}",
    )
