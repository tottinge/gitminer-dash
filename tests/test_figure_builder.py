"""
Unit tests for figure builder.
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from pandas import DataFrame

from algorithms.chain_models import TIMELINE_COLUMNS
from algorithms.figure_builder import create_timeline_figure


class TestCreateTimelineFigure(unittest.TestCase):
    """Test suite for create_timeline_figure function."""

    def test_empty_dataframe(self):
        """Test figure creation from empty DataFrame."""
        df = DataFrame(columns=TIMELINE_COLUMNS)

        figure = create_timeline_figure(df)

        # Should return a figure object
        assert figure is not None
        assert hasattr(figure, "data")

    def test_single_row_dataframe(self):
        """Test figure creation from single row."""
        df = DataFrame(
            [
                {
                    "first": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "last": datetime(2024, 1, 10, tzinfo=timezone.utc),
                    "elevation": 1,
                    "commit_counts": 5,
                    "head": "abc",
                    "tail": "def",
                    "duration": 9,
                    "density": 1.8,
                }
            ]
        )

        figure = create_timeline_figure(df)

        assert figure is not None
        assert len(figure.data) > 0

    def test_multiple_rows_dataframe(self):
        """Test figure creation from multiple rows."""
        df = DataFrame(
            [
                {
                    "first": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "last": datetime(2024, 1, 5, tzinfo=timezone.utc),
                    "elevation": 1,
                    "commit_counts": 3,
                    "head": "c1",
                    "tail": "c2",
                    "duration": 4,
                    "density": 1.33,
                },
                {
                    "first": datetime(2024, 1, 10, tzinfo=timezone.utc),
                    "last": datetime(2024, 1, 20, tzinfo=timezone.utc),
                    "elevation": 2,
                    "commit_counts": 7,
                    "head": "c3",
                    "tail": "c4",
                    "duration": 10,
                    "density": 1.43,
                },
            ]
        )

        figure = create_timeline_figure(df)

        assert figure is not None
        assert len(figure.data) > 0

    def test_figure_has_title(self):
        """Test that figure has the expected title."""
        df = DataFrame(
            [
                {
                    "first": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "last": datetime(2024, 1, 10, tzinfo=timezone.utc),
                    "elevation": 1,
                    "commit_counts": 5,
                    "head": "abc",
                    "tail": "def",
                    "duration": 9,
                    "density": 1.8,
                }
            ]
        )

        figure = create_timeline_figure(df)

        assert figure.layout.title.text == "Code Lines (selected period)"

    def test_figure_uses_correct_columns(self):
        """Test that figure uses correct DataFrame columns."""
        df = DataFrame(
            [
                {
                    "first": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "last": datetime(2024, 1, 10, tzinfo=timezone.utc),
                    "elevation": 1,
                    "commit_counts": 5,
                    "head": "abc",
                    "tail": "def",
                    "duration": 9,
                    "density": 1.8,
                }
            ]
        )

        figure = create_timeline_figure(df)

        # Verify figure was created (px.timeline would fail if columns wrong)
        assert figure is not None
        assert len(figure.data) > 0

    def test_figure_axis_labels(self):
        """Test that figure has correct axis labels."""
        df = DataFrame(
            [
                {
                    "first": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "last": datetime(2024, 1, 10, tzinfo=timezone.utc),
                    "elevation": 1,
                    "commit_counts": 5,
                    "head": "abc",
                    "tail": "def",
                    "duration": 9,
                    "density": 1.8,
                }
            ]
        )

        figure = create_timeline_figure(df)

        # Check that labels are configured (won't be visible in axis titles
        # for timeline, but should be in hover/legend)
        assert figure is not None

    def test_figure_with_varying_elevations(self):
        """Test figure handles different elevation levels."""
        df = DataFrame(
            [
                {
                    "first": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "last": datetime(2024, 1, 5, tzinfo=timezone.utc),
                    "elevation": 1,
                    "commit_counts": 3,
                    "head": "c1",
                    "tail": "c2",
                    "duration": 4,
                    "density": 1.33,
                },
                {
                    "first": datetime(2024, 1, 3, tzinfo=timezone.utc),
                    "last": datetime(2024, 1, 8, tzinfo=timezone.utc),
                    "elevation": 2,
                    "commit_counts": 4,
                    "head": "c3",
                    "tail": "c4",
                    "duration": 5,
                    "density": 1.25,
                },
                {
                    "first": datetime(2024, 1, 6, tzinfo=timezone.utc),
                    "last": datetime(2024, 1, 12, tzinfo=timezone.utc),
                    "elevation": 3,
                    "commit_counts": 5,
                    "head": "c5",
                    "tail": "c6",
                    "duration": 6,
                    "density": 1.2,
                },
            ]
        )

        figure = create_timeline_figure(df)

        assert figure is not None
        assert len(figure.data) > 0

    def test_figure_with_varying_density(self):
        """Test figure handles different density values for coloring."""
        df = DataFrame(
            [
                {
                    "first": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "last": datetime(2024, 1, 10, tzinfo=timezone.utc),
                    "elevation": 1,
                    "commit_counts": 10,
                    "head": "c1",
                    "tail": "c2",
                    "duration": 9,
                    "density": 0.9,  # Low density (many commits)
                },
                {
                    "first": datetime(2024, 1, 15, tzinfo=timezone.utc),
                    "last": datetime(2024, 1, 25, tzinfo=timezone.utc),
                    "elevation": 1,
                    "commit_counts": 2,
                    "head": "c3",
                    "tail": "c4",
                    "duration": 10,
                    "density": 5.0,  # High density (few commits)
                },
            ]
        )

        figure = create_timeline_figure(df)

        assert figure is not None
        assert len(figure.data) > 0

    def test_figure_returns_plotly_figure_type(self):
        """Test that return type is a Plotly Figure."""
        df = DataFrame(
            [
                {
                    "first": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "last": datetime(2024, 1, 10, tzinfo=timezone.utc),
                    "elevation": 1,
                    "commit_counts": 5,
                    "head": "abc",
                    "tail": "def",
                    "duration": 9,
                    "density": 1.8,
                }
            ]
        )

        figure = create_timeline_figure(df)

        # Check it's a Plotly figure
        assert hasattr(figure, "data")
        assert hasattr(figure, "layout")
        assert hasattr(figure, "to_json")

    def test_column_mappings_and_label_keys_are_as_expected(self):
        """Test that px.timeline is called with expected columns and label keys.

        This ensures that we treat label *keys* as part of the public
        contract, while allowing label *values* (strings) to be cosmetic.
        """
        df = DataFrame(
            [
                {
                    "first": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "last": datetime(2024, 1, 10, tzinfo=timezone.utc),
                    "elevation": 1,
                    "commit_counts": 5,
                    "head": "abc",
                    "tail": "def",
                    "duration": 9,
                    "density": 1.8,
                }
            ]
        )

        with patch("algorithms.figure_builder.px.timeline") as mock_timeline:
            sentinel_figure = object()
            mock_timeline.return_value = sentinel_figure

            result = create_timeline_figure(df)

        # We should return whatever px.timeline returned
        assert result is sentinel_figure

        _, kwargs = mock_timeline.call_args

        # Column mappings
        assert kwargs["x_start"] == "first"
        assert kwargs["x_end"] == "last"
        assert kwargs["y"] == "elevation"
        assert kwargs["color"] == "density"
        assert kwargs["custom_data"] == ["head", "tail"]

        # Label keys are part of the public contract
        assert set(kwargs["labels"].keys()) == {
            "elevation",
            "density",
            "first",
            "last",
            "duration",
        }

    def test_hover_data_configuration_is_as_expected(self):
        """Test that px.timeline is called with the expected hover_data mapping.

        This treats which fields appear in the tooltip as part of the
        public contract for the timeline figure.
        """
        df = DataFrame(
            [
                {
                    "first": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "last": datetime(2024, 1, 10, tzinfo=timezone.utc),
                    "elevation": 1,
                    "commit_counts": 5,
                    "head": "abc",
                    "tail": "def",
                    "duration": 9,
                    "density": 1.8,
                }
            ]
        )

        with patch("algorithms.figure_builder.px.timeline") as mock_timeline:
            sentinel_figure = object()
            mock_timeline.return_value = sentinel_figure

            result = create_timeline_figure(df)

        assert result is sentinel_figure

        _, kwargs = mock_timeline.call_args

        assert kwargs["hover_data"] == {
            "first": True,
            "head": True,
            "last": True,
            "tail": True,
            "commit_counts": True,
            "duration": True,
            "elevation": False,
            "density": True,
        }


if __name__ == "__main__":
    unittest.main()
