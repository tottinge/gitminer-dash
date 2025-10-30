"""
Unit tests for the weekly commits module.
"""

import unittest
from unittest.mock import Mock
from datetime import datetime, timedelta
from algorithms.weekly_commits import (
    get_week_ending,
    calculate_weekly_commits,
    extract_commit_details,
)


class TestGetWeekEnding(unittest.TestCase):
    """Test suite for the get_week_ending function."""

    def test_monday_returns_sunday(self):
        """Test that Monday returns the following Sunday."""
        monday = datetime(2025, 10, 27, 10, 0, 0)
        assert monday.weekday() == 0
        result = get_week_ending(monday)
        assert result.weekday() == 6
        assert result.day == 2
        assert result.month == 11
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59

    def test_sunday_returns_same_sunday(self):
        """Test that Sunday returns itself."""
        sunday = datetime(2025, 11, 2, 10, 0, 0)
        assert sunday.weekday() == 6
        result = get_week_ending(sunday)
        assert result.weekday() == 6
        assert result.day == 2
        assert result.month == 11

    def test_wednesday_returns_sunday(self):
        """Test that Wednesday returns the following Sunday."""
        wednesday = datetime(2025, 10, 29, 10, 0, 0)
        assert wednesday.weekday() == 2
        result = get_week_ending(wednesday)
        assert result.weekday() == 6
        assert result.day == 2
        assert result.month == 11

    def test_saturday_returns_sunday(self):
        """Test that Saturday returns the following Sunday."""
        saturday = datetime(2025, 11, 1, 10, 0, 0)
        assert saturday.weekday() == 5
        result = get_week_ending(saturday)
        assert result.weekday() == 6
        assert result.day == 2
        assert result.month == 11

    def test_preserves_timezone(self):
        """Test that timezone information is preserved."""
        from datetime import timezone

        monday_utc = datetime(2025, 10, 27, 10, 0, 0, tzinfo=timezone.utc)
        result = get_week_ending(monday_utc)
        assert result.tzinfo is not None
        assert result.weekday() == 6


class TestCalculateWeeklyCommits(unittest.TestCase):
    """Test suite for the calculate_weekly_commits function."""

    def test_empty_commits(self):
        """Test that empty commits list returns empty weeks."""
        begin = datetime(2025, 10, 1)
        end = datetime(2025, 10, 7)
        result = calculate_weekly_commits([], begin, end)
        assert result["min_commits"] == 0
        assert result["max_commits"] == 0
        assert result["avg_commits"] == 0.0
        assert len(result["weeks"]) > 0

    def test_single_commit(self):
        """Test calculation with a single commit."""
        commit = Mock()
        commit.committed_datetime = datetime(2025, 10, 15, 10, 0, 0)
        begin = datetime(2025, 10, 1)
        end = datetime(2025, 10, 31)
        result = calculate_weekly_commits([commit], begin, end)
        assert result["min_commits"] == 0
        assert result["max_commits"] == 1
        week_with_commit = [w for w in result["weeks"] if w["count"] > 0]
        assert len(week_with_commit) == 1
        assert week_with_commit[0]["count"] == 1

    def test_multiple_commits_same_week(self):
        """Test multiple commits in the same week."""
        commit1 = Mock()
        commit1.committed_datetime = datetime(2025, 10, 27, 10, 0, 0)
        commit2 = Mock()
        commit2.committed_datetime = datetime(2025, 10, 29, 10, 0, 0)
        commit3 = Mock()
        commit3.committed_datetime = datetime(2025, 11, 1, 10, 0, 0)
        begin = datetime(2025, 10, 1)
        end = datetime(2025, 11, 2)
        result = calculate_weekly_commits([commit1, commit2, commit3], begin, end)
        week_with_commits = [w for w in result["weeks"] if w["count"] == 3]
        assert len(week_with_commits) == 1
        assert result["max_commits"] == 3

    def test_commits_across_weeks(self):
        """Test commits distributed across multiple weeks."""
        commit1 = Mock()
        commit1.committed_datetime = datetime(2025, 10, 6, 10, 0, 0)
        commit2 = Mock()
        commit2.committed_datetime = datetime(2025, 10, 13, 10, 0, 0)
        commit3 = Mock()
        commit3.committed_datetime = datetime(2025, 10, 20, 10, 0, 0)
        begin = datetime(2025, 10, 1)
        end = datetime(2025, 10, 31)
        result = calculate_weekly_commits([commit1, commit2, commit3], begin, end)
        weeks_with_commits = [w for w in result["weeks"] if w["count"] > 0]
        assert len(weeks_with_commits) == 3
        assert result["max_commits"] == 1
        assert result["min_commits"] == 0

    def test_week_boundaries(self):
        """Test that weeks are properly bounded Monday-Sunday."""
        commit_sunday = Mock()
        commit_sunday.committed_datetime = datetime(2025, 10, 26, 23, 59, 59)
        commit_monday = Mock()
        commit_monday.committed_datetime = datetime(2025, 10, 27, 0, 0, 1)
        begin = datetime(2025, 10, 1)
        end = datetime(2025, 10, 31)
        result = calculate_weekly_commits([commit_sunday, commit_monday], begin, end)
        weeks_with_one_commit = [w for w in result["weeks"] if w["count"] == 1]
        assert len(weeks_with_one_commit) == 2

    def test_statistics_calculation(self):
        """Test min, max, and average calculations."""
        commits = []
        for i in range(2):
            commit = Mock()
            commit.committed_datetime = datetime(2025, 10, 6, 10 + i, 0, 0)
            commits.append(commit)
        for i in range(5):
            commit = Mock()
            commit.committed_datetime = datetime(2025, 10, 13, 10 + i, 0, 0)
            commits.append(commit)
        for i in range(3):
            commit = Mock()
            commit.committed_datetime = datetime(2025, 10, 27, 10 + i, 0, 0)
            commits.append(commit)
        begin = datetime(2025, 10, 1)
        end = datetime(2025, 10, 31)
        result = calculate_weekly_commits(commits, begin, end)
        assert result["min_commits"] == 0
        assert result["max_commits"] == 5
        total_weeks = len(result["weeks"])
        expected_avg = 10 / total_weeks
        assert abs(result["avg_commits"] - expected_avg) < 0.01


class TestExtractCommitDetails(unittest.TestCase):
    """Test suite for the extract_commit_details function."""

    def test_basic_commit_extraction(self):
        """Test extraction of basic commit details."""
        commit = Mock()
        commit.committed_datetime = datetime(2025, 10, 15, 14, 30, 45)
        commit.committer.name = "John Doe"
        commit.summary = "Fix bug in authentication"
        commit.stats.total = {"insertions": 10, "deletions": 5, "lines": 15}
        result = extract_commit_details(commit)
        assert result["date"] == "2025-10-15 14:30:45"
        assert result["committer"] == "John Doe"
        assert result["description"] == "Fix bug in authentication"
        assert result["lines_added"] == 10
        assert result["lines_removed"] == 5
        assert result["lines_modified"] == 15

    def test_commit_with_no_changes(self):
        """Test extraction when commit has no line changes."""
        commit = Mock()
        commit.committed_datetime = datetime(2025, 10, 15, 14, 30, 45)
        commit.committer.name = "Jane Smith"
        commit.summary = "Empty commit"
        commit.stats.total = {}
        result = extract_commit_details(commit)
        assert result["lines_added"] == 0
        assert result["lines_removed"] == 0
        assert result["lines_modified"] == 0


if __name__ == "__main__":
    unittest.main()
