"""
Unit and regression tests for DataFrame builder.
"""

import unittest
from datetime import datetime, timedelta, timezone

from pandas import DataFrame

from algorithms.chain_models import TimelineRow
from algorithms.dataframe_builder import create_timeline_dataframe


class TestCreateTimelineDataFrame(unittest.TestCase):
    """Test suite for create_timeline_dataframe function."""

    def test_empty_rows(self):
        """Test that empty rows list returns empty DataFrame."""
        df = create_timeline_dataframe([])
        
        assert len(df) == 0
        assert list(df.columns) == [
            "first", "last", "elevation", "commit_counts",
            "head", "tail", "duration", "density"
        ]

    def test_single_row(self):
        """Test DataFrame creation from a single row."""
        row = TimelineRow(
            first=datetime(2024, 1, 1, tzinfo=timezone.utc),
            last=datetime(2024, 1, 10, tzinfo=timezone.utc),
            elevation=1,
            commit_counts=5,
            head="abc",
            tail="def",
            duration=9,
            density=1.8
        )
        
        df = create_timeline_dataframe([row])
        
        assert len(df) == 1
        assert df.iloc[0]["elevation"] == 1
        assert df.iloc[0]["commit_counts"] == 5
        assert df.iloc[0]["head"] == "abc"
        assert df.iloc[0]["tail"] == "def"
        assert df.iloc[0]["duration"] == 9
        assert df.iloc[0]["density"] == 1.8

    def test_multiple_rows(self):
        """Test DataFrame creation from multiple rows."""
        rows = [
            TimelineRow(
                first=datetime(2024, 1, 1, tzinfo=timezone.utc),
                last=datetime(2024, 1, 5, tzinfo=timezone.utc),
                elevation=1,
                commit_counts=3,
                head="c1",
                tail="c2",
                duration=4,
                density=1.33
            ),
            TimelineRow(
                first=datetime(2024, 1, 10, tzinfo=timezone.utc),
                last=datetime(2024, 1, 20, tzinfo=timezone.utc),
                elevation=2,
                commit_counts=7,
                head="c3",
                tail="c4",
                duration=10,
                density=1.43
            ),
        ]
        
        df = create_timeline_dataframe(rows)
        
        assert len(df) == 2
        assert df.iloc[0]["head"] == "c1"
        assert df.iloc[1]["head"] == "c3"

    def test_column_order(self):
        """Test that DataFrame has columns in expected order."""
        row = TimelineRow(
            first=datetime(2024, 1, 1, tzinfo=timezone.utc),
            last=datetime(2024, 1, 10, tzinfo=timezone.utc),
            elevation=1,
            commit_counts=5,
            head="abc",
            tail="def",
            duration=9,
            density=1.8
        )
        
        df = create_timeline_dataframe([row])
        
        expected_columns = [
            "first", "last", "elevation", "commit_counts",
            "head", "tail", "duration", "density"
        ]
        assert list(df.columns) == expected_columns

    def test_datetime_column_types(self):
        """Test that datetime columns have correct dtype."""
        row = TimelineRow(
            first=datetime(2024, 1, 1, tzinfo=timezone.utc),
            last=datetime(2024, 1, 10, tzinfo=timezone.utc),
            elevation=1,
            commit_counts=5,
            head="abc",
            tail="def",
            duration=9,
            density=1.8
        )
        
        df = create_timeline_dataframe([row])
        
        # Check that datetime columns are properly typed
        assert df["first"].dtype == "datetime64[ns]"
        assert df["last"].dtype == "datetime64[ns]"

    def test_regression_timezone_aware_datetimes(self):
        """
        REGRESSION TEST for datetime conversion issue.
        
        This test ensures that timezone-aware datetime objects
        (which come from git commits) are properly converted to
        pandas datetime64[ns] format, preventing the error:
        "AttributeError: Can only use .dt accessor with datetimelike values"
        
        Background: When TimelineRow objects contain timezone-aware
        datetime objects and are passed to px.timeline(), Plotly
        internally tries to use the .dt accessor on what it thinks
        are datetime columns. If pandas doesn't recognize them as
        proper datetime types, this fails.
        
        The fix: Explicitly convert to datetime64[ns] after DataFrame creation.
        """
        # Create rows with timezone-aware datetimes (as git commits have)
        rows = [
            TimelineRow(
                first=datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc),
                last=datetime(2024, 1, 10, 15, 45, 0, tzinfo=timezone.utc),
                elevation=1,
                commit_counts=5,
                head="abc123",
                tail="def456",
                duration=9,
                density=1.8
            ),
            TimelineRow(
                first=datetime(2024, 1, 5, 8, 0, 0, tzinfo=timezone.utc),
                last=datetime(2024, 1, 15, 18, 30, 0, tzinfo=timezone.utc),
                elevation=2,
                commit_counts=8,
                head="ghi789",
                tail="jkl012",
                duration=10,
                density=1.25
            ),
        ]
        
        df = create_timeline_dataframe(rows)
        
        # Verify datetime columns are properly typed
        assert df["first"].dtype == "datetime64[ns]"
        assert df["last"].dtype == "datetime64[ns]"
        
        # Verify we can use .dt accessor (this would fail without the fix)
        try:
            _ = df["first"].dt.year
            _ = df["last"].dt.month
            datetime_accessor_works = True
        except AttributeError:
            datetime_accessor_works = False
        
        assert datetime_accessor_works, "Should be able to use .dt accessor on datetime columns"

    def test_preserves_data_integrity(self):
        """Test that all data is preserved correctly in DataFrame."""
        row = TimelineRow(
            first=datetime(2024, 1, 1, 14, 30, 0, tzinfo=timezone.utc),
            last=datetime(2024, 1, 10, 9, 15, 0, tzinfo=timezone.utc),
            elevation=3,
            commit_counts=42,
            head="first_sha_abc",
            tail="last_sha_xyz",
            duration=100,
            density=2.38095
        )
        
        df = create_timeline_dataframe([row])
        
        # Check all values preserved
        assert df.iloc[0]["elevation"] == 3
        assert df.iloc[0]["commit_counts"] == 42
        assert df.iloc[0]["head"] == "first_sha_abc"
        assert df.iloc[0]["tail"] == "last_sha_xyz"
        assert df.iloc[0]["duration"] == 100
        assert abs(df.iloc[0]["density"] - 2.38095) < 0.00001

    def test_datetime_values_preserved(self):
        """Test that datetime values are preserved during conversion."""
        original_first = datetime(2024, 3, 15, 10, 30, 45, tzinfo=timezone.utc)
        original_last = datetime(2024, 3, 25, 16, 45, 30, tzinfo=timezone.utc)
        
        row = TimelineRow(
            first=original_first,
            last=original_last,
            elevation=1,
            commit_counts=5,
            head="abc",
            tail="def",
            duration=10,
            density=2.0
        )
        
        df = create_timeline_dataframe([row])
        
        # Convert back to python datetime for comparison
        # (pandas datetime64 conversion may lose timezone info but preserves timestamp)
        df_first = df.iloc[0]["first"].to_pydatetime()
        df_last = df.iloc[0]["last"].to_pydatetime()
        
        # Check timestamps are equivalent (allowing for timezone conversion)
        assert df_first.replace(tzinfo=timezone.utc) == original_first
        assert df_last.replace(tzinfo=timezone.utc) == original_last

    def test_zero_values(self):
        """Test handling of zero values."""
        row = TimelineRow(
            first=datetime(2024, 1, 1, tzinfo=timezone.utc),
            last=datetime(2024, 1, 1, tzinfo=timezone.utc),
            elevation=1,
            commit_counts=0,
            head="sha",
            tail="sha",
            duration=0,
            density=0.0
        )
        
        df = create_timeline_dataframe([row])
        
        assert df.iloc[0]["commit_counts"] == 0
        assert df.iloc[0]["duration"] == 0
        assert df.iloc[0]["density"] == 0.0

    def test_column_types(self):
        """Test that all columns have expected types."""
        row = TimelineRow(
            first=datetime(2024, 1, 1, tzinfo=timezone.utc),
            last=datetime(2024, 1, 10, tzinfo=timezone.utc),
            elevation=1,
            commit_counts=5,
            head="abc",
            tail="def",
            duration=9,
            density=1.8
        )
        
        df = create_timeline_dataframe([row])
        
        # Check types
        assert df["first"].dtype == "datetime64[ns]"
        assert df["last"].dtype == "datetime64[ns]"
        assert df["elevation"].dtype in ["int64", "int32"]
        assert df["commit_counts"].dtype in ["int64", "int32"]
        assert df["head"].dtype == object  # string
        assert df["tail"].dtype == object  # string
        assert df["duration"].dtype in ["int64", "int32"]
        assert df["density"].dtype in ["float64", "float32"]


if __name__ == "__main__":
    unittest.main()
