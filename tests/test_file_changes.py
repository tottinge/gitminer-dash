#!/usr/bin/env python3
"""
Test file for the file_changes module.

This file contains tests for the file_changes_over_period and files_changes_over_period
functions in the algorithms/file_changes.py module.
"""


# Import from tests package to set up path
from tests import setup_path
setup_path()  # This ensures we can import modules from the project root
import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from pathlib import Path

# Import project modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from algorithms.file_changes import file_changes_over_period, files_changes_over_period, FileChangeStats


@pytest.fixture
def mock_repo():
    """Create a mock Git repository for testing."""
    mock_repo = MagicMock()
    
    # Create mock commits
    mock_commits = []
    for i in range(5):
        mock_commit = MagicMock()
        mock_commit.stats.files = {
            'file1.py': {'lines': 10},
            'file2.py': {'lines': 20},
            'file3.py': {'lines': 30}
        }
        mock_commits.append(mock_commit)
    
    # Set up the mock repo to return the mock commits
    mock_repo.iter_commits.return_value = mock_commits
    
    # Set up mock tree entries for file sizes
    mock_tree_entry1 = MagicMock()
    mock_tree_entry1.size = 1000
    
    mock_tree_entry2 = MagicMock()
    mock_tree_entry2.size = 1200
    
    # Set up mock trees for the first and last commits
    mock_tree1 = MagicMock()
    mock_tree1.__getitem__.return_value = mock_tree_entry1
    
    mock_tree2 = MagicMock()
    mock_tree2.__getitem__.return_value = mock_tree_entry2
    
    # Set up mock commits with the mock trees
    mock_repo.commit.side_effect = lambda commit: MagicMock(tree=mock_tree1 if commit == mock_commits[0] else mock_tree2)
    
    return mock_repo


def test_file_changes_over_period(mock_repo):
    """Test the file_changes_over_period function with a mock repository."""
    # Call the function with the mock repository
    commits, avg_changes, total_change, percent_change = file_changes_over_period(
        'file1.py',
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
        repo=mock_repo
    )
    
    # Verify the results
    assert commits == 5
    assert avg_changes == 10.0
    assert total_change == 200
    assert percent_change == 20.0
    
    # Verify the mock was called correctly
    mock_repo.iter_commits.assert_called_once()
    assert mock_repo.iter_commits.call_args[1]['paths'] == 'file1.py'


def test_file_changes_over_period_no_commits(mock_repo):
    """Test the file_changes_over_period function with no commits."""
    # Set up the mock to return no commits
    mock_repo.iter_commits.return_value = []
    
    # Call the function with the mock repository
    commits, avg_changes, total_change, percent_change = file_changes_over_period(
        'nonexistent.py',
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
        repo=mock_repo
    )
    
    # Verify the results
    assert commits == 0
    assert avg_changes == 0.0
    assert total_change == 0
    assert percent_change == 0.0


def test_files_changes_over_period(mock_repo):
    """Test the files_changes_over_period function with a mock repository."""
    # Call the function with the mock repository
    results = files_changes_over_period(
        ['file1.py', 'file2.py', 'file3.py'],
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
        repo=mock_repo
    )
    
    # Verify the results
    assert len(results) == 3
    assert isinstance(results['file1.py'], FileChangeStats)
    assert results['file1.py'].commits == 5
    assert results['file1.py'].avg_changes == 10.0
    assert results['file1.py'].total_change == 200
    assert results['file1.py'].percent_change == 20.0
    
    assert results['file2.py'].avg_changes == 20.0
    assert results['file3.py'].avg_changes == 30.0


def test_files_changes_over_period_with_error(mock_repo):
    """Test the files_changes_over_period function with a file that causes an error."""
    # Set up the mock to raise an exception for a specific file
    def mock_iter_commits(**kwargs):
        if kwargs['paths'] == 'error.py':
            raise ValueError("File not found")
        return mock_repo.iter_commits.return_value
    
    mock_repo.iter_commits.side_effect = mock_iter_commits
    
    # Call the function with the mock repository
    results = files_changes_over_period(
        ['file1.py', 'error.py', 'file3.py'],
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
        repo=mock_repo
    )
    
    # Verify the results
    assert len(results) == 3
    assert results['file1.py'].commits == 5
    assert results['error.py'].commits == 0  # Should have zeros for the error file
    assert results['file3.py'].commits == 5


def test_files_changes_over_period_empty_list(mock_repo):
    """Test the files_changes_over_period function with an empty list of files."""
    # Call the function with an empty list
    results = files_changes_over_period(
        [],
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
        repo=mock_repo
    )
    
    # Verify the results
    assert len(results) == 0


if __name__ == "__main__":
    # Run the tests
    pytest.main(["-v", __file__])