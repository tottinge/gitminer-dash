"""
Utility functions for creating Plotly figures.

This module provides common functionality for creating Plotly visualizations
used across different pages.
"""

import plotly.graph_objects as go


def create_empty_figure(
    message: str = "No data available", title: str | None = None
) -> go.Figure:
    """
    Create a Plotly figure with a 'no data' message.

    Args:
        message: Message to display (default: "No data available")
        title: Optional title for the figure

    Returns:
        A Plotly figure object with the message centered

    Example:
        >>> fig = create_empty_figure("No commits found")
        >>> fig.layout.annotations[0].text
        'No commits found'
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=20),
    )

    layout_updates = {
        "xaxis": dict(showgrid=False, zeroline=False, showticklabels=False),
        "yaxis": dict(showgrid=False, zeroline=False, showticklabels=False),
    }

    if title:
        layout_updates["title"] = title

    fig.update_layout(**layout_updates)

    return fig
