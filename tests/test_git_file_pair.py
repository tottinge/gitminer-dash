import unittest
from datetime import datetime
from unittest.mock import Mock

from utils.git import get_commits_for_file_pair


class TestGetCommitsForFilePair(unittest.TestCase):

    def create_mock_commit(self, hexsha, message, date, modified_files):
        """Helper to create a mock commit."""
        commit = Mock()
        commit.hexsha = hexsha
        commit.message = message
        commit.committed_datetime = date
        if modified_files is not None:
            parent = Mock()
            commit.parents = [parent]
            diff_items = []
            for file_path in modified_files:
                diff_item = Mock()
                diff_item.a_path = file_path
                diff_items.append(diff_item)
            commit.diff = Mock(return_value=diff_items)
        else:
            commit.parents = []
        return commit

    def test_empty_repo(self):
        """Test with no commits in the repo."""
        repo = Mock()
        repo.iter_commits = Mock(return_value=[])
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        result = get_commits_for_file_pair(repo, "file1.py", "file2.py", start, end)
        self.assertEqual([], result)

    def test_commits_with_both_files(self):
        """Test finding commits that modified both files."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        commit1 = self.create_mock_commit(
            "abc123def",
            "feat: update both files",
            datetime(2025, 6, 15, 10, 30),
            ["file1.py", "file2.py"],
        )
        commit2 = self.create_mock_commit(
            "def456ghi", "fix: only file1", datetime(2025, 7, 1, 14, 20), ["file1.py"]
        )
        commit3 = self.create_mock_commit(
            "ghi789jkl",
            "refactor: both files again",
            datetime(2025, 8, 10, 9, 45),
            ["file1.py", "file2.py", "other.py"],
        )
        repo = Mock()
        repo.iter_commits = Mock(return_value=[commit1, commit2, commit3])
        result = get_commits_for_file_pair(repo, "file1.py", "file2.py", start, end)
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
        commit1 = self.create_mock_commit(
            "abc123def",
            "before range",
            datetime(2025, 5, 15, 10, 30),
            ["file1.py", "file2.py"],
        )
        commit2 = self.create_mock_commit(
            "def456ghi",
            "in range",
            datetime(2025, 7, 1, 14, 20),
            ["file1.py", "file2.py"],
        )
        commit3 = self.create_mock_commit(
            "ghi789jkl",
            "after range",
            datetime(2025, 9, 10, 9, 45),
            ["file1.py", "file2.py"],
        )
        repo = Mock()
        repo.iter_commits = Mock(return_value=[commit1, commit2, commit3])
        result = get_commits_for_file_pair(repo, "file1.py", "file2.py", start, end)
        self.assertEqual(1, len(result))
        self.assertEqual("def456g", result[0]["hash"])
        self.assertEqual("in range", result[0]["message"])

    def test_message_truncation(self):
        """Test that long commit messages are truncated."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        long_message = "a" * 100 + "\nSecond line"
        commit = self.create_mock_commit(
            "abc123def",
            long_message,
            datetime(2025, 6, 15, 10, 30),
            ["file1.py", "file2.py"],
        )
        repo = Mock()
        repo.iter_commits = Mock(return_value=[commit])
        result = get_commits_for_file_pair(repo, "file1.py", "file2.py", start, end)
        self.assertEqual(1, len(result))
        self.assertEqual(80, len(result[0]["message"]))
        self.assertEqual("a" * 80, result[0]["message"])

    def test_initial_commit_no_parents(self):
        """Test handling of initial commit with no parents."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        commit = self.create_mock_commit(
            "abc123def", "Initial commit", datetime(2025, 6, 15, 10, 30), None
        )
        repo = Mock()
        repo.iter_commits = Mock(return_value=[commit])
        result = get_commits_for_file_pair(repo, "file1.py", "file2.py", start, end)
        self.assertEqual(0, len(result))


if __name__ == "__main__":
    unittest.main()
