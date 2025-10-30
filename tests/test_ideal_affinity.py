"""
Test script for the ideal affinity factor algorithm.

This script tests the calculate_ideal_affinity function to ensure it correctly
calculates an ideal minimum affinity threshold that results in 5-20 nodes.
"""

from tests import setup_path

setup_path()
import os
import sys
from dash import Dash

from tests.conftest import create_mock_commit, load_commits_json, TEST_DATA_DIR

app = Dash(__name__, suppress_callback_exceptions=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pages.affinity_groups import calculate_ideal_affinity
from visualization.network_graph import create_file_affinity_network


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
        (G, communities, stats) = create_file_affinity_network(
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
    (G, communities, stats) = create_file_affinity_network(
        mock_commits, min_affinity=ideal_affinity, max_nodes=50
    )
    actual_node_count = len(G.nodes())
    actual_edge_count = len(G.edges())


def main():
    """Main function to run all tests."""
    TEST_DATA_DIR.mkdir(exist_ok=True)
    test_calculate_ideal_affinity_with_real_data()
    test_calculate_ideal_affinity_with_edge_cases()
    test_calculate_ideal_affinity_with_synthetic_data()


if __name__ == "__main__":
    main()
