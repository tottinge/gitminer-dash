"""
Unit tests for chain analyzer.
"""

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import networkx as nx

from algorithms.chain_analyzer import analyze_commit_chains
from algorithms.chain_models import ChainData


class TestAnalyzeCommitChains(unittest.TestCase):
    """Test suite for analyze_commit_chains function."""

    def test_empty_graph(self):
        """Test that empty graph returns empty list."""
        graph = nx.Graph()
        chains = analyze_commit_chains(graph)
        assert len(chains) == 0

    def test_single_chain(self):
        """Test analysis of a single connected chain."""
        graph = nx.Graph()
        
        # Create a chain: c1 -> c2 -> c3
        graph.add_node(
            "c1",
            committed=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            sha="c1"
        )
        graph.add_node(
            "c2",
            committed=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            sha="c2"
        )
        graph.add_node(
            "c3",
            committed=datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
            sha="c3"
        )
        graph.add_edge("c1", "c2")
        graph.add_edge("c2", "c3")
        
        chains = analyze_commit_chains(graph)
        
        assert len(chains) == 1
        chain = chains[0]
        assert chain.earliest_sha == "c1"
        assert chain.latest_sha == "c3"
        assert chain.commit_count == 3
        assert chain.early_timestamp == datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert chain.late_timestamp == datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc)
        assert chain.duration == timedelta(days=2)

    def test_multiple_disconnected_chains(self):
        """Test analysis of multiple disconnected chains."""
        graph = nx.Graph()
        
        # Chain 1: c1 -> c2
        graph.add_node(
            "c1",
            committed=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            sha="c1"
        )
        graph.add_node(
            "c2",
            committed=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            sha="c2"
        )
        graph.add_edge("c1", "c2")
        
        # Chain 2: c3 -> c4 (disconnected from chain 1)
        graph.add_node(
            "c3",
            committed=datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
            sha="c3"
        )
        graph.add_node(
            "c4",
            committed=datetime(2024, 2, 2, 12, 0, 0, tzinfo=timezone.utc),
            sha="c4"
        )
        graph.add_edge("c3", "c4")
        
        chains = analyze_commit_chains(graph)
        
        assert len(chains) == 2
        
        # Chains can be in any order, so sort them
        chains_by_sha = {chain.earliest_sha: chain for chain in chains}
        
        chain1 = chains_by_sha["c1"]
        assert chain1.latest_sha == "c2"
        assert chain1.commit_count == 2
        
        chain2 = chains_by_sha["c3"]
        assert chain2.latest_sha == "c4"
        assert chain2.commit_count == 2

    def test_single_node_chain(self):
        """Test analysis of a single isolated node."""
        graph = nx.Graph()
        graph.add_node(
            "c1",
            committed=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            sha="c1"
        )
        
        chains = analyze_commit_chains(graph)
        
        assert len(chains) == 1
        chain = chains[0]
        assert chain.earliest_sha == "c1"
        assert chain.latest_sha == "c1"
        assert chain.commit_count == 1
        assert chain.duration == timedelta(0)

    def test_chain_with_unordered_commits(self):
        """Test that chains correctly identify earliest/latest regardless of add order."""
        graph = nx.Graph()
        
        # Add commits in non-chronological order
        graph.add_node(
            "c3",
            committed=datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
            sha="c3"
        )
        graph.add_node(
            "c1",
            committed=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            sha="c1"
        )
        graph.add_node(
            "c2",
            committed=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            sha="c2"
        )
        graph.add_edge("c3", "c2")
        graph.add_edge("c1", "c2")
        
        chains = analyze_commit_chains(graph)
        
        assert len(chains) == 1
        chain = chains[0]
        # Should correctly identify c1 as earliest and c3 as latest
        assert chain.earliest_sha == "c1"
        assert chain.latest_sha == "c3"
        assert chain.commit_count == 3

    def test_chain_data_is_immutable(self):
        """Test that ChainData is immutable (frozen dataclass)."""
        graph = nx.Graph()
        graph.add_node(
            "c1",
            committed=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            sha="c1"
        )
        
        chains = analyze_commit_chains(graph)
        chain = chains[0]
        
        # Should raise error when trying to modify the frozen dataclass
        with self.assertRaises(FrozenInstanceError):
            chain.commit_count = 999

    def test_chain_data_sortable(self):
        """Test that ChainData objects can be sorted by early_timestamp."""
        chain1 = ChainData(
            early_timestamp=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            late_timestamp=datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
            commit_count=2,
            duration=timedelta(days=1),
            earliest_sha="c2",
            latest_sha="c3"
        )
        
        chain2 = ChainData(
            early_timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            late_timestamp=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            commit_count=2,
            duration=timedelta(days=1),
            earliest_sha="c1",
            latest_sha="c2"
        )
        
        chains = sorted([chain1, chain2])
        
        # Should be sorted by early_timestamp
        assert chains[0].earliest_sha == "c1"
        assert chains[1].earliest_sha == "c2"

    def test_complex_graph_structure(self):
        """Test a more complex graph with branches."""
        graph = nx.Graph()
        
        # Create a branching structure
        #     c2
        #    /  \
        #  c1    c4
        #    \  /
        #     c3
        times = {
            "c1": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "c2": datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            "c3": datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
            "c4": datetime(2024, 1, 4, 12, 0, 0, tzinfo=timezone.utc),
        }
        
        for sha, time in times.items():
            graph.add_node(sha, committed=time, sha=sha)
        
        graph.add_edge("c1", "c2")
        graph.add_edge("c1", "c3")
        graph.add_edge("c2", "c4")
        graph.add_edge("c3", "c4")
        
        chains = analyze_commit_chains(graph)
        
        # All nodes are connected, so should be one chain
        assert len(chains) == 1
        chain = chains[0]
        assert chain.commit_count == 4
        assert chain.earliest_sha == "c1"
        assert chain.latest_sha == "c4"
        assert chain.duration == timedelta(days=3)


if __name__ == "__main__":
    unittest.main()
