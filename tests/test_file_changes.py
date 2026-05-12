"""Tests for `algorithms/file_changes.py`."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from algorithms.file_changes import (
    FileChangeStats,
    _blob_size_at_commit,
    _commits_touching_file,
    _dt_arg,
    _lines_changed_in_commit,
    file_changes_over_period,
    files_changes_over_period,
)
from tests import setup_path

setup_path()


_COMMIT_SHAS = ["sha1", "sha2", "sha3", "sha4", "sha5"]
_COMMIT_SHA_LIST_OUTPUT = "\n".join(_COMMIT_SHAS) + "\n"

_REV_LIST_OUTPUT_BY_FILE_PATH = {
    "nonexistent.py": "",
    "file1.py": _COMMIT_SHA_LIST_OUTPUT,
    "file2.py": _COMMIT_SHA_LIST_OUTPUT,
    "file3.py": _COMMIT_SHA_LIST_OUTPUT,
}

_NUMSTAT_OUTPUT_BY_FILE_PATH = {
    "file1.py": "5\t5\tfile1.py\n",  # 10 lines changed
    "file2.py": "10\t10\tfile2.py\n",  # 20 lines changed
    "file3.py": "15\t15\tfile3.py\n",  # 30 lines changed
}
_BLOB_SIZE_BY_COMMIT_SHA = {
    "sha5": "1000",
    "sha1": "1200",
}


def _rev_list_side_effect(*args: str) -> str:
    # args ends with: "--", <target_file>
    target_file = args[-1]
    if target_file == "error.py":
        raise ValueError("File not found")
    return _REV_LIST_OUTPUT_BY_FILE_PATH.get(
        target_file, _COMMIT_SHA_LIST_OUTPUT
    )


def _show_side_effect(_sha: str, *args: str) -> str:
    target_file = args[-1]
    return _NUMSTAT_OUTPUT_BY_FILE_PATH.get(target_file, "")


def _cat_file_side_effect(_flag: str, spec: str) -> str:
    # spec is: "<sha>:<path>"
    sha, _path = spec.split(":", 1)
    return _BLOB_SIZE_BY_COMMIT_SHA.get(sha, "1100")


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
    (commits, avg_changes, total_change, percent_change) = (
        file_changes_over_period(
            "file1.py",
            start=datetime.now() - timedelta(days=30),
            end=datetime.now(),
            repo=mock_repo,
        )
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
    (commits, avg_changes, total_change, percent_change) = (
        file_changes_over_period(
            "nonexistent.py",
            start=datetime.now() - timedelta(days=30),
            end=datetime.now(),
            repo=mock_repo,
        )
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
    assert results["file1.py"].file_path == "file1.py"
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


def test_file_changes_over_period_uses_default_window_when_start_end_none(
    monkeypatch, mock_repo
):
    """When start/end are None, use a 1-year window ending at now()."""
    fixed_now = datetime(2025, 1, 1, 12, 0, 0)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            return fixed_now if tz is None else fixed_now.astimezone(tz)

    # Patch datetime used in the module under test
    monkeypatch.setattr("algorithms.file_changes.datetime", FixedDateTime)

    with patch(
        "algorithms.file_changes._commits_touching_file"
    ) as mock_commits:
        file_changes_over_period("file1.py", repo=mock_repo)

    assert mock_commits.call_count == 1
    _repo, _target_file, start, end = mock_commits.call_args[0]
    assert start == fixed_now - timedelta(days=365)
    assert end == fixed_now


def test_file_changes_over_period_passes_each_sha_to_lines_changed(mock_repo):
    """Each SHA returned by _commits_touching_file must be passed to the helper."""
    with (
        patch(
            "algorithms.file_changes._commits_touching_file",
            return_value=_COMMIT_SHAS,
        ),
        patch("algorithms.file_changes._lines_changed_in_commit") as mock_lines,
    ):
        mock_lines.return_value = 10
        file_changes_over_period("file1.py", repo=mock_repo)

    called_shas = [call.args[1] for call in mock_lines.call_args_list]
    assert called_shas == _COMMIT_SHAS


def test_file_changes_over_period_passes_correct_args_to_blob_size(mock_repo):
    """_blob_size_at_commit must be called with (repo, sha, target_file)."""
    with (
        patch(
            "algorithms.file_changes._commits_touching_file",
            return_value=_COMMIT_SHAS,
        ),
        patch("algorithms.file_changes._blob_size_at_commit") as mock_blob,
    ):
        mock_blob.return_value = 1000
        file_changes_over_period("file1.py", repo=mock_repo)

    calls = mock_blob.call_args_list
    assert len(calls) == 2

    (repo1, oldest_sha, path1), _ = calls[0]
    (repo2, newest_sha, path2), _ = calls[1]

    assert repo1 is mock_repo
    assert repo2 is mock_repo
    assert (oldest_sha, newest_sha) == (
        _COMMIT_SHAS[-1],
        _COMMIT_SHAS[0],
    )
    assert path1 == path2 == "file1.py"


def test_dt_arg_normalizes_microseconds_and_separator():
    dt = datetime(2026, 5, 1, 12, 34, 56, 987654, tzinfo=timezone.utc)

    result = _dt_arg(dt)

    assert "T" not in result
    assert "." not in result
    assert ".000001" not in result


def test_commits_touching_file_calls_rev_list_with_expected_flags(mock_repo):
    start = datetime(2026, 5, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 5, 31, 23, 59, 59, tzinfo=timezone.utc)
    mock_repo.git.rev_list.side_effect = None
    mock_repo.git.rev_list.return_value = "sha1\n"

    shas = _commits_touching_file(mock_repo, "src/file.py", start, end)

    assert shas == ["sha1"]
    mock_repo.git.rev_list.assert_called_once_with(
        "--all",
        f"--since={_dt_arg(start)}",
        f"--until={_dt_arg(end)}",
        "--",
        "src/file.py",
    )


def test_commits_touching_file_trims_whitespace_and_ignores_blank_lines(
    mock_repo,
):
    start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    end = datetime(2026, 5, 2, tzinfo=timezone.utc)
    mock_repo.git.rev_list.side_effect = None
    mock_repo.git.rev_list.return_value = " sha1 \n\n\tsha2\t\n"

    shas = _commits_touching_file(mock_repo, "src/file.py", start, end)

    assert shas == ["sha1", "sha2"]


def test_blob_size_at_commit_calls_cat_file_with_expected_spec(mock_repo):
    mock_repo.git.cat_file.side_effect = None
    mock_repo.git.cat_file.return_value = "123\n"

    size = _blob_size_at_commit(mock_repo, "abc123", "src/file.py")

    assert size == 123
    mock_repo.git.cat_file.assert_called_once_with("-s", "abc123:src/file.py")


def test_blob_size_at_commit_returns_zero_when_cat_file_fails(mock_repo):
    mock_repo.git.cat_file.side_effect = RuntimeError("missing blob")

    size = _blob_size_at_commit(mock_repo, "abc123", "src/file.py")

    assert size == 0


def test_file_changes_over_period_no_lines_changed_keeps_avg_at_zero(mock_repo):
    """If numstat output is empty, avg_changes should be 0.0, not 1.0."""

    def no_changes_show_side_effect(_sha: str, *args: str) -> str:
        return ""  # no numstat lines at all

    mock_repo.git.show.side_effect = no_changes_show_side_effect

    commits, avg_changes, total_change, percent_change = (
        file_changes_over_period(
            "file1.py",
            start=datetime.now() - timedelta(days=30),
            end=datetime.now(),
            repo=mock_repo,
        )
    )

    assert commits == len(_COMMIT_SHAS)
    assert avg_changes == 0.0


def test_file_changes_over_period_zero_original_size_has_zero_percent_change(
    mock_repo,
):
    """When original size is 0, percent_change must be 0.0 (no division)."""

    def zero_size_cat_file(_flag: str, spec: str) -> str:
        sha, _ = spec.split(":", 1)
        if sha == _COMMIT_SHAS[-1]:  # oldest
            return "0"
        return "100"

    mock_repo.git.cat_file.side_effect = zero_size_cat_file

    _, _, _, percent_change = file_changes_over_period(
        "file1.py",
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
        repo=mock_repo,
    )

    assert percent_change == 0.0


def test_file_changes_over_period_small_original_size_computes_percent(
    mock_repo,
):
    """When original size is 1, percent_change should still be computed."""

    def tiny_sizes_cat_file(_flag: str, spec: str) -> str:
        sha, _ = spec.split(":", 1)
        if sha == _COMMIT_SHAS[-1]:  # oldest
            return "1"
        if sha == _COMMIT_SHAS[0]:  # newest
            return "2"
        return "1"

    mock_repo.git.cat_file.side_effect = tiny_sizes_cat_file

    _, _, _, percent_change = file_changes_over_period(
        "file1.py",
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
        repo=mock_repo,
    )

    assert percent_change == 100.0


def test_lines_changed_in_commit_calls_git_show_with_expected_flags(
    mock_repo,
):
    """Helper should invoke git show with stable numstat formatting flags."""
    mock_repo.git.show.side_effect = None
    mock_repo.git.show.return_value = "5\t7\tfile1.py\n"

    total = _lines_changed_in_commit(mock_repo, "abc123", "file1.py")

    assert total == 12
    mock_repo.git.show.assert_called_once_with(
        "abc123",
        "--numstat",
        "--format=",
        "--",
        "file1.py",
    )


def test_lines_changed_in_commit_skips_malformed_prefix_line(mock_repo):
    """Malformed lines must be skipped so a later valid numstat line is used."""
    mock_repo.git.show.side_effect = None
    mock_repo.git.show.return_value = "not-a-numstat-line\n2\t3\tfile1.py\n"

    total = _lines_changed_in_commit(mock_repo, "abc123", "file1.py")

    assert total == 5


def test_lines_changed_in_commit_non_digit_adds_defaults_to_zero(mock_repo):
    """Non-digit adds should be treated as zero, not one."""
    mock_repo.git.show.side_effect = None
    mock_repo.git.show.return_value = "-\t3\tfile1.py\n"

    total = _lines_changed_in_commit(mock_repo, "abc123", "file1.py")

    assert total == 3


def test_lines_changed_in_commit_non_digit_dels_defaults_to_zero(mock_repo):
    """Non-digit deletes should be treated as zero, not one."""
    mock_repo.git.show.side_effect = None
    mock_repo.git.show.return_value = "3\t-\tfile1.py\n"

    total = _lines_changed_in_commit(mock_repo, "abc123", "file1.py")

    assert total == 3


def test_lines_changed_in_commit_ignores_space_delimited_numstat(mock_repo):
    """Only tab-delimited numstat rows should be parsed as valid counts."""
    mock_repo.git.show.side_effect = None
    mock_repo.git.show.return_value = "3 4 file1.py\n"

    total = _lines_changed_in_commit(mock_repo, "abc123", "file1.py")

    assert total == 0


def test_files_changes_over_period_uses_default_window_when_start_end_none(
    monkeypatch, mock_repo
):
    """Plural helper should default to a 1-year window ending at now()."""
    fixed_now = datetime(2025, 2, 1, 8, 30, 0)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            return fixed_now if tz is None else fixed_now.astimezone(tz)

    monkeypatch.setattr("algorithms.file_changes.datetime", FixedDateTime)

    with patch(
        "algorithms.file_changes.file_changes_over_period",
        return_value=(1, 2.0, 3, 4.0),
    ) as mock_single:
        files_changes_over_period(["file1.py"], repo=mock_repo)

    assert mock_single.call_count == 1
    file_path, start, end, repo = mock_single.call_args[0]
    assert file_path == "file1.py"
    assert start == fixed_now - timedelta(days=365)
    assert end == fixed_now
    assert repo is mock_repo


def test_files_changes_over_period_forwards_explicit_start_end(
    mock_repo,
):
    """Explicit start/end should be forwarded unchanged to per-file helper."""
    explicit_start = datetime(2024, 1, 1, 0, 0, 0)
    explicit_end = datetime(2024, 1, 31, 0, 0, 0)

    with patch(
        "algorithms.file_changes.file_changes_over_period",
        return_value=(1, 2.0, 3, 4.0),
    ) as mock_single:
        files_changes_over_period(
            ["file1.py"],
            start=explicit_start,
            end=explicit_end,
            repo=mock_repo,
        )

    assert mock_single.call_count == 1
    assert mock_single.call_args[0] == (
        "file1.py",
        explicit_start,
        explicit_end,
        mock_repo,
    )


def test_files_changes_over_period_error_path_uses_exact_default_stats(
    mock_repo,
):
    """Error fallback row should keep all zero/default values exactly."""
    with patch(
        "algorithms.file_changes.file_changes_over_period",
        side_effect=ValueError("boom"),
    ):
        results = files_changes_over_period(
            ["broken.py"],
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 2),
            repo=mock_repo,
        )

    stats = results["broken.py"]
    assert stats.file_path == "broken.py"
    assert stats.commits == 0
    assert stats.avg_changes == 0.0
    assert stats.total_change == 0
    assert stats.percent_change == 0.0


def test_files_changes_over_period_logs_error_with_module_logger(mock_repo):
    """Error path should log with this module logger and a stable message."""
    logger = MagicMock()
    with (
        patch("algorithms.file_changes.logging.getLogger") as mock_get_logger,
        patch(
            "algorithms.file_changes.file_changes_over_period",
            side_effect=ValueError("boom"),
        ),
    ):
        mock_get_logger.return_value = logger
        files_changes_over_period(
            ["broken.py"],
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 2),
            repo=mock_repo,
        )

    mock_get_logger.assert_called_once_with("algorithms.file_changes")
    logger.exception.assert_called_once_with("Error processing file broken.py")


if __name__ == "__main__":
    pytest.main(["-v", __file__])
