"""
Calculate layout for timeline visualization of commit chains.

This module provides pure functions for converting clamped chains
into timeline rows with vertical stacking to prevent overlaps.
"""

from algorithms.chain_models import ClampedChain, TimelineRow
from algorithms.stacking import SequenceStacker


def calculate_chain_layout(
    clamped_chains: list[ClampedChain],
) -> list[TimelineRow]:
    """
    Calculate layout for timeline visualization.

    Converts clamped chains into timeline rows with vertical positioning
    (elevation) to prevent overlapping time spans.

    Args:
        clamped_chains: List of ClampedChain objects to layout

    Returns:
        List of TimelineRow objects with calculated elevations.
        Each row includes:
        - Timestamps (first, last)
        - Elevation (vertical stacking level)
        - Metadata (commit count, SHAs)
        - Derived metrics (duration in days, density)
    """
    rows = []
    stacker = SequenceStacker()

    for clamped in clamped_chains:
        # Calculate elevation using stacker to prevent overlaps
        height = stacker.height_for(
            [clamped.clamped_first, clamped.clamped_last]
        )

        # Calculate derived metrics
        duration_days = clamped.clamped_duration.days
        density = (
            (duration_days / clamped.commit_count)
            if clamped.commit_count
            else 0
        )

        row = TimelineRow(
            first=clamped.clamped_first,
            last=clamped.clamped_last,
            elevation=height,
            commit_counts=clamped.commit_count,
            head=clamped.earliest_sha,
            tail=clamped.latest_sha,
            duration=duration_days,
            density=density,
        )

        rows.append(row)

    return rows
