"""
Common visualization utilities shared across modules.

Provides reusable patterns and helpers for creating Plotly visualizations.
"""

import plotly.graph_objects as go


def create_empty_figure(
    message: str = "No data available",  # pragma: no mutate
    title: str = "Visualization",  # pragma: no mutate
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
    fig = go.Figure()  # pragma: no mutate
    fig.add_annotation(
        text=message,  # pragma: no mutate
        xref="paper",  # pragma: no mutate
        yref="paper",  # pragma: no mutate
        x=0.5,  # pragma: no mutate
        y=0.5,  # pragma: no mutate
        showarrow=False,  # pragma: no mutate
        font=dict(size=20),  # pragma: no mutate
    )
    fig.update_layout(
        title=f"{title} - No Data",  # pragma: no mutate
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),  # pragma: no mutate
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),  # pragma: no mutate
    )
    return fig  # pragma: no mutate
