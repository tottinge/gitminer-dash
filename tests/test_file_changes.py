"""Tests for `algorithms/file_changes.py`."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from algorithms.file_changes import (
    FileChangeStats,
    file_changes_over_period,
    files_changes_over_period,
)
from tests import setup_path

setup_path()


_SHAS = ["sha1", "sha2", "sha3", "sha4", "sha5"]
_SHA_LIST_OUTPUT = "\n".join(_SHAS) + "\n"

_REV_LIST_OUTPUT_BY_FILE = {
    "nonexistent.py": "",
    "file1.py": _SHA_LIST_OUTPUT,
    "file2.py": _SHA_LIST_OUTPUT,
    "file3.py": _SHA_LIST_OUTPUT,
}

_SHOW_NUMSTAT_BY_FILE = {
    "file1.py": "5\t5\tfile1.py\n",  # 10 lines changed
    "file2.py": "10\t10\tfile2.py\n",  # 20 lines changed
    "file3.py": "15\t15\tfile3.py\n",  # 30 lines changed
}

_CAT_FILE_SIZE_BY_SHA = {
    "sha5": "1000",
    "sha1": "1200",
}


def _rev_list_side_effect(*args: str) -> str:
    # args ends with: "--", <target_file>
    target_file = args[-1]
    if target_file == "error.py":
        raise ValueError("File not found")
    return _REV_LIST_OUTPUT_BY_FILE.get(target_file, _SHA_LIST_OUTPUT)


def _show_side_effect(_sha: str, *args: str) -> str:
    target_file = args[-1]
    return _SHOW_NUMSTAT_BY_FILE.get(target_file, "")


def _cat_file_side_effect(_flag: str, spec: str) -> str:
    # spec is: "<sha>:<path>"
    sha, _path = spec.split(":", 1)
    return _CAT_FILE_SIZE_BY_SHA.get(sha, "1100")


@pytest.fixture
def mock_repo():
    """Create a mock Git repository for testing."""
    repo = MagicMock()
    repo.git = MagicMock()
    repo.git.rev_list.side_effect = _rev_list_side_effect
    repo.git.show.side_effect = _show_side_effect
    repo.git.cat_file.side_effect = _cat_file_side_effect
    return repo


def test_file_changes_over_period(mock_repo):
    (commits, avg_changes, total_change, percent_change) = file_changes_over_period(
        "file1.py",
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
        repo=mock_repo,
    )

    assert commits == 5
    assert avg_changes == 10.0
    assert total_change == 200
    assert percent_change == 20.0

    # Primary contract: we query git for commits and per-commit stats.
    assert mock_repo.git.rev_list.called
    assert mock_repo.git.show.called
    assert mock_repo.git.cat_file.called


def test_file_changes_over_period_no_commits(mock_repo):
    (commits, avg_changes, total_change, percent_change) = file_changes_over_period(
        "nonexistent.py",
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
        repo=mock_repo,
    )

    assert commits == 0
    assert avg_changes == 0.0
    assert total_change == 0
    assert percent_change == 0.0


def test_files_changes_over_period(mock_repo):
    """Test the files_changes_over_period function with a mock repository."""
    results = files_changes_over_period(
        ["file1.py", "file2.py", "file3.py"],
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
        repo=mock_repo,
    )
    assert len(results) == 3
    assert isinstance(results["file1.py"], FileChangeStats)
    assert results["file1.py"].commits == 5
    assert results["file1.py"].avg_changes == 10.0
    assert results["file1.py"].total_change == 200
    assert results["file1.py"].percent_change == 20.0
    assert results["file2.py"].avg_changes == 20.0
    assert results["file3.py"].avg_changes == 30.0


def test_files_changes_over_period_with_error(mock_repo):
    results = files_changes_over_period(
        ["file1.py", "error.py", "file3.py"],
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
        repo=mock_repo,
    )

    assert len(results) == 3
    assert results["file1.py"].commits == 5
    assert results["error.py"].commits == 0
    assert results["file3.py"].commits == 5


def test_files_changes_over_period_empty_list(mock_repo):
    """Test the files_changes_over_period function with an empty list of files."""
    results = files_changes_over_period(
        [],
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
        repo=mock_repo,
    )
    assert len(results) == 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
