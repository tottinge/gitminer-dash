"""
Unit tests for commit graph building.
"""

import unittest
from unittest.mock import Mock
from datetime import datetime, timezone
from algorithms.commit_graph import build_commit_graph


class TestBuildCommitGraph(unittest.TestCase):
    """Test suite for build_commit_graph function."""

    def test_empty_commit_list(self):
        """Test that empty commit list returns empty graph."""
        graph = build_commit_graph([])
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_single_commit_with_parent(self):
        """Test basic case: one commit with one parent."""
        parent = Mock()
        parent.hexsha = "abc123"
        parent.committed_datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        commit = Mock()
        commit.hexsha = "def456"
        commit.committed_datetime = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        commit.parents = [parent]

        graph = build_commit_graph([commit])

        # Should have 2 nodes (parent and commit) and 1 edge
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert "abc123" in graph.nodes
        assert "def456" in graph.nodes
        assert graph.has_edge("abc123", "def456")

    def test_node_attributes(self):
        """Test that nodes have correct attributes."""
        parent = Mock()
        parent.hexsha = "abc123"
        parent.committed_datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        commit = Mock()
        commit.hexsha = "def456"
        commit.committed_datetime = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        commit.parents = [parent]

        graph = build_commit_graph([commit])

        # Check parent node attributes
        assert graph.nodes["abc123"]["committed"] == parent.committed_datetime
        assert graph.nodes["abc123"]["sha"] == "abc123"

        # Check commit node attributes
        assert graph.nodes["def456"]["committed"] == commit.committed_datetime
        assert graph.nodes["def456"]["sha"] == "def456"

    def test_merge_commits_skipped(self):
        """Test that merge commits (multiple parents) are skipped."""
        parent1 = Mock()
        parent1.hexsha = "abc123"
        parent1.committed_datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        parent2 = Mock()
        parent2.hexsha = "xyz789"
        parent2.committed_datetime = datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        merge_commit = Mock()
        merge_commit.hexsha = "merge999"
        merge_commit.committed_datetime = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        merge_commit.parents = [parent1, parent2]  # Multiple parents

        graph = build_commit_graph([merge_commit])

        # Merge commit should be skipped, resulting in empty graph
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_linear_chain(self):
        """Test a linear chain of commits."""
        commit1 = Mock()
        commit1.hexsha = "c1"
        commit1.committed_datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        commit1.parents = []

        commit2 = Mock()
        commit2.hexsha = "c2"
        commit2.committed_datetime = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        commit2.parents = [commit1]

        commit3 = Mock()
        commit3.hexsha = "c3"
        commit3.committed_datetime = datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc)
        commit3.parents = [commit2]

        graph = build_commit_graph([commit1, commit2, commit3])

        # Should have 3 nodes and 2 edges
        assert len(graph.nodes) == 3
        assert len(graph.edges) == 2
        assert graph.has_edge("c1", "c2")
        assert graph.has_edge("c2", "c3")

    def test_orphan_commit(self):
        """Test commit with no parents (initial commit)."""
        commit = Mock()
        commit.hexsha = "orphan"
        commit.committed_datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        commit.parents = []

        graph = build_commit_graph([commit])

        # Orphan commits are skipped (no parents to iterate over)
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_mixed_commits(self):
        """Test mix of regular commits and merge commits."""
        parent = Mock()
        parent.hexsha = "parent"
        parent.committed_datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        regular_commit = Mock()
        regular_commit.hexsha = "regular"
        regular_commit.committed_datetime = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        regular_commit.parents = [parent]

        parent2 = Mock()
        parent2.hexsha = "parent2"
        parent2.committed_datetime = datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc)

        merge_commit = Mock()
        merge_commit.hexsha = "merge"
        merge_commit.committed_datetime = datetime(2024, 1, 4, 12, 0, 0, tzinfo=timezone.utc)
        merge_commit.parents = [parent, parent2]

        graph = build_commit_graph([regular_commit, merge_commit])

        # Only regular commit should be in graph
        assert len(graph.nodes) == 2
        assert "parent" in graph.nodes
        assert "regular" in graph.nodes
        assert "merge" not in graph.nodes

    def test_duplicate_commits(self):
        """Test that duplicate commits don't create duplicate nodes."""
        parent = Mock()
        parent.hexsha = "parent"
        parent.committed_datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        commit = Mock()
        commit.hexsha = "commit"
        commit.committed_datetime = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        commit.parents = [parent]

        # Pass the same commit twice
        graph = build_commit_graph([commit, commit])

        # Should still only have 2 nodes
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1


if __name__ == "__main__":
    unittest.main()
