#!/usr/bin/env python3
"""
Test file for the diff_analysis module.

This file contains tests for the get_diffs_in_period function,
specifically testing edge cases like empty data.
"""

# Import from tests package to set up path
from tests import setup_path
setup_path()  # This ensures we can import modules from the project root

import os
import sys
import pytest
from unittest.mock import MagicMock
from datetime import datetime
from pandas import DataFrame

# Import project modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from algorithms.diff_analysis import get_diffs_in_period


def test_dataframe_initialized_with_correct_columns_when_empty():
    """Test that DataFrame is initialized with correct columns even when the commits list is empty."""
    # Arrange: Empty commits list
    commits_data = []
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 31)
    
    # Act: Call get_diffs_in_period with empty commits
    result = get_diffs_in_period(commits_data, start, end)
    
    # Assert: Verify that the DataFrame has the correct columns
    assert isinstance(result, DataFrame)
    assert list(result.columns) == ["date", "kind", "count"]
    
    # Assert: Verify that the DataFrame is empty
    assert len(result) == 0
    assert result.empty


def test_dataframe_with_single_commit():
    """Test that DataFrame is correctly populated with a single commit."""
    # Arrange: Create a mock commit
    mock_commit = MagicMock()
    mock_commit.committed_datetime.date.return_value = datetime(2024, 1, 15).date()
    mock_commit.stats.total = {"insertions": 10, "deletions": 5}
    
    commits_data = [mock_commit]
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 31)
    
    # Act: Call get_diffs_in_period
    result = get_diffs_in_period(commits_data, start, end)
    
    # Assert: Verify the DataFrame structure
    assert isinstance(result, DataFrame)
    assert list(result.columns) == ["date", "kind", "count"]
    
    # Assert: Verify the data
    assert len(result) == 3  # Should have 3 rows: possible mods, net inserts, net deletes
    
    # Check the values
    kinds = result['kind'].tolist()
    counts = result['count'].tolist()
    
    assert "possible mods" in kinds
    assert "net inserts" in kinds
    assert "net deletes" in kinds
    
    # Find the count for each kind
    mods_count = result[result['kind'] == 'possible mods']['count'].iloc[0]
    inserts_count = result[result['kind'] == 'net inserts']['count'].iloc[0]
    deletes_count = result[result['kind'] == 'net deletes']['count'].iloc[0]
    
    assert mods_count == 5  # min(10, 5)
    assert inserts_count == 5  # 10 - 5
    assert deletes_count == 0  # 5 - 5


def test_dataframe_with_multiple_commits_same_day():
    """Test that DataFrame correctly aggregates multiple commits on the same day."""
    # Arrange: Create multiple mock commits on the same day
    mock_commit1 = MagicMock()
    mock_commit1.committed_datetime.date.return_value = datetime(2024, 1, 15).date()
    mock_commit1.stats.total = {"insertions": 10, "deletions": 5}
    
    mock_commit2 = MagicMock()
    mock_commit2.committed_datetime.date.return_value = datetime(2024, 1, 15).date()
    mock_commit2.stats.total = {"insertions": 20, "deletions": 15}
    
    commits_data = [mock_commit1, mock_commit2]
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 31)
    
    # Act: Call get_diffs_in_period
    result = get_diffs_in_period(commits_data, start, end)
    
    # Assert: Verify the DataFrame structure
    assert isinstance(result, DataFrame)
    assert list(result.columns) == ["date", "kind", "count"]
    
    # Assert: Verify aggregation
    assert len(result) == 3  # Should have 3 rows for the same day
    
    # Find the count for each kind
    mods_count = result[result['kind'] == 'possible mods']['count'].iloc[0]
    inserts_count = result[result['kind'] == 'net inserts']['count'].iloc[0]
    deletes_count = result[result['kind'] == 'net deletes']['count'].iloc[0]
    
    # First commit: min(10, 5) = 5, net inserts = 5, net deletes = 0
    # Second commit: min(20, 15) = 15, net inserts = 5, net deletes = 0
    # Total: mods = 20, inserts = 10, deletes = 0
    assert mods_count == 20
    assert inserts_count == 10
    assert deletes_count == 0


def test_dataframe_with_commits_different_days():
    """Test that DataFrame correctly handles commits on different days."""
    # Arrange: Create mock commits on different days
    mock_commit1 = MagicMock()
    mock_commit1.committed_datetime.date.return_value = datetime(2024, 1, 15).date()
    mock_commit1.stats.total = {"insertions": 10, "deletions": 5}
    
    mock_commit2 = MagicMock()
    mock_commit2.committed_datetime.date.return_value = datetime(2024, 1, 16).date()
    mock_commit2.stats.total = {"insertions": 20, "deletions": 25}
    
    commits_data = [mock_commit1, mock_commit2]
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 31)
    
    # Act: Call get_diffs_in_period
    result = get_diffs_in_period(commits_data, start, end)
    
    # Assert: Verify the DataFrame structure
    assert isinstance(result, DataFrame)
    assert list(result.columns) == ["date", "kind", "count"]
    
    # Assert: Verify we have data for both days
    assert len(result) == 6  # 3 rows per day
    
    # Check dates
    dates = result['date'].unique()
    assert len(dates) == 2
    assert datetime(2024, 1, 15).date() in dates
    assert datetime(2024, 1, 16).date() in dates


if __name__ == "__main__":
    # Run the tests
    pytest.main(["-v", __file__])
