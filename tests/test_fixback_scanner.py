"""Tests for `insights/fixback_scanner.py`."""

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from insights.fixback_scanner import (
    _hunk_fingerprints_from_patch,
    _period_from_months,
    build_fixback_scan_report,
    main,
)


def _commit(
    sha: str,
    when: datetime,
    message: str,
    files: list[str],
    parent_count: int = 1,
    patches: dict[str, str] | None = None,
):
    def _diff(_other: object, create_patch: bool = False):
        if not create_patch or not patches:
            return []
        return [
            SimpleNamespace(
                a_path=file_path,
                b_path=file_path,
                change_type=None,
                diff=patch_text.encode("utf-8"),
            )
            for file_path, patch_text in sorted(patches.items())
        ]

    return SimpleNamespace(
        hexsha=sha,
        committed_datetime=when,
        message=message,
        parents=[object()] * parent_count,
        stats=SimpleNamespace(files={file_path: {} for file_path in files}),
        diff=_diff,
    )


def test_period_from_months_uses_calendar_months():
    now = datetime(2026, 4, 21, 12, 0, tzinfo=timezone.utc)
    start, end = _period_from_months(6, now=now)
    assert end == now
    assert start == datetime(2025, 10, 21, 12, 0, tzinfo=timezone.utc)


def test_hunk_fingerprints_ignore_hunk_header_line_numbers():
    first_patch = """@@ -10,2 +10,2 @@
-    value = 1
+    value = 2
"""
    second_patch = """@@ -210,2 +410,2 @@
-    value = 1
+    value = 2
"""
    assert _hunk_fingerprints_from_patch(
        first_patch
    ) == _hunk_fingerprints_from_patch(second_patch)


def test_build_fixback_scan_report_detects_short_term_fixback_sequence():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    commits = [
        _commit(
            "ccccccc3", base.replace(day=31), "chore: tidy a", ["src/a.py"]
        ),
        _commit(
            "aaaaaaa1",
            base,
            "feat: add a",
            ["src/a.py", "src/shared.py"],
        ),
        _commit("bbbbbbb2", base.replace(day=3), "fix: a bug", ["src/a.py"]),
    ]
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with patch(
        "insights.fixback_scanner.get_commits_for_period",
        return_value=commits,
    ):
        report = build_fixback_scan_report(
            repo=mock_repo,
            period_start=base.replace(month=1, day=1),
            period_end=base.replace(month=2, day=1),
            months=6,
            revisit_days=14,
            top_n=10,
        )

    assert report["summary"]["revisit_events"] == 1
    assert report["summary"]["fixback_events"] == 1
    assert report["file_candidates"][0]["file_path"] == "src/a.py"
    assert report["file_candidates"][0]["pattern_commits"] == [
        "aaaaaaa",
        "bbbbbbb",
    ]
    assert report["episodes"][0]["followup_fixlike"] is True


def test_build_fixback_scan_report_includes_hunk_fingerprint_overlap():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    shared_patch = """@@ -5,2 +5,2 @@
-value = 1
+value = 2
"""
    commits = [
        _commit(
            "aaaaaaa1",
            base,
            "feat: add a",
            ["src/a.py"],
            patches={"src/a.py": shared_patch},
        ),
        _commit(
            "bbbbbbb2",
            base.replace(day=2),
            "fix: adjust a",
            ["src/a.py"],
            patches={"src/a.py": shared_patch},
        ),
    ]
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with patch(
        "insights.fixback_scanner.get_commits_for_period",
        return_value=commits,
    ):
        report = build_fixback_scan_report(
            repo=mock_repo,
            period_start=base.replace(month=1, day=1),
            period_end=base.replace(month=2, day=1),
            months=6,
            revisit_days=14,
            top_n=10,
        )

    episode = report["episodes"][0]
    assert episode["shared_hunk_count"] == 1
    assert (
        episode["shared_hunk_fingerprints"]
        == episode["anchor_hunk_fingerprints"]
        == episode["followup_hunk_fingerprints"]
    )


def test_build_fixback_scan_report_ranks_fixback_above_plain_revisit():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    commits = [
        _commit("aaaaaaa1", base, "feat: add a", ["src/a.py"]),
        _commit("bbbbbbb2", base.replace(day=2), "fix: a bug", ["src/a.py"]),
        _commit("ccccccc3", base, "feat: add b", ["src/b.py"]),
        _commit(
            "ddddddd4", base.replace(day=2), "chore: tweak b", ["src/b.py"]
        ),
    ]
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with patch(
        "insights.fixback_scanner.get_commits_for_period",
        return_value=commits,
    ):
        report = build_fixback_scan_report(
            repo=mock_repo,
            period_start=base.replace(month=1, day=1),
            period_end=base.replace(month=2, day=1),
            months=6,
            revisit_days=14,
            top_n=10,
        )

    assert report["file_candidates"][0]["file_path"] == "src/a.py"
    assert report["file_candidates"][1]["file_path"] == "src/b.py"


def test_build_fixback_scan_report_skips_merge_commits_by_default():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    commits = [
        _commit(
            "aaaaaaa1",
            base,
            "merge: bulk update",
            ["src/a.py"],
            parent_count=2,
        ),
        _commit(
            "bbbbbbb2", base.replace(day=3), "fix: follow-up", ["src/a.py"]
        ),
    ]
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with patch(
        "insights.fixback_scanner.get_commits_for_period",
        return_value=commits,
    ):
        report = build_fixback_scan_report(
            repo=mock_repo,
            period_start=base.replace(month=1, day=1),
            period_end=base.replace(month=2, day=1),
            months=6,
            revisit_days=14,
            top_n=10,
        )

    assert report["summary"]["merge_commits_skipped"] == 1
    assert report["summary"]["candidate_files"] == 0
    assert report["file_candidates"] == []


def test_main_defaults_to_six_months(capsys):
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with (
        patch("insights.fixback_scanner.Repo", return_value=mock_repo),
        patch(
            "insights.fixback_scanner.get_commits_for_period", return_value=[]
        ),
    ):
        exit_code = main(["."])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["period"]["months"] == 6


def test_main_rejects_non_positive_months():
    with pytest.raises(SystemExit) as caught:
        main([".", "--months", "0"])

    assert caught.value.code == 2
