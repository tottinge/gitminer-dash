#!/usr/bin/env python3
"""
Test script for demonstrating the improved affinity network functionality.

This script compares the original and improved affinity network functions
using real repository data and shows the benefits of the improvements.
"""

# Import from tests package to set up path
from tests import setup_path

setup_path()  # This ensures we can import modules from the project root
import os
import sys
import json
from datetime import datetime
from pathlib import Path
import networkx as nx
import plotly.graph_objects as go
from git import Repo

# Import project modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import date_utils
from improved_affinity_network import (
    create_improved_file_affinity_network,
    create_improved_network_visualization,
)

# Import original functions (copied to avoid Dash initialization issues)
from collections import defaultdict
from itertools import combinations


def create_file_affinity_network(commits, min_affinity=0.5, max_nodes=50):
    """Original affinity network function (copied from affinity_groups.py)."""
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


# Constants
TEST_DATA_DIR = Path(os.path.join(os.path.dirname(__file__), "test_data"))
TEST_PERIODS = ["Last 6 Months", "Last 1 Year", "Last 5 Years"]


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

    with open(filepath) as f:
        commits = json.load(f)

    print(f"Loaded {len(commits)} commits from {filepath}")
    return commits


def compare_networks(period, min_affinity_original=0.5, min_affinity_improved=0.2):
    """
    Compare the original and improved affinity network functions.

    Args:
        period: Time period string
        min_affinity_original: Minimum affinity threshold for original function
        min_affinity_improved: Minimum affinity threshold for improved function

    Returns:
        Dictionary with comparison results
    """
    print(f"\nComparing networks for {period}")
    print(
        f"Original min_affinity: {min_affinity_original}, Improved min_affinity: {min_affinity_improved}"
    )

    # Load commit data
    commits_data = load_commits_data(period)
    if not commits_data:
        return None

    # Create mock commits
    mock_commits = [create_mock_commit(commit) for commit in commits_data]

    # Create original network
    start_time = datetime.now()
    G_original, communities_original = create_file_affinity_network(
        mock_commits, min_affinity=min_affinity_original
    )
    original_time = (datetime.now() - start_time).total_seconds()

    # Create improved network
    start_time = datetime.now()
    G_improved, communities_improved, stats = create_improved_file_affinity_network(
        mock_commits, min_affinity=min_affinity_improved
    )
    improved_time = (datetime.now() - start_time).total_seconds()

    # Compare network properties
    comparison = {
        "period": period,
        "original": {
            "min_affinity": min_affinity_original,
            "nodes": len(G_original.nodes()),
            "edges": len(G_original.edges()),
            "communities": len(communities_original),
            "processing_time": original_time,
        },
        "improved": {
            "min_affinity": min_affinity_improved,
            "nodes": len(G_improved.nodes()),
            "edges": len(G_improved.edges()),
            "communities": len(communities_improved),
            "processing_time": improved_time,
            "stats": stats,
        },
    }

    # Print comparison
    print("\nComparison Results:")
    print(
        f"Original Network: {comparison['original']['nodes']} nodes, {comparison['original']['edges']} edges, "
        + f"{comparison['original']['communities']} communities, {comparison['original']['processing_time']:.2f} seconds"
    )
    print(
        f"Improved Network: {comparison['improved']['nodes']} nodes, {comparison['improved']['edges']} edges, "
        + f"{comparison['improved']['communities']} communities, {comparison['improved']['processing_time']:.2f} seconds"
    )

    # Save visualizations
    save_comparison_visualizations(
        G_original, communities_original, G_improved, communities_improved, period
    )

    return comparison


def save_comparison_visualizations(
    G_original, communities_original, G_improved, communities_improved, period
):
    """
    Save visualizations of the original and improved networks for comparison.

    Args:
        G_original: Original NetworkX graph
        communities_original: Original communities
        G_improved: Improved NetworkX graph
        communities_improved: Improved communities
        period: Time period string
    """
    # Create a simple visualization of the original network
    pos_original = nx.spring_layout(G_original, seed=42)
    fig_original = go.Figure()

    # Add edges
    edge_x = []
    edge_y = []
    for edge in G_original.edges():
        x0, y0 = pos_original[edge[0]]
        x1, y1 = pos_original[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    fig_original.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=1, color="#888"),
            hoverinfo="none",
            mode="lines",
        )
    )

    # Add nodes
    node_x = []
    node_y = []
    for node in G_original.nodes():
        x, y = pos_original[node]
        node_x.append(x)
        node_y.append(y)

    fig_original.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers",
            marker=dict(size=10, color="blue"),
            text=list(G_original.nodes()),
            hoverinfo="text",
        )
    )

    fig_original.update_layout(
        title=f"Original Network - {period} (min_affinity=0.5)",
        showlegend=False,
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )

    # Save original visualization
    filename = f"comparison_original_{period.replace(' ', '_').lower()}.html"
    filepath = TEST_DATA_DIR / filename
    fig_original.write_html(str(filepath))
    print(f"Saved original visualization to {filepath}")

    # Create improved visualization
    fig_improved = create_improved_network_visualization(
        G_improved,
        communities_improved,
        title=f"Improved Network - {period} (min_affinity=0.2)",
    )

    # Save improved visualization
    filename = f"comparison_improved_{period.replace(' ', '_').lower()}.html"
    filepath = TEST_DATA_DIR / filename
    fig_improved.write_html(str(filepath))
    print(f"Saved improved visualization to {filepath}")


def main():
    """Main function to run the comparison tests."""
    # Ensure test data directory exists
    TEST_DATA_DIR.mkdir(exist_ok=True)

    all_comparisons = []

    # Compare networks for each test period
    for period in TEST_PERIODS:
        comparison = compare_networks(period)
        if comparison:
            all_comparisons.append(comparison)

    # Save all comparison results
    results_file = TEST_DATA_DIR / "network_comparison_results.json"
    with open(results_file, "w") as f:
        json.dump(all_comparisons, f, indent=2)

    print(f"\nAll comparison results saved to {results_file}")

    # Print summary
    print("\nSummary of Improvements:")
    for comparison in all_comparisons:
        original = comparison["original"]
        improved = comparison["improved"]

        edge_increase = improved["edges"] - original["edges"]
        edge_percent = (
            (edge_increase / original["edges"] * 100)
            if original["edges"] > 0
            else float("inf")
        )

        print(
            f"{comparison['period']}: "
            + f"Edges increased from {original['edges']} to {improved['edges']} "
            + f"({edge_percent:.1f}% increase)"
        )


if __name__ == "__main__":
    main()
