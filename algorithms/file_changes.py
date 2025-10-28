from typing import List, NamedTuple, Optional, Dict, Tuple
from datetime import datetime, timedelta
from statistics import mean
import git
from git import Repo


class FileChangeStats(NamedTuple):
    """
    Statistics about changes to a file over a period of time.
    
    Attributes:
        file_path: Path to the file
        commits: Number of commits that modified the file
        avg_changes: Average number of lines changed per commit
        total_change: Absolute difference between original and final file size
        percent_change: Percentage change in file size
    """
    file_path: str
    commits: int
    avg_changes: float
    total_change: int
    percent_change: float


def file_changes_over_period(
    target_file: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    repo: Optional[git.Repo] = None
) -> Tuple[int, float, int, float]:
    """
    Calculate statistics about changes to a file over a period of time.
    
    Args:
        target_file: Path to the file to analyze
        start: Start date for the analysis (default: 1 year ago)
        end: End date for the analysis (default: now)
        repo: Git repository object (default: repository in current directory)
        
    Returns:
        A tuple of (commits, avg_changes, total_change, percent_change)
    """
    start = start or datetime.now() - timedelta(days=365)
    end = end or datetime.now()
    repo = repo or Repo('.')
    
    total_commits = list(repo.iter_commits(paths=target_file, since=start, until=end))
    
    if not total_commits:
        return 0, 0.0, 0, 0.0
    
    commits = len(total_commits)
    avg_changes = mean(commit.stats.files[target_file]['lines'] for commit in total_commits)
    
    original_size = repo.commit(total_commits[0]).tree[target_file].size
    final_size = repo.commit(total_commits[-1]).tree[target_file].size
    total_change = abs(final_size - original_size)
    
    percent_change = (final_size - original_size) / original_size * 100 if original_size > 0 else 0.0
    
    return commits, avg_changes, total_change, percent_change


def files_changes_over_period(
    target_files: List[str],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    repo: Optional[git.Repo] = None
) -> Dict[str, FileChangeStats]:
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
    start = start or datetime.now() - timedelta(days=365)
    end = end or datetime.now()
    repo = repo or Repo('.')
    
    results = {}
    
    for file_path in target_files:
        try:
            commits, avg_changes, total_change, percent_change = file_changes_over_period(
                file_path, start, end, repo
            )
            
            stats = FileChangeStats(
                file_path=file_path,
                commits=commits,
                avg_changes=avg_changes,
                total_change=total_change,
                percent_change=percent_change
            )
            
            results[file_path] = stats
            
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            results[file_path] = FileChangeStats(
                file_path=file_path,
                commits=0,
                avg_changes=0.0,
                total_change=0,
                percent_change=0.0
            )
    
    return results