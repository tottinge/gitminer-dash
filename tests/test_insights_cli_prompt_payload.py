"""Tests prompt payload output mode in `insights/cli.py`."""

import json
from unittest.mock import MagicMock, patch

from insights.cli import main
from insights.models import (
    AnalysisSnapshot,
    EvidenceRef,
    HotspotCandidate,
    InsightReport,
)


def test_main_emits_prompt_payload_when_flag_enabled(capsys):
    snapshot = AnalysisSnapshot(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=3,
        file_commit_counts={"src/a.py": 3},
        file_recent_commits={"src/a.py": ["aaaaaaa"]},
    )
    report = InsightReport(
        schema_version="1.0.0",
        repo_path="/example/repo",
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-31T00:00:00+00:00",
        total_commits=3,
        hotspots=[
            HotspotCandidate(
                file_path="src/a.py",
                score=3.0,
                evidence=[
                    EvidenceRef(kind="file", value="src/a.py"),
                    EvidenceRef(kind="metric", value="commit_count=3"),
                ],
            )
        ],
    )
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with (
        patch("insights.cli.Repo", return_value=mock_repo),
        patch(
            "insights.cli.build_analysis_snapshot",
            return_value=snapshot,
        ),
        patch(
            "insights.cli.build_insight_report",
            return_value=report,
        ),
    ):
        exit_code = main(
            [
                ".",
                "--from",
                "2026-01-01",
                "--to",
                "2026-01-31",
                "--prompt-payload",
            ]
        )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["prompt_payload_version"] == "1.0.0"
    assert payload["schema_version"] == "1.0.0"
    assert payload["hotspots"][0]["rank"] == 1
    assert payload["hotspots"][0]["file_path"] == "src/a.py"
    assert payload["hotspots"][0]["evidence"] == [
        {"kind": "file", "value": "src/a.py"},
        {"kind": "metric", "value": "commit_count=3"},
    ]
