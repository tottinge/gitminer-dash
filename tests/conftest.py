"""
Shared test fixtures and utilities for the test suite.

This module provides common fixtures and helper functions used across
multiple test files, reducing code duplication.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import pytest
from dash import Dash

# Test data directory
TEST_DATA_DIR = Path(os.path.join(os.path.dirname(__file__), "test_data"))


class MockCommit:
    """Mock commit object for testing."""

    def __init__(self, data):
        self.hexsha = data["hash"]
        self.message = data["message"]
        self.committed_date = datetime.fromisoformat(data["date"]).timestamp()
        self.committed_datetime = datetime.fromisoformat(data["date"])

        class MockStats:
            def __init__(self, files):
                self.files = {file: {"insertions": 1, "deletions": 1} for file in files}

        self.stats = MockStats(data["files"])


def create_mock_commit(commit_data):
    """
    Create a mock commit object from simplified commit data.

    Args:
        commit_data: Dictionary with commit data

    Returns:
        A mock commit object with the necessary attributes
    """
    return MockCommit(commit_data)


def load_commits_json(period):
    """
    Load raw commit data from a JSON file.

    Args:
        period: Time period string

    Returns:
        List of commit dictionaries, or None if file doesn't exist
    """
    filename = f"commits_{period.replace(' ', '_').lower()}.json"
    filepath = TEST_DATA_DIR / filename
    if not filepath.exists():
        return None
    with open(filepath) as f:
        return json.load(f)


def load_commits_data(period):
    """
    Load commit data from a file and convert to mock commits.

    Args:
        period: Time period string

    Returns:
        List of mock commit objects (empty list if file doesn't exist)
    """
    commits_json = load_commits_json(period)
    if commits_json is None:
        return []
    return [create_mock_commit(commit) for commit in commits_json]


@pytest.fixture
def dash_app():
    """Create a Dash app instance for testing."""
    return Dash(__name__, suppress_callback_exceptions=True)


@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return TEST_DATA_DIR


@pytest.fixture
def mock_commit_factory():
    """Factory fixture for creating mock commits."""
    return create_mock_commit


@pytest.fixture
def commits_loader():
    """Factory fixture for loading commit data."""
    return load_commits_data
