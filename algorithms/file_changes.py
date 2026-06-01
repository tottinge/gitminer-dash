import logging
from datetime import datetime, timedelta
from statistics import mean
from typing import NamedTuple

import git

from utils.git import get_repo as get_repo_util

DEFAULT_LOOKBACK_DAYS = 365


class FileChangeStats(NamedTuple):
    """Statistics about changes to a file over a period of time."""

    file_path: str
    commits: int
    avg_changes: float
    total_change: int
    percent_change: float


def _resolve_period_bounds(
    start: datetime | None, end: datetime | None
) -> tuple[datetime, datetime]:
    if start is not None and end is not None:
        return start, end

    now = datetime.now()
    period_start = (
        start
        if start is not None
        else now - timedelta(days=DEFAULT_LOOKBACK_DAYS)
    )
    period_end = end if end is not None else now
    return period_start, period_end


def _build_file_change_stats(
    file_path: str,
    commits: int,
    avg_changes: float,
    total_change: int,
    percent_change: float,
) -> FileChangeStats:
    return FileChangeStats(
        file_path=file_path,
        commits=commits,
        avg_changes=avg_changes,
        total_change=total_change,
        percent_change=percent_change,
    )


def zero_file_change_stats(file_path: str) -> FileChangeStats:
    """Return a zeroed file-change record for the requested file path."""
    return _build_file_change_stats(
        file_path=file_path,
        commits=0,
        avg_changes=0.0,
        total_change=0,
        percent_change=0.0,
    )


def _as_legacy_tuple(stats: FileChangeStats) -> tuple[int, float, int, float]:
    """Return tuple shape used by legacy callers of file_changes_over_period."""
    return (
        stats.commits,
        stats.avg_changes,
        stats.total_change,
        stats.percent_change,
    )


def _dt_arg(dt: datetime) -> str:
    # Keep formatting stable across naive/aware datetimes.
    return dt.astimezone().replace(microsecond=0).isoformat(sep=" ")


def _commits_touching_file(
    repo: git.Repo,
    target_file: str,
    start: datetime,
    end: datetime,
) -> list[str]:
    """Return commit SHAs that touch target_file in [start, end].

    Uses the git CLI directly rather than Commit.stats to avoid GitPython's
    batch object reader desync issues.
    """
    output = repo.git.rev_list(
        "--all",
        f"--since={_dt_arg(start)}",
        f"--until={_dt_arg(end)}",
        "--",
        target_file,
    )

    shas = [line.strip() for line in output.splitlines() if line.strip()]
    return shas


def _lines_changed_in_commit(repo: git.Repo, sha: str, target_file: str) -> int:
    """Return total lines changed (adds + dels) for target_file in commit sha."""
    # `--format=` suppresses commit headers; `--numstat` gives per-file counts.
    output = repo.git.show(sha, "--numstat", "--format=", "--", target_file)
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        adds_s, dels_s, _path = parts[0], parts[1], parts[2]
        adds = int(adds_s) if adds_s.isdigit() else 0
        dels = int(dels_s) if dels_s.isdigit() else 0
        return adds + dels
    return 0


def _blob_size_at_commit(repo: git.Repo, sha: str, target_file: str) -> int:
    """Return blob size (in bytes) for target_file at commit sha."""
    try:
        return int(repo.git.cat_file("-s", f"{sha}:{target_file}").strip())
    except Exception:
        return 0


def _calculate_percent_change(original_size: int, final_size: int) -> float:
    if original_size <= 0:
        return 0.0
    return (final_size - original_size) / original_size * 100


def _summarize_file_change_stats(
    repo: git.Repo, target_file: str, shas: list[str]
) -> FileChangeStats:
    if not shas:
        return zero_file_change_stats(target_file)

    lines_changed = [
        _lines_changed_in_commit(repo, sha, target_file) for sha in shas
    ]
    commits = len(shas)
    avg_changes = mean(lines_changed)

    newest_sha = shas[0]
    oldest_sha = shas[-1]
    original_size = _blob_size_at_commit(repo, oldest_sha, target_file)
    final_size = (
        _blob_size_at_commit(repo, newest_sha, target_file) or original_size
    )

    total_change = abs(final_size - original_size)
    percent_change = _calculate_percent_change(original_size, final_size)
    return _build_file_change_stats(
        file_path=target_file,
        commits=commits,
        avg_changes=avg_changes,
        total_change=total_change,
        percent_change=percent_change,
    )


def file_changes_over_period(
    target_file: str,
    start: datetime | None = None,
    end: datetime | None = None,
    repo: git.Repo | None = None,
) -> tuple[int, float, int, float]:
    """Calculate statistics about changes to a file over a period of time."""
    start, end = _resolve_period_bounds(start, end)
    repo = repo or get_repo_util()
    shas = list(_commits_touching_file(repo, target_file, start, end))
    stats = _summarize_file_change_stats(
        repo=repo, target_file=target_file, shas=shas
    )
    return _as_legacy_tuple(stats)


def files_changes_over_period(
    target_files: list[str],
    start: datetime | None = None,
    end: datetime | None = None,
    repo: git.Repo | None = None,
) -> dict[str, FileChangeStats]:
    """
    Calculate statistics about changes to multiple files over a period of time.

    Args:
        target_files: List of file paths to analyze
        start: Start date for the analysis (default: 1 year ago)
        end: End date for the analysis (default: now)
        repo: Git repository object (default: repository in current directory)

    Returns:
        A dictionary mapping file paths to FileChangeStats objects
    """
    start, end = _resolve_period_bounds(start, end)
    repo = repo or get_repo_util()
    results: dict[str, FileChangeStats] = {}

    for file_path in target_files:
        try:
            change_summary = file_changes_over_period(
                file_path, start, end, repo
            )
            stats = _build_file_change_stats(
                file_path=file_path,
                commits=change_summary[0],
                avg_changes=change_summary[1],
                total_change=change_summary[2],
                percent_change=change_summary[3],
            )

            results[file_path] = stats

        except Exception:
            logging.getLogger(__name__).exception(
                f"Error processing file {file_path}"
            )
            results[file_path] = zero_file_change_stats(file_path)

    return results
