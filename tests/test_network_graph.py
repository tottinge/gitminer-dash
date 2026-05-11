"""
Unit tests for the network graph visualization module.
"""

import unittest
from unittest.mock import Mock, patch

import networkx as nx
import plotly.graph_objects as go

from algorithms.affinity_network import AFFINITY_STATS_KEYS
from visualization.common import create_empty_figure
from visualization.network_graph import (
    _build_network_figure,
    _build_node_trace,
    _build_weighted_edge_traces,
    _collect_node_plot_data,
    _create_edge_traces,
    _create_non_singleton_community_traces,
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
        assert set(AFFINITY_STATS_KEYS).issubset(stats)
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

        precomputed_affinities = {("a.py", "b.py"): 0.5}
        (G, communities, stats) = create_file_affinity_network(
            [commit],
            min_affinity=0.4,
            precomputed_affinities=precomputed_affinities,
        )
        assert len(G.nodes()) == 2
        assert len(G.edges()) == 1
        assert G.has_edge("a.py", "b.py")

    def test_min_affinity_filtering(self):
        """Test that min_affinity threshold filters edges."""
        commit = Mock()
        commit.stats.files = {"a.py": {}, "b.py": {}}

        precomputed_affinities = {("a.py", "b.py"): 0.8}
        (G, communities, stats) = create_file_affinity_network(
            [commit],
            min_affinity=0.9,
            precomputed_affinities=precomputed_affinities,
        )
        assert len(G.edges()) == 0

    def test_node_attributes(self):
        """Test that nodes have correct attributes."""
        commit = Mock()
        commit.stats.files = {"a.py": {}, "b.py": {}}

        precomputed_affinities = {("a.py", "b.py"): 0.5}
        (G, communities, stats) = create_file_affinity_network(
            [commit],
            min_affinity=0.0,
            precomputed_affinities=precomputed_affinities,
        )
        assert "commit_count" in G.nodes["a.py"]
        assert "commit_count" in G.nodes["b.py"]
        assert G.nodes["a.py"]["commit_count"] == 1
        assert G.nodes["b.py"]["commit_count"] == 1

    def test_edge_weights(self):
        """Test that edges have correct weight values."""
        commit = Mock()
        commit.stats.files = {"a.py": {}, "b.py": {}}

        precomputed_affinities = {("a.py", "b.py"): 0.42}
        (G, communities, stats) = create_file_affinity_network(
            [commit],
            min_affinity=0.1,
            precomputed_affinities=precomputed_affinities,
        )
        assert G.edges["a.py", "b.py"]["weight"] == 0.42

    def test_stats_tracking(self):
        """Test that statistics are correctly tracked."""
        commit1 = Mock()
        commit1.stats.files = {"a.py": {}, "b.py": {}}
        commit2 = Mock()
        commit2.stats.files = {"b.py": {}, "c.py": {}}

        precomputed_affinities = {("a.py", "b.py"): 0.5, ("b.py", "c.py"): 0.4}
        (G, communities, stats) = create_file_affinity_network(
            [commit1, commit2],
            min_affinity=0.0,
            precomputed_affinities=precomputed_affinities,
        )
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
        with (
            patch(
                "algorithms.affinity_network.count_files_in_commits",
                return_value={"a.py": 1, "b.py": 2, "c.py": 2},
            ),
            patch(
                "algorithms.affinity_network.count_multi_file_commits",
                return_value=2,
            ),
            patch(
                "algorithms.affinity_network.get_top_files_by_affinity",
                return_value={"a.py", "b.py", "c.py"},
            ),
            patch(
                "algorithms.affinity_network.filter_low_degree_nodes",
                return_value=1,
            ),
            patch(
                "algorithms.affinity_network.detect_and_assign_communities",
                return_value=(
                    ["community-1", "community-2"],
                    {"communities": 2, "avg_community_size": 1.5},
                ),
            ),
            patch(
                "algorithms.affinity_network.calculate_graph_statistics",
                return_value={"avg_node_degree": 1.5, "avg_edge_weight": 0.5},
            ),
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
        assert set(AFFINITY_STATS_KEYS).issubset(stats)

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

        precomputed_affinities = {("a.py", "b.py"): 0.5}
        (G, communities, stats) = create_file_affinity_network(
            [commit],
            min_affinity=0.0,
            precomputed_affinities=precomputed_affinities,
        )
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
            "algorithms.affinity_network.calculate_affinities",
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
        commits[0].stats.files = {
            "a.py": {},
            "b.py": {},
            "c.py": {},
            "d.py": {},
        }

        affinities = {
            ("a.py", "b.py"): 0.9,
            ("a.py", "c.py"): 0.8,
            ("c.py", "d.py"): 0.7,
        }

        with (
            patch(
                "algorithms.affinity_network.calculate_affinities",
                return_value=affinities,
            ),
            patch(
                "algorithms.affinity_network.get_top_files_by_affinity",
                return_value={"a.py", "b.py", "c.py"},
            ),
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

        with patch(
            "algorithms.affinity_network.calculate_affinities"
        ) as mock_calc:
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

        marker_traces = [
            t for t in fig.data if "markers" in getattr(t, "mode", "")
        ]
        total_nodes_plotted = sum(len(t.x) for t in marker_traces)

        assert total_nodes_plotted == len(G.nodes())

    def test_visualization_uses_given_layout_positions_for_edges_and_nodes(
        self,
    ):
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

        with patch(
            "visualization.network_graph.nx.spring_layout",
            return_value=fixed_pos,
        ):
            fig = create_network_visualization(
                G, communities, title="Layout Test"
            )

        # Edges: look for a line trace that connects the two fixed coordinates.
        line_traces = [t for t in fig.data if getattr(t, "mode", "") == "lines"]
        coords = {(tuple(t.x), tuple(t.y)) for t in line_traces}

        assert ((0.0, 1.0, None), (0.0, 2.0, None)) in coords

        # Nodes: all node markers should be at the fixed positions we provided.
        marker_traces = [
            t for t in fig.data if "markers" in getattr(t, "mode", "")
        ]
        xs = [x for t in marker_traces for x in t.x]
        ys = [y for t in marker_traces for y in t.y]

        assert set(zip(xs, ys, strict=True)) == {(0.0, 0.0), (1.0, 2.0)}

    def test_create_file_affinity_network_with_large_synthetic_dataset(self):
        """Larger synthetic dataset should produce a non-trivial but bounded graph.

        This is a higher-level integration test that exercises the real
        calculate_affinities path over multiple file groups with different
        co-change densities. It is intentionally less brittle: we assert
        structural properties of the resulting graph rather than exact
        counts, so future tuning of the affinity algorithm is allowed
        as long as the overall shape remains sane.
        """
        commits: list[Mock] = []

        # Group 1: dense cluster of three files that almost always change together.
        for _ in range(5):
            c = Mock()
            c.stats = Mock()
            c.stats.files = {
                "group1_file1.py": {},
                "group1_file2.py": {},
                "group1_file3.py": {},
            }
            commits.append(c)

        # Group 2: medium-density cluster with varying pairs/triples.
        for i in range(10):
            files = ["group2_file1.py"]
            if i % 2 == 0:
                files.append("group2_file2.py")
            if i % 3 == 0:
                files.append("group2_file3.py")

            c = Mock()
            c.stats = Mock()
            c.stats.files = {name: {} for name in files}
            commits.append(c)

        # Group 3: mostly single-file commits with occasional co-changes.
        for i in range(20):
            files = ["group3_file1.py"]
            if i % 10 == 0:
                files.append("group3_file2.py")
            if i % 15 == 0:
                files.append("group3_file3.py")

            c = Mock()
            c.stats = Mock()
            c.stats.files = {name: {} for name in files}
            commits.append(c)

        G, communities, stats = create_file_affinity_network(
            commits,
            min_affinity=0.2,
            max_nodes=50,
        )

        # Basic sanity: graph is non-empty but respects max_nodes.
        assert len(G.nodes()) >= 5
        assert len(G.nodes()) <= 50
        assert len(G.edges()) >= 1

        # Ensure that each synthetic group contributed at least one node.
        assert "group1_file1.py" in G.nodes
        assert "group2_file1.py" in G.nodes
        assert "group3_file1.py" in G.nodes

        # The stats dict should remain internally consistent with the graph.
        assert stats["nodes_after_filtering"] == len(G.nodes())
        assert stats["edges_after_filtering"] == len(G.edges())

        # We expect at least one multi-node connected component.
        components = list(nx.connected_components(G))
        assert any(len(component) > 1 for component in components)

    def test_create_edge_traces_empty_graph_contract(self):
        """Empty edge sets should produce one explicit empty line trace."""
        G = nx.Graph()
        traces = _create_edge_traces(G, pos={})

        assert len(traces) == 1
        trace = traces[0]
        assert trace.x is not None
        assert trace.y is not None
        assert len(trace.x) == 0
        assert len(trace.y) == 0
        assert trace.mode == "lines"
        assert trace.hoverinfo == "none"
        assert trace.showlegend is False
        assert trace.line.width == 0

    def test_create_edge_traces_non_empty_contract(self):
        """Edge traces should preserve geometry, text, and width scaling."""
        G = nx.Graph()
        G.add_edge("a.py", "b.py", weight=0.25)
        G.add_edge("a.py", "c.py", weight=0.5)

        pos = {
            "a.py": (0.0, 0.0),
            "b.py": (1.0, 0.0),
            "c.py": (0.0, 1.0),
        }

        traces = _create_edge_traces(G, pos)
        assert len(traces) == 2

        # Shared contract for each edge trace
        for trace in traces:
            assert trace.mode == "lines"
            assert trace.hoverinfo == "text"
            assert trace.showlegend is False
            assert trace.x is not None
            assert trace.y is not None
            assert len(trace.x) == 3
            assert len(trace.y) == 3
            assert trace.x[2] is None
            assert trace.y[2] is None

        width_by_text = {trace.text: trace.line.width for trace in traces}
        assert set(width_by_text.keys()) == {
            "a.py - b.py<br>Affinity: 0.25",
            "a.py - c.py<br>Affinity: 0.50",
        }
        assert round(width_by_text["a.py - b.py<br>Affinity: 0.25"], 2) == 5.0
        assert round(width_by_text["a.py - c.py<br>Affinity: 0.50"], 2) == 8.0

    def test_create_network_visualization_calls_contracts(self):
        """Visualization should call collaborators with stable parameters."""
        G = nx.Graph()
        G.add_edge("a.py", "b.py", weight=0.5)
        communities = [["a.py", "b.py"]]
        fixed_pos = {"a.py": (0.0, 0.0), "b.py": (1.0, 1.0)}

        edge_trace = go.Scatter(x=[0, 1, None], y=[0, 1, None], mode="lines")
        node_trace = go.Scatter(x=[0, 1], y=[0, 1], mode="markers")

        with (
            patch(
                "visualization.network_graph.nx.spring_layout",
                return_value=fixed_pos,
            ) as mock_layout,
            patch(
                "visualization.network_graph._create_edge_traces",
                return_value=[edge_trace],
            ) as mock_edges,
            patch(
                "visualization.network_graph._create_node_traces",
                return_value=[node_trace],
            ) as mock_nodes,
        ):
            fig = create_network_visualization(
                G, communities, title="Strict Network"
            )

        mock_layout.assert_called_once_with(G, seed=42, iterations=40)
        mock_edges.assert_called_once_with(G, fixed_pos)
        mock_nodes.assert_called_once_with(G, fixed_pos, communities)

        assert len(fig.data) == 2
        assert fig.layout.title.text == "Strict Network"
        assert fig.layout.title.font.size == 16
        assert fig.layout.showlegend is True
        assert fig.layout.hovermode == "closest"
        assert fig.layout.xaxis.showgrid is False
        assert fig.layout.xaxis.zeroline is False
        assert fig.layout.xaxis.showticklabels is False
        assert fig.layout.yaxis.showgrid is False
        assert fig.layout.yaxis.zeroline is False
        assert fig.layout.yaxis.showticklabels is False

    def test_create_network_visualization_empty_graph_passes_message_and_title(
        self,
    ):
        """Empty-graph path should pass explicit message/title to helper."""
        G = nx.Graph()

        with patch(
            "visualization.network_graph.create_empty_figure"
        ) as mock_empty:
            sentinel = object()
            mock_empty.return_value = sentinel

            result = create_network_visualization(
                G, communities=[], title="Chosen Title"
            )

        assert result is sentinel
        mock_empty.assert_called_once_with(
            message="No data available for the selected time period",
            title="Chosen Title",
        )

    def test_build_network_figure_happy_path(self):
        """Assembles edge and node traces into a titled figure."""
        edge_trace = go.Scatter(x=[0, 1, None], y=[0, 1, None], mode="lines")
        node_trace = go.Scatter(x=[0, 1], y=[0, 1], mode="markers")

        fig = _build_network_figure(
            edge_traces=[edge_trace],
            node_traces=[node_trace],
            title="Network Title",
        )

        assert len(fig.data) == 2
        assert fig.layout.title.text == "Network Title"
        assert fig.layout.showlegend is True
        assert fig.layout.hovermode == "closest"

    def test_build_network_figure_layout_serialized_contract(self):
        """Layout should preserve exact title/font, margin, and hidden-axis settings."""
        edge_trace = go.Scatter(x=[0, 1, None], y=[0, 1, None], mode="lines")
        node_trace = go.Scatter(x=[0, 1], y=[0, 1], mode="markers")

        fig = _build_network_figure(
            edge_traces=[edge_trace],
            node_traces=[node_trace],
            title="Exact Layout",
        )

        assert fig.layout.title.to_plotly_json() == {
            "text": "Exact Layout",
            "font": {"size": 16},
        }
        assert fig.layout.margin.to_plotly_json() == {
            "b": 20,
            "l": 5,
            "r": 5,
            "t": 40,
        }
        assert fig.layout.xaxis.to_plotly_json() == {
            "showgrid": False,
            "zeroline": False,
            "showticklabels": False,
        }
        assert fig.layout.yaxis.to_plotly_json() == {
            "showgrid": False,
            "zeroline": False,
            "showticklabels": False,
        }

    def test_collect_node_plot_data_happy_path(self):
        """Collects node coordinates, tooltip text, and marker sizes."""
        graph = nx.Graph()
        graph.add_node("a.py", commit_count=4)
        graph.add_node("b.py", commit_count=2)
        graph.add_edge("a.py", "b.py")
        positions = {"a.py": (0.0, 0.5), "b.py": (1.0, 1.5)}

        node_x, node_y, node_text, node_size = _collect_node_plot_data(
            G=graph,
            pos=positions,
            nodes=["a.py", "b.py"],
        )

        assert node_x == [0.0, 1.0]
        assert node_y == [0.5, 1.5]
        assert node_text == [
            "File: a.py<br>Commits: 4<br>Connections: 1",
            "File: b.py<br>Commits: 2<br>Connections: 1",
        ]
        assert node_size == [14.0, 13.0]

    def test_create_non_singleton_community_traces_edge_cases(self):
        """Skips singleton communities and returns traces for multi-node groups."""
        graph = nx.Graph()
        graph.add_node("a.py", community=0, commit_count=3)
        graph.add_node("b.py", community=0, commit_count=1)
        graph.add_node("c.py", community=1, commit_count=5)
        graph.add_edge("a.py", "b.py")
        positions = {
            "a.py": (0.0, 0.0),
            "b.py": (1.0, 0.0),
            "c.py": (2.0, 0.0),
        }

        traces = _create_non_singleton_community_traces(
            G=graph,
            pos=positions,
            community_ids={0, 1},
            community_colors=["#111111", "#222222"],
        )

        assert len(traces) == 1
        assert traces[0].name == "Group 1"
        assert traces[0].marker.color == "#111111"
        assert list(traces[0].x) == [0.0, 1.0]

    def test_build_weighted_edge_traces_happy_path(self):
        """Builds one trace per weighted segment with scaled widths."""
        traces = _build_weighted_edge_traces(
            edge_x=[0.0, 1.0, None, 1.0, 2.0, None],
            edge_y=[0.0, 0.0, None, 0.0, 0.5, None],
            edge_weights=[0.25, 0.5],
            edge_texts=["a-b", "b-c"],
            max_weight=0.5,
        )

        assert len(traces) == 2
        assert traces[0].text == "a-b"
        assert traces[1].text == "b-c"
        assert round(traces[0].line.width, 2) == 5.0
        assert round(traces[1].line.width, 2) == 8.0

    def test_build_node_trace_happy_path(self):
        """Builds a marker trace preserving coordinates, labels, and style."""
        trace = _build_node_trace(
            node_x=[0.0, 1.0],
            node_y=[1.0, 2.0],
            node_text=["node-a", "node-b"],
            node_size=[12.0, 18.0],
            color="#abcdef",
            name="Group X",
        )

        assert list(trace.x) == [0.0, 1.0]
        assert list(trace.y) == [1.0, 2.0]
        assert list(trace.text) == ["node-a", "node-b"]
        assert list(trace.marker.size) == [12.0, 18.0]
        assert trace.marker.color == "#abcdef"
        assert trace.name == "Group X"


if __name__ == "__main__":
    unittest.main()
