"""Build normalized analysis snapshots from repository commits."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from git import Repo

from algorithms.commit_frequency import count_file_commits
from data import commits_in_period_for_repo_path
from insights.models import AnalysisSnapshot
from insights.schema_version import ANALYSIS_SCHEMA_VERSION


def get_commits_for_period(
    repo: Repo, period_start: datetime, period_end: datetime
) -> list:
    """Load commits from all refs in a date range."""
    repo_path = repo.working_tree_dir or repo.git_dir
    return list(
        commits_in_period_for_repo_path(
            repo_path=repo_path, beginning=period_start, ending=period_end
        )
    )


def build_analysis_snapshot(
    repo: Repo,
    period_start: datetime,
    period_end: datetime,
    max_evidence_commits_per_file: int = 5,
) -> AnalysisSnapshot:
    """Create a deterministic analysis snapshot from commit history."""
    commits = get_commits_for_period(
        repo=repo, period_start=period_start, period_end=period_end
    )
    ordered_commits = sorted(
        commits, key=lambda commit: (commit.committed_datetime, commit.hexsha)
    )

    file_commit_counts = count_file_commits(ordered_commits)
    file_recent_commits: defaultdict[str, list[str]] = defaultdict(list)

    for commit in ordered_commits:
        commit_sha = commit.hexsha[:7]
        for file_path in sorted(commit.stats.files):
            file_shas = file_recent_commits[file_path]
            if commit_sha not in file_shas and (
                len(file_shas) < max_evidence_commits_per_file
            ):
                file_shas.append(commit_sha)

    return AnalysisSnapshot(
        schema_version=ANALYSIS_SCHEMA_VERSION,
        repo_path=repo.working_tree_dir or "",
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        total_commits=len(ordered_commits),
        file_commit_counts={
            file_path: file_commit_counts[file_path]
            for file_path in sorted(file_commit_counts)
        },
        file_recent_commits={
            file_path: file_recent_commits[file_path]
            for file_path in sorted(file_recent_commits)
        },
    )
