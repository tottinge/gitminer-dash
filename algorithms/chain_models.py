"""
Data models for commit chain analysis.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
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
