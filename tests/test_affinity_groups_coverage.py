"""
Additional tests for pages/affinity_groups.py to improve coverage.

These tests focus on error handling, edge cases, and the caching behavior
that are not covered by existing tests.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import plotly.graph_objects as go
import pytest
from dash import Dash

app = Dash(__name__, suppress_callback_exceptions=True)


@patch("data.commits_in_period")
@patch("pages.affinity_groups.date_utils.parse_date_range_from_store")
def test_callback_with_invalid_date_range(mock_parse, mock_commits):
    """Test that invalid date range is handled gracefully."""
    from pages.affinity_groups import update_file_affinity_graph

    mock_parse.side_effect = ValueError("Invalid date format")

    store_data = {"invalid": "data"}
    max_nodes = 50
    min_affinity = 0.2

    figure, graph_data = update_file_affinity_graph(store_data, max_nodes, min_affinity)

    assert isinstance(figure, go.Figure)
    assert graph_data == {}
    assert hasattr(figure, "layout")
    if hasattr(figure.layout, "annotations") and figure.layout.annotations:
        message = figure.layout.annotations[0].text
        assert "Invalid date range" in message or "Invalid date format" in message


@patch("pages.affinity_groups.create_file_affinity_network")
@patch("data.commits_in_period")
@patch("pages.affinity_groups.date_utils.parse_date_range_from_store")
def test_callback_with_network_creation_error(mock_parse, mock_commits, mock_network):
    """Test that errors during network creation are handled."""
    from pages.affinity_groups import update_file_affinity_graph

    mock_parse.return_value = (datetime(2024, 1, 1), datetime(2024, 1, 31))
    mock_commits.return_value = []
    mock_network.side_effect = RuntimeError("Network creation failed")

    store_data = {"start_date": "2024-01-01", "end_date": "2024-01-31"}
    max_nodes = 50
    min_affinity = 0.2

    figure, graph_data = update_file_affinity_graph(store_data, max_nodes, min_affinity)

    assert isinstance(figure, go.Figure)
    assert graph_data == {}


@patch("data.commits_in_period")
@patch("pages.affinity_groups.date_utils.parse_date_range_from_store")
def test_callback_with_empty_commits(mock_parse, mock_commits):
    """Test callback behavior with no commits in the period."""
    from pages.affinity_groups import update_file_affinity_graph

    mock_parse.return_value = (datetime(2024, 1, 1), datetime(2024, 1, 31))
    mock_commits.return_value = []

    store_data = {"start_date": "2024-01-01", "end_date": "2024-01-31"}
    max_nodes = 50
    min_affinity = 0.2

    figure, graph_data = update_file_affinity_graph(store_data, max_nodes, min_affinity)

    assert isinstance(figure, go.Figure)
    # Empty commits should return valid but possibly empty graph
    assert isinstance(graph_data, dict)


@patch("pages.affinity_groups.calculate_affinities")
@patch("data.commits_in_period")
@patch("pages.affinity_groups.date_utils.parse_date_range_from_store")
def test_affinity_caching_behavior(mock_parse, mock_commits, mock_calc_affinities):
    """Test that affinity calculations are cached properly."""
    from pages.affinity_groups import _AFFINITY_CACHE, update_file_affinity_graph

    # Clear cache before test
    _AFFINITY_CACHE.clear()

    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 31)
    mock_parse.return_value = (start, end)

    # Create mock commits with files
    mock_commit = Mock()
    mock_commit.hexsha = "abc123"
    mock_commit.committed_datetime = datetime(2024, 1, 15)
    mock_commit.message = "test commit"
    mock_commit.stats = Mock()
    mock_commit.stats.files = {"file1.py": {}, "file2.py": {}}

    mock_commits.return_value = [mock_commit]
    mock_calc_affinities.return_value = {("file1.py", "file2.py"): 0.5}

    store_data = {"start_date": "2024-01-01", "end_date": "2024-01-31"}
    max_nodes = 50
    min_affinity = 0.2

    # First call should calculate affinities
    figure1, data1 = update_file_affinity_graph(store_data, max_nodes, min_affinity)
    assert mock_calc_affinities.call_count == 1

    # Second call with same date range should use cache
    figure2, data2 = update_file_affinity_graph(store_data, max_nodes, min_affinity)
    assert mock_calc_affinities.call_count == 1  # Still 1, not 2

    # Third call with different parameters should still use cache
    figure3, data3 = update_file_affinity_graph(store_data, 100, 0.3)
    assert mock_calc_affinities.call_count == 1  # Still 1


@patch("pages.affinity_groups.calculate_affinities")
@patch("data.commits_in_period")
@patch("pages.affinity_groups.date_utils.parse_date_range_from_store")
def test_affinity_cache_different_date_ranges(mock_parse, mock_commits, mock_calc):
    """Test that different date ranges create separate cache entries."""
    from pages.affinity_groups import _AFFINITY_CACHE, update_file_affinity_graph

    _AFFINITY_CACHE.clear()

    mock_commit = Mock()
    mock_commit.hexsha = "abc123"
    mock_commit.committed_datetime = datetime(2024, 1, 15)
    mock_commit.message = "test"
    mock_commit.stats = Mock()
    mock_commit.stats.files = {"file1.py": {}}
    mock_commits.return_value = [mock_commit]
    mock_calc.return_value = {}

    # First date range
    mock_parse.return_value = (datetime(2024, 1, 1), datetime(2024, 1, 31))
    update_file_affinity_graph({"start": "2024-01-01"}, 50, 0.2)

    # Second date range should trigger new calculation
    mock_parse.return_value = (datetime(2024, 2, 1), datetime(2024, 2, 28))
    update_file_affinity_graph({"start": "2024-02-01"}, 50, 0.2)

    assert mock_calc.call_count == 2


def test_get_commits_for_group_files_with_no_parents():
    """Test handling of commits without parents (initial commit)."""
    from pages.affinity_groups import get_commits_for_group_files

    with patch("pages.affinity_groups.data.commits_in_period") as mock_commits:
        mock_commit = Mock()
        mock_commit.hexsha = "abc123"
        mock_commit.committed_datetime = datetime(2024, 1, 15, 10, 30)
        mock_commit.message = "Initial commit"
        mock_commit.parents = []  # No parents

        mock_commits.return_value = [mock_commit]

        group_files = ["file1.py", "file2.py"]
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        result = get_commits_for_group_files(group_files, start, end)

        # Should handle commits without parents gracefully
        assert isinstance(result, list)


def test_get_commits_for_group_files_with_missing_paths():
    """Test handling of diff items without a_path or b_path."""
    from pages.affinity_groups import get_commits_for_group_files

    with patch("pages.affinity_groups.data.commits_in_period") as mock_commits:
        mock_commit = Mock()
        mock_commit.hexsha = "abc123"
        mock_commit.committed_datetime = datetime(2024, 1, 15, 10, 30)
        mock_commit.message = "Test commit"
        mock_commit.parents = [Mock()]

        # Diff items without proper paths
        diff_item1 = Mock(spec=[])  # No a_path or b_path attributes
        diff_item2 = Mock()
        diff_item2.a_path = None
        diff_item2.b_path = "file1.py"

        mock_commit.diff.return_value = [diff_item1, diff_item2]
        mock_commits.return_value = [mock_commit]

        group_files = ["file1.py", "file2.py"]
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        result = get_commits_for_group_files(group_files, start, end)

        # Should handle missing paths without crashing
        assert isinstance(result, list)


def test_get_commits_for_group_files_truncates_long_message():
    """Test that long commit messages are truncated to 100 chars."""
    from pages.affinity_groups import get_commits_for_group_files

    with patch("pages.affinity_groups.data.commits_in_period") as mock_commits:
        long_message = "A" * 150  # 150 character message
        mock_commit = Mock()
        mock_commit.hexsha = "abc123def456"
        mock_commit.committed_datetime = datetime(2024, 1, 15, 10, 30)
        mock_commit.message = long_message
        mock_commit.parents = [Mock()]

        diff_item1 = Mock()
        diff_item1.a_path = "file1.py"
        diff_item2 = Mock()
        diff_item2.a_path = "file2.py"
        mock_commit.diff.return_value = [diff_item1, diff_item2]

        mock_commits.return_value = [mock_commit]

        group_files = ["file1.py", "file2.py"]
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        result = get_commits_for_group_files(group_files, start, end)

        assert len(result) == 1
        assert len(result[0]["message"]) == 100


def test_get_commits_for_group_files_multiline_message():
    """Test that only first line of commit message is used."""
    from pages.affinity_groups import get_commits_for_group_files

    with patch("pages.affinity_groups.data.commits_in_period") as mock_commits:
        multiline = "feat: first line\n\nThis is the body\nMore details here"
        mock_commit = Mock()
        mock_commit.hexsha = "abc123def456"
        mock_commit.committed_datetime = datetime(2024, 1, 15, 10, 30)
        mock_commit.message = multiline
        mock_commit.parents = [Mock()]

        diff_item1 = Mock()
        diff_item1.a_path = "file1.py"
        diff_item2 = Mock()
        diff_item2.a_path = "file2.py"
        mock_commit.diff.return_value = [diff_item1, diff_item2]

        mock_commits.return_value = [mock_commit]

        group_files = ["file1.py", "file2.py"]
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        result = get_commits_for_group_files(group_files, start, end)

        assert len(result) == 1
        assert result[0]["message"] == "feat: first line"


def test_get_commits_for_group_files_sorts_by_timestamp():
    """Test that commits are sorted by timestamp, most recent first."""
    from pages.affinity_groups import get_commits_for_group_files

    with patch("pages.affinity_groups.data.commits_in_period") as mock_commits:
        # Create commits in non-chronological order
        mock_commit1 = Mock()
        mock_commit1.hexsha = "aaa111"
        mock_commit1.committed_datetime = datetime(2024, 1, 10, 10, 0)
        mock_commit1.message = "Older commit"
        mock_commit1.parents = [Mock()]
        diff1 = Mock()
        diff1.a_path = "file1.py"
        diff2 = Mock()
        diff2.a_path = "file2.py"
        mock_commit1.diff.return_value = [diff1, diff2]

        mock_commit2 = Mock()
        mock_commit2.hexsha = "bbb222"
        mock_commit2.committed_datetime = datetime(2024, 1, 20, 15, 0)
        mock_commit2.message = "Newer commit"
        mock_commit2.parents = [Mock()]
        mock_commit2.diff.return_value = [diff1, diff2]

        # Return in wrong order
        mock_commits.return_value = [mock_commit1, mock_commit2]

        group_files = ["file1.py", "file2.py"]
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        result = get_commits_for_group_files(group_files, start, end)

        assert len(result) == 2
        # Most recent should be first
        assert result[0]["timestamp"] == "2024-01-20 15:00"
        assert result[1]["timestamp"] == "2024-01-10 10:00"


def test_update_node_details_table_parses_tooltip_correctly():
    """Test that node names are correctly extracted from tooltip text."""
    from pages.affinity_groups import update_node_details_table

    with (
        patch("pages.affinity_groups.get_commits_for_group_files") as mock_commits,
        patch(
            "pages.affinity_groups.date_utils.parse_date_range_from_store"
        ) as mock_parse,
    ):
        mock_parse.return_value = (datetime(2024, 1, 1), datetime(2024, 1, 31))
        mock_commits.return_value = []

        # Test tooltip with <br> tags
        click_data = {
            "points": [{"text": "File: src/main.py<br>Commits: 10<br>Connections: 3"}]
        }
        graph_data = {
            "nodes": {
                "src/main.py": {
                    "commit_count": 10,
                    "community": 0,
                }
            },
            "communities": {0: ["src/main.py"]},
        }
        date_range_data = {"start": "2024-01-01"}

        result = update_node_details_table(click_data, graph_data, date_range_data)

        # Should parse correctly and call with correct files
        assert mock_commits.called
        call_args = mock_commits.call_args[0]
        assert "src/main.py" in call_args[0]


def test_update_node_details_table_empty_graph_data():
    """Test handling of empty graph data."""
    from pages.affinity_groups import update_node_details_table

    click_data = {"points": [{"text": "File: test.py"}]}
    graph_data = {}
    date_range_data = {}

    result = update_node_details_table(click_data, graph_data, date_range_data)

    assert result == []


def test_update_node_details_table_missing_community():
    """Test handling of nodes without community assignments."""
    from pages.affinity_groups import update_node_details_table

    with (
        patch("pages.affinity_groups.get_commits_for_group_files") as mock_commits,
        patch(
            "pages.affinity_groups.date_utils.parse_date_range_from_store"
        ) as mock_parse,
    ):
        mock_parse.return_value = (datetime(2024, 1, 1), datetime(2024, 1, 31))
        mock_commits.return_value = []

        click_data = {"points": [{"text": "test.py"}]}
        graph_data = {
            "nodes": {
                "test.py": {
                    # Missing 'community' key - should default to 0
                    "commit_count": 5,
                }
            },
            "communities": {},
        }
        date_range_data = {}

        result = update_node_details_table(click_data, graph_data, date_range_data)

        # Should handle missing community gracefully
        assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
