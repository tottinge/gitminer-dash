"""Tests for `algorithms/commit_frequency.py`."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from algorithms.commit_frequency import calculate_file_commit_frequency
from algorithms.file_changes import FileChangeStats
from tests import setup_path

setup_path()


@pytest.fixture
def mock_repo():
    """Create a mock Git repository for testing."""
    repo = MagicMock()
    return repo


@pytest.fixture
def mock_commits_with_files():
    """Create mock commits with various file statistics."""
    commits = []

    # Commit 1: touches file1.py and file2.py
    commit1 = MagicMock()
    commit1.stats.files = {"file1.py": {}, "file2.py": {}}
    commits.append(commit1)

    # Commit 2: touches file1.py and file3.py
    commit2 = MagicMock()
    commit2.stats.files = {"file1.py": {}, "file3.py": {}}
    commits.append(commit2)

    # Commit 3: touches file1.py only
    commit3 = MagicMock()
    commit3.stats.files = {"file1.py": {}}
    commits.append(commit3)

    # Commit 4: touches file2.py only
    commit4 = MagicMock()
    commit4.stats.files = {"file2.py": {}}
    commits.append(commit4)

    # Commit 5: touches file4.py only
    commit5 = MagicMock()
    commit5.stats.files = {"file4.py": {}}
    commits.append(commit5)

    return commits


@pytest.fixture
def mock_file_stats():
    """Create mock file statistics for testing."""
    return {
        "file1.py": FileChangeStats(
            file_path="file1.py",
            commits=3,
            avg_changes=10.5,
            total_change=100,
            percent_change=25.3,
        ),
        "file2.py": FileChangeStats(
            file_path="file2.py",
            commits=2,
            avg_changes=5.2,
            total_change=50,
            percent_change=10.1,
        ),
        "file3.py": FileChangeStats(
            file_path="file3.py",
            commits=1,
            avg_changes=2.0,
            total_change=20,
            percent_change=5.0,
        ),
    }


def test_calculate_file_commit_frequency_basic(
    mock_commits_with_files, mock_repo, mock_file_stats
):
    """Test basic functionality with multiple files and commits."""
    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    with patch(
        "algorithms.file_changes.files_changes_over_period",
        return_value=mock_file_stats,
    ):
        result = calculate_file_commit_frequency(
            mock_commits_with_files, mock_repo, begin, end, top_n=3
        )

    # Should return top 3 files: file1.py (3), file2.py (2), file3.py (1)
    assert len(result) == 3

    # Check file1.py (most commits)
    assert result[0]["filename"] == "file1.py"
    assert result[0]["count"] == 3
    assert result[0]["avg_changes"] == 10.5
    assert result[0]["total_change"] == 100
    assert result[0]["percent_change"] == 25.3

    # Check file2.py
    assert result[1]["filename"] == "file2.py"
    assert result[1]["count"] == 2
    assert result[1]["avg_changes"] == 5.2

    # Check file3.py
    assert result[2]["filename"] == "file3.py"
    assert result[2]["count"] == 1
    assert result[2]["avg_changes"] == 2.0


def test_calculate_file_commit_frequency_respects_top_n(
    mock_commits_with_files, mock_repo, mock_file_stats
):
    """Test that top_n parameter correctly limits results."""
    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    with patch(
        "algorithms.file_changes.files_changes_over_period",
        return_value=mock_file_stats,
    ):
        result = calculate_file_commit_frequency(
            mock_commits_with_files, mock_repo, begin, end, top_n=2
        )

    # Should only return top 2 files
    assert len(result) == 2
    assert result[0]["filename"] == "file1.py"
    assert result[1]["filename"] == "file2.py"


def test_calculate_file_commit_frequency_top_n_one(
    mock_commits_with_files, mock_repo, mock_file_stats
):
    """Test with top_n=1 to get only the most committed file."""
    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    with patch(
        "algorithms.file_changes.files_changes_over_period",
        return_value=mock_file_stats,
    ):
        result = calculate_file_commit_frequency(
            mock_commits_with_files, mock_repo, begin, end, top_n=1
        )

    assert len(result) == 1
    assert result[0]["filename"] == "file1.py"
    assert result[0]["count"] == 3


def test_calculate_file_commit_frequency_top_n_zero(
    mock_commits_with_files, mock_repo, mock_file_stats
):
    """Test with top_n=0 to get empty results."""
    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    with patch(
        "algorithms.file_changes.files_changes_over_period",
        return_value=mock_file_stats,
    ):
        result = calculate_file_commit_frequency(
            mock_commits_with_files, mock_repo, begin, end, top_n=0
        )

    assert len(result) == 0


def test_calculate_file_commit_frequency_empty_commits(mock_repo):
    """Test with no commits."""
    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    with patch(
        "algorithms.file_changes.files_changes_over_period", return_value={}
    ):
        result = calculate_file_commit_frequency(
            [], mock_repo, begin, end, top_n=20
        )

    assert len(result) == 0


def test_calculate_file_commit_frequency_missing_file_stats(
    mock_commits_with_files, mock_repo
):
    """Test when file_stats doesn't include some files."""
    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    # Only provide stats for file1.py, not file2.py or file3.py
    partial_stats = {
        "file1.py": FileChangeStats(
            file_path="file1.py",
            commits=3,
            avg_changes=10.5,
            total_change=100,
            percent_change=25.3,
        ),
    }

    with patch(
        "algorithms.file_changes.files_changes_over_period",
        return_value=partial_stats,
    ):
        result = calculate_file_commit_frequency(
            mock_commits_with_files, mock_repo, begin, end, top_n=5
        )

    # Should still return all files, but missing ones have zero stats
    assert len(result) == 4  # file1, file2, file3, file4

    # file1.py has real stats
    file1_result = next(r for r in result if r["filename"] == "file1.py")
    assert file1_result["count"] == 3
    assert file1_result["avg_changes"] == 10.5

    # file2.py has count from commits but zeros for change stats
    file2_result = next(r for r in result if r["filename"] == "file2.py")
    assert file2_result["count"] == 2
    assert file2_result["avg_changes"] == 0.0
    assert file2_result["total_change"] == 0
    assert file2_result["percent_change"] == 0.0


def test_calculate_file_commit_frequency_rounding(
    mock_commits_with_files, mock_repo
):
    """Test that floating point values are properly rounded."""
    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    file_stats = {
        "file1.py": FileChangeStats(
            file_path="file1.py",
            commits=3,
            avg_changes=10.666666,  # Should round to 10.67
            total_change=100,
            percent_change=25.333333,  # Should round to 25.33
        ),
    }

    with patch(
        "algorithms.file_changes.files_changes_over_period",
        return_value=file_stats,
    ):
        result = calculate_file_commit_frequency(
            mock_commits_with_files, mock_repo, begin, end, top_n=1
        )

    assert result[0]["avg_changes"] == 10.67
    assert result[0]["percent_change"] == 25.33


def test_calculate_file_commit_frequency_calls_files_changes_with_correct_args(
    mock_commits_with_files, mock_repo
):
    """Test that files_changes_over_period is called with correct arguments."""
    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    with patch(
        "algorithms.file_changes.files_changes_over_period", return_value={}
    ) as mock_files_changes:
        calculate_file_commit_frequency(
            mock_commits_with_files, mock_repo, begin, end, top_n=3
        )

    # Check it was called once
    assert mock_files_changes.call_count == 1

    # Check the arguments
    call_args = mock_files_changes.call_args[0]
    filenames, start, end_arg, repo = call_args

    # Should pass top 3 filenames: file1.py, file2.py, file3.py
    assert set(filenames) == {"file1.py", "file2.py", "file3.py"}
    assert start == begin
    assert end_arg == end
    assert repo is mock_repo


def test_calculate_file_commit_frequency_value_error_propagates(mock_repo):
    """Test that ValueError from commit processing is propagated."""
    # Create a commit that raises ValueError when accessing stats.files
    bad_commit = MagicMock()
    bad_commit.stats.files.keys.side_effect = ValueError("Bad commit")

    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    with pytest.raises(ValueError, match="Bad commit"):
        calculate_file_commit_frequency(
            [bad_commit], mock_repo, begin, end, top_n=20
        )


def test_calculate_file_commit_frequency_preserves_commit_order(
    mock_commits_with_files, mock_repo, mock_file_stats
):
    """Test that files are ordered by commit count (descending)."""
    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    with patch(
        "algorithms.file_changes.files_changes_over_period",
        return_value=mock_file_stats,
    ):
        result = calculate_file_commit_frequency(
            mock_commits_with_files, mock_repo, begin, end, top_n=10
        )

    # Should be ordered: file1.py (3), file2.py (2), file3.py (1), file4.py (1)
    counts = [r["count"] for r in result]
    assert counts == sorted(counts, reverse=True)


def test_calculate_file_commit_frequency_single_commit_single_file(mock_repo):
    """Test with a single commit touching a single file."""
    commit = MagicMock()
    commit.stats.files = {"only_file.py": {}}

    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    file_stats = {
        "only_file.py": FileChangeStats(
            file_path="only_file.py",
            commits=1,
            avg_changes=5.0,
            total_change=10,
            percent_change=2.0,
        ),
    }

    with patch(
        "algorithms.file_changes.files_changes_over_period",
        return_value=file_stats,
    ):
        result = calculate_file_commit_frequency(
            [commit], mock_repo, begin, end, top_n=20
        )

    assert len(result) == 1
    assert result[0]["filename"] == "only_file.py"
    assert result[0]["count"] == 1


def test_calculate_file_commit_frequency_top_n_exceeds_file_count(
    mock_commits_with_files, mock_repo, mock_file_stats
):
    """Test when top_n is larger than the number of files."""
    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    with patch(
        "algorithms.file_changes.files_changes_over_period",
        return_value=mock_file_stats,
    ):
        result = calculate_file_commit_frequency(
            mock_commits_with_files, mock_repo, begin, end, top_n=100
        )

    # Should return all 4 files, not 100
    assert len(result) == 4


def test_calculate_file_commit_frequency_default_top_n(
    mock_commits_with_files, mock_repo, mock_file_stats
):
    """Test that default top_n is 20."""
    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    with patch(
        "algorithms.file_changes.files_changes_over_period",
        return_value=mock_file_stats,
    ):
        # Call without top_n argument
        result = calculate_file_commit_frequency(
            mock_commits_with_files, mock_repo, begin, end
        )

    # Should still work (default is 20, but we only have 4 files)
    assert len(result) == 4


def test_calculate_file_commit_frequency_with_large_dataset(mock_repo):
    """Test with a large number of files to ensure top_n works correctly."""
    # Create 50 commits, each touching a unique file
    commits = []
    for i in range(50):
        commit = MagicMock()
        commit.stats.files = {f"file{i}.py": {}}
        commits.append(commit)

    # Add extra commits to some files to create a frequency distribution
    # file0.py gets 10 extra commits (11 total)
    for _ in range(10):
        commit = MagicMock()
        commit.stats.files = {"file0.py": {}}
        commits.append(commit)

    # file1.py gets 5 extra commits (6 total)
    for _ in range(5):
        commit = MagicMock()
        commit.stats.files = {"file1.py": {}}
        commits.append(commit)

    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    with patch(
        "algorithms.file_changes.files_changes_over_period", return_value={}
    ):
        result = calculate_file_commit_frequency(
            commits, mock_repo, begin, end, top_n=5
        )

    # Should return exactly 5 files
    assert len(result) == 5

    # Top file should be file0.py with 11 commits
    assert result[0]["filename"] == "file0.py"
    assert result[0]["count"] == 11

    # Second should be file1.py with 6 commits
    assert result[1]["filename"] == "file1.py"
    assert result[1]["count"] == 6


def test_calculate_file_commit_frequency_zero_stats(
    mock_commits_with_files, mock_repo
):
    """Test handling of files with zero change statistics."""
    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    file_stats = {
        "file1.py": FileChangeStats(
            file_path="file1.py",
            commits=0,
            avg_changes=0.0,
            total_change=0,
            percent_change=0.0,
        ),
    }

    with patch(
        "algorithms.file_changes.files_changes_over_period",
        return_value=file_stats,
    ):
        result = calculate_file_commit_frequency(
            mock_commits_with_files, mock_repo, begin, end, top_n=1
        )

    # Should still return the file with its zero stats
    assert len(result) == 1
    assert result[0]["filename"] == "file1.py"
    assert result[0]["count"] == 3  # From commit count
    assert result[0]["avg_changes"] == 0.0  # From file stats
    assert result[0]["total_change"] == 0
    assert result[0]["percent_change"] == 0.0


def test_calculate_file_commit_frequency_negative_percent_change(
    mock_commits_with_files, mock_repo
):
    """Test handling of negative percent changes (file shrinkage)."""
    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    file_stats = {
        "file1.py": FileChangeStats(
            file_path="file1.py",
            commits=3,
            avg_changes=10.5,
            total_change=100,
            percent_change=-25.75,  # File shrank
        ),
    }

    with patch(
        "algorithms.file_changes.files_changes_over_period",
        return_value=file_stats,
    ):
        result = calculate_file_commit_frequency(
            mock_commits_with_files, mock_repo, begin, end, top_n=1
        )

    assert result[0]["percent_change"] == -25.75


def test_calculate_file_commit_frequency_commit_with_no_files(mock_repo):
    """Test handling of commits that touch no files (edge case)."""
    commit = MagicMock()
    commit.stats.files = {}  # No files touched

    begin = datetime.now() - timedelta(days=30)
    end = datetime.now()

    with patch(
        "algorithms.file_changes.files_changes_over_period", return_value={}
    ):
        result = calculate_file_commit_frequency(
            [commit], mock_repo, begin, end, top_n=20
        )

    assert len(result) == 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
