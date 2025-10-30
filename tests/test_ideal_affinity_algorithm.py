"""
Test script for the ideal affinity factor algorithm.

This script tests the calculate_ideal_affinity function to ensure it correctly
calculates an ideal minimum affinity threshold that results in 5-20 nodes.
"""

from tests import setup_path

setup_path()
import os
import sys
import networkx as nx
from collections import defaultdict
from itertools import combinations

from tests.conftest import create_mock_commit, load_commits_json, TEST_DATA_DIR


def calculate_ideal_affinity(commits, target_node_count=15, max_nodes=50):
    """
    Calculate an ideal minimum affinity threshold that will result in approximately
    the target number of connected nodes.

    Args:
        commits: Iterable of commit objects
        target_node_count: Target number of nodes in the final graph (default: 15)
        max_nodes: Maximum number of nodes to consider (default: 50)

    Returns:
        A tuple of (ideal_min_affinity, estimated_node_count, estimated_edge_count)
    """
    if not commits:
        return (0.2, 0, 0)
    if hasattr(commits, "seek") and callable(getattr(commits, "seek")):
        commits.seek(0)
    elif not hasattr(commits, "__len__"):
        commits = list(commits)
    affinities = defaultdict(float)
    for commit in commits:
        files_in_commit = len(commit.stats.files)
        if files_in_commit < 2:
            continue
        for combo in combinations(commit.stats.files, 2):
            ordered_key = tuple(sorted(combo))
            affinities[ordered_key] += 1 / files_in_commit
    file_total_affinity = defaultdict(float)
    for (file1, file2), affinity in affinities.items():
        file_total_affinity[file1] += affinity
        file_total_affinity[file2] += affinity
    top_files = sorted(file_total_affinity.items(), key=lambda x: x[1], reverse=True)[
        :max_nodes
    ]
    top_file_set = {file for (file, _) in top_files}
    relevant_affinities = []
    for (file1, file2), affinity in affinities.items():
        if file1 in top_file_set and file2 in top_file_set:
            relevant_affinities.append(affinity)
    if not relevant_affinities:
        return (0.2, 0, 0)
    sorted_affinities = sorted(relevant_affinities, reverse=True)
    thresholds = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
    best_threshold = 0.2
    best_node_count = 0
    best_edge_count = 0
    for threshold in thresholds:
        edge_count = sum((1 for a in relevant_affinities if a >= threshold))
        connected_nodes = set()
        for (file1, file2), affinity in affinities.items():
            if (
                file1 in top_file_set
                and file2 in top_file_set
                and (affinity >= threshold)
            ):
                connected_nodes.add(file1)
                connected_nodes.add(file2)
        node_count = len(connected_nodes)
        if 5 <= node_count <= 20:
            best_threshold = threshold
            best_node_count = node_count
            best_edge_count = edge_count
            break
        if node_count > 0 and abs(node_count - target_node_count) < abs(
            best_node_count - target_node_count
        ):
            best_threshold = threshold
            best_node_count = node_count
            best_edge_count = edge_count
    return (best_threshold, best_node_count, best_edge_count)


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
        return (nx.Graph(), [])
    affinities = defaultdict(float)
    for commit in commits:
        files_in_commit = len(commit.stats.files)
        if files_in_commit < 2:
            continue
        for combo in combinations(commit.stats.files, 2):
            ordered_key = tuple(sorted(combo))
            affinities[ordered_key] += 1 / files_in_commit
    G = nx.Graph()
    all_files = set()
    for file_pair in affinities.keys():
        all_files.update(file_pair)
    file_total_affinity = defaultdict(float)
    for (file1, file2), affinity in affinities.items():
        file_total_affinity[file1] += affinity
        file_total_affinity[file2] += affinity
    top_files = sorted(file_total_affinity.items(), key=lambda x: x[1], reverse=True)[
        :max_nodes
    ]
    top_file_set = {file for (file, _) in top_files}
    for file in top_file_set:
        G.add_node(file)
    for (file1, file2), affinity in affinities.items():
        if (
            file1 in top_file_set
            and file2 in top_file_set
            and (affinity >= min_affinity)
        ):
            G.add_edge(file1, file2, weight=affinity)
    if len(G.nodes()) > 0:
        communities = nx.community.louvain_communities(G)
        for i, community in enumerate(communities):
            for node in community:
                G.nodes[node]["community"] = i
    else:
        communities = []
    return (G, communities)


def test_calculate_ideal_affinity_with_real_data():
    """Test the calculate_ideal_affinity function with real commit data."""
    test_periods = ["Last 6 Months", "Last 1 Year", "Last 5 Years"]
    for period in test_periods:
        commits_data = load_commits_json(period)
        if not commits_data:
            continue
        mock_commits = [create_mock_commit(commit) for commit in commits_data]
        (ideal_affinity, node_count, edge_count) = calculate_ideal_affinity(
            mock_commits, target_node_count=15, max_nodes=50
        )
        (G, communities) = create_file_affinity_network(
            mock_commits, min_affinity=ideal_affinity, max_nodes=50
        )
        actual_node_count = len(G.nodes())
        actual_edge_count = len(G.edges())


def test_calculate_ideal_affinity_with_edge_cases():
    """Test the calculate_ideal_affinity function with edge cases."""
    (ideal_affinity, node_count, edge_count) = calculate_ideal_affinity(
        [], target_node_count=15, max_nodes=50
    )
    single_commit = [
        {
            "hash": "123456",
            "author": "Test Author",
            "date": "2025-10-23T13:53:00",
            "message": "Test commit",
            "files": ["file1.py", "file2.py", "file3.py"],
        }
    ]
    mock_commits = [create_mock_commit(commit) for commit in single_commit]
    (ideal_affinity, node_count, edge_count) = calculate_ideal_affinity(
        mock_commits, target_node_count=15, max_nodes=50
    )
    no_pairs_commits = [
        {
            "hash": "123456",
            "author": "Test Author",
            "date": "2025-10-23T13:53:00",
            "message": "Test commit 1",
            "files": ["file1.py"],
        },
        {
            "hash": "789012",
            "author": "Test Author",
            "date": "2025-10-23T14:53:00",
            "message": "Test commit 2",
            "files": ["file2.py"],
        },
    ]
    mock_commits = [create_mock_commit(commit) for commit in no_pairs_commits]
    (ideal_affinity, node_count, edge_count) = calculate_ideal_affinity(
        mock_commits, target_node_count=15, max_nodes=50
    )


def test_calculate_ideal_affinity_with_synthetic_data():
    """Test the calculate_ideal_affinity function with synthetic data."""
    synthetic_commits = []
    for i in range(5):
        synthetic_commits.append(
            {
                "hash": f"group1_{i}",
                "author": "Test Author",
                "date": f"2025-10-{23 - i}T13:53:00",
                "message": f"Group 1 commit {i}",
                "files": ["group1_file1.py", "group1_file2.py", "group1_file3.py"],
            }
        )
    for i in range(10):
        files = ["group2_file1.py"]
        if i % 2 == 0:
            files.append("group2_file2.py")
        if i % 3 == 0:
            files.append("group2_file3.py")
        synthetic_commits.append(
            {
                "hash": f"group2_{i}",
                "author": "Test Author",
                "date": f"2025-09-{30 - i}T13:53:00",
                "message": f"Group 2 commit {i}",
                "files": files,
            }
        )
    for i in range(20):
        files = ["group3_file1.py"]
        if i % 10 == 0:
            files.append("group3_file2.py")
        if i % 15 == 0:
            files.append("group3_file3.py")
        synthetic_commits.append(
            {
                "hash": f"group3_{i}",
                "author": "Test Author",
                "date": f"2025-08-{31 - i}T13:53:00",
                "message": f"Group 3 commit {i}",
                "files": files,
            }
        )
    mock_commits = [create_mock_commit(commit) for commit in synthetic_commits]
    (ideal_affinity, node_count, edge_count) = calculate_ideal_affinity(
        mock_commits, target_node_count=15, max_nodes=50
    )
    (G, communities) = create_file_affinity_network(
        mock_commits, min_affinity=ideal_affinity, max_nodes=50
    )
    actual_node_count = len(G.nodes())
    actual_edge_count = len(G.edges())
    assert 5 <= actual_node_count <= 20


def main():
    """Main function to run all tests."""
    TEST_DATA_DIR.mkdir(exist_ok=True)
    test_calculate_ideal_affinity_with_real_data()
    test_calculate_ideal_affinity_with_edge_cases()
    test_calculate_ideal_affinity_with_synthetic_data()


if __name__ == "__main__":
    main()
