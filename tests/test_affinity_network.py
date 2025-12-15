"""
Test script for diagnosing issues with the file affinity network visualization.

This script loads git commit data from a repository, processes it through the
create_file_affinity_network function, and provides detailed diagnostics about
the resulting graph.
"""

from tests import setup_path

setup_path()

import json
import os
import sys
from datetime import datetime
<<<<<<< HEAD
from itertools import combinations

import networkx as nx
import plotly.express as px
import plotly.graph_objects as go
=======
from pathlib import Path

>>>>>>> 70ef25b (refactor: bring everything within complexity bounds, and eliminate test order dependencies)
from git import Repo

from tests.conftest import TEST_DATA_DIR, create_mock_commit, load_commits_json
from utils import date_utils
from visualization.network_graph import (
    create_file_affinity_network,
    create_network_visualization,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


TEST_PERIODS = ["Last 6 Months", "Last 1 Year", "Last 5 Years"]


def ensure_test_data_dir():
    """Create the test data directory if it doesn't exist."""
    TEST_DATA_DIR.mkdir(exist_ok=True)


def get_repository_path():
    """Get the repository path from command line or use current directory."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    return os.getcwd()


def get_commits_for_period(repo_path, period):
    """
    Get commits for the specified time period.

    Args:
        repo_path: Path to the git repository
        period: Time period string (e.g., "Last 6 Months")

    Returns:
        List of commit objects
    """
    repo = Repo(repo_path)
    (begin, end) = date_utils.calculate_date_range(period)
    commits = []
    for commit in repo.iter_commits():
        commit_date = datetime.fromtimestamp(commit.committed_date).astimezone()
        if begin <= commit_date <= end:
            commits.append(commit)
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
    filename = f"commits_{period.replace(' ', '_').lower()}.json"
    filepath = TEST_DATA_DIR / filename
    with open(filepath, "w") as f:
        json.dump(simplified_commits, f, indent=2)
    return filepath


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
    if isinstance(commits[0], dict):
        mock_commits = [create_mock_commit(commit) for commit in commits]
        commits = mock_commits
    files_in_commits = set()
    for commit in commits:
        files_in_commit = commit.stats.files.keys()
        files_in_commits.update(files_in_commit)
    start_time = datetime.now()
    (G, communities, _stats) = create_file_affinity_network(
        commits, min_affinity=min_affinity, max_nodes=max_nodes
    )
    end_time = datetime.now()
    num_nodes = len(G.nodes())
    num_edges = len(G.edges())
    num_communities = len(communities)
    is_valid = num_nodes > 0 and num_edges > 0
    if num_nodes > 0:
        degrees = [degree for (_, degree) in G.degree()]
        avg_degree = sum(degrees) / len(degrees) if degrees else 0
        max_degree = max(degrees) if degrees else 0
        min_degree = min(degrees) if degrees else 0
    if num_edges > 0:
        weights = [data["weight"] for (_, _, data) in G.edges(data=True)]
        avg_weight = sum(weights) / len(weights) if weights else 0
        max_weight = max(weights) if weights else 0
        min_weight = min(weights) if weights else 0
    if num_communities > 0:
        community_sizes = [len(community) for community in communities]
        avg_community_size = sum(community_sizes) / len(community_sizes)
        max_community_size = max(community_sizes)
        min_community_size = min(community_sizes)
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
    fig = create_network_visualization(G, communities)
    filename = (
        f"network_{period.replace(' ', '_').lower()}_{min_affinity}_{max_nodes}.html"
    )
    filepath = TEST_DATA_DIR / filename
    fig.write_html(str(filepath))
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
    if isinstance(commits[0], dict):
        mock_commits = [create_mock_commit(commit) for commit in commits]
    else:
        mock_commits = commits
    for min_affinity in [0.1, 0.2, 0.3, 0.4, 0.5]:
        for max_nodes in [20, 50, 100]:
            try:
                (G, communities, _stats) = create_file_affinity_network(
                    mock_commits, min_affinity=min_affinity, max_nodes=max_nodes
                )
                if len(G.nodes()) > 0 and len(G.edges()) > 0:
                    save_visualization(G, communities, period, min_affinity, max_nodes)
                result = analyze_affinity_network(
                    mock_commits, period, min_affinity, max_nodes
                )
                results.append(result)
            except Exception as e:
                pass
    return results


def main():
    """Main function to run the tests."""
    ensure_test_data_dir()
    repo_path = get_repository_path()
    all_results = []
    for period in TEST_PERIODS:
        commits_data = load_commits_json(period)
        if commits_data is None:
            try:
                commits = get_commits_for_period(repo_path, period)
                save_commits_data(commits, period)
            except Exception as e:
                continue
        try:
            result = analyze_affinity_network(commits, period)
            all_results.append(result)
            if isinstance(commits[0], dict):
                mock_commits = [create_mock_commit(commit) for commit in commits]
                (G, communities, _stats) = create_file_affinity_network(mock_commits)
            else:
                (G, communities, _stats) = create_file_affinity_network(commits)
            if len(G.nodes()) > 0:
                save_visualization(G, communities, period, 0.5, 50)
            param_results = try_affinity_network_with_different_parameters(
                commits, period
            )
            all_results.extend(param_results)
        except Exception as e:
            pass
    results_file = TEST_DATA_DIR / "affinity_network_results.json"
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)
    for result in all_results:
        valid_str = "VALID" if result["is_valid"] else "INVALID"


if __name__ == "__main__":
    main()
