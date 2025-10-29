#!/usr/bin/env python3
"""
Test script for the ideal affinity factor algorithm.

This script tests the calculate_ideal_affinity function to ensure it correctly
calculates an ideal minimum affinity threshold that results in 5-20 nodes.
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
from collections import defaultdict
from itertools import combinations
from dash import Dash

# Create a Dash app instance to prevent PageError when importing pages
app = Dash(__name__, suppress_callback_exceptions=True)

# Import project modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Import after Dash app instantiation to avoid PageError
from pages.affinity_groups import calculate_ideal_affinity
from visualization.network_graph import create_file_affinity_network

# Test data directory
TEST_DATA_DIR = Path(os.path.join(os.path.dirname(__file__), "test_data"))


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

    with open(filepath, "r") as f:
        commits = json.load(f)

    print(f"Loaded {len(commits)} commits from {filepath}")
    return commits


def test_calculate_ideal_affinity_with_real_data():
    """Test the calculate_ideal_affinity function with real commit data."""
    print("\nTesting calculate_ideal_affinity with real data...")

    # Test periods
    test_periods = ["Last 6 Months", "Last 1 Year", "Last 5 Years"]

    for period in test_periods:
        # Load commit data
        commits_data = load_commits_data(period)
        if not commits_data:
            print(f"Skipping {period} - no data available")
            continue

        # Create mock commits
        mock_commits = [create_mock_commit(commit) for commit in commits_data]

        # Calculate ideal affinity
        ideal_affinity, node_count, edge_count = calculate_ideal_affinity(
            mock_commits, target_node_count=15, max_nodes=50
        )

        print(f"\nResults for {period}:")
        print(f"Ideal affinity: {ideal_affinity:.2f}")
        print(f"Estimated nodes: {node_count}")
        print(f"Estimated edges: {edge_count}")

        # Verify the node count is within the expected range (5-20)
        if 5 <= node_count <= 20:
            print(f"✓ Node count {node_count} is within the expected range (5-20)")
        else:
            print(f"✗ Node count {node_count} is outside the expected range (5-20)")

        # Verify the result by creating a network with the calculated affinity
        G, communities, stats = create_file_affinity_network(
            mock_commits, min_affinity=ideal_affinity, max_nodes=50
        )

        actual_node_count = len(G.nodes())
        actual_edge_count = len(G.edges())

        print(f"Actual nodes: {actual_node_count}")
        print(f"Actual edges: {actual_edge_count}")

        # Verify the actual node count is within the expected range (5-20)
        if 5 <= actual_node_count <= 20:
            print(
                f"✓ Actual node count {actual_node_count} is within the expected range (5-20)"
            )
        else:
            print(
                f"✗ Actual node count {actual_node_count} is outside the expected range (5-20)"
            )


def test_calculate_ideal_affinity_with_edge_cases():
    """Test the calculate_ideal_affinity function with edge cases."""
    print("\nTesting calculate_ideal_affinity with edge cases...")

    # Test with empty commits
    print("\nTest with empty commits:")
    ideal_affinity, node_count, edge_count = calculate_ideal_affinity(
        [], target_node_count=15, max_nodes=50
    )
    print(f"Ideal affinity: {ideal_affinity:.2f}")
    print(f"Estimated nodes: {node_count}")
    print(f"Estimated edges: {edge_count}")

    # Test with a single commit
    print("\nTest with a single commit:")
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
    ideal_affinity, node_count, edge_count = calculate_ideal_affinity(
        mock_commits, target_node_count=15, max_nodes=50
    )
    print(f"Ideal affinity: {ideal_affinity:.2f}")
    print(f"Estimated nodes: {node_count}")
    print(f"Estimated edges: {edge_count}")

    # Test with commits that have no file pairs
    print("\nTest with commits that have no file pairs:")
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
    ideal_affinity, node_count, edge_count = calculate_ideal_affinity(
        mock_commits, target_node_count=15, max_nodes=50
    )
    print(f"Ideal affinity: {ideal_affinity:.2f}")
    print(f"Estimated nodes: {node_count}")
    print(f"Estimated edges: {edge_count}")


def test_calculate_ideal_affinity_with_synthetic_data():
    """Test the calculate_ideal_affinity function with synthetic data."""
    print("\nTesting calculate_ideal_affinity with synthetic data...")

    # Create synthetic commits with known affinity patterns
    synthetic_commits = []

    # Group 1: Files that always change together (high affinity)
    for i in range(5):
        synthetic_commits.append(
            {
                "hash": f"group1_{i}",
                "author": "Test Author",
                "date": f"2025-10-{23-i}T13:53:00",
                "message": f"Group 1 commit {i}",
                "files": ["group1_file1.py", "group1_file2.py", "group1_file3.py"],
            }
        )

    # Group 2: Files that sometimes change together (medium affinity)
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
                "date": f"2025-09-{30-i}T13:53:00",
                "message": f"Group 2 commit {i}",
                "files": files,
            }
        )

    # Group 3: Files that rarely change together (low affinity)
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
                "date": f"2025-08-{31-i}T13:53:00",
                "message": f"Group 3 commit {i}",
                "files": files,
            }
        )

    # Create mock commits
    mock_commits = [create_mock_commit(commit) for commit in synthetic_commits]

    # Calculate ideal affinity
    ideal_affinity, node_count, edge_count = calculate_ideal_affinity(
        mock_commits, target_node_count=15, max_nodes=50
    )

    print(f"\nResults for synthetic data:")
    print(f"Ideal affinity: {ideal_affinity:.2f}")
    print(f"Estimated nodes: {node_count}")
    print(f"Estimated edges: {edge_count}")

    # Verify the node count is within the expected range (5-20)
    if 5 <= node_count <= 20:
        print(f"✓ Node count {node_count} is within the expected range (5-20)")
    else:
        print(f"✗ Node count {node_count} is outside the expected range (5-20)")

    # Verify the result by creating a network with the calculated affinity
    G, communities, stats = create_file_affinity_network(
        mock_commits, min_affinity=ideal_affinity, max_nodes=50
    )

    actual_node_count = len(G.nodes())
    actual_edge_count = len(G.edges())

    print(f"Actual nodes: {actual_node_count}")
    print(f"Actual edges: {actual_edge_count}")

    # Verify the actual node count is within the expected range (5-20)
    if 5 <= actual_node_count <= 20:
        print(
            f"✓ Actual node count {actual_node_count} is within the expected range (5-20)"
        )
    else:
        print(
            f"✗ Actual node count {actual_node_count} is outside the expected range (5-20)"
        )


def main():
    """Main function to run all tests."""
    # Ensure test data directory exists
    TEST_DATA_DIR.mkdir(exist_ok=True)

    # Run tests
    test_calculate_ideal_affinity_with_real_data()
    test_calculate_ideal_affinity_with_edge_cases()
    test_calculate_ideal_affinity_with_synthetic_data()

    print("\nAll tests completed!")


if __name__ == "__main__":
    main()
