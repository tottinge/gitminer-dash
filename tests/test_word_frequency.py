import unittest
from algorithms.word_frequency import calculate_word_frequency, STOP_WORDS


class TestWordFrequency(unittest.TestCase):

    def test_empty_messages(self):
        """Test with empty message list."""
        result = calculate_word_frequency([])
        self.assertEqual({}, result)

    def test_single_message_simple(self):
        """Test with a single simple message."""
        messages = ["fix bug"]
        result = calculate_word_frequency(messages)
        self.assertEqual({"fix": 1, "bug": 1}, result)

    def test_multiple_messages(self):
        """Test word counting across multiple messages."""
        messages = [
            "fix bug in parser",
            "refactor parser logic",
            "test parser functionality"
        ]
        result = calculate_word_frequency(messages)
        self.assertEqual(3, result["parser"])
        self.assertEqual(1, result["fix"])
        self.assertEqual(1, result["bug"])
        self.assertEqual(1, result["refactor"])
        self.assertEqual(1, result["logic"])
        self.assertEqual(1, result["test"])
        self.assertEqual(1, result["functionality"])

    def test_case_insensitivity(self):
        """Test that word counting is case-insensitive."""
        messages = [
            "Fix the bug",
            "fix the issue",
            "FIX the problem"
        ]
        result = calculate_word_frequency(messages)
        self.assertEqual(3, result["fix"])
        self.assertEqual(1, result["bug"])
        self.assertEqual(1, result["issue"])
        self.assertEqual(1, result["problem"])

    def test_stop_words_excluded(self):
        """Test that stop words are excluded by default."""
        messages = ["fix the bug in the code"]
        result = calculate_word_frequency(messages)
        self.assertNotIn("the", result)
        self.assertNotIn("in", result)
        self.assertIn("fix", result)
        self.assertIn("bug", result)
        self.assertIn("code", result)

    def test_stop_words_included(self):
        """Test that stop words can be included when flag is False."""
        messages = ["fix the bug"]
        result = calculate_word_frequency(messages, exclude_stop_words=False)
        self.assertIn("the", result)
        self.assertEqual(1, result["the"])

    def test_min_word_length_default(self):
        """Test that words shorter than 3 characters are excluded by default."""
        messages = ["a fix to do it"]
        result = calculate_word_frequency(messages)
        self.assertNotIn("a", result)
        self.assertNotIn("to", result)
        self.assertNotIn("do", result)
        self.assertNotIn("it", result)
        self.assertIn("fix", result)

    def test_min_word_length_custom(self):
        """Test custom minimum word length."""
        messages = ["a big fix to do"]
        result = calculate_word_frequency(messages, min_word_length=2, exclude_stop_words=False)
        self.assertNotIn("a", result)  # length 1
        self.assertIn("to", result)    # length 2
        self.assertIn("do", result)    # length 2
        self.assertIn("big", result)   # length 3
        self.assertIn("fix", result)   # length 3

    def test_special_characters_ignored(self):
        """Test that special characters and numbers are ignored."""
        messages = [
            "fix bug #123",
            "update version 2.0",
            "add feature (urgent)"
        ]
        result = calculate_word_frequency(messages)
        self.assertNotIn("123", result)
        self.assertNotIn("#123", result)
        self.assertNotIn("2.0", result)
        self.assertIn("fix", result)
        self.assertIn("bug", result)
        self.assertIn("update", result)
        self.assertIn("version", result)
        self.assertIn("add", result)
        self.assertIn("feature", result)
        self.assertIn("urgent", result)

    def test_multiline_messages(self):
        """Test handling of multi-line commit messages."""
        messages = [
            "feat: add new feature\n\nThis adds a new feature\nwith multiple lines"
        ]
        result = calculate_word_frequency(messages)
        self.assertEqual(2, result["feature"])  # appears twice
        self.assertEqual(2, result["new"])      # appears twice
        self.assertEqual(1, result["feat"])
        self.assertEqual(1, result["add"])
        self.assertEqual(1, result["adds"])
        self.assertEqual(1, result["multiple"])
        self.assertEqual(1, result["lines"])

    def test_conventional_commit_format(self):
        """Test with conventional commit message format."""
        messages = [
            "feat: add user authentication",
            "fix: resolve login bug",
            "refactor: improve code structure"
        ]
        result = calculate_word_frequency(messages)
        self.assertIn("feat", result)
        self.assertIn("fix", result)
        self.assertIn("refactor", result)
        self.assertIn("add", result)
        self.assertIn("user", result)
        self.assertIn("authentication", result)
        self.assertIn("resolve", result)
        self.assertIn("login", result)
        self.assertIn("bug", result)


if __name__ == "__main__":
    unittest.main()
