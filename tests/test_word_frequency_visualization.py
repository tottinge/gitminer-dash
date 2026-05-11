import unittest

from visualization.word_frequency import create_word_frequency_treemap


class TestWordFrequencyTreemap(unittest.TestCase):

    def test_empty_word_counts(self):
        """Test with empty word counts dictionary."""
        fig = create_word_frequency_treemap({})
        # Should have annotation for "no data"
        self.assertEqual(1, len(fig.layout.annotations))
        self.assertIn("No word frequency data", fig.layout.annotations[0].text)

    def test_simple_word_counts(self):
        """Test with simple word frequency data."""
        word_counts = {"bug": 5, "fix": 3, "feature": 2}
        fig = create_word_frequency_treemap(word_counts)

        # Should have treemap data
        self.assertEqual(1, len(fig.data))
        treemap = fig.data[0]

        # Check that all words are present
        self.assertIn("bug", treemap.labels)
        self.assertIn("fix", treemap.labels)
        self.assertIn("feature", treemap.labels)

        # Check values
        self.assertIn(5, treemap.values)
        self.assertIn(3, treemap.values)
        self.assertIn(2, treemap.values)

    def test_top_n_limit(self):
        """Test that top_n parameter limits the number of words displayed."""
        # Create 100 words with different frequencies
        word_counts = {f"word{i}": 100 - i for i in range(100)}

        fig = create_word_frequency_treemap(word_counts, top_n=10)
        treemap = fig.data[0]

        # Should only have 10 words
        self.assertEqual(10, len(treemap.labels))

        # Should have the top 10 words
        self.assertIn("word0", treemap.labels)  # frequency 100
        self.assertIn("word9", treemap.labels)  # frequency 91
        self.assertNotIn("word10", treemap.labels)  # frequency 90 (excluded)

    def test_sorting_by_frequency(self):
        """Test that words are sorted by frequency."""
        word_counts = {"low": 1, "high": 10, "medium": 5}
        fig = create_word_frequency_treemap(word_counts)
        treemap = fig.data[0]

        # First item should be highest frequency
        first_idx = 0
        self.assertEqual("high", treemap.labels[first_idx])
        self.assertEqual(10, treemap.values[first_idx])

    def test_custom_title(self):
        """Test with custom title."""
        word_counts = {"test": 5}
        custom_title = "Custom Word Cloud"
        fig = create_word_frequency_treemap(word_counts, title=custom_title)

        self.assertEqual(custom_title, fig.layout.title.text)

    def test_default_title(self):
        """Test default title."""
        word_counts = {"test": 5}
        fig = create_word_frequency_treemap(word_counts)

        self.assertEqual("Commit Message Word Frequency", fig.layout.title.text)

    def test_treemap_structure(self):
        """Test that treemap has correct structure."""
        word_counts = {"bug": 5, "fix": 3}
        fig = create_word_frequency_treemap(word_counts)
        treemap = fig.data[0]

        # All parents should be empty (root level)
        self.assertEqual(2, len(treemap.parents))
        self.assertTrue(all(p == "" for p in treemap.parents))

        # Should have hover template
        self.assertIn("label", treemap.hovertemplate)
        self.assertIn("value", treemap.hovertemplate)

    def test_single_word(self):
        """Test with single word."""
        word_counts = {"single": 42}
        fig = create_word_frequency_treemap(word_counts)
        treemap = fig.data[0]

        self.assertEqual(1, len(treemap.labels))
        self.assertEqual("single", treemap.labels[0])
        self.assertEqual(42, treemap.values[0])

    def test_empty_word_counts_with_custom_title_uses_exact_empty_contract(
        self,
    ):
        """Empty-path should preserve exact message and custom title propagation."""
        fig = create_word_frequency_treemap({}, title="Chosen Title")

        self.assertEqual(1, len(fig.layout.annotations))
        self.assertEqual(
            "No word frequency data available",
            fig.layout.annotations[0].to_plotly_json()["text"],
        )
        self.assertEqual(
            {"text": "Chosen Title - No Data"},
            fig.layout.title.to_plotly_json(),
        )

    def test_default_top_n_limits_to_50_words(self):
        """Default top_n should cap output at 50 entries."""
        word_counts = {f"word{i}": 1000 - i for i in range(60)}

        fig = create_word_frequency_treemap(word_counts)
        treemap = fig.data[0]

        self.assertEqual(50, len(treemap.labels))
        self.assertIn("word49", treemap.labels)
        self.assertNotIn("word50", treemap.labels)

    def test_treemap_style_contract(self):
        """Treemap should retain explicit text position, marker style, and hover template."""
        fig = create_word_frequency_treemap({"bug": 5, "fix": 3})
        treemap = fig.data[0]

        self.assertEqual("middle center", treemap.textposition)
        self.assertEqual(
            "<b>%{label}</b><br>Count: %{value}<br><extra></extra>",
            treemap.hovertemplate,
        )

        marker_json = treemap.marker.to_plotly_json()
        self.assertIn("colorscale", marker_json)
        self.assertEqual(9, len(marker_json["colorscale"]))
        self.assertEqual(
            [0.0, "rgb(247,251,255)"], marker_json["colorscale"][0]
        )
        self.assertEqual([1.0, "rgb(8,48,107)"], marker_json["colorscale"][-1])
        self.assertEqual({"color": "white", "width": 2}, marker_json["line"])

    def test_treemap_layout_title_font_and_margin_contract(self):
        """Layout should preserve title font and margin defaults."""
        fig = create_word_frequency_treemap({"bug": 5}, title="Word Counts")

        self.assertEqual(
            {"text": "Word Counts", "font": {"size": 16}},
            fig.layout.title.to_plotly_json(),
        )
        self.assertEqual(
            {"t": 50, "l": 0, "r": 0, "b": 0},
            fig.layout.margin.to_plotly_json(),
        )


if __name__ == "__main__":
    unittest.main()
