"""Unit tests for the affinity calculator module."""

from unittest.mock import Mock

import pytest

from algorithms.affinity_calculator import calculate_affinities


def test_empty_list():
    """Test that empty list returns empty affinities."""
    affinities = calculate_affinities([])
    assert len(affinities) == 0


def test_none_input():
    """Test that None input returns empty affinities."""
    affinities = calculate_affinities(None)
    assert len(affinities) == 0


def test_single_file_commits_ignored():
    """Test that commits with only one file are ignored."""
    commit = Mock()
    commit.stats.files = {"a.py": {}}
    affinities = calculate_affinities([commit])
    assert len(affinities) == 0


def test_two_file_commit():
    """Test affinity calculation for a commit with two files."""
    commit = Mock()
    commit.stats.files = {"a.py": {}, "b.py": {}}
    affinities = calculate_affinities([commit])
    assert len(affinities) == 1
    assert affinities["a.py", "b.py"] == 0.5


def test_three_file_commit():
    """Test affinity calculation for a commit with three files."""
    commit = Mock()
    commit.stats.files = {"a.py": {}, "b.py": {}, "c.py": {}}
    affinities = calculate_affinities([commit])
    assert len(affinities) == 3
    assert affinities["a.py", "b.py"] == 1 / 3
    assert affinities["a.py", "c.py"] == 1 / 3
    assert affinities["b.py", "c.py"] == 1 / 3


def test_multiple_commits_accumulate():
    """Test that affinities accumulate across multiple commits."""
    commit1 = Mock()
    commit1.stats.files = {"a.py": {}, "b.py": {}}
    commit2 = Mock()
    commit2.stats.files = {"a.py": {}, "b.py": {}}
    affinities = calculate_affinities([commit1, commit2])
    assert affinities["a.py", "b.py"] == 1.0


def test_file_pair_ordering():
    """Test that file pairs are always sorted consistently."""
    commit = Mock()
    commit.stats.files = {"z.py": {}, "a.py": {}}
    affinities = calculate_affinities([commit])
    assert ("a.py", "z.py") in affinities
    assert ("z.py", "a.py") not in affinities


def test_mixed_file_counts():
    """Test commits with different numbers of files."""
    commit1 = Mock()
    commit1.stats.files = {"a.py": {}, "b.py": {}}
    commit2 = Mock()
    commit2.stats.files = {"b.py": {}, "c.py": {}, "d.py": {}}
    affinities = calculate_affinities([commit1, commit2])
    assert affinities["a.py", "b.py"] == 0.5
    assert affinities["b.py", "c.py"] == 1 / 3
    assert affinities["b.py", "d.py"] == 1 / 3
    assert affinities["c.py", "d.py"] == 1 / 3


def test_iterator_consumption():
    """Test that function handles iterators properly by converting to list."""
    commit1 = Mock()
    commit1.stats.files = {"a.py": {}, "b.py": {}}
    commit2 = Mock()
    commit2.stats.files = {"c.py": {}, "d.py": {}}

    def commit_generator():
        yield commit1
        yield commit2

    affinities = calculate_affinities(commit_generator())
    assert len(affinities) == 2
    assert ("a.py", "b.py") in affinities
    assert ("c.py", "d.py") in affinities


def test_real_world_scenario():
    """Test a realistic scenario with multiple overlapping files."""
    commit1 = Mock()
    commit1.stats.files = {"config.py": {}, "main.py": {}}
    commit2 = Mock()
    commit2.stats.files = {"config.py": {}, "utils.py": {}}
    commit3 = Mock()
    commit3.stats.files = {"config.py": {}, "main.py": {}, "utils.py": {}}
    affinities = calculate_affinities([commit1, commit2, commit3])
    assert abs(affinities["config.py", "main.py"] - (0.5 + 1 / 3)) < 0.001
    assert abs(affinities["config.py", "utils.py"] - (0.5 + 1 / 3)) < 0.001
    assert abs(affinities["main.py", "utils.py"] - 1 / 3) < 0.001


if __name__ == "__main__":
    pytest.main([__file__])
