"""
Common visualization utilities shared across modules.

Provides reusable patterns and helpers for creating Plotly visualizations.
"""

import plotly.graph_objects as go


def create_empty_figure(
    message: str = "No data available", title: str = "Visualization"
) -> go.Figure:
    """
    Create a Plotly figure with a 'no data' message.

    This helper creates a consistent empty state visualization across
    different chart types when no data is available to display.

    Args:
        message: Message to display (default: "No data available")
        title: Title for the figure (default: "Visualization")

    Returns:
        A Plotly figure object with the message centered and axes hidden
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
    fig.update_layout(
        title=f"{title} - No Data",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
    return fig
