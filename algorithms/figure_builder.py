"""
Build Plotly timeline figures from DataFrames.

This module provides pure functions for creating configured
Plotly timeline visualizations.
"""

import plotly.express as px
from pandas import DataFrame

from algorithms.chain_models import (
    TIMELINE_COLOR_COLUMN,
    TIMELINE_CUSTOM_DATA_COLUMNS,
    TIMELINE_HOVER_DATA,
    TIMELINE_LABELS,
    TIMELINE_X_END_COLUMN,
    TIMELINE_X_START_COLUMN,
    TIMELINE_Y_COLUMN,
)


def create_timeline_figure(df: DataFrame):
    """
    Create a Plotly timeline figure from a DataFrame.

    Configures a timeline visualization with appropriate labels,
    hover data, and styling for commit chain visualization.

    Args:
        df: DataFrame with columns:
            - first: Start timestamps
            - last: End timestamps
            - elevation: Vertical position
            - density: Commit sparsity metric
            - commit_counts: Number of commits
            - head: Earliest commit SHA
            - tail: Latest commit SHA
            - duration: Duration in days

    Returns:
        Plotly Figure object configured for timeline display.
    """
    figure = px.timeline(
        data_frame=df,
        x_start=TIMELINE_X_START_COLUMN,
        x_end=TIMELINE_X_END_COLUMN,
        y=TIMELINE_Y_COLUMN,
        color=TIMELINE_COLOR_COLUMN,
        # Expose chain boundary SHAs so the codelines page can recover the
        # full chain when a bar is selected.
        custom_data=TIMELINE_CUSTOM_DATA_COLUMNS,
        title="Code Lines (selected period)",
        labels=TIMELINE_LABELS,  # pragma: no mutate
        hover_data=TIMELINE_HOVER_DATA,
    )
    return figure
