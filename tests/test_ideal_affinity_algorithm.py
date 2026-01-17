"""
Test script for the ideal affinity factor algorithm.

This script tests the calculate_ideal_affinity function to ensure it correctly
calculates an ideal minimum affinity threshold that results in 5-20 nodes.
"""

from tests import setup_path

setup_path()
import os
import sys
from unittest.mock import patch

from algorithms.affinity_analysis import calculate_ideal_affinity
from tests.conftest import TEST_DATA_DIR, create_mock_commit, load_commits_json
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
        (G, communities, _stats) = create_file_affinity_network(
            mock_commits, min_affinity=ideal_affinity, max_nodes=50
        )
        actual_node_count = len(G.nodes())
        actual_edge_count = len(G.edges())


def test_calculate_ideal_affinity_with_edge_cases():
    """Test the calculate_ideal_affinity function with edge cases and defaults."""
    # When no commits are provided, we should get the documented default values.
    ideal_affinity, node_count, edge_count = calculate_ideal_affinity(
        [], target_node_count=15, max_nodes=50
    )
    assert ideal_affinity == 0.2
    assert node_count == 0
    assert edge_count == 0

    # When there are commits but no relevant affinities, we should also fall back
    # to the same default tuple.
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

    with patch(
        "algorithms.affinity_analysis.calculate_affinities", return_value={}
    ), patch(
        "algorithms.affinity_analysis.get_top_files_and_affinities",
        return_value=(set(), []),
    ):
        ideal_affinity, node_count, edge_count = calculate_ideal_affinity(
            mock_commits, target_node_count=15, max_nodes=50
        )

    assert ideal_affinity == 0.2
    assert node_count == 0
    assert edge_count == 0

    # Sanity check: when there *are* affinities, we should not crash. The
    # specific values depend on the real data and are covered in other tests.
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
    assert isinstance(ideal_affinity, float)
    assert isinstance(node_count, int)
    assert isinstance(edge_count, int)


def test_calculate_ideal_affinity_parameter_defaults():
    """Default parameter values should be stable and explicit.

    Rather than introspecting ``__defaults__`` directly (which can be affected by
    wrappers used by tooling such as mutation-test runners), verify behaviour:
    calling the function with no explicit tuning arguments should be equivalent
    to calling it with the documented defaults.
    """
    base_commit = {
        "hash": "123456",
        "author": "Test Author",
        "date": "2025-10-23T13:53:00",
        "message": "Test commit",
        "files": ["file1.py", "file2.py"],
    }
    mock_commits = [create_mock_commit(base_commit)]

    # Patch heavy internals so we can focus purely on how the parameters are
    # propagated into the implementation.
    with patch(
        "algorithms.affinity_analysis.calculate_affinities", return_value={}
    ), patch(
        "algorithms.affinity_analysis.get_top_files_and_affinities",
        return_value=(set(), []),
    ) as mock_get:
        # First call relies on the function's default values.
        calculate_ideal_affinity(mock_commits)
        # Second call supplies the documented defaults explicitly.
        calculate_ideal_affinity(
            mock_commits, target_node_count=15, max_nodes=50
        )

    # ``get_top_files_and_affinities`` should have been called twice with the
    # same ``max_nodes`` value, and that value should be 50.
    assert mock_get.call_count == 2
    first_call_args = mock_get.call_args_list[0][0]
    second_call_args = mock_get.call_args_list[1][0]
    assert first_call_args[2] == second_call_args[2] == 50


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
                "files": [
                    "group1_file1.py",
                    "group1_file2.py",
                    "group1_file3.py",
                ],
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
    (G, communities, _stats) = create_file_affinity_network(
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
