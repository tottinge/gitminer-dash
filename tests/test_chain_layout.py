"""
Unit tests for chain layout calculator.
"""

import unittest
from datetime import datetime, timedelta, timezone
from algorithms.chain_layout import calculate_chain_layout
from algorithms.chain_models import ClampedChain, TimelineRow


class TestCalculateChainLayout(unittest.TestCase):
    """Test suite for calculate_chain_layout function."""

    def test_empty_chains(self):
        """Test that empty chains list returns empty rows."""
        rows = calculate_chain_layout([])
        assert len(rows) == 0

    def test_single_chain(self):
        """Test layout of a single chain."""
        chain = ClampedChain(
            clamped_first=datetime(2024, 1, 1, tzinfo=timezone.utc),
            clamped_last=datetime(2024, 1, 10, tzinfo=timezone.utc),
            clamped_duration=timedelta(days=9),
            commit_count=5,
            earliest_sha="abc",
            latest_sha="def"
        )
        
        rows = calculate_chain_layout([chain])
        
        assert len(rows) == 1
        row = rows[0]
        assert row.first == datetime(2024, 1, 1, tzinfo=timezone.utc)
        assert row.last == datetime(2024, 1, 10, tzinfo=timezone.utc)
        assert row.elevation == 1  # First chain should be at level 1
        assert row.commit_counts == 5
        assert row.head == "abc"
        assert row.tail == "def"
        assert row.duration == 9
        assert row.density == 9 / 5

    def test_non_overlapping_chains_same_level(self):
        """Test that non-overlapping chains get same elevation."""
        chains = [
            ClampedChain(
                clamped_first=datetime(2024, 1, 1, tzinfo=timezone.utc),
                clamped_last=datetime(2024, 1, 5, tzinfo=timezone.utc),
                clamped_duration=timedelta(days=4),
                commit_count=2,
                earliest_sha="c1",
                latest_sha="c2"
            ),
            ClampedChain(
                clamped_first=datetime(2024, 1, 10, tzinfo=timezone.utc),
                clamped_last=datetime(2024, 1, 15, tzinfo=timezone.utc),
                clamped_duration=timedelta(days=5),
                commit_count=3,
                earliest_sha="c3",
                latest_sha="c4"
            ),
        ]
        
        rows = calculate_chain_layout(chains)
        
        assert len(rows) == 2
        # Both should be at elevation 1 (no overlap)
        assert rows[0].elevation == 1
        assert rows[1].elevation == 1

    def test_overlapping_chains_different_levels(self):
        """Test that overlapping chains get different elevations."""
        chains = [
            ClampedChain(
                clamped_first=datetime(2024, 1, 1, tzinfo=timezone.utc),
                clamped_last=datetime(2024, 1, 10, tzinfo=timezone.utc),
                clamped_duration=timedelta(days=9),
                commit_count=2,
                earliest_sha="c1",
                latest_sha="c2"
            ),
            ClampedChain(
                clamped_first=datetime(2024, 1, 5, tzinfo=timezone.utc),
                clamped_last=datetime(2024, 1, 15, tzinfo=timezone.utc),
                clamped_duration=timedelta(days=10),
                commit_count=3,
                earliest_sha="c3",
                latest_sha="c4"
            ),
        ]
        
        rows = calculate_chain_layout(chains)
        
        assert len(rows) == 2
        # Should be at different elevations (overlap)
        assert rows[0].elevation == 1
        assert rows[1].elevation == 2

    def test_zero_duration_chain(self):
        """Test chain with zero duration."""
        chain = ClampedChain(
            clamped_first=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            clamped_last=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            clamped_duration=timedelta(0),
            commit_count=1,
            earliest_sha="single",
            latest_sha="single"
        )
        
        rows = calculate_chain_layout([chain])
        
        assert len(rows) == 1
        row = rows[0]
        assert row.duration == 0
        assert row.density == 0

    def test_zero_commit_count_density(self):
        """Test that zero commit count results in zero density (not division by zero)."""
        chain = ClampedChain(
            clamped_first=datetime(2024, 1, 1, tzinfo=timezone.utc),
            clamped_last=datetime(2024, 1, 10, tzinfo=timezone.utc),
            clamped_duration=timedelta(days=9),
            commit_count=0,  # Edge case
            earliest_sha="abc",
            latest_sha="def"
        )
        
        rows = calculate_chain_layout([chain])
        
        assert len(rows) == 1
        row = rows[0]
        assert row.density == 0  # Should not raise division by zero

    def test_density_calculation(self):
        """Test that density is correctly calculated as days per commit."""
        chains = [
            ClampedChain(
                clamped_first=datetime(2024, 1, 1, tzinfo=timezone.utc),
                clamped_last=datetime(2024, 1, 11, tzinfo=timezone.utc),
                clamped_duration=timedelta(days=10),
                commit_count=5,
                earliest_sha="c1",
                latest_sha="c2"
            ),
            ClampedChain(
                clamped_first=datetime(2024, 2, 1, tzinfo=timezone.utc),
                clamped_last=datetime(2024, 2, 21, tzinfo=timezone.utc),
                clamped_duration=timedelta(days=20),
                commit_count=4,
                earliest_sha="c3",
                latest_sha="c4"
            ),
        ]
        
        rows = calculate_chain_layout(chains)
        
        assert rows[0].density == 10 / 5  # 2.0
        assert rows[1].density == 20 / 4  # 5.0

    def test_preserves_all_metadata(self):
        """Test that all chain metadata is preserved in rows."""
        chain = ClampedChain(
            clamped_first=datetime(2024, 1, 1, tzinfo=timezone.utc),
            clamped_last=datetime(2024, 1, 10, tzinfo=timezone.utc),
            clamped_duration=timedelta(days=9),
            commit_count=42,
            earliest_sha="first_commit_sha",
            latest_sha="last_commit_sha"
        )
        
        rows = calculate_chain_layout([chain])
        row = rows[0]
        
        # Verify all metadata preserved
        assert row.commit_counts == 42
        assert row.head == "first_commit_sha"
        assert row.tail == "last_commit_sha"
        assert row.first == chain.clamped_first
        assert row.last == chain.clamped_last

    def test_multiple_chains_complex_stacking(self):
        """Test complex stacking scenario with multiple overlaps."""
        chains = [
            # Level 1
            ClampedChain(
                clamped_first=datetime(2024, 1, 1, tzinfo=timezone.utc),
                clamped_last=datetime(2024, 1, 5, tzinfo=timezone.utc),
                clamped_duration=timedelta(days=4),
                commit_count=2,
                earliest_sha="c1",
                latest_sha="c2"
            ),
            # Level 2 (overlaps with c1)
            ClampedChain(
                clamped_first=datetime(2024, 1, 3, tzinfo=timezone.utc),
                clamped_last=datetime(2024, 1, 7, tzinfo=timezone.utc),
                clamped_duration=timedelta(days=4),
                commit_count=2,
                earliest_sha="c3",
                latest_sha="c4"
            ),
            # Level 1 (doesn't overlap with c1)
            ClampedChain(
                clamped_first=datetime(2024, 1, 10, tzinfo=timezone.utc),
                clamped_last=datetime(2024, 1, 15, tzinfo=timezone.utc),
                clamped_duration=timedelta(days=5),
                commit_count=3,
                earliest_sha="c5",
                latest_sha="c6"
            ),
            # Level 2 (overlaps with c5)
            ClampedChain(
                clamped_first=datetime(2024, 1, 12, tzinfo=timezone.utc),
                clamped_last=datetime(2024, 1, 17, tzinfo=timezone.utc),
                clamped_duration=timedelta(days=5),
                commit_count=3,
                earliest_sha="c7",
                latest_sha="c8"
            ),
        ]
        
        rows = calculate_chain_layout(chains)
        
        assert len(rows) == 4
        assert rows[0].elevation == 1  # c1
        assert rows[1].elevation == 2  # c3 (overlaps c1)
        assert rows[2].elevation == 1  # c5 (doesn't overlap c1)
        assert rows[3].elevation == 2  # c7 (overlaps c5)

    def test_timeline_row_is_immutable(self):
        """Test that TimelineRow is immutable (frozen dataclass)."""
        chain = ClampedChain(
            clamped_first=datetime(2024, 1, 1, tzinfo=timezone.utc),
            clamped_last=datetime(2024, 1, 10, tzinfo=timezone.utc),
            clamped_duration=timedelta(days=9),
            commit_count=5,
            earliest_sha="abc",
            latest_sha="def"
        )
        
        rows = calculate_chain_layout([chain])
        row = rows[0]
        
        # Should raise error when trying to modify
        with self.assertRaises(Exception):  # FrozenInstanceError
            row.elevation = 999

    def test_order_independence(self):
        """Test that output order matches input order."""
        chains = [
            ClampedChain(
                clamped_first=datetime(2024, 1, 10, tzinfo=timezone.utc),
                clamped_last=datetime(2024, 1, 15, tzinfo=timezone.utc),
                clamped_duration=timedelta(days=5),
                commit_count=2,
                earliest_sha="second",
                latest_sha="second_end"
            ),
            ClampedChain(
                clamped_first=datetime(2024, 1, 1, tzinfo=timezone.utc),
                clamped_last=datetime(2024, 1, 5, tzinfo=timezone.utc),
                clamped_duration=timedelta(days=4),
                commit_count=2,
                earliest_sha="first",
                latest_sha="first_end"
            ),
        ]
        
        rows = calculate_chain_layout(chains)
        
        # Output should be in same order as input
        assert rows[0].head == "second"
        assert rows[1].head == "first"


if __name__ == "__main__":
    unittest.main()
