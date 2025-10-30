"""
Test file for the most_committed page module.

This file contains tests for the populate_graph callback function,
specifically testing edge cases like empty data.
"""

from tests import setup_path

setup_path()
import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from pandas import DataFrame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def populate_graph():
    """Import and return the populate_graph function with proper mocking."""
    with patch("dash.register_page"):
        from pages.most_committed import populate_graph as pg

        return pg


@pytest.fixture
def mock_store_data():
    """Create mock store data for testing."""
    return {
        "period": "30",
        "begin": "2024-01-01T00:00:00",
        "end": "2024-01-31T23:59:59",
    }


@patch("pages.most_committed.data.commits_in_period")
@patch("pages.most_committed.data.get_repo")
@patch("pages.most_committed.calculate_file_commit_frequency")
def test_no_data_message_displayed(
    mock_calc, mock_get_repo, mock_commits, mock_store_data, populate_graph
):
    """Test that graph displays 'No data in selected period' message when no commit data is available."""
    mock_commits.return_value = []
    mock_get_repo.return_value = MagicMock()
    mock_calc.return_value = []
    (figure, table_data, style) = populate_graph(mock_store_data)
    assert len(figure.layout.annotations) == 1
    assert figure.layout.annotations[0].text == "No data in selected period"
    assert figure.layout.annotations[0].xref == "paper"
    assert figure.layout.annotations[0].yref == "paper"
    assert figure.layout.annotations[0].x == 0.5
    assert figure.layout.annotations[0].y == 0.5
    assert table_data == []
    assert style == {"display": "block"}


@patch("pages.most_committed.data.commits_in_period")
@patch("pages.most_committed.data.get_repo")
@patch("pages.most_committed.calculate_file_commit_frequency")
def test_dataframe_initialized_with_correct_columns_when_empty(
    mock_calc, mock_get_repo, mock_commits, mock_store_data, populate_graph
):
    """Test that DataFrame is initialized with correct columns even when the usages list is empty."""
    mock_commits.return_value = []
    mock_get_repo.return_value = MagicMock()
    mock_calc.return_value = []
    (figure, table_data, style) = populate_graph(mock_store_data)
    assert isinstance(table_data, list)
    assert len(table_data) == 0


@patch("pages.most_committed.data.commits_in_period")
@patch("pages.most_committed.data.get_repo")
@patch("pages.most_committed.calculate_file_commit_frequency")
def test_dataframe_columns_with_valid_data(
    mock_calc, mock_get_repo, mock_commits, mock_store_data, populate_graph
):
    """Test that DataFrame contains correct columns when data is present."""
    mock_commits.return_value = [MagicMock()]
    mock_get_repo.return_value = MagicMock()
    mock_calc.return_value = [
        {
            "filename": "test.py",
            "count": 10,
            "avg_changes": 5.5,
            "total_change": 55,
            "percent_change": 10.0,
        }
    ]
    (figure, table_data, style) = populate_graph(mock_store_data)
    assert len(table_data) == 1
    assert "filename" in table_data[0]
    assert "count" in table_data[0]
    assert "avg_changes" in table_data[0]
    assert "total_change" in table_data[0]
    assert "percent_change" in table_data[0]
    assert table_data[0]["filename"] == "test.py"
    assert table_data[0]["count"] == 10
    assert table_data[0]["avg_changes"] == 5.5


if __name__ == "__main__":
    pytest.main(["-v", __file__])
