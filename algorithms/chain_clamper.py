"""
Clamp commit chains to specific time periods.

This module provides pure functions for filtering and adjusting
chain time spans to fit within specified date ranges.
"""

from datetime import datetime
from typing import List
from algorithms.chain_models import ChainData, ClampedChain


def clamp_chains_to_period(
    chains: List[ChainData],
    start_date: datetime,
    end_date: datetime
) -> List[ClampedChain]:
    """
    Clamp commit chains to a specific time period.
    
    Adjusts each chain's time span to fit within the given date range.
    Chains that fall completely outside the range are filtered out.
    
    Args:
        chains: List of ChainData objects to clamp
        start_date: Start of the target period (inclusive)
        end_date: End of the target period (inclusive)
        
    Returns:
        List of ClampedChain objects. Chains are filtered and adjusted:
        - Start timestamp is max(chain.early_timestamp, start_date)
        - End timestamp is min(chain.late_timestamp, end_date)
        - Chains where clamped_first > clamped_last are excluded
    """
    clamped_chains = []
    
    for chain in chains:
        # Clamp timestamps to the period bounds
        clamped_first = max(chain.early_timestamp, start_date)
        clamped_last = min(chain.late_timestamp, end_date)
        
        # Skip chains that don't overlap with the period
        if clamped_first > clamped_last:
            continue
        
        clamped_duration = clamped_last - clamped_first
        
        clamped_chain = ClampedChain(
            clamped_first=clamped_first,
            clamped_last=clamped_last,
            clamped_duration=clamped_duration,
            commit_count=chain.commit_count,
            earliest_sha=chain.earliest_sha,
            latest_sha=chain.latest_sha
        )
        
        clamped_chains.append(clamped_chain)
    
    return clamped_chains
