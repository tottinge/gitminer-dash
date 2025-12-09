"""
Utility functions for creating Plotly figures.

This module provides common functionality for creating Plotly visualizations
used across different pages.
"""

import textwrap

import plotly.graph_objects as go


def _wrap_message(message: str, width: int = 36, max_lines: int = 4) -> str:
    """Wrap a message to fit inside a Plotly annotation.

    - Inserts HTML <br> line breaks between wrapped lines.
    - Truncates to at most `max_lines` lines and appends an ellipsis if needed.
    """
    if not message:
        return ""

    lines = textwrap.wrap(
        message, width=width, break_long_words=False, break_on_hyphens=True
    )
    if not lines:
        return message

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        # ensure a clean ellipsis at the end
        if lines[-1].endswith("…"):
            pass
        elif lines[-1].endswith("..."):
            lines[-1] = lines[-1]
        else:
            lines[-1] = lines[-1].rstrip() + "…"

    return "<br>".join(lines)


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
    # Wrap and possibly truncate the message so it fits within the plot area
    wrapped = _wrap_message(message, width=36, max_lines=4)

    fig = go.Figure()
    fig.add_annotation(
        text=wrapped,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        xanchor="center",
        yanchor="middle",
        align="center",
        showarrow=False,
        font=dict(size=16),
    )

    layout_updates = {
        "xaxis": dict(showgrid=False, zeroline=False, showticklabels=False),
        "yaxis": dict(showgrid=False, zeroline=False, showticklabels=False),
        "margin": dict(l=10, r=10, b=10, t=40 if title else 10),
    }

    if title:
        layout_updates["title"] = title

    fig.update_layout(**layout_updates)

    return fig
