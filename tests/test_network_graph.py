"""
Unit tests for the network graph visualization module.
"""

import unittest
from unittest.mock import Mock, patch

import networkx as nx

from visualization.common import create_empty_figure
from visualization.network_graph import (
    create_file_affinity_network,
    create_network_visualization,
)


class TestNetworkGraph(unittest.TestCase):
    """Test suite for network graph visualization functions."""

    def test_empty_commits(self):
        """Test that empty commits list returns empty graph."""
        (G, communities, stats) = create_file_affinity_network([])
        assert len(G.nodes()) == 0
        assert len(G.edges()) == 0
        assert len(communities) == 0
        assert "error" in stats

    def test_single_file_commits_ignored(self):
        """Test that commits with only one file produce no graph."""
        commit = Mock()
        commit.stats.files = {"a.py": {}}
        (G, communities, stats) = create_file_affinity_network([commit])
        assert len(G.nodes()) == 0
        assert len(G.edges()) == 0

    def test_two_file_commit_creates_edge(self):
        """Test that a commit with two files creates one edge."""
        commit = Mock()
        commit.stats.files = {"a.py": {}, "b.py": {}}
        (G, communities, stats) = create_file_affinity_network(
            [commit], min_affinity=0.4
        )
        assert len(G.nodes()) == 2
        assert len(G.edges()) == 1
        assert G.has_edge("a.py", "b.py")

    def test_min_affinity_filtering(self):
        """Test that min_affinity threshold filters edges."""
        commit = Mock()
        commit.stats.files = {"a.py": {}, "b.py": {}}
        (G, communities, stats) = create_file_affinity_network(
            [commit], min_affinity=0.9
        )
        assert len(G.edges()) == 0

    def test_node_attributes(self):
        """Test that nodes have correct attributes."""
        commit = Mock()
        commit.stats.files = {"a.py": {}, "b.py": {}}
        (G, communities, stats) = create_file_affinity_network([commit])
        assert "commit_count" in G.nodes["a.py"]
        assert "commit_count" in G.nodes["b.py"]
        assert G.nodes["a.py"]["commit_count"] == 1
        assert G.nodes["b.py"]["commit_count"] == 1

    def test_edge_weights(self):
        """Test that edges have correct weight values."""
        commit = Mock()
        commit.stats.files = {"a.py": {}, "b.py": {}}
        (G, communities, stats) = create_file_affinity_network(
            [commit], min_affinity=0.1
        )
        assert G.edges["a.py", "b.py"]["weight"] == 0.5

    def test_stats_tracking(self):
        """Test that statistics are correctly tracked."""
        commit1 = Mock()
        commit1.stats.files = {"a.py": {}, "b.py": {}}
        commit2 = Mock()
        commit2.stats.files = {"b.py": {}, "c.py": {}}
        (G, communities, stats) = create_file_affinity_network([commit1, commit2])
        assert stats["total_commits"] == 2
        assert stats["commits_with_multiple_files"] == 2
        assert stats["unique_files"] == 3
        assert stats["nodes_after_filtering"] > 0

    def test_stats_values_for_simple_commit_set(self):
        """Stats dict should contain consistent, correctly wired counts for a simple graph."""
        # Three commits: two multi-file, one single-file
        commit1 = Mock()
        commit1.stats.files = {"a.py": {}, "b.py": {}}
        commit2 = Mock()
        commit2.stats.files = {"b.py": {}, "c.py": {}}
        commit3 = Mock()
        commit3.stats.files = {"c.py": {}}

        commits = [commit1, commit2, commit3]

        # Control collaborators so we can assert stats precisely while still
        # going through the public function.
        with patch(
            "visualization.network_graph.count_files_in_commits",
            return_value={"a.py": 1, "b.py": 2, "c.py": 2},
        ), patch(
            "visualization.network_graph.count_multi_file_commits",
            return_value=2,
        ), patch(
            "visualization.network_graph.get_top_files_by_affinity",
            return_value={"a.py", "b.py", "c.py"},
        ), patch(
            "visualization.network_graph.filter_low_degree_nodes",
            return_value=1,
        ), patch(
            "visualization.network_graph.detect_and_assign_communities",
            return_value=(
                ["community-1", "community-2"],
                {"communities": 2, "avg_community_size": 1.5},
            ),
        ), patch(
            "visualization.network_graph.calculate_graph_statistics",
            return_value={"avg_node_degree": 1.5, "avg_edge_weight": 0.5},
        ):
            # Provide explicit affinities so we know exactly which pairs exist.
            precomputed_affinities = {
                ("a.py", "b.py"): 0.5,
                ("b.py", "c.py"): 0.5,
            }

            G, communities, stats = create_file_affinity_network(
                commits,
                min_affinity=0.1,
                max_nodes=10,
                precomputed_affinities=precomputed_affinities,
            )

        # Top-level stats populated from inputs and helpers
        assert stats["total_commits"] == 3
        assert stats["commits_with_multiple_files"] == 2
        assert stats["unique_files"] == 3
        assert stats["file_pairs"] == 2

        # Graph-related counts should align with affinities/top-file set
        assert stats["nodes_before_filtering"] == 3
        assert stats["edges_before_filtering"] == 2
        assert stats["isolated_nodes"] == 1
        assert stats["nodes_after_filtering"] == len(G.nodes())
        assert stats["edges_after_filtering"] == len(G.edges())

        # Aggregated graph statistics from helpers should be wired into stats
        assert stats["avg_node_degree"] == 1.5
        assert stats["avg_edge_weight"] == 0.5
        assert stats["communities"] == 2
        assert stats["avg_community_size"] == 1.5

    def test_create_empty_figure(self):
        """Test that empty figure is created correctly."""
        fig = create_empty_figure(message="Test message", title="Test Title")
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
        (G, communities, stats) = create_file_affinity_network([commit])
        fig = create_network_visualization(G, communities, title="Test Network")
        assert fig is not None
        assert "Test Network" in fig.layout.title.text
        assert len(fig.data) > 0

    def test_min_affinity_threshold_is_inclusive(self):
        """Edges with weight == min_affinity should be kept; below should be dropped."""
        # Use precomputed affinities to control weights precisely.
        commits = [Mock(), Mock()]
        affinities = {("a.py", "b.py"): 0.2, ("a.py", "c.py"): 0.19}

        for commit in commits:
            commit.stats = Mock()
            commit.stats.files = {"a.py": {}, "b.py": {}, "c.py": {}}

        with patch(
            "visualization.network_graph.calculate_affinities",
            return_value=affinities,
        ):
            (G, communities, stats) = create_file_affinity_network(
                commits, min_affinity=0.2, max_nodes=10
            )

        assert ("a.py", "b.py") in G.edges or ("b.py", "a.py") in G.edges
        assert not G.has_edge("a.py", "c.py")

    def test_max_nodes_respects_top_file_set(self):
        """Graph nodes and edges must be restricted to the top files set."""
        commits = [Mock()]
        commits[0].stats = Mock()
        commits[0].stats.files = {"a.py": {}, "b.py": {}, "c.py": {}, "d.py": {}}

        affinities = {
            ("a.py", "b.py"): 0.9,
            ("a.py", "c.py"): 0.8,
            ("c.py", "d.py"): 0.7,
        }

        with patch(
            "visualization.network_graph.calculate_affinities",
            return_value=affinities,
        ), patch(
            "visualization.network_graph.get_top_files_by_affinity",
            return_value={"a.py", "b.py", "c.py"},
        ):
            (G, communities, stats) = create_file_affinity_network(
                commits, max_nodes=3, min_affinity=0.1
            )

        # Only top files should appear as nodes
        assert set(G.nodes()) == {"a.py", "b.py", "c.py"}
        # Edge entirely outside top set must not appear
        assert not G.has_edge("c.py", "d.py")

    def test_precomputed_affinities_path_is_used(self):
        """When precomputed_affinities are provided, we must not recalculate them."""
        commits = [Mock()]
        commits[0].stats = Mock()
        commits[0].stats.files = {"a.py": {}, "b.py": {}}

        precomputed = {("a.py", "b.py"): 0.5}

        with patch("visualization.network_graph.calculate_affinities") as mock_calc:
            (G, communities, stats) = create_file_affinity_network(
                commits,
                min_affinity=0.1,
                max_nodes=10,
                precomputed_affinities=precomputed,
            )

        # Should not call calculate_affinities when precomputed affinities provided
        mock_calc.assert_not_called()
        assert G.has_edge("a.py", "b.py")

    def test_edge_width_scales_with_weight_in_visualization(self):
        """Edges with higher weight should be drawn thicker in the figure."""
        G = nx.Graph()
        G.add_node("a.py", commit_count=1)
        G.add_node("b.py", commit_count=1)
        G.add_node("c.py", commit_count=1)

        # Two edges with clearly different weights
        G.add_edge("a.py", "b.py", weight=0.1)
        G.add_edge("a.py", "c.py", weight=1.0)

        communities = []

        fig = create_network_visualization(G, communities, title="Weights Test")

        # Line traces correspond to edges
        line_traces = [t for t in fig.data if getattr(t, "mode", "") == "lines"]
        widths = [t.line.width for t in line_traces]

        assert len(widths) >= 2
        assert max(widths) > min(widths)

    def test_node_traces_cover_all_nodes(self):
        """Visualization must include a marker for every node in the graph."""
        G = nx.Graph()
        G.add_node("a.py", commit_count=1)
        G.add_node("b.py", commit_count=2)
        G.add_edge("a.py", "b.py", weight=0.5)

        communities = []

        fig = create_network_visualization(G, communities, title="Nodes Test")

        marker_traces = [t for t in fig.data if "markers" in getattr(t, "mode", "")]
        total_nodes_plotted = sum(len(t.x) for t in marker_traces)

        assert total_nodes_plotted == len(G.nodes())

    def test_visualization_uses_given_layout_positions_for_edges_and_nodes(self):
        """create_network_visualization must respect layout positions from spring_layout.

        We patch the layout to return fixed coordinates and then verify that both
        edge traces and node traces in the final figure reflect those positions.
        """
        G = nx.Graph()
        G.add_node("a.py", commit_count=1)
        G.add_node("b.py", commit_count=1)
        G.add_edge("a.py", "b.py", weight=0.5)

        communities: list = []

        fixed_pos = {"a.py": (0.0, 0.0), "b.py": (1.0, 2.0)}

        with patch("visualization.network_graph.nx.spring_layout", return_value=fixed_pos):
            fig = create_network_visualization(G, communities, title="Layout Test")

        # Edges: look for a line trace that connects the two fixed coordinates.
        line_traces = [t for t in fig.data if getattr(t, "mode", "") == "lines"]
        coords = {(tuple(t.x), tuple(t.y)) for t in line_traces}

        assert ( (0.0, 1.0, None), (0.0, 2.0, None) ) in coords

        # Nodes: all node markers should be at the fixed positions we provided.
        marker_traces = [t for t in fig.data if "markers" in getattr(t, "mode", "")]
        xs = [x for t in marker_traces for x in t.x]
        ys = [y for t in marker_traces for y in t.y]

        assert set(zip(xs, ys, strict=True)) == {(0.0, 0.0), (1.0, 2.0)}


if __name__ == "__main__":
    unittest.main()
