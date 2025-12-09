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


class TestWeeklyCommitsCallback(unittest.TestCase):
    """Test suite for the weekly commits page callback."""

    def test_click_event_triggers_callback(self):
        """Test that clicking on a bar triggers the callback."""
        from unittest.mock import patch

        with patch("dash.register_page"):
            from pages.weekly_commits import layout

            # Verify the callback exists by attempting to import it
            try:
                from pages.weekly_commits import update_commit_details_table
                callback_exists = True
            except ImportError:
                callback_exists = False

            assert callback_exists, "Callback update_commit_details_table should exist"

    def test_callback_produces_table_from_fake_week_data(self):
        """Test that given fake data of a week's commits, the callback produces the correct table."""
        from unittest.mock import patch, Mock

        # Create fake commits for a week
        commit1 = Mock()
        commit1.hexsha = "abc123"
        commit1.committed_datetime = datetime(2025, 10, 27, 10, 0, 0)
        commit1.committer.name = "Alice"
        commit1.summary = "Add feature X"
        commit1.stats.total = {"insertions": 10, "deletions": 2, "lines": 12}

        commit2 = Mock()
        commit2.hexsha = "def456"
        commit2.committed_datetime = datetime(2025, 10, 28, 14, 30, 0)
        commit2.committer.name = "Bob"
        commit2.summary = "Fix bug Y"
        commit2.stats.total = {"insertions": 5, "deletions": 3, "lines": 8}

        # Create fake click data (Plotly clickData format)
        click_data = {
            "points": [
                {
                    "x": "25-11-02",  # Week ending date
                }
            ]
        }

        # Create fake store data
        store_data = {
            "weeks": [
                {
                    "week_ending": "2025-11-02T23:59:59",
                    "x_label": "25-11-02",
                    "commits": ["abc123", "def456"],
                }
            ]
        }

        with patch("dash.register_page"), patch(
            "pages.weekly_commits.data.get_repo"
        ) as mock_repo:
            mock_repo_obj = Mock()
            mock_repo_obj.commit.side_effect = lambda sha: {
                "abc123": commit1,
                "def456": commit2,
            }[sha]
            mock_repo.return_value = mock_repo_obj

            from pages.weekly_commits import update_commit_details_table

            table_data, message = update_commit_details_table(
                click_data, store_data
            )

            # Verify table has correct structure and data
            assert len(table_data) == 2
            assert table_data[0]["committer"] == "Alice"
            assert table_data[0]["description"] == "Add feature X"
            assert table_data[0]["lines_added"] == 10
            assert table_data[0]["lines_removed"] == 2
            assert table_data[1]["committer"] == "Bob"
            assert table_data[1]["description"] == "Fix bug Y"

            # Verify message is updated
            assert "2 commits" in message or "25-11-02" in message

    def test_none_click_data_returns_empty_table(self):
        """Test that None click_data returns empty table and default message."""
        from unittest.mock import patch

        with patch("dash.register_page"):
            from pages.weekly_commits import update_commit_details_table

            store_data = {"weeks": []}
            table_data, message = update_commit_details_table(None, store_data)

            assert table_data == []
            assert message == "Click on a week's bar to see commit details."

    def test_invalid_store_data_returns_empty_table(self):
        """Test that invalid store_data returns empty table and default message."""
        from unittest.mock import patch

        with patch("dash.register_page"):
            from pages.weekly_commits import update_commit_details_table

            click_data = {"points": [{"x": "25-11-02"}]}

            # Test with None store_data
            table_data, message = update_commit_details_table(click_data, None)
            assert table_data == []
            assert message == "Click on a week's bar to see commit details."

            # Test with store_data missing 'weeks'
            table_data, message = update_commit_details_table(click_data, {})
            assert table_data == []
            assert message == "Click on a week's bar to see commit details."

    def test_no_matching_week_returns_empty_table(self):
        """Test that click_data not matching any week returns empty table and message."""
        from unittest.mock import patch

        with patch("dash.register_page"):
            from pages.weekly_commits import update_commit_details_table

            click_data = {"points": [{"x": "25-12-31"}]}
            store_data = {
                "weeks": [
                    {
                        "week_ending": "2025-11-02T23:59:59",
                        "x_label": "25-11-02",
                        "commits": ["abc123"],
                    }
                ]
            }

            table_data, message = update_commit_details_table(click_data, store_data)

            assert table_data == []
            assert message == "No commits found for week ending 25-12-31"

    def test_valid_week_with_multiple_commits(self):
        """Test that valid week with multiple commits populates table correctly."""
        from unittest.mock import patch, Mock

        # Create mock commits
        commit1 = Mock()
        commit1.hexsha = "sha1"
        commit1.committed_datetime = datetime(2025, 10, 27, 9, 0, 0)
        commit1.committer.name = "Developer 1"
        commit1.summary = "First commit"
        commit1.stats.total = {"insertions": 15, "deletions": 3, "lines": 18}

        commit2 = Mock()
        commit2.hexsha = "sha2"
        commit2.committed_datetime = datetime(2025, 10, 28, 10, 0, 0)
        commit2.committer.name = "Developer 2"
        commit2.summary = "Second commit"
        commit2.stats.total = {"insertions": 8, "deletions": 2, "lines": 10}

        commit3 = Mock()
        commit3.hexsha = "sha3"
        commit3.committed_datetime = datetime(2025, 10, 29, 11, 0, 0)
        commit3.committer.name = "Developer 3"
        commit3.summary = "Third commit"
        commit3.stats.total = {"insertions": 20, "deletions": 5, "lines": 25}

        click_data = {"points": [{"x": "25-11-02"}]}
        store_data = {
            "weeks": [
                {
                    "week_ending": "2025-11-02T23:59:59",
                    "x_label": "25-11-02",
                    "commits": ["sha1", "sha2", "sha3"],
                }
            ]
        }

        with patch("dash.register_page"), patch(
            "pages.weekly_commits.data.get_repo"
        ) as mock_repo:
            mock_repo_obj = Mock()
            mock_repo_obj.commit.side_effect = lambda sha: {
                "sha1": commit1,
                "sha2": commit2,
                "sha3": commit3,
            }[sha]
            mock_repo.return_value = mock_repo_obj

            from pages.weekly_commits import update_commit_details_table

            table_data, message = update_commit_details_table(
                click_data, store_data
            )

            # Verify all three commits are in the table
            assert len(table_data) == 3
            assert table_data[0]["committer"] == "Developer 1"
            assert table_data[0]["description"] == "First commit"
            assert table_data[0]["lines_added"] == 15
            assert table_data[0]["lines_removed"] == 3
            assert table_data[0]["lines_modified"] == 18

            assert table_data[1]["committer"] == "Developer 2"
            assert table_data[1]["description"] == "Second commit"
            assert table_data[1]["lines_added"] == 8

            assert table_data[2]["committer"] == "Developer 3"
            assert table_data[2]["description"] == "Third commit"
            assert table_data[2]["lines_added"] == 20

    def test_message_reflects_commit_count_and_week(self):
        """Test that message accurately reflects number of commits and week ending date."""
        from unittest.mock import patch, Mock

        commit1 = Mock()
        commit1.hexsha = "sha1"
        commit1.committed_datetime = datetime(2025, 10, 27, 10, 0, 0)
        commit1.committer.name = "Dev"
        commit1.summary = "Commit"
        commit1.stats.total = {"insertions": 1, "deletions": 1, "lines": 2}

        commit2 = Mock()
        commit2.hexsha = "sha2"
        commit2.committed_datetime = datetime(2025, 10, 28, 10, 0, 0)
        commit2.committer.name = "Dev"
        commit2.summary = "Commit"
        commit2.stats.total = {"insertions": 1, "deletions": 1, "lines": 2}

        commit3 = Mock()
        commit3.hexsha = "sha3"
        commit3.committed_datetime = datetime(2025, 10, 29, 10, 0, 0)
        commit3.committer.name = "Dev"
        commit3.summary = "Commit"
        commit3.stats.total = {"insertions": 1, "deletions": 1, "lines": 2}

        commit4 = Mock()
        commit4.hexsha = "sha4"
        commit4.committed_datetime = datetime(2025, 10, 30, 10, 0, 0)
        commit4.committer.name = "Dev"
        commit4.summary = "Commit"
        commit4.stats.total = {"insertions": 1, "deletions": 1, "lines": 2}

        commit5 = Mock()
        commit5.hexsha = "sha5"
        commit5.committed_datetime = datetime(2025, 10, 31, 10, 0, 0)
        commit5.committer.name = "Dev"
        commit5.summary = "Commit"
        commit5.stats.total = {"insertions": 1, "deletions": 1, "lines": 2}

        click_data = {"points": [{"x": "25-11-02"}]}
        store_data = {
            "weeks": [
                {
                    "week_ending": "2025-11-02T23:59:59",
                    "x_label": "25-11-02",
                    "commits": ["sha1", "sha2", "sha3", "sha4", "sha5"],
                }
            ]
        }

        with patch("dash.register_page"), patch(
            "pages.weekly_commits.data.get_repo"
        ) as mock_repo:
            mock_repo_obj = Mock()
            mock_repo_obj.commit.side_effect = lambda sha: {
                "sha1": commit1,
                "sha2": commit2,
                "sha3": commit3,
                "sha4": commit4,
                "sha5": commit5,
            }[sha]
            mock_repo.return_value = mock_repo_obj

            from pages.weekly_commits import update_commit_details_table

            table_data, message = update_commit_details_table(
                click_data, store_data
            )

            # Verify message contains correct count and week
            assert "5 commits" in message
            assert "25-11-02" in message


if __name__ == "__main__":
    unittest.main()
