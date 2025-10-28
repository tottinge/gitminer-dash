"""
Unit tests for the affinity calculator module.
"""
import unittest
from unittest.mock import Mock
from algorithms.affinity_calculator import calculate_affinities


class TestAffinityCalculator(unittest.TestCase):
    """Test suite for the calculate_affinities function."""
    
    def test_empty_list(self):
        """Test that empty list returns empty affinities."""
        affinities = calculate_affinities([])
        assert len(affinities) == 0
    
    def test_none_input(self):
        """Test that None input returns empty affinities."""
        affinities = calculate_affinities(None)
        assert len(affinities) == 0
    
    def test_single_file_commits_ignored(self):
        """Test that commits with only one file are ignored."""
        commit = Mock()
        commit.stats.files = {'a.py': {}}
        
        affinities = calculate_affinities([commit])
        assert len(affinities) == 0
    
    def test_two_file_commit(self):
        """Test affinity calculation for a commit with two files."""
        commit = Mock()
        commit.stats.files = {'a.py': {}, 'b.py': {}}
        
        affinities = calculate_affinities([commit])
        
        # Should have one pair with affinity 1/2 = 0.5
        assert len(affinities) == 1
        assert affinities[('a.py', 'b.py')] == 0.5
    
    def test_three_file_commit(self):
        """Test affinity calculation for a commit with three files."""
        commit = Mock()
        commit.stats.files = {'a.py': {}, 'b.py': {}, 'c.py': {}}
        
        affinities = calculate_affinities([commit])
        
        # Should have 3 pairs, each with affinity 1/3
        assert len(affinities) == 3
        assert affinities[('a.py', 'b.py')] == 1/3
        assert affinities[('a.py', 'c.py')] == 1/3
        assert affinities[('b.py', 'c.py')] == 1/3
    
    def test_multiple_commits_accumulate(self):
        """Test that affinities accumulate across multiple commits."""
        commit1 = Mock()
        commit1.stats.files = {'a.py': {}, 'b.py': {}}
        
        commit2 = Mock()
        commit2.stats.files = {'a.py': {}, 'b.py': {}}
        
        affinities = calculate_affinities([commit1, commit2])
        
        # Both commits contribute 0.5, total should be 1.0
        assert affinities[('a.py', 'b.py')] == 1.0
    
    def test_file_pair_ordering(self):
        """Test that file pairs are always sorted consistently."""
        commit = Mock()
        commit.stats.files = {'z.py': {}, 'a.py': {}}
        
        affinities = calculate_affinities([commit])
        
        # Should be sorted alphabetically
        assert ('a.py', 'z.py') in affinities
        assert ('z.py', 'a.py') not in affinities
    
    def test_mixed_file_counts(self):
        """Test commits with different numbers of files."""
        commit1 = Mock()
        commit1.stats.files = {'a.py': {}, 'b.py': {}}  # 2 files
        
        commit2 = Mock()
        commit2.stats.files = {'b.py': {}, 'c.py': {}, 'd.py': {}}  # 3 files
        
        affinities = calculate_affinities([commit1, commit2])
        
        # a-b: 1/2 from commit1
        assert affinities[('a.py', 'b.py')] == 0.5
        
        # b-c: 1/3 from commit2
        assert affinities[('b.py', 'c.py')] == 1/3
        
        # b-d: 1/3 from commit2  
        assert affinities[('b.py', 'd.py')] == 1/3
        
        # c-d: 1/3 from commit2
        assert affinities[('c.py', 'd.py')] == 1/3
    
    def test_iterator_consumption(self):
        """Test that function handles iterators properly by converting to list."""
        commit1 = Mock()
        commit1.stats.files = {'a.py': {}, 'b.py': {}}
        
        commit2 = Mock()
        commit2.stats.files = {'c.py': {}, 'd.py': {}}
        
        # Create a generator (iterator)
        def commit_generator():
            yield commit1
            yield commit2
        
        affinities = calculate_affinities(commit_generator())
        
        # Should process both commits even though it's an iterator
        assert len(affinities) == 2
        assert ('a.py', 'b.py') in affinities
        assert ('c.py', 'd.py') in affinities
    
    def test_real_world_scenario(self):
        """Test a realistic scenario with multiple overlapping files."""
        # Commit 1: Modified config and main
        commit1 = Mock()
        commit1.stats.files = {'config.py': {}, 'main.py': {}}
        
        # Commit 2: Modified config and utils
        commit2 = Mock()
        commit2.stats.files = {'config.py': {}, 'utils.py': {}}
        
        # Commit 3: Modified all three
        commit3 = Mock()
        commit3.stats.files = {'config.py': {}, 'main.py': {}, 'utils.py': {}}
        
        affinities = calculate_affinities([commit1, commit2, commit3])
        
        # config-main: 1/2 (commit1) + 1/3 (commit3) = 0.5 + 0.333... = 0.833...
        assert abs(affinities[('config.py', 'main.py')] - (0.5 + 1/3)) < 0.001
        
        # config-utils: 1/2 (commit2) + 1/3 (commit3) = 0.5 + 0.333... = 0.833...
        assert abs(affinities[('config.py', 'utils.py')] - (0.5 + 1/3)) < 0.001
        
        # main-utils: 1/3 (commit3) = 0.333...
        assert abs(affinities[('main.py', 'utils.py')] - 1/3) < 0.001


if __name__ == '__main__':
    unittest.main()
