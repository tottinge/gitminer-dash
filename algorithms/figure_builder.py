"""
Build Plotly timeline figures from DataFrames.

This module provides pure functions for creating configured
Plotly timeline visualizations.
"""

import plotly.express as px
from pandas import DataFrame


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
        x_start="first",
        x_end="last",
        y="elevation",
        color="density",
        title="Code Lines (selected period)",
        labels={
            "elevation": "",
            "density": "Commit Sparsity",
            "first": "Begun",
            "last": "Ended",
            "duration": "Days",
        },
        hover_data={
            "first": True,
            "head": True,
            "last": True,
            "tail": True,
            "commit_counts": True,
            "duration": True,
            "elevation": False,
            "density": True,
        },
    )
    return figure
