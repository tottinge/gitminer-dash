"""
Tests for the affinity graph callback function.

These tests verify that the update_file_affinity_graph callback function works correctly
with mock commit data and handles the case when no repository path is provided.

Instead of relying on an external repository, these tests use controlled test data
loaded from JSON files in the test_data directory. This ensures that the tests
produce consistent results regardless of the repository they're run against.
"""

from tests import setup_path

setup_path()
import sys
from unittest.mock import patch
import plotly.graph_objects as go
import pytest
from dash import Dash

# Pytest automatically loads conftest.py, so load_commits_data is available
from tests.conftest import load_commits_data

app = Dash(__name__, suppress_callback_exceptions=True)


@patch("data.commits_in_period")
def test_callback_with_mock_data(mock_commits_in_period):
    mock_commits = load_commits_data("last_6_months")
    mock_commits_in_period.return_value = mock_commits
    from pages.affinity_groups import update_file_affinity_graph

    period = "Last 30 days"
    max_nodes = 50
    min_affinity = 0.2
    try:
        result = update_file_affinity_graph(period, max_nodes, min_affinity)
        if isinstance(result, tuple):
            (figure, graph_data) = result
        else:
            figure = result
        assert isinstance(figure, go.Figure)
        if hasattr(figure, "data"):
            node_traces = [trace for trace in figure.data if trace.mode == "markers"]
            edge_traces = [trace for trace in figure.data if trace.mode == "lines"]
            assert len(node_traces) > 0, "Figure should have at least one node trace"
            assert len(edge_traces) > 0, "Figure should have at least one edge trace"
    except Exception as e:
        pytest.fail(f"Test failed with exception: {str(e)}")


@patch("data.commits_in_period")
def test_callback_without_repo_path(mock_commits_in_period):
    mock_commits_in_period.side_effect = ValueError(
        "No repository path provided. Please run the application with a repository path as a command-line argument."
    )
    for module in list(sys.modules.keys()):
        if module in ["date_utils", "data", "pages.affinity_groups"]:
            del sys.modules[module]
    sys.argv = ["app.py"]
    from pages.affinity_groups import update_file_affinity_graph

    period = "Last 30 days"
    max_nodes = 50
    min_affinity = 0.2
    try:
        result = update_file_affinity_graph(period, max_nodes, min_affinity)
        if isinstance(result, tuple):
            (figure, graph_data) = result
        else:
            figure = result
        assert isinstance(figure, go.Figure)
        if (
            hasattr(figure, "layout")
            and hasattr(figure.layout, "annotations")
            and figure.layout.annotations
        ):
            message = figure.layout.annotations[0].text
            assert (
                "No repository path provided" in message
            ), "Figure should contain message about missing repository path"
    except Exception as e:
        pytest.fail(f"Test failed with exception: {str(e)}")


if __name__ == "__main__":
    test_callback_with_mock_data()
    test_callback_without_repo_path()
