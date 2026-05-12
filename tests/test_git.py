import unittest
from unittest.mock import Mock

from utils.git import tree_entry_size


class TestTreeEntrySize(unittest.TestCase):

    def test_returns_entry_size_when_path_exists(self):
        repo = Mock()
        entry = Mock(size=123)
        commit = Mock()
        commit.tree = {"src/main.py": entry}
        repo.commit.return_value = commit

        result = tree_entry_size(repo, "HEAD", "src/main.py")

        self.assertEqual(123, result)
        repo.commit.assert_called_once_with("HEAD")

    def test_returns_zero_when_path_is_missing(self):
        repo = Mock()
        commit = Mock()
        commit.tree = {}
        repo.commit.return_value = commit

        result = tree_entry_size(repo, "HEAD", "src/main.py")

        self.assertEqual(0, result)

    def test_returns_zero_when_size_attribute_is_missing(self):
        repo = Mock()
        entry_without_size = object()
        commit = Mock()
        commit.tree = {"src/main.py": entry_without_size}
        repo.commit.return_value = commit

        result = tree_entry_size(repo, "HEAD", "src/main.py")

        self.assertEqual(0, result)

    def test_returns_zero_when_size_is_none(self):
        repo = Mock()
        entry = Mock(size=None)
        commit = Mock()
        commit.tree = {"src/main.py": entry}
        repo.commit.return_value = commit

        result = tree_entry_size(repo, "HEAD", "src/main.py")

        self.assertEqual(0, result)

    def test_returns_zero_when_commit_resolution_fails(self):
        repo = Mock()
        repo.commit.side_effect = RuntimeError("bad ref")

        result = tree_entry_size(repo, "HEAD", "src/main.py")

        self.assertEqual(0, result)


if __name__ == "__main__":
    unittest.main()
