"""
Word Frequency Visualization Module

Provides visualization functions for word frequency data from commit messages.
"""

import plotly.graph_objects as go

from visualization.common import create_empty_figure


def create_word_frequency_treemap(
    word_counts: dict[str, int],
    title: str = "Commit Message Word Frequency",
    top_n: int = 50,
) -> go.Figure:
    """Create a treemap visualization of word frequencies.

    Args:
        word_counts: Dictionary mapping words to their frequency counts
        title: Title for the visualization (default: "Commit Message Word Frequency")
        top_n: Maximum number of words to display (default: 50)

    Returns:
        A Plotly figure object containing the treemap
    """
    if not word_counts:
        return create_empty_figure(
            message="No word frequency data available", title=title
        )

    # Sort by frequency and take top N
    sorted_words = sorted(
        word_counts.items(), key=lambda x: x[1], reverse=True
    )[:top_n]

    # Prepare data for treemap
    words = [word for word, _ in sorted_words]
    counts = [count for _, count in sorted_words]

    # Create treemap
    fig = go.Figure(
        go.Treemap(
            labels=words,
            parents=[""] * len(words),  # All at root level
            values=counts,
            textposition="middle center",
            marker=dict(colorscale="Blues", line=dict(width=2, color="white")),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br><extra></extra>",
        )
    )

    fig.update_layout(
        title=title,
        title_font=dict(size=16),
        margin=dict(t=50, l=0, r=0, b=0),
    )

    return fig
