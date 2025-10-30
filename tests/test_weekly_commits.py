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


class TestGetWeekEnding(unittest.TestCase):  # noqa: S101
    """Test suite for the get_week_ending function."""

    def test_monday_returns_sunday(self):  # noqa: S101
        """Test that Monday returns the following Sunday."""
        # Use a date we know is Monday (2025-10-27)
        monday = datetime(2025, 10, 27, 10, 0, 0)
        assert monday.weekday() == 0  # Verify it's Monday

        result = get_week_ending(monday)
        assert result.weekday() == 6  # Sunday
        assert result.day == 2  # Nov 2, 2025
        assert result.month == 11
        assert result.hour == 23
        assert result.minute == 59
        assert result.second == 59

    def test_sunday_returns_same_sunday(self):  # noqa: S101
        """Test that Sunday returns itself."""
        sunday = datetime(2025, 11, 2, 10, 0, 0)
        assert sunday.weekday() == 6  # Verify it's Sunday

        result = get_week_ending(sunday)
        assert result.weekday() == 6  # Sunday
        assert result.day == 2
        assert result.month == 11

    def test_wednesday_returns_sunday(self):  # noqa: S101
        """Test that Wednesday returns the following Sunday."""
        wednesday = datetime(2025, 10, 29, 10, 0, 0)
        assert wednesday.weekday() == 2  # Verify it's Wednesday

        result = get_week_ending(wednesday)
        assert result.weekday() == 6  # Sunday
        assert result.day == 2  # Nov 2, 2025
        assert result.month == 11

    def test_saturday_returns_sunday(self):  # noqa: S101
        """Test that Saturday returns the following Sunday."""
        saturday = datetime(2025, 11, 1, 10, 0, 0)
        assert saturday.weekday() == 5  # Verify it's Saturday

        result = get_week_ending(saturday)
        assert result.weekday() == 6  # Sunday
        assert result.day == 2  # Nov 2, 2025
        assert result.month == 11

    def test_preserves_timezone(self):  # noqa: S101
        """Test that timezone information is preserved."""
        from datetime import timezone

        monday_utc = datetime(2025, 10, 27, 10, 0, 0, tzinfo=timezone.utc)

        result = get_week_ending(monday_utc)
        assert result.tzinfo is not None  # Should preserve timezone
        assert result.weekday() == 6  # Sunday


class TestCalculateWeeklyCommits(unittest.TestCase):  # noqa: S101
    """Test suite for the calculate_weekly_commits function."""

    def test_empty_commits(self):  # noqa: S101
        """Test that empty commits list returns empty weeks."""
        begin = datetime(2025, 10, 1)
        end = datetime(2025, 10, 7)
        result = calculate_weekly_commits([], begin, end)

        assert result["min_commits"] == 0
        assert result["max_commits"] == 0
        assert result["avg_commits"] == 0.0
        assert len(result["weeks"]) > 0  # Should still have weeks

    def test_single_commit(self):  # noqa: S101
        """Test calculation with a single commit."""
        commit = Mock()
        commit.committed_datetime = datetime(2025, 10, 15, 10, 0, 0)  # A Wednesday

        begin = datetime(2025, 10, 1)
        end = datetime(2025, 10, 31)

        result = calculate_weekly_commits([commit], begin, end)

        assert result["min_commits"] == 0  # Some weeks will be empty
        assert result["max_commits"] == 1

        # Find the week with the commit
        week_with_commit = [w for w in result["weeks"] if w["count"] > 0]
        assert len(week_with_commit) == 1
        assert week_with_commit[0]["count"] == 1

    def test_multiple_commits_same_week(self):  # noqa: S101
        """Test multiple commits in the same week."""
        commit1 = Mock()
        commit1.committed_datetime = datetime(2025, 10, 27, 10, 0, 0)  # Monday

        commit2 = Mock()
        commit2.committed_datetime = datetime(2025, 10, 29, 10, 0, 0)  # Wednesday

        commit3 = Mock()
        commit3.committed_datetime = datetime(2025, 11, 1, 10, 0, 0)  # Saturday

        begin = datetime(2025, 10, 1)
        end = datetime(2025, 11, 2)

        result = calculate_weekly_commits([commit1, commit2, commit3], begin, end)

        # All three commits should be in the same week (ending Nov 2)
        week_with_commits = [w for w in result["weeks"] if w["count"] == 3]
        assert len(week_with_commits) == 1
        assert result["max_commits"] == 3

    def test_commits_across_weeks(self):  # noqa: S101
        """Test commits distributed across multiple weeks."""
        commit1 = Mock()
        commit1.committed_datetime = datetime(2025, 10, 6, 10, 0, 0)  # Week 1

        commit2 = Mock()
        commit2.committed_datetime = datetime(2025, 10, 13, 10, 0, 0)  # Week 2

        commit3 = Mock()
        commit3.committed_datetime = datetime(2025, 10, 20, 10, 0, 0)  # Week 3

        begin = datetime(2025, 10, 1)
        end = datetime(2025, 10, 31)

        result = calculate_weekly_commits([commit1, commit2, commit3], begin, end)

        weeks_with_commits = [w for w in result["weeks"] if w["count"] > 0]
        assert len(weeks_with_commits) == 3
        assert result["max_commits"] == 1
        assert result["min_commits"] == 0  # Some weeks are empty

    def test_week_boundaries(self):  # noqa: S101
        """Test that weeks are properly bounded Monday-Sunday."""
        # Create commits on Sunday and Monday (different weeks)
        commit_sunday = Mock()
        commit_sunday.committed_datetime = datetime(2025, 10, 26, 23, 59, 59)  # Sunday

        commit_monday = Mock()
        commit_monday.committed_datetime = datetime(2025, 10, 27, 0, 0, 1)  # Monday

        begin = datetime(2025, 10, 1)
        end = datetime(2025, 10, 31)

        result = calculate_weekly_commits([commit_sunday, commit_monday], begin, end)

        # Should have two different weeks with 1 commit each
        weeks_with_one_commit = [w for w in result["weeks"] if w["count"] == 1]
        assert len(weeks_with_one_commit) == 2

    def test_statistics_calculation(self):  # noqa: S101
        """Test min, max, and average calculations."""
        commits = []

        # Week 1: 2 commits
        for i in range(2):
            commit = Mock()
            commit.committed_datetime = datetime(2025, 10, 6, 10 + i, 0, 0)
            commits.append(commit)

        # Week 2: 5 commits
        for i in range(5):
            commit = Mock()
            commit.committed_datetime = datetime(2025, 10, 13, 10 + i, 0, 0)
            commits.append(commit)

        # Week 3: 0 commits (implicit)

        # Week 4: 3 commits
        for i in range(3):
            commit = Mock()
            commit.committed_datetime = datetime(2025, 10, 27, 10 + i, 0, 0)
            commits.append(commit)

        begin = datetime(2025, 10, 1)
        end = datetime(2025, 10, 31)

        result = calculate_weekly_commits(commits, begin, end)

        assert result["min_commits"] == 0
        assert result["max_commits"] == 5
        # Average should be (2 + 5 + 0 + 3) / number_of_weeks
        total_weeks = len(result["weeks"])
        expected_avg = 10 / total_weeks
        assert abs(result["avg_commits"] - expected_avg) < 0.01


class TestExtractCommitDetails(unittest.TestCase):  # noqa: S101
    """Test suite for the extract_commit_details function."""

    def test_basic_commit_extraction(self):  # noqa: S101
        """Test extraction of basic commit details."""
        commit = Mock()
        commit.committed_datetime = datetime(2025, 10, 15, 14, 30, 45)
        commit.committer.name = "John Doe"
        commit.summary = "Fix bug in authentication"
        commit.stats.total = {
            "insertions": 10,
            "deletions": 5,
            "lines": 15,
        }

        result = extract_commit_details(commit)

        assert result["date"] == "2025-10-15 14:30:45"
        assert result["committer"] == "John Doe"
        assert result["description"] == "Fix bug in authentication"
        assert result["lines_added"] == 10
        assert result["lines_removed"] == 5
        assert result["lines_modified"] == 15

    def test_commit_with_no_changes(self):  # noqa: S101
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
