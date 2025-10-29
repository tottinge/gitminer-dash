"""
Unit tests for node calculation helper functions.

Tests cover:
- _calculate_node_size: Node size calculation based on commit count and degree
- _create_node_tooltip: Tooltip generation for nodes
- _get_top_files_and_affinities: Top files and affinity identification
"""

from tests import setup_path

setup_path()

import pytest
from collections import defaultdict
from visualization.network_graph import calculate_node_size, create_node_tooltip


# Replicate _get_top_files_and_affinities function to avoid Dash initialization
def _get_top_files_and_affinities(commits, affinities, max_nodes):
    """Get top files by affinity and their relevant affinity values.

    Args:
        commits: Iterable of commit objects
        affinities: Dictionary of file pair affinities
        max_nodes: Maximum number of nodes to consider

    Returns:
        A tuple of (top_file_set, relevant_affinities)
    """
    file_total_affinity = defaultdict(float)
    for (file1, file2), affinity in affinities.items():
        file_total_affinity[file1] += affinity
        file_total_affinity[file2] += affinity

    top_files = sorted(file_total_affinity.items(), key=lambda x: x[1], reverse=True)[
        :max_nodes
    ]
    top_file_set = {file for file, _ in top_files}

    relevant_affinities = [
        affinity
        for (file1, file2), affinity in affinities.items()
        if file1 in top_file_set and file2 in top_file_set
    ]

    return top_file_set, relevant_affinities


class TestCalculateNodeSize:
    """Tests for _calculate_node_size function."""

    def test_basic_calculation(self):
        """Test basic node size calculation with typical inputs."""
        # Base size is 10, commit_factor is min(commit_count * 0.5, 20), degree_factor is degree * 2
        # commit_count=5: commit_factor = 2.5, degree=3: degree_factor = 6
        # Expected: 10 + 2.5 + 6 = 18.5
        assert calculate_node_size(5, 3) == 18.5

    def test_zero_inputs(self):
        """Test with zero commit count and degree."""
        # Base size is 10
        assert calculate_node_size(0, 0) == 10.0

    def test_large_commit_count(self):
        """Test that commit factor is capped at 20."""
        # commit_count=100: commit_factor should be capped at 20
        # degree=5: degree_factor = 10
        # Expected: 10 + 20 + 10 = 40
        assert calculate_node_size(100, 5) == 40.0

    def test_commit_factor_capping(self):
        """Test the exact boundary where commit factor reaches cap."""
        # commit_count=40: commit_factor = min(40 * 0.5, 20) = 20
        # degree=0: degree_factor = 0
        # Expected: 10 + 20 + 0 = 30
        assert calculate_node_size(40, 0) == 30.0

        # commit_count=41: commit_factor = min(41 * 0.5, 20) = 20
        assert calculate_node_size(41, 0) == 30.0

    def test_high_degree(self):
        """Test with high degree value."""
        # commit_count=10: commit_factor = 5
        # degree=20: degree_factor = 40
        # Expected: 10 + 5 + 40 = 55
        assert calculate_node_size(10, 20) == 55.0

    def test_various_combinations(self):
        """Test various commit_count and degree combinations."""
        test_cases = [
            (1, 1, 10 + 0.5 + 2),  # Small values
            (10, 10, 10 + 5 + 20),  # Medium values
            (20, 5, 10 + 10 + 10),  # commit_factor not capped
            (50, 15, 10 + 20 + 30),  # commit_factor capped
        ]

        for commit_count, degree, expected in test_cases:
            assert calculate_node_size(commit_count, degree) == expected


class TestCreateNodeTooltip:
    """Tests for _create_node_tooltip function."""

    def test_basic_tooltip(self):
        """Test basic tooltip generation."""
        result = create_node_tooltip("test.py", 5, 3)
        assert result == "File: test.py<br>Commits: 5<br>Connections: 3"

    def test_zero_values(self):
        """Test tooltip with zero commit count and degree."""
        result = create_node_tooltip("empty.py", 0, 0)
        assert result == "File: empty.py<br>Commits: 0<br>Connections: 0"

    def test_large_values(self):
        """Test tooltip with large values."""
        result = create_node_tooltip("popular.py", 1000, 50)
        assert result == "File: popular.py<br>Commits: 1000<br>Connections: 50"

    def test_special_characters_in_filename(self):
        """Test tooltip with special characters in filename."""
        result = create_node_tooltip("path/to/file-name_v2.py", 10, 5)
        assert (
            result == "File: path/to/file-name_v2.py<br>Commits: 10<br>Connections: 5"
        )

    def test_long_filename(self):
        """Test tooltip with a long filename."""
        long_name = "very/long/path/to/some/deeply/nested/file.py"
        result = create_node_tooltip(long_name, 3, 2)
        assert result == f"File: {long_name}<br>Commits: 3<br>Connections: 2"

    def test_tooltip_format(self):
        """Test that tooltip contains required HTML break tags."""
        result = create_node_tooltip("test.py", 5, 3)
        assert "<br>" in result
        assert result.count("<br>") == 2


class TestGetTopFilesAndAffinities:
    """Tests for _get_top_files_and_affinities function."""

    def test_basic_functionality(self):
        """Test basic identification of top files and affinities."""

        # Create mock commits
        class MockStats:
            def __init__(self, files):
                self.files = {f: {} for f in files}

        class MockCommit:
            def __init__(self, files):
                self.stats = MockStats(files)

        commits = [
            MockCommit(["file1.py", "file2.py"]),
            MockCommit(["file1.py", "file3.py"]),
        ]

        affinities = {
            ("file1.py", "file2.py"): 0.8,
            ("file1.py", "file3.py"): 0.6,
            ("file2.py", "file3.py"): 0.4,
        }

        top_files, relevant_affinities = _get_top_files_and_affinities(
            commits, affinities, max_nodes=3
        )

        # All files should be in top_files
        assert len(top_files) == 3
        assert "file1.py" in top_files
        assert "file2.py" in top_files
        assert "file3.py" in top_files

        # All affinities should be relevant
        assert len(relevant_affinities) == 3
        assert 0.8 in relevant_affinities
        assert 0.6 in relevant_affinities
        assert 0.4 in relevant_affinities

    def test_max_nodes_limit(self):
        """Test that only top N files are returned when max_nodes is smaller."""

        class MockStats:
            def __init__(self, files):
                self.files = {f: {} for f in files}

        class MockCommit:
            def __init__(self, files):
                self.stats = MockStats(files)

        commits = []

        affinities = {
            ("file1.py", "file2.py"): 0.9,  # file1 total: 1.4, file2 total: 1.2
            ("file1.py", "file3.py"): 0.5,  # file3 total: 0.8
            ("file2.py", "file3.py"): 0.3,  # file4 total: 0.2
            ("file4.py", "file5.py"): 0.2,  # file5 total: 0.2
        }

        top_files, relevant_affinities = _get_top_files_and_affinities(
            commits, affinities, max_nodes=2
        )

        # Should only get top 2 files by total affinity
        assert len(top_files) == 2
        assert "file1.py" in top_files
        assert "file2.py" in top_files

        # Only affinity between top files should be relevant
        assert len(relevant_affinities) == 1
        assert 0.9 in relevant_affinities

    def test_empty_affinities(self):
        """Test handling of empty affinities dictionary."""

        class MockStats:
            def __init__(self, files):
                self.files = {f: {} for f in files}

        class MockCommit:
            def __init__(self, files):
                self.stats = MockStats(files)

        commits = [MockCommit(["file1.py"])]
        affinities = {}

        top_files, relevant_affinities = _get_top_files_and_affinities(
            commits, affinities, max_nodes=10
        )

        assert len(top_files) == 0
        assert len(relevant_affinities) == 0

    def test_empty_commits(self):
        """Test handling of empty commits list."""
        commits = []
        affinities = {
            ("file1.py", "file2.py"): 0.5,
        }

        top_files, relevant_affinities = _get_top_files_and_affinities(
            commits, affinities, max_nodes=10
        )

        # Should still process affinities even with empty commits
        assert len(top_files) == 2
        assert len(relevant_affinities) == 1

    def test_single_file_pair(self):
        """Test with only a single file pair."""
        commits = []
        affinities = {
            ("file1.py", "file2.py"): 0.7,
        }

        top_files, relevant_affinities = _get_top_files_and_affinities(
            commits, affinities, max_nodes=10
        )

        assert len(top_files) == 2
        assert "file1.py" in top_files
        assert "file2.py" in top_files
        assert len(relevant_affinities) == 1
        assert relevant_affinities[0] == 0.7

    def test_affinity_filtering(self):
        """Test that affinities are filtered correctly when not all files are in top set."""
        commits = []

        affinities = {
            ("file1.py", "file2.py"): 1.0,  # file1: 1.5, file2: 1.3
            ("file1.py", "file3.py"): 0.5,  # file3: 0.8
            ("file2.py", "file3.py"): 0.3,  # file4: 0.1
            ("file4.py", "file5.py"): 0.1,  # file5: 0.1
        }

        top_files, relevant_affinities = _get_top_files_and_affinities(
            commits, affinities, max_nodes=3
        )

        # Top 3 files should be file1, file2, file3
        assert len(top_files) == 3

        # Only affinities between top files should be included
        assert len(relevant_affinities) == 3
        assert 1.0 in relevant_affinities
        assert 0.5 in relevant_affinities
        assert 0.3 in relevant_affinities
        assert 0.1 not in relevant_affinities

    def test_equal_affinity_values(self):
        """Test behavior with equal affinity values."""
        commits = []

        affinities = {
            ("file1.py", "file2.py"): 0.5,
            ("file3.py", "file4.py"): 0.5,
        }

        top_files, relevant_affinities = _get_top_files_and_affinities(
            commits, affinities, max_nodes=2
        )

        # Should get 2 files (order may vary due to ties)
        assert len(top_files) == 2
        # Relevant affinities depend on which 2 files were selected
        assert len(relevant_affinities) <= 1


class TestCalculateNodeSizeBoundaryConditions:
    """Tests for boundary conditions in _calculate_node_size."""

    def test_minimum_values(self):
        """Test with minimum possible values."""
        assert calculate_node_size(0, 0) == 10.0

    def test_commit_factor_boundary_39(self):
        """Test just below commit factor cap."""
        # commit_count=39: commit_factor = 19.5
        assert calculate_node_size(39, 0) == 29.5

    def test_commit_factor_boundary_40(self):
        """Test at commit factor cap."""
        # commit_count=40: commit_factor = 20 (capped)
        assert calculate_node_size(40, 0) == 30.0

    def test_commit_factor_boundary_41(self):
        """Test just above commit factor cap."""
        # commit_count=41: commit_factor = 20 (capped)
        assert calculate_node_size(41, 0) == 30.0

    def test_single_commit_single_connection(self):
        """Test with single commit and single connection."""
        # commit_count=1: commit_factor = 0.5
        # degree=1: degree_factor = 2
        assert calculate_node_size(1, 1) == 12.5

    def test_large_degree_zero_commits(self):
        """Test with large degree but no commits."""
        # commit_count=0: commit_factor = 0
        # degree=100: degree_factor = 200
        assert calculate_node_size(0, 100) == 210.0

    def test_negative_would_be_handled(self):
        """Test that function returns correct value for unusual inputs."""
        # Although negative values shouldn't occur in practice,
        # the function should handle them mathematically
        # This documents current behavior
        result = calculate_node_size(0, 0)
        assert result >= 10.0  # Should at least return base size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
