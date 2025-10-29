"""
Tests for the affinity graph callback function.

These tests verify that the update_file_affinity_graph callback function works correctly
with mock commit data and handles the case when no repository path is provided.

Instead of relying on an external repository, these tests use controlled test data
loaded from JSON files in the test_data directory. This ensures that the tests
produce consistent results regardless of the repository they're run against.
"""

# Import from tests package to set up path
from tests import setup_path

setup_path()  # This ensures we can import modules from the project root
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import plotly.graph_objects as go
import pytest
from dash import Dash

app = Dash(__name__, suppress_callback_exceptions=True)

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
        return []

    with open(filepath) as f:
        commits = json.load(f)

    print(f"Loaded {len(commits)} commits from {filepath}")
    return [create_mock_commit(commit) for commit in commits]


# Test the callback with mock data
@patch("data.commits_in_period")
def test_callback_with_mock_data(mock_commits_in_period):
    print("Testing callback with mock data...")

    # Load mock commit data
    mock_commits = load_commits_data("last_6_months")
    mock_commits_in_period.return_value = mock_commits

    from pages.affinity_groups import update_file_affinity_graph

    period = "Last 30 days"
    max_nodes = 50
    min_affinity = 0.2

    try:
        result = update_file_affinity_graph(period, max_nodes, min_affinity)
        print("Callback succeeded with mock data.")
        print(f"Result type: {type(result)}")

        # The callback now returns a tuple: (figure, graph_data)
        if isinstance(result, tuple):
            figure, graph_data = result
            print(f"Returned tuple with figure and graph_data")
            print(f"Graph data keys: {graph_data.keys() if graph_data else 'None'}")
        else:
            figure = result
            print("Returned single figure (legacy)")

        print(f"Figure type: {type(figure)}")
        print(f"Is it a Plotly figure? {isinstance(figure, go.Figure)}")
        assert isinstance(figure, go.Figure)

        # Check if the figure contains data traces
        if hasattr(figure, "data"):
            print(f"Figure contains {len(figure.data)} data traces")

            # Count node and edge traces
            node_traces = [trace for trace in figure.data if trace.mode == "markers"]
            edge_traces = [trace for trace in figure.data if trace.mode == "lines"]

            print(f"Node traces: {len(node_traces)}")
            print(f"Edge traces: {len(edge_traces)}")

            # Verify that the figure has at least some nodes and edges
            assert len(node_traces) > 0, "Figure should have at least one node trace"
            assert len(edge_traces) > 0, "Figure should have at least one edge trace"
    except Exception as e:
        print(f"Callback failed with mock data: {str(e)}")
        pytest.fail(f"Test failed with exception: {str(e)}")


# Test the callback without repository path
@patch("data.commits_in_period")
def test_callback_without_repo_path(mock_commits_in_period):
    print("\nTesting callback without repository path...")

    # Mock the commits_in_period function to raise the expected error
    mock_commits_in_period.side_effect = ValueError(
        "No repository path provided. Please run the application with a repository path as a command-line argument."
    )

    # Force reload of modules to ensure sys.argv is used
    for module in list(sys.modules.keys()):
        if module in ["date_utils", "data", "pages.affinity_groups"]:
            del sys.modules[module]

    sys.argv = ["app.py"]  # No repository path

    from pages.affinity_groups import update_file_affinity_graph

    period = "Last 30 days"
    max_nodes = 50
    min_affinity = 0.2

    try:
        result = update_file_affinity_graph(period, max_nodes, min_affinity)
        print("Callback succeeded without repository path.")
        print(f"Result type: {type(result)}")

        # The callback now returns a tuple: (figure, graph_data)
        if isinstance(result, tuple):
            figure, graph_data = result
            print(f"Returned tuple with figure and graph_data")
        else:
            figure = result
            print("Returned single figure (legacy)")

        print(f"Figure type: {type(figure)}")
        print(f"Is it a Plotly figure? {isinstance(figure, go.Figure)}")

        assert isinstance(figure, go.Figure)

        # Check if the figure contains an error message
        if (
            hasattr(figure, "layout")
            and hasattr(figure.layout, "annotations")
            and figure.layout.annotations
        ):
            message = figure.layout.annotations[0].text
            print(f"Figure contains annotation: {message}")
            assert (
                "No repository path provided" in message
            ), "Figure should contain message about missing repository path"

    except Exception as e:
        print(f"Callback failed without repository path: {str(e)}")
        pytest.fail(f"Test failed with exception: {str(e)}")


if __name__ == "__main__":
    test_callback_with_mock_data()
    test_callback_without_repo_path()
