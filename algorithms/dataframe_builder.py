"""
Build pandas DataFrames from timeline data.

This module provides pure functions for converting timeline rows
into properly-typed pandas DataFrames for visualization.
"""

from pandas import DataFrame

from algorithms.chain_models import TimelineRow


def create_timeline_dataframe(timeline_rows: list[TimelineRow]) -> DataFrame:
    """
    Create a pandas DataFrame from timeline rows.
    
    Converts TimelineRow objects into a DataFrame with properly typed columns,
    especially ensuring datetime columns are correctly typed for Plotly.
    
    This function includes a fix for timezone-aware datetime handling:
    DateTime objects from git commits are timezone-aware, but pandas/Plotly
    can have issues with them. We explicitly convert to pandas datetime64[ns]
    to ensure compatibility.
    
    Args:
        timeline_rows: List of TimelineRow objects
        
    Returns:
        DataFrame with columns:
        - first (datetime64[ns]): Start timestamp
        - last (datetime64[ns]): End timestamp
        - elevation (int): Vertical stacking level
        - commit_counts (int): Number of commits
        - head (str): Earliest commit SHA
        - tail (str): Latest commit SHA
        - duration (int): Duration in days
        - density (float): Commit sparsity metric
    """
    # Convert TimelineRow objects to dictionaries
    rows = [
        dict(
            first=row.first,
            last=row.last,
            elevation=row.elevation,
            commit_counts=row.commit_counts,
            head=row.head,
            tail=row.tail,
            duration=row.duration,
            density=row.density,
        )
        for row in timeline_rows
    ]
    
    # Create DataFrame
    df = DataFrame(
        rows,
        columns=[
            "first",
            "last",
            "elevation",
            "commit_counts",
            "head",
            "tail",
            "duration",
            "density",
        ],
    )
    
    # Convert datetime columns to pandas datetime type
    # This prevents "Can only use .dt accessor with datetimelike values" errors
    # and ensures compatibility with px.timeline()
    if len(df) > 0:
        # Convert to pandas datetime, handling timezone-aware datetimes
        # We convert to UTC and then make timezone-naive for pandas datetime64[ns]
        import pandas as pd
        df["first"] = pd.to_datetime(df["first"], utc=True).dt.tz_localize(None)
        df["last"] = pd.to_datetime(df["last"], utc=True).dt.tz_localize(None)
    
    return df
