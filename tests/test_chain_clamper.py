"""
Unit and property-based tests for chain clamping.
"""

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

from algorithms.chain_clamper import clamp_chains_to_period
from algorithms.chain_models import ChainData


class TestClampChainsToPeriod(unittest.TestCase):
    """Test suite for clamp_chains_to_period function."""

    def test_empty_chains_list(self):
        """Test that empty chains list returns empty result."""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = clamp_chains_to_period([], start, end)
        assert len(result) == 0

    def test_chain_within_period(self):
        """Test chain that falls completely within the period."""
        chain = ChainData(
            early_timestamp=datetime(2024, 1, 10, tzinfo=timezone.utc),
            late_timestamp=datetime(2024, 1, 20, tzinfo=timezone.utc),
            commit_count=5,
            duration=timedelta(days=10),
            earliest_sha="abc",
            latest_sha="def",
        )

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = clamp_chains_to_period([chain], start, end)

        assert len(result) == 1
        clamped = result[0]
        # Should not be clamped at all
        assert clamped.clamped_first == chain.early_timestamp
        assert clamped.clamped_last == chain.late_timestamp
        assert clamped.clamped_duration == timedelta(days=10)
        assert clamped.commit_count == 5

    def test_chain_before_period(self):
        """Test chain that falls completely before the period."""
        chain = ChainData(
            early_timestamp=datetime(2023, 12, 1, tzinfo=timezone.utc),
            late_timestamp=datetime(2023, 12, 15, tzinfo=timezone.utc),
            commit_count=3,
            duration=timedelta(days=14),
            earliest_sha="abc",
            latest_sha="def",
        )

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = clamp_chains_to_period([chain], start, end)

        # Chain should be filtered out
        assert len(result) == 0

    def test_chain_after_period(self):
        """Test chain that falls completely after the period."""
        chain = ChainData(
            early_timestamp=datetime(2024, 2, 1, tzinfo=timezone.utc),
            late_timestamp=datetime(2024, 2, 15, tzinfo=timezone.utc),
            commit_count=3,
            duration=timedelta(days=14),
            earliest_sha="abc",
            latest_sha="def",
        )

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = clamp_chains_to_period([chain], start, end)

        # Chain should be filtered out
        assert len(result) == 0

    def test_chain_overlaps_start(self):
        """Test chain that starts before period but ends within it."""
        chain = ChainData(
            early_timestamp=datetime(2023, 12, 20, tzinfo=timezone.utc),
            late_timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            commit_count=5,
            duration=timedelta(days=26),
            earliest_sha="abc",
            latest_sha="def",
        )

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = clamp_chains_to_period([chain], start, end)

        assert len(result) == 1
        clamped = result[0]
        # Should be clamped at the start
        assert clamped.clamped_first == start
        assert clamped.clamped_last == chain.late_timestamp
        assert clamped.clamped_duration == timedelta(days=14)

    def test_chain_overlaps_end(self):
        """Test chain that starts within period but ends after it."""
        chain = ChainData(
            early_timestamp=datetime(2024, 1, 20, tzinfo=timezone.utc),
            late_timestamp=datetime(2024, 2, 10, tzinfo=timezone.utc),
            commit_count=5,
            duration=timedelta(days=21),
            earliest_sha="abc",
            latest_sha="def",
        )

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = clamp_chains_to_period([chain], start, end)

        assert len(result) == 1
        clamped = result[0]
        # Should be clamped at the end
        assert clamped.clamped_first == chain.early_timestamp
        assert clamped.clamped_last == end
        assert clamped.clamped_duration == timedelta(days=11)

    def test_chain_spans_entire_period(self):
        """Test chain that starts before and ends after the period."""
        chain = ChainData(
            early_timestamp=datetime(2023, 12, 1, tzinfo=timezone.utc),
            late_timestamp=datetime(2024, 2, 28, tzinfo=timezone.utc),
            commit_count=10,
            duration=timedelta(days=89),
            earliest_sha="abc",
            latest_sha="def",
        )

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = clamp_chains_to_period([chain], start, end)

        assert len(result) == 1
        clamped = result[0]
        # Should be clamped at both ends
        assert clamped.clamped_first == start
        assert clamped.clamped_last == end
        assert clamped.clamped_duration == timedelta(days=30)

    def test_multiple_chains_mixed(self):
        """Test multiple chains with various overlaps."""
        chains = [
            # Chain 1: completely within period
            ChainData(
                early_timestamp=datetime(2024, 1, 10, tzinfo=timezone.utc),
                late_timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
                commit_count=3,
                duration=timedelta(days=5),
                earliest_sha="c1",
                latest_sha="c2",
            ),
            # Chain 2: outside period (before)
            ChainData(
                early_timestamp=datetime(2023, 12, 1, tzinfo=timezone.utc),
                late_timestamp=datetime(2023, 12, 15, tzinfo=timezone.utc),
                commit_count=2,
                duration=timedelta(days=14),
                earliest_sha="c3",
                latest_sha="c4",
            ),
            # Chain 3: overlaps start
            ChainData(
                early_timestamp=datetime(2023, 12, 25, tzinfo=timezone.utc),
                late_timestamp=datetime(2024, 1, 5, tzinfo=timezone.utc),
                commit_count=4,
                duration=timedelta(days=11),
                earliest_sha="c5",
                latest_sha="c6",
            ),
        ]

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = clamp_chains_to_period(chains, start, end)

        # Should filter out chain 2
        assert len(result) == 2

        # Verify by SHA
        result_by_sha = {r.earliest_sha: r for r in result}

        # Chain 1: unchanged
        assert result_by_sha["c1"].clamped_first == datetime(
            2024, 1, 10, tzinfo=timezone.utc
        )

        # Chain 3: clamped at start
        assert result_by_sha["c5"].clamped_first == start

    def test_preserves_commit_count_and_shas(self):
        """Test that clamping preserves original commit count and SHAs."""
        chain = ChainData(
            early_timestamp=datetime(2023, 12, 1, tzinfo=timezone.utc),
            late_timestamp=datetime(2024, 2, 28, tzinfo=timezone.utc),
            commit_count=42,
            duration=timedelta(days=89),
            earliest_sha="first_commit",
            latest_sha="last_commit",
        )

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = clamp_chains_to_period([chain], start, end)

        clamped = result[0]
        # These should be preserved even though timestamps are clamped
        assert clamped.commit_count == 42
        assert clamped.earliest_sha == "first_commit"
        assert clamped.latest_sha == "last_commit"

    def test_zero_duration_chain(self):
        """Test chain with zero duration (single instant)."""
        instant = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        chain = ChainData(
            early_timestamp=instant,
            late_timestamp=instant,
            commit_count=1,
            duration=timedelta(0),
            earliest_sha="single",
            latest_sha="single",
        )

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = clamp_chains_to_period([chain], start, end)

        assert len(result) == 1
        clamped = result[0]
        assert clamped.clamped_duration == timedelta(0)

    def test_clamped_chain_is_immutable(self):
        """Test that ClampedChain is immutable (frozen dataclass)."""
        chain = ChainData(
            early_timestamp=datetime(2024, 1, 10, tzinfo=timezone.utc),
            late_timestamp=datetime(2024, 1, 20, tzinfo=timezone.utc),
            commit_count=5,
            duration=timedelta(days=10),
            earliest_sha="abc",
            latest_sha="def",
        )

        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = clamp_chains_to_period([chain], start, end)
        clamped = result[0]

        # Should raise error when trying to modify the frozen dataclass
        with self.assertRaises(FrozenInstanceError):
            clamped.commit_count = 999


class TestClampingProperties(unittest.TestCase):
    """Property-based tests for clamping invariants."""

    def test_clamped_duration_never_negative(self):
        """Property: clamped duration is always >= 0."""
        chains = [
            ChainData(
                early_timestamp=datetime(2024, 1, i, tzinfo=timezone.utc),
                late_timestamp=datetime(2024, 1, i + 5, tzinfo=timezone.utc),
                commit_count=3,
                duration=timedelta(days=5),
                earliest_sha=f"c{i}",
                latest_sha=f"c{i+1}",
            )
            for i in range(1, 20)
        ]

        start = datetime(2024, 1, 10, tzinfo=timezone.utc)
        end = datetime(2024, 1, 20, tzinfo=timezone.utc)

        result = clamp_chains_to_period(chains, start, end)

        for clamped in result:
            assert clamped.clamped_duration.total_seconds() >= 0

    def test_clamped_timestamps_within_bounds(self):
        """Property: clamped timestamps always within [start, end]."""
        chains = [
            ChainData(
                early_timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc)
                + timedelta(days=i),
                late_timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc)
                + timedelta(days=i + 10),
                commit_count=3,
                duration=timedelta(days=10),
                earliest_sha=f"c{i}",
                latest_sha=f"c{i+1}",
            )
            for i in range(-5, 30, 3)
        ]

        start = datetime(2024, 1, 10, tzinfo=timezone.utc)
        end = datetime(2024, 1, 25, tzinfo=timezone.utc)

        result = clamp_chains_to_period(chains, start, end)

        for clamped in result:
            assert clamped.clamped_first >= start
            assert clamped.clamped_last <= end
            assert clamped.clamped_first <= clamped.clamped_last

    def test_clamped_first_never_after_clamped_last(self):
        """Property: clamped_first <= clamped_last for all results."""
        chains = [
            ChainData(
                early_timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc)
                + timedelta(hours=i),
                late_timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc)
                + timedelta(hours=i + 12),
                commit_count=2,
                duration=timedelta(hours=12),
                earliest_sha=f"c{i}",
                latest_sha=f"c{i+1}",
            )
            for i in range(0, 100, 6)
        ]

        start = datetime(2024, 1, 2, tzinfo=timezone.utc)
        end = datetime(2024, 1, 3, tzinfo=timezone.utc)

        result = clamp_chains_to_period(chains, start, end)

        for clamped in result:
            assert clamped.clamped_first <= clamped.clamped_last

    def test_no_chains_outside_period(self):
        """Property: no result chain exists completely outside the period."""
        chains = [
            ChainData(
                early_timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc)
                + timedelta(days=i),
                late_timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc)
                + timedelta(days=i + 3),
                commit_count=2,
                duration=timedelta(days=3),
                earliest_sha=f"c{i}",
                latest_sha=f"c{i+1}",
            )
            for i in range(1, 50)
        ]

        start = datetime(2024, 1, 15, tzinfo=timezone.utc)
        end = datetime(2024, 1, 25, tzinfo=timezone.utc)

        result = clamp_chains_to_period(chains, start, end)

        for clamped in result:
            # Must have some overlap with period
            assert not (clamped.clamped_last < start or clamped.clamped_first > end)


if __name__ == "__main__":
    unittest.main()
