"""
Unit tests for the network graph visualization module.
"""

import unittest
from unittest.mock import Mock
import networkx as nx
from visualization.network_graph import (
    create_file_affinity_network,
    create_network_visualization,
    create_no_data_figure,
)


class TestNetworkGraph(unittest.TestCase):
    """Test suite for network graph visualization functions."""

    def test_empty_commits(self):
        """Test that empty commits list returns empty graph."""
        G, communities, stats = create_file_affinity_network([])

        assert len(G.nodes()) == 0
        assert len(G.edges()) == 0
        assert len(communities) == 0
        assert "error" in stats

    def test_single_file_commits_ignored(self):
        """Test that commits with only one file produce no graph."""
        commit = Mock()
        commit.stats.files = {"a.py": {}}

        G, communities, stats = create_file_affinity_network([commit])

        assert len(G.nodes()) == 0
        assert len(G.edges()) == 0

    def test_two_file_commit_creates_edge(self):
        """Test that a commit with two files creates one edge."""
        commit = Mock()
        commit.stats.files = {"a.py": {}, "b.py": {}}

        G, communities, stats = create_file_affinity_network([commit], min_affinity=0.4)

        # Should have 2 nodes and 1 edge
        assert len(G.nodes()) == 2
        assert len(G.edges()) == 1
        assert G.has_edge("a.py", "b.py")

    def test_min_affinity_filtering(self):
        """Test that min_affinity threshold filters edges."""
        commit = Mock()
        commit.stats.files = {"a.py": {}, "b.py": {}}

        # With high min_affinity, edge should be filtered out
        G, communities, stats = create_file_affinity_network([commit], min_affinity=0.9)

        # Nodes exist but no edges meet threshold
        assert len(G.edges()) == 0

    def test_node_attributes(self):
        """Test that nodes have correct attributes."""
        commit = Mock()
        commit.stats.files = {"a.py": {}, "b.py": {}}

        G, communities, stats = create_file_affinity_network([commit])

        # Check commit_count attribute exists
        assert "commit_count" in G.nodes["a.py"]
        assert "commit_count" in G.nodes["b.py"]
        assert G.nodes["a.py"]["commit_count"] == 1
        assert G.nodes["b.py"]["commit_count"] == 1

    def test_edge_weights(self):
        """Test that edges have correct weight values."""
        commit = Mock()
        commit.stats.files = {"a.py": {}, "b.py": {}}

        G, communities, stats = create_file_affinity_network([commit], min_affinity=0.1)

        # Weight should be 1/2 = 0.5
        assert G.edges["a.py", "b.py"]["weight"] == 0.5

    def test_stats_tracking(self):
        """Test that statistics are correctly tracked."""
        commit1 = Mock()
        commit1.stats.files = {"a.py": {}, "b.py": {}}

        commit2 = Mock()
        commit2.stats.files = {"b.py": {}, "c.py": {}}

        G, communities, stats = create_file_affinity_network([commit1, commit2])

        assert stats["total_commits"] == 2
        assert stats["commits_with_multiple_files"] == 2
        assert stats["unique_files"] == 3
        assert stats["nodes_after_filtering"] > 0

    def test_create_no_data_figure(self):
        """Test that no data figure is created correctly."""
        fig = create_no_data_figure(message="Test message", title="Test Title")

        assert fig is not None
        assert "Test Title" in fig.layout.title.text

    def test_create_visualization_with_empty_graph(self):
        """Test visualization with empty graph returns no data figure."""
        G = nx.Graph()
        communities = []

        fig = create_network_visualization(G, communities)

        assert fig is not None
        assert "No Data" in fig.layout.title.text

    def test_create_visualization_with_nodes(self):
        """Test visualization with actual graph."""
        commit = Mock()
        commit.stats.files = {"a.py": {}, "b.py": {}}

        G, communities, stats = create_file_affinity_network([commit])
        fig = create_network_visualization(G, communities, title="Test Network")

        assert fig is not None
        assert "Test Network" in fig.layout.title.text
        assert len(fig.data) > 0  # Should have traces


if __name__ == "__main__":
    unittest.main()
