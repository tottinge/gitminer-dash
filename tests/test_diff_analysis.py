"""
Test file for the diff_analysis module.

This file contains tests for the get_diffs_in_period function,
specifically testing edge cases like empty data.
"""

from tests import setup_path

setup_path()
import os
import sys
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pandas import DataFrame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from algorithms.diff_analysis import (
    _calculate_diff_breakdown,
    get_diffs_in_period,
)


def _build_commit(
    committed_at: datetime, insertions: int, deletions: int
) -> SimpleNamespace:
    return SimpleNamespace(
        committed_datetime=committed_at,
        stats=SimpleNamespace(
            total={"insertions": insertions, "deletions": deletions}
        ),
    )


def test_dataframe_initialized_with_correct_columns_when_empty():
    """Test that DataFrame is initialized with correct columns even when the commits list is empty."""
    commits_data = []
    result = get_diffs_in_period(commits_data)
    assert isinstance(result, DataFrame)
    assert list(result.columns) == ["date", "kind", "count"]
    assert len(result) == 0
    assert result.empty


def test_dataframe_with_single_commit():
    """Test that DataFrame is correctly populated with a single commit."""
    mock_commit = MagicMock()
    mock_commit.committed_datetime.date.return_value = datetime(
        2024, 1, 15
    ).date()
    mock_commit.stats.total = {"insertions": 10, "deletions": 5}
    commits_data = [mock_commit]
    result = get_diffs_in_period(commits_data)
    assert isinstance(result, DataFrame)
    assert list(result.columns) == ["date", "kind", "count"]
    assert len(result) == 3
    kinds = result["kind"].tolist()
    counts = result["count"].tolist()
    assert "possible mods" in kinds
    assert "net inserts" in kinds
    assert "net deletes" in kinds
    mods_count = result[result["kind"] == "possible mods"]["count"].iloc[0]
    inserts_count = result[result["kind"] == "net inserts"]["count"].iloc[0]
    deletes_count = result[result["kind"] == "net deletes"]["count"].iloc[0]
    assert mods_count == 5
    assert inserts_count == 5
    assert deletes_count == 0


def test_dataframe_with_multiple_commits_same_day():
    """Test that DataFrame correctly aggregates multiple commits on the same day."""
    mock_commit1 = MagicMock()
    mock_commit1.committed_datetime.date.return_value = datetime(
        2024, 1, 15
    ).date()
    mock_commit1.stats.total = {"insertions": 10, "deletions": 5}
    mock_commit2 = MagicMock()
    mock_commit2.committed_datetime.date.return_value = datetime(
        2024, 1, 15
    ).date()
    mock_commit2.stats.total = {"insertions": 20, "deletions": 15}
    commits_data = [mock_commit1, mock_commit2]
    result = get_diffs_in_period(commits_data)
    assert isinstance(result, DataFrame)
    assert list(result.columns) == ["date", "kind", "count"]
    assert len(result) == 3
    mods_count = result[result["kind"] == "possible mods"]["count"].iloc[0]
    inserts_count = result[result["kind"] == "net inserts"]["count"].iloc[0]
    deletes_count = result[result["kind"] == "net deletes"]["count"].iloc[0]
    assert mods_count == 20
    assert inserts_count == 10
    assert deletes_count == 0


def test_dataframe_with_commits_different_days():
    """Test that DataFrame correctly handles commits on different days."""
    mock_commit1 = MagicMock()
    mock_commit1.committed_datetime.date.return_value = datetime(
        2024, 1, 15
    ).date()
    mock_commit1.stats.total = {"insertions": 10, "deletions": 5}
    mock_commit2 = MagicMock()
    mock_commit2.committed_datetime.date.return_value = datetime(
        2024, 1, 16
    ).date()
    mock_commit2.stats.total = {"insertions": 20, "deletions": 25}
    commits_data = [mock_commit1, mock_commit2]
    result = get_diffs_in_period(commits_data)
    assert isinstance(result, DataFrame)
    assert list(result.columns) == ["date", "kind", "count"]
    assert len(result) == 6
    dates = result["date"].unique()
    assert len(dates) == 2
    assert datetime(2024, 1, 15).date() in dates
    assert datetime(2024, 1, 16).date() in dates


@pytest.mark.parametrize(
    ("insertions", "deletions", "expected"),
    [
        (10, 5, (5, 5, 0)),
        (4, 9, (4, 0, 5)),
        (7, 7, (7, 0, 0)),
        (0, 3, (0, 0, 3)),
        (3, 0, (0, 3, 0)),
    ],
)
def test_calculate_diff_breakdown_returns_expected_components(
    insertions, deletions, expected
):
    assert _calculate_diff_breakdown(insertions, deletions) == expected


def test_dataframe_aggregates_net_deletions_across_same_day_commits():
    day = datetime(2024, 2, 1, 12, 0, 0)
    commits_data = [
        _build_commit(day, insertions=5, deletions=10),
        _build_commit(day, insertions=3, deletions=8),
    ]

    result = get_diffs_in_period(commits_data)
    net_deletions_count = result[result["kind"] == "net deletes"]["count"].iloc[
        0
    ]
    assert net_deletions_count == 10


if __name__ == "__main__":
    pytest.main(["-v", __file__])
