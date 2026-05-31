import unittest
from datetime import datetime
from unittest.mock import Mock

from tests.conftest import create_mock_commit_with_diffs
from utils.git import get_commits_for_file_pair


class TestGetCommitsForFilePair(unittest.TestCase):

    def test_empty_repo(self):
        """Test with no commits in the repo."""
        repo = Mock()
        repo.iter_commits = Mock(return_value=[])
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        result = get_commits_for_file_pair(
            repo, "file1.py", "file2.py", start, end
        )
        self.assertEqual([], result)

    def test_commits_with_both_files(self):
        """Test finding commits that modified both files."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        commit1 = create_mock_commit_with_diffs(
            hexsha="abc123def",
            message="feat: update both files",
            date=datetime(2025, 6, 15, 10, 30),
            modified_files=["file1.py", "file2.py"],
        )
        commit2 = create_mock_commit_with_diffs(
            hexsha="def456ghi",
            message="fix: only file1",
            date=datetime(2025, 7, 1, 14, 20),
            modified_files=["file1.py"],
        )
        commit3 = create_mock_commit_with_diffs(
            hexsha="ghi789jkl",
            message="refactor: both files again",
            date=datetime(2025, 8, 10, 9, 45),
            modified_files=["file1.py", "file2.py", "other.py"],
        )
        repo = Mock()
        repo.iter_commits = Mock(return_value=[commit1, commit2, commit3])
        result = get_commits_for_file_pair(
            repo, "file1.py", "file2.py", start, end
        )
        self.assertEqual(2, len(result))
        self.assertEqual("abc123d", result[0]["hash"])
        self.assertEqual("2025-06-15 10:30", result[0]["date"])
        self.assertEqual("feat: update both files", result[0]["message"])
        self.assertEqual("ghi789j", result[1]["hash"])
        self.assertEqual("refactor: both files again", result[1]["message"])

    def test_date_filtering(self):
        """Test that commits outside the date range are filtered out."""
        start = datetime(2025, 6, 1)
        end = datetime(2025, 7, 31)
        commit1 = create_mock_commit_with_diffs(
            hexsha="abc123def",
            message="before range",
            date=datetime(2025, 5, 15, 10, 30),
            modified_files=["file1.py", "file2.py"],
        )
        commit2 = create_mock_commit_with_diffs(
            hexsha="def456ghi",
            message="in range",
            date=datetime(2025, 7, 1, 14, 20),
            modified_files=["file1.py", "file2.py"],
        )
        commit3 = create_mock_commit_with_diffs(
            hexsha="ghi789jkl",
            message="after range",
            date=datetime(2025, 9, 10, 9, 45),
            modified_files=["file1.py", "file2.py"],
        )
        repo = Mock()
        repo.iter_commits = Mock(return_value=[commit1, commit2, commit3])
        result = get_commits_for_file_pair(
            repo, "file1.py", "file2.py", start, end
        )
        self.assertEqual(1, len(result))
        self.assertEqual("def456g", result[0]["hash"])
        self.assertEqual("in range", result[0]["message"])

    def test_commit_date_equal_to_period_start_is_included(self):
        """Commit exactly at period start should be included."""
        start = datetime(2025, 6, 1, 0, 0)
        end = datetime(2025, 7, 31, 23, 59)
        commit = create_mock_commit_with_diffs(
            hexsha="start01abcdef",
            message="boundary start",
            date=start,
            modified_files=["file1.py", "file2.py"],
        )
        repo = Mock()
        repo.iter_commits = Mock(return_value=[commit])

        result = get_commits_for_file_pair(
            repo, "file1.py", "file2.py", start, end
        )

        self.assertEqual(1, len(result))
        self.assertEqual("start01", result[0]["hash"])
        self.assertEqual("boundary start", result[0]["message"])

    def test_commit_date_equal_to_period_end_is_included(self):
        """Commit exactly at period end should be included."""
        start = datetime(2025, 6, 1, 0, 0)
        end = datetime(2025, 7, 31, 23, 59)
        commit = create_mock_commit_with_diffs(
            hexsha="end01abcdef12",
            message="boundary end",
            date=end,
            modified_files=["file1.py", "file2.py"],
        )
        repo = Mock()
        repo.iter_commits = Mock(return_value=[commit])

        result = get_commits_for_file_pair(
            repo, "file1.py", "file2.py", start, end
        )

        self.assertEqual(1, len(result))
        self.assertEqual("end01ab", result[0]["hash"])
        self.assertEqual("boundary end", result[0]["message"])

    def test_commit_outside_period_is_excluded(self):
        """Commit outside the period should not be included."""
        start = datetime(2025, 6, 1, 0, 0)
        end = datetime(2025, 7, 31, 23, 59)
        before_start = create_mock_commit_with_diffs(
            hexsha="before01abcde",
            message="before start",
            date=datetime(2025, 5, 31, 23, 59),
            modified_files=["file1.py", "file2.py"],
        )
        after_end = create_mock_commit_with_diffs(
            hexsha="after01abcdef",
            message="after end",
            date=datetime(2025, 8, 1, 0, 0),
            modified_files=["file1.py", "file2.py"],
        )
        repo = Mock()
        repo.iter_commits = Mock(return_value=[before_start, after_end])

        result = get_commits_for_file_pair(
            repo, "file1.py", "file2.py", start, end
        )

        self.assertEqual([], result)

    def test_message_truncation(self):
        """Test that long commit messages are truncated."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        long_message = "a" * 100 + "\nSecond line"
        commit = create_mock_commit_with_diffs(
            hexsha="abc123def",
            message=long_message,
            date=datetime(2025, 6, 15, 10, 30),
            modified_files=["file1.py", "file2.py"],
        )
        repo = Mock()
        repo.iter_commits = Mock(return_value=[commit])
        result = get_commits_for_file_pair(
            repo, "file1.py", "file2.py", start, end
        )
        self.assertEqual(1, len(result))
        self.assertEqual(80, len(result[0]["message"]))
        self.assertEqual("a" * 80, result[0]["message"])

    def test_message_uses_only_first_line_when_short(self):
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        commit = create_mock_commit_with_diffs(
            hexsha="abc123def",
            message="short summary\ndetails should not be included",
            date=datetime(2025, 6, 15, 10, 30),
            modified_files=["file1.py", "file2.py"],
        )
        repo = Mock()
        repo.iter_commits = Mock(return_value=[commit])

        result = get_commits_for_file_pair(
            repo, "file1.py", "file2.py", start, end
        )

        self.assertEqual(1, len(result))
        self.assertEqual("short summary", result[0]["message"])
        self.assertNotIn("\n", result[0]["message"])

    def test_initial_commit_no_parents(self):
        """Test handling of initial commit with no parents."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        commit = create_mock_commit_with_diffs(
            hexsha="abc123def",
            message="Initial commit",
            date=datetime(2025, 6, 15, 10, 30),
            modified_files=None,
        )
        repo = Mock()
        repo.iter_commits = Mock(return_value=[commit])
        result = get_commits_for_file_pair(
            repo, "file1.py", "file2.py", start, end
        )
        self.assertEqual(0, len(result))

    def test_diff_is_requested_from_first_parent(self):
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        parent = Mock()
        commit = Mock()
        commit.hexsha = "abc123def456"
        commit.message = "feat: update both"
        commit.committed_datetime = datetime(2025, 6, 15, 10, 30)
        commit.parents = [parent]

        first = Mock()
        first.a_path = "file1.py"
        second = Mock()
        second.a_path = "file2.py"
        commit.diff = Mock(return_value=[first, second])

        repo = Mock()
        repo.iter_commits = Mock(return_value=[commit])

        result = get_commits_for_file_pair(
            repo, "file1.py", "file2.py", start, end
        )

        commit.diff.assert_called_once_with(parent)
        self.assertEqual(1, len(result))


if __name__ == "__main__":
    unittest.main()
