"""Tests for `insights/suggest_maintenance.py`."""

import json
import shutil
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from insights.suggest_maintenance import main


class _DictReport:
    def __init__(self, payload: dict):
        self._payload = payload

    def to_dict(self) -> dict:
        return self._payload


class _TrackingTempDir:
    def __init__(self, path: Path):
        self.path = path
        self.cleaned = False

    def __enter__(self) -> str:
        self.path.mkdir(parents=True, exist_ok=False)
        return str(self.path)

    def __exit__(self, exc_type, exc, traceback) -> None:
        shutil.rmtree(self.path)
        self.cleaned = True


@contextmanager
def _patch_dependencies(mock_repo: MagicMock):
    fixback_payload = {
        "summary": {
            "commits_analyzed": 12,
            "files_scanned": 7,
            "revisit_events": 6,
            "fixback_events": 2,
        },
        "file_candidates": [
            {
                "file_path": "src/a.py",
                "score": 8.5,
                "touch_count": 5,
                "revisit_events": 4,
                "fixback_events": 1,
                "revisit_rate": 0.8,
                "fixback_rate": 0.25,
            }
        ],
    }
    hotspot_payload = {
        "hotspots": [
            {
                "file_path": "src/a.py",
                "score": 11.0,
                "evidence": [
                    {"kind": "metric", "value": "commit_count=11"},
                    {"kind": "commit", "value": "abcdef0"},
                ],
            }
        ]
    }
    bridge_payload = {
        "bridges": [
            {
                "file_path": "src/a.py",
                "bridge_score": 1.3,
                "bridge_ratio": 0.6,
                "commit_count": 11,
                "connected_communities": [0, 2],
            }
        ]
    }
    mutant_records = [
        SimpleNamespace(
            module="src.a",
            status="survived",
            source_path=Path("/example/repo/src/a.py"),
        ),
        SimpleNamespace(
            module="src.a",
            status="no_tests",
            source_path=Path("/example/repo/src/a.py"),
        ),
    ]
    fake_mutant_common = SimpleNamespace(
        collect_mutants=lambda _root: mutant_records,
        summarize_statuses=lambda _records: {
            "survived": 1,
            "no_tests": 1,
        },
        relative_path_str=(
            lambda source_path, root: source_path.resolve()
            .relative_to(root.resolve())
            .as_posix()
        ),
    )
    with ExitStack() as stack:
        stack.enter_context(
            patch("insights.suggest_maintenance.Repo", return_value=mock_repo)
        )
        stack.enter_context(
            patch(
                "insights.suggest_maintenance.build_fixback_scan_report",
                return_value=fixback_payload,
            )
        )
        stack.enter_context(
            patch(
                "insights.suggest_maintenance.build_analysis_snapshot",
                return_value=MagicMock(),
            )
        )
        stack.enter_context(
            patch(
                "insights.suggest_maintenance.build_insight_report",
                return_value=_DictReport(hotspot_payload),
            )
        )
        stack.enter_context(
            patch(
                "insights.suggest_maintenance.build_bridge_metrics_report",
                return_value=_DictReport(bridge_payload),
            )
        )
        stack.enter_context(
            patch(
                "insights.suggest_maintenance._load_mutant_common",
                return_value=fake_mutant_common,
            )
        )
        yield


def test_main_emits_maintenance_payload(capsys):
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"
    mock_repo.git_dir = "/example/repo/.git"
    with _patch_dependencies(mock_repo):
        exit_code = main(
            [
                ".",
                "--months",
                "6",
                "--top",
                "5",
                "--as-of",
                "2026-04-21T00:00:00+00:00",
            ]
        )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report_type"] == "maintenance-suggestions"
    assert payload["summary"]["commits_analyzed"] == 12
    assert payload["signals"]["hotspots"][0]["commit_count"] == 11
    assert payload["signals"]["bridges"][0]["bridge_score"] == 1.3
    assert payload["signals"]["mutation"]["mutant_count"] == 2
    assert payload["recommendations"]


def test_main_cleans_temporary_workspace(tmp_path: Path, capsys):
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"
    mock_repo.git_dir = "/example/repo/.git"
    tracker = _TrackingTempDir(tmp_path / "workspace")

    with (
        _patch_dependencies(mock_repo),
        patch(
            "insights.suggest_maintenance.tempfile.TemporaryDirectory",
            return_value=tracker,
        ),
    ):
        exit_code = main(["."])

    assert exit_code == 0
    assert tracker.cleaned is True
    assert not tracker.path.exists()
    assert capsys.readouterr().out


def test_main_rejects_non_positive_months():
    with pytest.raises(SystemExit) as caught:
        main([".", "--months", "0"])
    assert caught.value.code == 2
