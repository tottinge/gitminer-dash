#!/usr/bin/env python3
"""
Test script for diagnosing issues with the file affinity network visualization.

This script loads git commit data from a repository, processes it through the
create_file_affinity_network function, and provides detailed diagnostics about
the resulting graph.
"""


# Import from tests package to set up path
from tests import setup_path

setup_path()  # This ensures we can import modules from the project root
import os
import sys
import json
import pickle
from datetime import datetime
from pathlib import Path
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from git import Repo, Commit
from collections import defaultdict
from itertools import combinations

# Import project modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import date_utils


# Copy of functions from affinity_groups.py to avoid Dash initialization issues
def create_file_affinity_network(commits, min_affinity=0.5, max_nodes=50):
    """
    Create a network graph of file affinities based on commit history.

    Args:
        commits: Iterable of commit objects
        min_affinity: Minimum affinity threshold for including edges
        max_nodes: Maximum number of nodes to include in the graph

    Returns:
        A tuple of (networkx graph, communities)
    """
    if not commits:
        return nx.Graph(), []

    # Calculate affinities as in strongest_pairings.py
    affinities = defaultdict(float)
    for commit in commits:
        files_in_commit = len(commit.stats.files)
        if files_in_commit < 2:
            continue
        for combo in combinations(commit.stats.files, 2):
            ordered_key = tuple(sorted(combo))
            affinities[ordered_key] += 1 / files_in_commit

    # Create a network graph
    G = nx.Graph()

    # Add nodes (files)
    all_files = set()
    for file_pair in affinities.keys():
        all_files.update(file_pair)

    # Sort files by their total affinity and limit to max_nodes
    file_total_affinity = defaultdict(float)
    for (file1, file2), affinity in affinities.items():
        file_total_affinity[file1] += affinity
        file_total_affinity[file2] += affinity

    top_files = sorted(file_total_affinity.items(), key=lambda x: x[1], reverse=True)[
        :max_nodes
    ]
    top_file_set = {file for file, _ in top_files}

    # Add nodes for top files
    for file in top_file_set:
        G.add_node(file)

    # Add edges with weights based on affinity
    for (file1, file2), affinity in affinities.items():
        if file1 in top_file_set and file2 in top_file_set and affinity >= min_affinity:
            G.add_edge(file1, file2, weight=affinity)

    # Find communities/clusters using Louvain method
    # Check if the graph has any nodes before calling louvain_communities
    if len(G.nodes()) > 0:
        communities = nx.community.louvain_communities(G)

        # Assign community ID to each node
        for i, community in enumerate(communities):
            for node in community:
                G.nodes[node]["community"] = i
    else:
        # Return empty communities list if graph is empty
        communities = []

    return G, communities


def create_network_visualization(G, communities):
    """
    Create a Plotly figure for visualizing the file affinity network.

    Args:
        G: NetworkX graph of file affinities
        communities: List of communities detected in the graph

    Returns:
        A Plotly figure object
    """
    if len(G.nodes()) == 0:
        # Return a figure with a 'no data' message
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for the selected time period",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20),
        )
        fig.update_layout(
            title="File Affinity Network - No Data",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        )
        return fig

    # Use a force-directed layout algorithm
    pos = nx.spring_layout(G, seed=42)

    # Create edge traces
    edge_x = []
    edge_y = []
    edge_weights = []

    # Check if there are any edges before creating edge trace
    if len(G.edges()) > 0:
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_weights.append(G.edges[edge]["weight"])

        # Normalize edge weights for width
        max_weight = max(edge_weights) if edge_weights else 1

        # Create separate edge traces for each edge with its own width
        edge_traces = []
        for i in range(0, len(edge_x), 3):  # Each edge is 3 points (x0, x1, None)
            if i + 2 < len(edge_x):  # Ensure we have a complete edge
                # Calculate width for this edge
                edge_idx = i // 3
                if edge_idx < len(edge_weights):
                    width = 2 + (edge_weights[edge_idx] / max_weight) * 6
                else:
                    width = 2  # Default width if index is out of range

                # Create a trace for this single edge
                edge_trace = go.Scatter(
                    x=edge_x[i : i + 3],  # Just this edge's x coordinates
                    y=edge_y[i : i + 3],  # Just this edge's y coordinates
                    line=dict(width=width, color="#888"),
                    hoverinfo="none",
                    mode="lines",
                    showlegend=False,
                )
                edge_traces.append(edge_trace)

        # If no edges were created, create an empty edge trace
        if not edge_traces:
            edge_trace = go.Scatter(
                x=[],
                y=[],
                line=dict(width=0, color="#888"),
                hoverinfo="none",
                mode="lines",
            )
            edge_traces = [edge_trace]
    else:
        # Create an empty edge trace if there are no edges
        edge_trace = go.Scatter(
            x=[], y=[], line=dict(width=0, color="#888"), hoverinfo="none", mode="lines"
        )
        edge_traces = [edge_trace]

    # Create node traces (one per community for different colors)
    node_traces = []

    # Get a color map for communities
    community_colors = px.colors.qualitative.Plotly

    # Get community IDs from node attributes, handle case where there are no communities
    community_ids = set(nx.get_node_attributes(G, "community").values())

    # If there are no communities but there are nodes, create a single community with all nodes
    if not community_ids and len(G.nodes()) > 0:
        # Create a trace with all nodes in a single color
        node_x = []
        node_y = []
        node_text = []
        node_size = []

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            # Node size based on degree (number of connections)
            node_size.append(10 + G.degree(node) * 2)

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers",
            hoverinfo="text",
            text=node_text,
            marker=dict(
                color=community_colors[0],
                size=node_size,
                line=dict(width=1, color="#333"),
            ),
            name="All Files",
        )

        node_traces.append(node_trace)
    else:
        # Process each community
        for community_id in community_ids:
            community_nodes = [
                node
                for node, data in G.nodes(data=True)
                if data.get("community") == community_id
            ]

            node_x = []
            node_y = []
            node_text = []
            node_size = []

            for node in community_nodes:
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                node_text.append(node)
                # Node size based on degree (number of connections)
                node_size.append(10 + G.degree(node) * 2)

            color = community_colors[community_id % len(community_colors)]

            node_trace = go.Scatter(
                x=node_x,
                y=node_y,
                mode="markers",
                hoverinfo="text",
                text=node_text,
                marker=dict(
                    color=color, size=node_size, line=dict(width=1, color="#333")
                ),
                name=f"Group {community_id + 1}",
            )

            node_traces.append(node_trace)

    # Create figure
    fig = go.Figure(
        data=[*edge_traces, *node_traces],
        layout=go.Layout(
            title="File Affinity Network",
            title_font=dict(size=16),  # Changed from titlefont to title_font
            showlegend=True,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )

    return fig


# Constants
TEST_DATA_DIR = Path(os.path.join(os.path.dirname(__file__), "test_data"))
TEST_PERIODS = ["Last 6 Months", "Last 1 Year", "Last 5 Years"]


def ensure_test_data_dir():
    """Create the test data directory if it doesn't exist."""
    TEST_DATA_DIR.mkdir(exist_ok=True)


def get_repository_path():
    """Get the repository path from command line or use current directory."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    return os.getcwd()  # Use current directory as fallback


def get_commits_for_period(repo_path, period):
    """
    Get commits for the specified time period.

    Args:
        repo_path: Path to the git repository
        period: Time period string (e.g., "Last 6 Months")

    Returns:
        List of commit objects
    """
    print(f"Getting commits for period: {period}")
    repo = Repo(repo_path)

    # Calculate date range
    begin, end = date_utils.calculate_date_range(period)
    print(f"Date range: {begin.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")

    # Get commits in the date range
    commits = []
    for commit in repo.iter_commits():
        commit_date = datetime.fromtimestamp(commit.committed_date).astimezone()
        if begin <= commit_date <= end:
            commits.append(commit)

    print(f"Found {len(commits)} commits in the period")
    return commits


def save_commits_data(commits, period):
    """
    Save commit data to a file for later use.

    Args:
        commits: List of commit objects
        period: Time period string

    Returns:
        Path to the saved file
    """
    # Create a simplified representation of commits for saving
    simplified_commits = []
    for commit in commits:
        files_changed = list(commit.stats.files.keys())
        simplified_commit = {
            "hash": commit.hexsha,
            "author": str(commit.author),
            "date": datetime.fromtimestamp(commit.committed_date).isoformat(),
            "message": commit.message,
            "files": files_changed,
        }
        simplified_commits.append(simplified_commit)

    # Save to file
    filename = f"commits_{period.replace(' ', '_').lower()}.json"
    filepath = TEST_DATA_DIR / filename
    with open(filepath, "w") as f:
        json.dump(simplified_commits, f, indent=2)

    print(f"Saved {len(simplified_commits)} commits to {filepath}")
    return filepath


def load_commits_data(period):
    """
    Load commit data from a file.

    Args:
        period: Time period string

    Returns:
        List of simplified commit objects
    """
    filename = f"commits_{period.replace(' ', '_').lower()}.json"
    filepath = TEST_DATA_DIR / filename

    if not filepath.exists():
        print(f"No saved data found for {period}")
        return None

    with open(filepath, "r") as f:
        commits = json.load(f)

    print(f"Loaded {len(commits)} commits from {filepath}")
    return commits


def create_mock_commit(commit_data):
    """
    Create a mock commit object from simplified commit data.

    Args:
        commit_data: Dictionary with commit data

    Returns:
        A mock commit object with the necessary attributes
    """

    class MockCommit:
        def __init__(self, data):
            self.hexsha = data["hash"]
            self.message = data["message"]
            self.committed_date = datetime.fromisoformat(data["date"]).timestamp()
            self.committed_datetime = datetime.fromisoformat(data["date"])

            class MockStats:
                def __init__(self, files):
                    self.files = {
                        file: {"insertions": 1, "deletions": 1} for file in files
                    }

            self.stats = MockStats(data["files"])

    return MockCommit(commit_data)


def analyze_affinity_network(commits, period, min_affinity=0.5, max_nodes=50):
    """
    Analyze the affinity network created from the commits.

    Args:
        commits: List of commit objects (real or mock)
        period: Time period string
        min_affinity: Minimum affinity threshold
        max_nodes: Maximum number of nodes

    Returns:
        Dictionary with analysis results
    """
    print(f"\nAnalyzing affinity network for {period}")
    print(f"Parameters: min_affinity={min_affinity}, max_nodes={max_nodes}")

    # Create mock commits if needed
    if isinstance(commits[0], dict):
        mock_commits = [create_mock_commit(commit) for commit in commits]
        commits = mock_commits

    # Count files in commits
    files_in_commits = set()
    for commit in commits:
        files_in_commit = commit.stats.files.keys()
        files_in_commits.update(files_in_commit)

    print(f"Total unique files in commits: {len(files_in_commits)}")

    # Create the affinity network
    start_time = datetime.now()
    G, communities = create_file_affinity_network(
        commits, min_affinity=min_affinity, max_nodes=max_nodes
    )
    end_time = datetime.now()

    # Analyze the graph
    num_nodes = len(G.nodes())
    num_edges = len(G.edges())
    num_communities = len(communities)

    print(f"Graph creation took {(end_time - start_time).total_seconds():.2f} seconds")
    print(f"Graph has {num_nodes} nodes and {num_edges} edges")
    print(f"Found {num_communities} communities")

    # Check if the graph is valid
    is_valid = num_nodes > 0 and num_edges > 0

    if not is_valid:
        print("WARNING: Graph appears to be invalid (no nodes or edges)")

    # Get node degrees
    if num_nodes > 0:
        degrees = [degree for _, degree in G.degree()]
        avg_degree = sum(degrees) / len(degrees) if degrees else 0
        max_degree = max(degrees) if degrees else 0
        min_degree = min(degrees) if degrees else 0
        print(
            f"Node degree stats: min={min_degree}, avg={avg_degree:.2f}, max={max_degree}"
        )

    # Get edge weights
    if num_edges > 0:
        weights = [data["weight"] for _, _, data in G.edges(data=True)]
        avg_weight = sum(weights) / len(weights) if weights else 0
        max_weight = max(weights) if weights else 0
        min_weight = min(weights) if weights else 0
        print(
            f"Edge weight stats: min={min_weight:.2f}, avg={avg_weight:.2f}, max={max_weight:.2f}"
        )

    # Analyze communities
    if num_communities > 0:
        community_sizes = [len(community) for community in communities]
        avg_community_size = sum(community_sizes) / len(community_sizes)
        max_community_size = max(community_sizes)
        min_community_size = min(community_sizes)
        print(
            f"Community size stats: min={min_community_size}, avg={avg_community_size:.2f}, max={max_community_size}"
        )

    # Return analysis results
    return {
        "period": period,
        "min_affinity": min_affinity,
        "max_nodes": max_nodes,
        "num_commits": len(commits),
        "num_unique_files": len(files_in_commits),
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "num_communities": num_communities,
        "is_valid": is_valid,
        "node_degree_stats": {
            "min": min_degree if num_nodes > 0 else None,
            "avg": avg_degree if num_nodes > 0 else None,
            "max": max_degree if num_nodes > 0 else None,
        },
        "edge_weight_stats": {
            "min": min_weight if num_edges > 0 else None,
            "avg": avg_weight if num_edges > 0 else None,
            "max": max_weight if num_edges > 0 else None,
        },
        "community_size_stats": {
            "min": min_community_size if num_communities > 0 else None,
            "avg": avg_community_size if num_communities > 0 else None,
            "max": max_community_size if num_communities > 0 else None,
        },
    }


def save_visualization(G, communities, period, min_affinity, max_nodes):
    """
    Save the network visualization to an HTML file.

    Args:
        G: NetworkX graph
        communities: List of communities
        period: Time period string
        min_affinity: Minimum affinity threshold
        max_nodes: Maximum number of nodes

    Returns:
        Path to the saved file
    """
    # Create the visualization
    fig = create_network_visualization(G, communities)

    # Save to file
    filename = (
        f"network_{period.replace(' ', '_').lower()}_{min_affinity}_{max_nodes}.html"
    )
    filepath = TEST_DATA_DIR / filename
    fig.write_html(str(filepath))

    print(f"Saved visualization to {filepath}")
    return filepath


def try_affinity_network_with_different_parameters(commits, period):
    """
    Test the affinity network with different parameter combinations.

    Args:
        commits: List of commit objects or dictionaries
        period: Time period string

    Returns:
        List of analysis results
    """
    results = []

    # Create mock commits if needed
    if isinstance(commits[0], dict):
        mock_commits = [create_mock_commit(commit) for commit in commits]
    else:
        mock_commits = commits

    # Test with different min_affinity values
    for min_affinity in [0.1, 0.2, 0.3, 0.4, 0.5]:
        # Test with different max_nodes values
        for max_nodes in [20, 50, 100]:
            try:
                # Create and analyze the network
                G, communities = create_file_affinity_network(
                    mock_commits, min_affinity=min_affinity, max_nodes=max_nodes
                )

                # Save visualization if the graph is valid
                if len(G.nodes()) > 0 and len(G.edges()) > 0:
                    save_visualization(G, communities, period, min_affinity, max_nodes)

                # Analyze the network
                result = analyze_affinity_network(
                    mock_commits, period, min_affinity, max_nodes
                )
                results.append(result)

                print(
                    f"Tested with min_affinity={min_affinity}, max_nodes={max_nodes}: "
                    + f"{len(G.nodes())} nodes, {len(G.edges())} edges"
                )
            except Exception as e:
                print(
                    f"Error testing with min_affinity={min_affinity}, max_nodes={max_nodes}: {str(e)}"
                )

    return results


def main():
    """Main function to run the tests."""
    # Ensure test data directory exists
    ensure_test_data_dir()

    # Get repository path
    repo_path = get_repository_path()
    print(f"Using repository at: {repo_path}")

    all_results = []

    # Process each test period
    for period in TEST_PERIODS:
        # Try to load saved commit data
        commits = load_commits_data(period)

        # If no saved data, get commits and save them
        if commits is None:
            try:
                commits = get_commits_for_period(repo_path, period)
                save_commits_data(commits, period)
            except Exception as e:
                print(f"Error getting commits for {period}: {str(e)}")
                continue

        # Test with default parameters
        try:
            result = analyze_affinity_network(commits, period)
            all_results.append(result)

            # Create and save visualization
            if isinstance(commits[0], dict):
                mock_commits = [create_mock_commit(commit) for commit in commits]
                G, communities = create_file_affinity_network(mock_commits)
            else:
                G, communities = create_file_affinity_network(commits)

            if len(G.nodes()) > 0:
                save_visualization(G, communities, period, 0.5, 50)

            # Test with different parameters
            param_results = try_affinity_network_with_different_parameters(
                commits, period
            )
            all_results.extend(param_results)
        except Exception as e:
            print(f"Error analyzing network for {period}: {str(e)}")

    # Save all results
    results_file = TEST_DATA_DIR / "affinity_network_results.json"
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nAll results saved to {results_file}")

    # Print summary
    print("\nSummary of Results:")
    for result in all_results:
        valid_str = "VALID" if result["is_valid"] else "INVALID"
        print(
            f"{result['period']} (min_affinity={result['min_affinity']}, max_nodes={result['max_nodes']}): "
            + f"{result['num_nodes']} nodes, {result['num_edges']} edges - {valid_str}"
        )


if __name__ == "__main__":
    main()
