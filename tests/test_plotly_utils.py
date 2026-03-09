"""Unit tests for utils.plotly_utils."""

import unittest
from unittest.mock import patch

from utils.plotly_utils import _wrap_message, create_empty_figure


class TestPlotlyUtils(unittest.TestCase):
    """Test suite for message wrapping and empty figure helpers."""

    def test_wrap_message_empty_returns_empty_string(self):
        assert _wrap_message("") == ""

    def test_wrap_message_uses_default_wrap_contract(self):
        with patch(
            "utils.plotly_utils.textwrap.wrap", return_value=["wrapped"]
        ) as mock_wrap:
            result = _wrap_message("hello world")

        assert result == "wrapped"
        mock_wrap.assert_called_once_with(
            "hello world",
            width=36,
            break_long_words=False,
            break_on_hyphens=True,
        )

    def test_wrap_message_truncates_and_appends_ellipsis(self):
        with patch(
            "utils.plotly_utils.textwrap.wrap",
            return_value=["line1", "line2", "line3", "line4", "line5"],
        ):
            result = _wrap_message("irrelevant", width=12, max_lines=4)

        assert result == "line1<br>line2<br>line3<br>line4…"

    def test_wrap_message_default_max_lines_is_four(self):
        with patch(
            "utils.plotly_utils.textwrap.wrap",
            return_value=["l1", "l2", "l3", "l4", "l5"],
        ):
            result = _wrap_message("irrelevant")

        assert result == "l1<br>l2<br>l3<br>l4…"

    def test_wrap_message_exactly_max_lines_does_not_truncate(self):
        with patch(
            "utils.plotly_utils.textwrap.wrap",
            return_value=["l1", "l2", "l3", "l4"],
        ):
            result = _wrap_message("irrelevant", max_lines=4)

        assert result == "l1<br>l2<br>l3<br>l4"

    def test_wrap_message_preserves_existing_three_dot_ellipsis(self):
        with patch(
            "utils.plotly_utils.textwrap.wrap",
            return_value=["line1", "line2", "line3", "line4...", "line5"],
        ):
            result = _wrap_message("irrelevant", width=12, max_lines=4)

        assert result == "line1<br>line2<br>line3<br>line4..."

    def test_wrap_message_preserves_existing_unicode_ellipsis(self):
        with patch(
            "utils.plotly_utils.textwrap.wrap",
            return_value=["line1", "line2", "line3", "line4…", "line5"],
        ):
            result = _wrap_message("irrelevant", width=12, max_lines=4)

        assert result == "line1<br>line2<br>line3<br>line4…"

    def test_wrap_message_uses_rstrip_when_appending_ellipsis(self):
        with patch(
            "utils.plotly_utils.textwrap.wrap",
            return_value=["line1", "line2", "line3", "  line4  ", "line5"],
        ):
            result = _wrap_message("irrelevant", width=12, max_lines=4)

        assert result == "line1<br>line2<br>line3<br>  line4…"

    def test_create_empty_figure_calls_wrap_message_with_contract(self):
        with patch(
            "utils.plotly_utils._wrap_message", return_value="wrapped text"
        ) as mock_wrap:
            fig = create_empty_figure(
                message="No commits found here", title="Custom"
            )

        mock_wrap.assert_called_once_with(
            "No commits found here", width=36, max_lines=4
        )
        assert len(fig.layout.annotations) == 1
        assert fig.layout.annotations[0].text == "wrapped text"
        assert fig.layout.title.text == "Custom"

    def test_create_empty_figure_default_layout_contract(self):
        fig = create_empty_figure()

        assert len(fig.layout.annotations) == 1
        annotation = fig.layout.annotations[0]
        assert annotation.text == "No data available"
        assert annotation.xref == "paper"
        assert annotation.yref == "paper"
        assert annotation.x == 0.5
        assert annotation.y == 0.5
        assert annotation.xanchor == "center"
        assert annotation.yanchor == "middle"
        assert annotation.align == "center"
        assert annotation.showarrow is False
        assert annotation.font.size == 16
        assert fig.layout.title.text in (None, "")
        assert fig.layout.xaxis.showgrid is False
        assert fig.layout.xaxis.zeroline is False
        assert fig.layout.xaxis.showticklabels is False
        assert fig.layout.yaxis.showgrid is False
        assert fig.layout.yaxis.zeroline is False
        assert fig.layout.yaxis.showticklabels is False

    def test_create_empty_figure_title_updates_margin_and_title(self):
        fig = create_empty_figure(
            message=(
                "This is a long message intended to wrap cleanly inside "
                "a no-data figure annotation"
            ),
            title="Weekly Commits",
        )

        assert fig.layout.title.text == "Weekly Commits"
        assert "<br>" in fig.layout.annotations[0].text


if __name__ == "__main__":
    unittest.main()
