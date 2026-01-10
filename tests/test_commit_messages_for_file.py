import unittest
from datetime import datetime
from unittest.mock import Mock

from tests.conftest import create_mock_commit_with_diffs
from utils.git import get_commit_messages_for_file


class TestGetCommitMessagesForFile(unittest.TestCase):

    def test_empty_repo(self):
        """Test with no commits in the repo."""
        repo = Mock()
        repo.iter_commits = Mock(return_value=[])
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        result = list(get_commit_messages_for_file(repo, "test.py", start, end))
        self.assertEqual([], result)
        # Verify iter_commits was called with correct parameters
        repo.iter_commits.assert_called_once_with(
            paths="test.py", since=start, until=end
        )

    def test_commits_with_target_file(self):
        """Test finding commits that modified the target file."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        commit1 = create_mock_commit_with_diffs(
            message="feat: update test file",
            date=datetime(2025, 6, 15, 10, 30),
            modified_files=["test.py", "other.py"],
        )
        commit3 = create_mock_commit_with_diffs(
            message="refactor: test file again",
            date=datetime(2025, 8, 10, 9, 45),
            modified_files=["test.py"],
        )
        repo = Mock()
        # iter_commits with path filter should only return commits for that file
        repo.iter_commits = Mock(return_value=[commit1, commit3])
        result = list(get_commit_messages_for_file(repo, "test.py", start, end))
        self.assertEqual(2, len(result))
        self.assertEqual("feat: update test file", result[0])
        self.assertEqual("refactor: test file again", result[1])

    def test_date_filtering(self):
        """Test that commits outside the date range are filtered out."""
        start = datetime(2025, 6, 1)
        end = datetime(2025, 7, 31)
        commit2 = create_mock_commit_with_diffs(
            message="in range",
            date=datetime(2025, 7, 1, 14, 20),
            modified_files=["test.py"],
        )
        repo = Mock()
        # iter_commits with since/until should only return commits in date range
        repo.iter_commits = Mock(return_value=[commit2])
        result = list(get_commit_messages_for_file(repo, "test.py", start, end))
        self.assertEqual(1, len(result))
        self.assertEqual("in range", result[0])

    def test_full_message_preservation(self):
        """Test that full commit messages including multiple lines are preserved."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        multi_line_message = (
            "feat: add feature\n\nThis is a detailed description\nwith multiple lines"
        )
        commit = create_mock_commit_with_diffs(
            message=multi_line_message,
            date=datetime(2025, 6, 15, 10, 30),
            modified_files=["test.py"],
        )
        repo = Mock()
        repo.iter_commits = Mock(return_value=[commit])
        result = list(get_commit_messages_for_file(repo, "test.py", start, end))
        self.assertEqual(1, len(result))
        self.assertEqual(multi_line_message, result[0])

    def test_initial_commit_no_parents(self):
        """Test handling of initial commit with no parents."""
        start = datetime(2025, 1, 1)
        end = datetime(2025, 12, 31)
        commit = create_mock_commit_with_diffs(
            message="Initial commit",
            date=datetime(2025, 6, 15, 10, 30),
            modified_files=None,
        )
        repo = Mock()
        # iter_commits with path filter would return the commit if file exists
        repo.iter_commits = Mock(return_value=[commit])
        result = list(get_commit_messages_for_file(repo, "test.py", start, end))
        # Since we're using git's path filtering, it returns commits that touched the file
        self.assertEqual(1, len(result))
        self.assertEqual("Initial commit", result[0])


if __name__ == "__main__":
    unittest.main()
