"""
Data models for commit chain analysis.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class ChainData:
    """
    Represents a connected chain of commits.
    
    Attributes:
        early_timestamp: Timestamp of the earliest commit in the chain
        late_timestamp: Timestamp of the latest commit in the chain
        commit_count: Number of commits in the chain
        duration: Time span from earliest to latest commit
        earliest_sha: SHA hash of the earliest commit
        latest_sha: SHA hash of the latest commit
    """
    early_timestamp: datetime
    late_timestamp: datetime
    commit_count: int
    duration: timedelta
    earliest_sha: str
    latest_sha: str
    
    def __lt__(self, other):
        """Allow sorting by early_timestamp."""
        return self.early_timestamp < other.early_timestamp


@dataclass(frozen=True, slots=True)
class ClampedChain:
    """
    Represents a commit chain clamped to a specific time period.
    
    Attributes:
        clamped_first: Start of chain, clamped to period bounds
        clamped_last: End of chain, clamped to period bounds
        clamped_duration: Duration of the clamped time span
        commit_count: Number of commits in the original chain
        earliest_sha: SHA hash of the earliest commit in the chain
        latest_sha: SHA hash of the latest commit in the chain
    """
    clamped_first: datetime
    clamped_last: datetime
    clamped_duration: timedelta
    commit_count: int
    earliest_sha: str
    latest_sha: str


@dataclass(frozen=True, slots=True)
class TimelineRow:
    """
    Represents a row for timeline visualization.
    
    Attributes:
        first: Start timestamp
        last: End timestamp
        elevation: Vertical position in the timeline (stacking level)
        commit_counts: Number of commits in the chain
        head: SHA of the earliest commit
        tail: SHA of the latest commit
        duration: Duration in days
        density: Commit sparsity metric (days per commit)
    """
    first: datetime
    last: datetime
    elevation: int
    commit_counts: int
    head: str
    tail: str
    duration: int
    density: float
