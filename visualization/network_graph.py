"""
Network Graph Visualization Module

This module provides functions for creating and visualizing file affinity networks.
It consolidates the best features from the original implementations in affinity_groups.py
and improved_affinity_network.py.
"""

import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict
from typing import Tuple, Dict, List, Any

from algorithms.affinity_calculator import calculate_affinities
from algorithms.affinity_analysis import get_file_total_affinities, get_top_files_by_affinity
from utils.git import ensure_list


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
    min_edge_count: int = 1
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
    # Initialize stats
    stats = {
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

    # Convert to list to handle iterator consumption
    commits = ensure_list(commits)

    stats["total_commits"] = len(commits)

    # Calculate affinities using shared function
    affinities = calculate_affinities(commits)

    # Count file occurrences and commits with multiple files
    file_counts = defaultdict(int)
    for commit in commits:
        files_in_commit = len(commit.stats.files)
        for file in commit.stats.files:
            file_counts[file] += 1
        if files_in_commit >= 2:
            stats["commits_with_multiple_files"] += 1

    # Get unique files
    all_files = set()
    for file_pair in affinities.keys():
        all_files.update(file_pair)

    stats["unique_files"] = len(all_files)
    stats["file_pairs"] = len(affinities)

    # Create network graph
    G = nx.Graph()

    # Get top files by total affinity
    top_file_set = get_top_files_by_affinity(affinities, max_nodes)

    # Add nodes for top files with commit count attribute
    for file in top_file_set:
        G.add_node(file, commit_count=file_counts[file])

    stats["nodes_before_filtering"] = len(G.nodes())

    # Add edges with weights based on affinity
    for (file1, file2), affinity in affinities.items():
        if file1 in top_file_set and file2 in top_file_set and affinity >= min_affinity:
            G.add_edge(file1, file2, weight=affinity)

    stats["edges_before_filtering"] = len(G.edges())

    # Remove nodes with too few connections
    if min_edge_count > 0:
        nodes_to_remove = [
            node for node, degree in G.degree() if degree < min_edge_count
        ]
        G.remove_nodes_from(nodes_to_remove)
        stats["isolated_nodes"] = len(nodes_to_remove)

    stats["nodes_after_filtering"] = len(G.nodes())
    stats["edges_after_filtering"] = len(G.edges())

    # Find communities using Louvain method
    communities = []
    if len(G.nodes()) > 0:
        communities = nx.community.louvain_communities(G)
        stats["communities"] = len(communities)

        # Calculate average community size
        if communities:
            community_sizes = [len(community) for community in communities]
            stats["avg_community_size"] = sum(community_sizes) / len(communities)

        # Assign community ID to each node
        for i, community in enumerate(communities):
            for node in community:
                G.nodes[node]["community"] = i

    # Calculate average node degree
    if len(G.nodes()) > 0:
        degrees = [degree for _, degree in G.degree()]
        stats["avg_node_degree"] = sum(degrees) / len(G.nodes())

    # Calculate average edge weight
    if len(G.edges()) > 0:
        weights = [data["weight"] for _, _, data in G.edges(data=True)]
        stats["avg_edge_weight"] = sum(weights) / len(G.edges())

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


def create_network_visualization(
    G: nx.Graph,
    communities: list,
    title: str = "File Affinity Network"
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

    # Use force-directed layout
    pos = nx.spring_layout(G, seed=42)

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
    G: nx.Graph,
    pos: dict,
    community_nodes: list,
    color: str,
    community_id: int
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
