"""Unit tests for visualization.common helpers."""

import unittest

from visualization.common import create_empty_figure


class TestVisualizationCommon(unittest.TestCase):
    """Test suite for shared visualization helpers."""

    def test_create_empty_figure_default_serialized_contract(self):
        """Default empty figure should use the exact annotation/layout contract."""
        fig = create_empty_figure()

        assert len(fig.layout.annotations) == 1
        assert fig.layout.annotations[0].to_plotly_json() == {
            "font": {"size": 20},
            "showarrow": False,
            "text": "No data available",
            "x": 0.5,
            "xref": "paper",
            "y": 0.5,
            "yref": "paper",
        }
        assert fig.layout.xaxis.to_plotly_json() == {
            "showgrid": False,
            "zeroline": False,
            "showticklabels": False,
        }
        assert fig.layout.yaxis.to_plotly_json() == {
            "showgrid": False,
            "zeroline": False,
            "showticklabels": False,
        }
        assert fig.layout.title.to_plotly_json() == {
            "text": "Visualization - No Data"
        }

    def test_create_empty_figure_custom_message_and_title(self):
        """Custom message/title should flow into annotation and title text."""
        fig = create_empty_figure(
            message="No commits in this range",
            title="Commits",
        )

        assert len(fig.layout.annotations) == 1
        assert (
            fig.layout.annotations[0].to_plotly_json()["text"]
            == "No commits in this range"
        )
        assert fig.layout.title.to_plotly_json() == {
            "text": "Commits - No Data"
        }


if __name__ == "__main__":
    unittest.main()
