"""
Unit tests for specific cases in pages/affinity_groups.py.

These tests cover:
1. _get_cached_affinities() returns cached data if available and computes otherwise
2. _build_graph_data_store() correctly transforms graph and communities into serializable store format
3. update_file_affinity_graph() handles invalid date range error properly
4. update_file_affinity_graph() returns repo error figure if no repository path provided
5. update_file_affinity_graph() handles exceptions during graph generation and returns error figure
"""

from datetime import datetime
from unittest.mock import Mock, patch

import networkx as nx
import plotly.graph_objects as go
import pytest
from dash import Dash

app = Dash(__name__, suppress_callback_exceptions=True)


class TestGetCachedAffinities:
    """Tests for _get_cached_affinities() function."""

    @patch("pages.affinity_groups.calculate_affinities")
    def test_get_cached_affinities_computes_when_not_cached(
        self, mock_calculate
    ):
        """Test that _get_cached_affinities computes affinities when not in cache."""
        from pages.affinity_groups import (
            _AFFINITY_CACHE,
            _get_cached_affinities,
        )

        # Clear cache
        _AFFINITY_CACHE.clear()

        # Setup
        starting = datetime(2024, 1, 1)
        ending = datetime(2024, 1, 31)
        mock_commits = [Mock()]
        expected_affinities = {("file1.py", "file2.py"): 0.75}
        mock_calculate.return_value = expected_affinities

        # Execute
        result = _get_cached_affinities(starting, ending, mock_commits)

        # Verify
        assert result == expected_affinities
        mock_calculate.assert_called_once_with(mock_commits)
        # Check it was added to cache
        cache_key = (starting.isoformat(), ending.isoformat())
        assert cache_key in _AFFINITY_CACHE
        assert _AFFINITY_CACHE[cache_key] == expected_affinities

    @patch("pages.affinity_groups.calculate_affinities")
    def test_get_cached_affinities_returns_cached_data(self, mock_calculate):
        """Test that _get_cached_affinities returns cached data without recomputing."""
        from pages.affinity_groups import (
            _AFFINITY_CACHE,
            _get_cached_affinities,
        )

        # Setup cache
        starting = datetime(2024, 1, 1)
        ending = datetime(2024, 1, 31)
        cache_key = (starting.isoformat(), ending.isoformat())
        cached_affinities = {("file1.py", "file2.py"): 0.85}
        _AFFINITY_CACHE[cache_key] = cached_affinities

        # Execute
        mock_commits = [Mock()]
        result = _get_cached_affinities(starting, ending, mock_commits)

        # Verify
        assert result == cached_affinities
        mock_calculate.assert_not_called()

    @patch("pages.affinity_groups.calculate_affinities")
    def test_get_cached_affinities_different_dates_compute_separately(
        self, mock_calculate
    ):
        """Test that different date ranges compute separately and both are cached."""
        from pages.affinity_groups import (
            _AFFINITY_CACHE,
            _get_cached_affinities,
        )

        _AFFINITY_CACHE.clear()

        # First date range
        starting1 = datetime(2024, 1, 1)
        ending1 = datetime(2024, 1, 31)
        affinities1 = {("file1.py", "file2.py"): 0.6}
        mock_calculate.return_value = affinities1

        result1 = _get_cached_affinities(starting1, ending1, [Mock()])

        # Second date range
        starting2 = datetime(2024, 2, 1)
        ending2 = datetime(2024, 2, 28)
        affinities2 = {("file3.py", "file4.py"): 0.8}
        mock_calculate.return_value = affinities2

        result2 = _get_cached_affinities(starting2, ending2, [Mock()])

        # Verify both computed
        assert mock_calculate.call_count == 2
        assert result1 == affinities1
        assert result2 == affinities2

        # Verify both cached
        assert len(_AFFINITY_CACHE) == 2


class TestBuildGraphDataStore:
    """Tests for _build_graph_data_store() function."""

    def test_build_graph_data_store_basic_structure(self):
        """Test that _build_graph_data_store creates correct serializable structure."""
        from pages.affinity_groups import _build_graph_data_store

        # Create simple graph
        G = nx.Graph()
        G.add_node("file1.py", community=0, commit_count=5)
        G.add_node("file2.py", community=0, commit_count=3)
        G.add_node("file3.py", community=1, commit_count=7)
        G.add_edge("file1.py", "file2.py")

        communities = [{"file1.py", "file2.py"}, {"file3.py"}]

        # Execute
        result = _build_graph_data_store(G, communities)

        # Verify structure
        assert "nodes" in result
        assert "communities" in result
        assert isinstance(result["nodes"], dict)
        assert isinstance(result["communities"], dict)

    def test_build_graph_data_store_node_data(self):
        """Test that node data is correctly transformed."""
        from pages.affinity_groups import _build_graph_data_store

        G = nx.Graph()
        G.add_node("file1.py", community=0, commit_count=10)
        G.add_node("file2.py", community=0, commit_count=5)
        G.add_edge("file1.py", "file2.py")

        communities = [{"file1.py", "file2.py"}]

        result = _build_graph_data_store(G, communities)

        # Verify file1.py data
        assert "file1.py" in result["nodes"]
        node1 = result["nodes"]["file1.py"]
        assert node1["commit_count"] == 10
        assert node1["community"] == 0
        assert node1["degree"] == 1  # Connected to file2.py
        assert isinstance(node1["connected_communities"], list)

        # Verify file2.py data
        assert "file2.py" in result["nodes"]
        node2 = result["nodes"]["file2.py"]
        assert node2["commit_count"] == 5
        assert node2["degree"] == 1

    def test_build_graph_data_store_connected_communities(self):
        """Test that connected_communities are correctly computed."""
        from pages.affinity_groups import _build_graph_data_store

        G = nx.Graph()
        G.add_node("file1.py", community=0, commit_count=5)
        G.add_node("file2.py", community=1, commit_count=3)
        G.add_node("file3.py", community=2, commit_count=4)
        G.add_edge("file1.py", "file2.py")
        G.add_edge("file1.py", "file3.py")

        communities = [{"file1.py"}, {"file2.py"}, {"file3.py"}]

        result = _build_graph_data_store(G, communities)

        # file1.py connects to communities 1 and 2
        assert set(result["nodes"]["file1.py"]["connected_communities"]) == {
            1,
            2,
        }
        # file2.py connects to community 0
        assert result["nodes"]["file2.py"]["connected_communities"] == [0]

    def test_build_graph_data_store_communities_list(self):
        """Test that communities are correctly indexed."""
        from pages.affinity_groups import _build_graph_data_store

        G = nx.Graph()
        G.add_node("file1.py", community=0, commit_count=5)
        G.add_node("file2.py", community=0, commit_count=3)
        G.add_node("file3.py", community=1, commit_count=4)

        communities = [{"file1.py", "file2.py"}, {"file3.py"}]

        result = _build_graph_data_store(G, communities)

        # Verify communities are converted to lists
        assert result["communities"][0] == ["file1.py", "file2.py"] or result[
            "communities"
        ][0] == ["file2.py", "file1.py"]
        assert result["communities"][1] == ["file3.py"]

    def test_build_graph_data_store_empty_graph(self):
        """Test handling of empty graph."""
        from pages.affinity_groups import _build_graph_data_store

        G = nx.Graph()
        communities = []

        result = _build_graph_data_store(G, communities)

        assert result == {"nodes": {}, "communities": {}}

    def test_build_graph_data_store_node_without_community(self):
        """Test that nodes without community attribute default to 0."""
        from pages.affinity_groups import _build_graph_data_store

        G = nx.Graph()
        G.add_node("file1.py", commit_count=5)  # No community attribute

        communities = []

        result = _build_graph_data_store(G, communities)

        assert result["nodes"]["file1.py"]["community"] == 0


class TestUpdateFileAffinityGraphInvalidDateRange:
    """Test for update_file_affinity_graph() handling invalid date range."""

    @patch("pages.affinity_groups.date_utils.parse_date_range_from_store")
    def test_update_file_affinity_graph_invalid_date_range(self, mock_parse):
        """Test that invalid date range returns error figure with empty graph data."""
        from pages.affinity_groups import update_file_affinity_graph

        # Setup - simulate ValueError from date parsing
        mock_parse.side_effect = ValueError("Invalid date format: bad-date")

        store_data = {"invalid": "data"}
        max_nodes = 50
        min_affinity = 0.2

        # Execute
        figure, graph_data = update_file_affinity_graph(
            store_data, max_nodes, min_affinity
        )

        # Verify
        assert isinstance(figure, go.Figure)
        assert graph_data == {}
        assert hasattr(figure, "layout")
        if hasattr(figure.layout, "annotations") and figure.layout.annotations:
            message = figure.layout.annotations[0].text
            assert "Invalid date range" in message
            assert "Invalid date format" in message or "bad-date" in message


class TestUpdateFileAffinityGraphNoRepository:
    """Test for update_file_affinity_graph() handling missing repository path."""

    @patch("data.commits_in_period")
    @patch("pages.affinity_groups.date_utils.parse_date_range_from_store")
    def test_update_file_affinity_graph_no_repository_path(
        self, mock_parse, mock_commits
    ):
        """Test that missing repository path returns appropriate error figure."""
        from pages.affinity_groups import update_file_affinity_graph

        # Setup
        mock_parse.return_value = (datetime(2024, 1, 1), datetime(2024, 1, 31))
        mock_commits.side_effect = ValueError("No repository path provided")

        store_data = {"start": "2024-01-01", "end": "2024-01-31"}
        max_nodes = 50
        min_affinity = 0.2

        # Execute
        figure, graph_data = update_file_affinity_graph(
            store_data, max_nodes, min_affinity
        )

        # Verify
        assert isinstance(figure, go.Figure)
        assert graph_data == {}
        assert hasattr(figure, "layout")
        if hasattr(figure.layout, "annotations") and figure.layout.annotations:
            message = figure.layout.annotations[0].text
            assert "No repository path provided" in message
            assert "Repository Path Required" in figure.layout.title.text


class TestUpdateFileAffinityGraphExceptionHandling:
    """Test for update_file_affinity_graph() handling exceptions during graph generation."""

    @patch("pages.affinity_groups.create_file_affinity_network")
    @patch("data.commits_in_period")
    @patch("pages.affinity_groups.date_utils.parse_date_range_from_store")
    def test_update_file_affinity_graph_network_creation_exception(
        self, mock_parse, mock_commits, mock_network
    ):
        """Test that exceptions during network creation return error figure."""
        from pages.affinity_groups import update_file_affinity_graph

        # Setup
        mock_parse.return_value = (datetime(2024, 1, 1), datetime(2024, 1, 31))
        mock_commits.return_value = [Mock()]
        mock_network.side_effect = RuntimeError(
            "Graph computation failed unexpectedly"
        )

        store_data = {"start": "2024-01-01", "end": "2024-01-31"}
        max_nodes = 50
        min_affinity = 0.2

        # Execute
        figure, graph_data = update_file_affinity_graph(
            store_data, max_nodes, min_affinity
        )

        # Verify
        assert isinstance(figure, go.Figure)
        assert graph_data == {}
        assert hasattr(figure, "layout")
        if hasattr(figure.layout, "annotations") and figure.layout.annotations:
            message = figure.layout.annotations[0].text
            assert "Graph generation failed" in message
            assert (
                "Graph computation failed unexpectedly" in message
                or "computation failed" in message
            )

    @patch("pages.affinity_groups.create_file_affinity_network")
    @patch("data.commits_in_period")
    @patch("pages.affinity_groups.date_utils.parse_date_range_from_store")
    def test_update_file_affinity_graph_generic_exception(
        self, mock_parse, mock_commits, mock_network
    ):
        """Test that generic exceptions are caught and return error figure."""
        from pages.affinity_groups import update_file_affinity_graph

        # Setup
        mock_parse.return_value = (datetime(2024, 1, 1), datetime(2024, 1, 31))
        mock_commits.return_value = []
        mock_network.side_effect = Exception("Unexpected error")

        store_data = {"start": "2024-01-01"}
        max_nodes = 50
        min_affinity = 0.2

        # Execute
        figure, graph_data = update_file_affinity_graph(
            store_data, max_nodes, min_affinity
        )

        # Verify
        assert isinstance(figure, go.Figure)
        assert graph_data == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
