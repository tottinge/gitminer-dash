"""
Tests for the group commits table callback.

These tests verify that clicking on a node in the affinity graph
populates the commits table correctly with commits containing
multiple files from the selected group.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from dash import Dash

app = Dash(__name__, suppress_callback_exceptions=True)


@patch("pages.affinity_groups.data.commits_in_period")
def test_get_commits_for_group_files_with_multiple_file_commits(
    mock_commits_in_period,
):
    """Test that commits containing at least 2 group files are returned."""
    from algorithms.commit_filter import get_commits_for_group_files

    # Mock commits
    mock_commit1 = Mock()
    mock_commit1.hexsha = "abc123def456"
    mock_commit1.committed_datetime = datetime(2024, 1, 15, 10, 30)
    mock_commit1.message = "feat: update main and utils"
    mock_commit1.parents = [Mock()]

    # Mock diff to show both files were modified
    diff_item1 = Mock()
    diff_item1.a_path = "src/main.py"
    diff_item2 = Mock()
    diff_item2.a_path = "src/utils.py"
    mock_commit1.diff.return_value = [diff_item1, diff_item2]

    # Mock commit with only one file
    mock_commit2 = Mock()
    mock_commit2.hexsha = "xyz789ghi012"
    mock_commit2.committed_datetime = datetime(2024, 1, 16, 14, 20)
    mock_commit2.message = "fix: update helper"
    mock_commit2.parents = [Mock()]

    diff_item3 = Mock()
    diff_item3.a_path = "src/helper.py"
    mock_commit2.diff.return_value = [diff_item3]

    commits = [mock_commit1, mock_commit2]
    group_files = ["src/main.py", "src/utils.py", "src/helper.py"]

    result = get_commits_for_group_files(commits, group_files)

    # Only the first commit should be returned (has 2+ files)
    assert len(result) == 1
    assert result[0]["hash"] == "abc123d"
    assert result[0]["timestamp"] == "2024-01-15 10:30"
    assert result[0]["message"] == "feat: update main and utils"
    assert "src/main.py" in result[0]["group_files"]
    assert "src/utils.py" in result[0]["group_files"]


@patch("pages.affinity_groups.data.commits_in_period")
def test_get_commits_for_group_files_with_no_matching_commits(
    mock_commits_in_period,
):
    """Test that no commits are returned when no commits have 2+ group files."""
    from algorithms.commit_filter import get_commits_for_group_files

    mock_commit = Mock()
    mock_commit.hexsha = "abc123"
    mock_commit.committed_datetime = datetime(2024, 1, 15, 10, 30)
    mock_commit.message = "feat: update single file"
    mock_commit.parents = [Mock()]

    diff_item = Mock()
    diff_item.a_path = "src/other.py"
    mock_commit.diff.return_value = [diff_item]

    commits = [mock_commit]
    group_files = ["src/main.py", "src/utils.py"]

    result = get_commits_for_group_files(commits, group_files)

    assert len(result) == 0


@patch("pages.affinity_groups.get_commits_for_group_files")
@patch("pages.affinity_groups.date_utils.parse_date_range_from_store")
def test_update_node_details_table_with_valid_click(
    mock_parse, mock_get_commits
):
    """Test that clicking a node returns commits for that group."""
    from pages.affinity_groups import update_node_details_table

    click_data = {
        "points": [
            {"text": "File: src/main.py<br>Commits: 10<br>Connections: 3"}
        ]
    }
    graph_data = {
        "nodes": {
            "src/main.py": {
                "commit_count": 10,
                "degree": 3,
                "community": 0,
                "connected_communities": [0],
            },
            "src/utils.py": {
                "commit_count": 5,
                "degree": 2,
                "community": 0,
                "connected_communities": [0],
            },
        },
        "communities": {0: ["src/main.py", "src/utils.py"]},
    }
    date_range_data = {
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "preset": "custom",
    }

    # Mock dependencies
    mock_commits = [
        {
            "hash": "abc123d",
            "timestamp": "2024-01-15 10:30",
            "message": "feat: update files",
            "group_files": "src/main.py, src/utils.py",
        }
    ]

    mock_parse.return_value = (datetime(2024, 1, 1), datetime(2024, 1, 31))
    mock_get_commits.return_value = mock_commits

    result = update_node_details_table(click_data, graph_data, date_range_data)

    assert len(result) == 1
    assert result[0]["hash"] == "abc123d"
    assert result[0]["timestamp"] == "2024-01-15 10:30"


def test_update_node_details_table_with_no_click():
    """Test that no data is returned when nothing is clicked."""
    from pages.affinity_groups import update_node_details_table

    click_data = None
    graph_data = {"nodes": {}, "communities": {}}
    date_range_data = {}

    result = update_node_details_table(click_data, graph_data, date_range_data)

    assert result == []


def test_update_node_details_table_with_invalid_node():
    """Test handling of clicks on nodes not in the graph data."""
    from pages.affinity_groups import update_node_details_table

    click_data = {
        "points": [
            {"text": "File: nonexistent.py<br>Commits: 0<br>Connections: 0"}
        ]
    }
    graph_data = {
        "nodes": {
            "src/main.py": {
                "commit_count": 10,
                "degree": 3,
                "community": 0,
                "connected_communities": [0],
            }
        },
        "communities": {0: ["src/main.py"]},
    }
    date_range_data = {}

    result = update_node_details_table(click_data, graph_data, date_range_data)

    assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
