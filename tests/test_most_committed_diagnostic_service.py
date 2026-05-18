"""Tests for file-change diagnostic helpers in pages.most_committed_service."""

from datetime import datetime, timezone
from unittest.mock import Mock

from pages.most_committed_service import (
    generate_file_change_diagnostic_payload,
    generate_table_selection_file_change_diagnostic_payload,
)


def _evidence_row(
    *,
    sha: str,
    day: int,
    message: str,
    neighbors: list[str] | None = None,
    hunk_fingerprints: list[str] | None = None,
):
    timestamp = datetime(2026, 5, day, 12, 0, tzinfo=timezone.utc)
    return {
        "hash": sha,
        "date": timestamp.strftime("%Y-%m-%d %H:%M"),
        "message": message,
        "committed_at": timestamp,
        "cochanged_neighbors": neighbors or [],
        "hunk_fingerprints": hunk_fingerprints or [],
    }


def test_generate_table_selection_payload_returns_no_selection_contract():
    parse_date_range_fn = Mock()
    get_repo_fn = Mock()
    collect_file_commit_evidence_fn = Mock()
    classify_commit_messages_fn = Mock()

    payload = generate_table_selection_file_change_diagnostic_payload(
        active_cell=None,
        table_data=[],
        date_range_data={"period": "Last 30 days"},
        focused_intent="all",
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_file_commit_evidence_fn=collect_file_commit_evidence_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )

    assert payload["status"] == "no_file_selected"
    assert payload["message_count"] == 0
    assert payload["evidence_rows"] == []
    parse_date_range_fn.assert_not_called()
    get_repo_fn.assert_not_called()
    collect_file_commit_evidence_fn.assert_not_called()
    classify_commit_messages_fn.assert_not_called()


def test_generate_file_payload_returns_invalid_date_range_contract():
    parse_date_range_fn = Mock(side_effect=ValueError("Bad date range"))
    get_repo_fn = Mock()
    collect_file_commit_evidence_fn = Mock()
    classify_commit_messages_fn = Mock()

    payload = generate_file_change_diagnostic_payload(
        filename="src/core.py",
        date_range_data={"period": "Broken"},
        focused_intent="all",
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_file_commit_evidence_fn=collect_file_commit_evidence_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )

    assert payload["status"] == "invalid_date_range"
    assert payload["filename"] == "src/core.py"
    assert payload["error_detail"] == "Bad date range"
    get_repo_fn.assert_not_called()
    collect_file_commit_evidence_fn.assert_not_called()
    classify_commit_messages_fn.assert_not_called()


def test_generate_file_payload_returns_no_messages_contract():
    period_start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 5, 31, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(period_start, period_end))
    get_repo_fn = Mock(return_value=object())
    collect_file_commit_evidence_fn = Mock(return_value=[])
    classify_commit_messages_fn = Mock()

    payload = generate_file_change_diagnostic_payload(
        filename="src/core.py",
        date_range_data={"period": "Last 30 days"},
        focused_intent="all",
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_file_commit_evidence_fn=collect_file_commit_evidence_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )

    assert payload["status"] == "no_messages"
    assert payload["filename"] == "src/core.py"
    assert payload["message_count"] == 0
    classify_commit_messages_fn.assert_not_called()


def test_generate_file_payload_handles_missing_repository_path_error():
    period_start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 5, 31, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(period_start, period_end))
    get_repo_fn = Mock(side_effect=ValueError("No repository path provided"))
    collect_file_commit_evidence_fn = Mock()
    classify_commit_messages_fn = Mock()

    payload = generate_file_change_diagnostic_payload(
        filename="src/core.py",
        date_range_data={"period": "Last 30 days"},
        focused_intent="all",
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_file_commit_evidence_fn=collect_file_commit_evidence_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )

    assert payload["status"] == "repository_unavailable"
    assert payload["filename"] == "src/core.py"
    collect_file_commit_evidence_fn.assert_not_called()
    classify_commit_messages_fn.assert_not_called()


def test_generate_file_payload_populates_diagnostic_metrics_and_labels():
    period_start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 5, 31, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(period_start, period_end))
    get_repo_fn = Mock(return_value=object())
    collect_file_commit_evidence_fn = Mock(
        return_value=[
            _evidence_row(
                sha="aaa1111",
                day=1,
                message="feat(core): add parser",
                neighbors=["src/a.py"],
                hunk_fingerprints=["hunk-a"],
            ),
            _evidence_row(
                sha="bbb2222",
                day=2,
                message="fix(core): patch parser",
                neighbors=["src/a.py", "src/b.py"],
                hunk_fingerprints=["hunk-a"],
            ),
            _evidence_row(
                sha="ccc3333",
                day=4,
                message="chore(core): tidy parser",
                neighbors=["src/c.py"],
                hunk_fingerprints=["hunk-c"],
            ),
            _evidence_row(
                sha="ddd4444",
                day=5,
                message="fix(core): patch parser follow-up",
                neighbors=["src/a.py"],
                hunk_fingerprints=["hunk-c"],
            ),
        ]
    )
    classify_commit_messages_fn = Mock(
        return_value={
            "message_count": 4,
            "intent_counts": [
                {"intent": "fix", "count": 2},
                {"intent": "chore", "count": 1},
                {"intent": "feat", "count": 1},
            ],
            "classifications": [
                {"intent": "feat", "message": "feat(core): add parser"},
                {"intent": "fix", "message": "fix(core): patch parser"},
                {"intent": "chore", "message": "chore(core): tidy parser"},
                {
                    "intent": "fix",
                    "message": "fix(core): patch parser follow-up",
                },
            ],
        }
    )

    payload = generate_file_change_diagnostic_payload(
        filename="src/core.py",
        date_range_data={"period": "Last 30 days"},
        focused_intent="all",
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_file_commit_evidence_fn=collect_file_commit_evidence_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )

    assert payload["status"] == "ok"
    assert payload["filename"] == "src/core.py"
    assert payload["message_count"] == 4
    assert payload["filtered_message_count"] == 4
    assert payload["intent_leader"] == "fix"
    assert payload["fixlike_ratio_percent"] == 50
    assert payload["short_gap_followups"] == 3
    assert payload["short_gap_shared_hunk_followups"] == 2
    assert payload["median_revisit_days"] == 1.0
    assert payload["unique_cochange_neighbors"] == 3
    assert payload["cochange_commit_coverage_percent"] == 100
    assert payload["average_neighbors_per_commit"] == 1.25
    assert payload["coupling_signal_score"] == 1
    assert payload["rework_episode_count"] == 2
    assert "possible_thrash" in payload["advisory_labels"]
    assert "coupling_pressure" not in payload["advisory_labels"]
    assert (
        payload["confidence_hint"]
        == "Medium confidence: trend based on 4 commits."
    )
    assert len(payload["rework_episodes"]) == 2
    assert payload["rework_episodes"][0]["anchor_hash"] == "aaa1111"
    assert payload["rework_episodes"][0]["shared_hunk_count"] == 1
    assert payload["rework_episodes"][0]["rework_signal_score"] == 3


def test_generate_file_payload_applies_intent_focus_to_evidence_rows():
    period_start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 5, 31, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(period_start, period_end))
    get_repo_fn = Mock(return_value=object())
    collect_file_commit_evidence_fn = Mock(
        return_value=[
            _evidence_row(
                sha="aaa1111", day=1, message="feat(core): add parser"
            ),
            _evidence_row(
                sha="bbb2222", day=2, message="fix(core): patch parser"
            ),
            _evidence_row(
                sha="ccc3333", day=4, message="fix(core): adjust parser"
            ),
        ]
    )
    classify_commit_messages_fn = Mock(
        return_value={
            "message_count": 3,
            "intent_counts": [
                {"intent": "fix", "count": 2},
                {"intent": "feat", "count": 1},
            ],
            "classifications": [
                {"intent": "feat", "message": "feat(core): add parser"},
                {"intent": "fix", "message": "fix(core): patch parser"},
                {"intent": "fix", "message": "fix(core): adjust parser"},
            ],
        }
    )

    payload = generate_file_change_diagnostic_payload(
        filename="src/core.py",
        date_range_data={"period": "Last 30 days"},
        focused_intent="fix",
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_file_commit_evidence_fn=collect_file_commit_evidence_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )

    assert payload["status"] == "ok"
    assert payload["focused_intent"] == "fix"
    assert payload["message_count"] == 3
    assert payload["filtered_message_count"] == 2
    assert {row["intent"] for row in payload["evidence_rows"]} == {"fix"}
    assert len(payload["classifications"]) == 2


def test_generate_file_payload_avoids_false_thrash_without_shared_hunks():
    period_start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 5, 31, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(period_start, period_end))
    get_repo_fn = Mock(return_value=object())
    collect_file_commit_evidence_fn = Mock(
        return_value=[
            _evidence_row(
                sha="aaa1111",
                day=1,
                message="feat(core): add parser",
            ),
            _evidence_row(
                sha="bbb2222",
                day=2,
                message="fix(core): patch parser",
            ),
            _evidence_row(
                sha="ccc3333",
                day=3,
                message="feat(core): expand parser",
            ),
            _evidence_row(
                sha="ddd4444",
                day=4,
                message="fix(core): patch parser follow-up",
            ),
        ]
    )
    classify_commit_messages_fn = Mock(
        return_value={
            "message_count": 4,
            "intent_counts": [
                {"intent": "fix", "count": 2},
                {"intent": "feat", "count": 2},
            ],
            "classifications": [
                {"intent": "feat", "message": "feat(core): add parser"},
                {"intent": "fix", "message": "fix(core): patch parser"},
                {"intent": "feat", "message": "feat(core): expand parser"},
                {
                    "intent": "fix",
                    "message": "fix(core): patch parser follow-up",
                },
            ],
        }
    )

    payload = generate_file_change_diagnostic_payload(
        filename="src/core.py",
        date_range_data={"period": "Last 30 days"},
        focused_intent="all",
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_file_commit_evidence_fn=collect_file_commit_evidence_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )

    assert payload["status"] == "ok"
    assert payload["short_gap_followups"] == 3
    assert payload["short_gap_shared_hunk_followups"] == 0
    assert payload["rework_episode_count"] == 0
    assert payload["rework_episodes"] == []
    assert "possible_thrash" not in payload["advisory_labels"]


def test_generate_file_payload_adds_coupling_pressure_independently():
    period_start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 5, 31, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(period_start, period_end))
    get_repo_fn = Mock(return_value=object())
    collect_file_commit_evidence_fn = Mock(
        return_value=[
            _evidence_row(
                sha="aaa1111",
                day=1,
                message="feat(core): add parser branch",
                neighbors=["src/a.py", "src/b.py"],
            ),
            _evidence_row(
                sha="bbb2222",
                day=2,
                message="feat(core): add parser cache",
                neighbors=["src/c.py", "src/d.py"],
            ),
            _evidence_row(
                sha="ccc3333",
                day=4,
                message="chore(core): move parser constants",
                neighbors=["src/e.py", "src/f.py"],
            ),
            _evidence_row(
                sha="ddd4444",
                day=5,
                message="feat(core): add parser tracing",
                neighbors=["src/g.py", "src/h.py"],
            ),
            _evidence_row(
                sha="eee5555",
                day=7,
                message="chore(core): tidy parser imports",
                neighbors=["src/i.py", "src/j.py"],
            ),
            _evidence_row(
                sha="fff6666",
                day=8,
                message="chore(core): rename parser helpers",
                neighbors=["src/k.py", "src/l.py"],
            ),
        ]
    )
    classify_commit_messages_fn = Mock(
        return_value={
            "message_count": 6,
            "intent_counts": [
                {"intent": "feat", "count": 3},
                {"intent": "chore", "count": 3},
            ],
            "classifications": [
                {"intent": "feat", "message": "feat(core): add parser branch"},
                {"intent": "feat", "message": "feat(core): add parser cache"},
                {
                    "intent": "chore",
                    "message": "chore(core): move parser constants",
                },
                {"intent": "feat", "message": "feat(core): add parser tracing"},
                {
                    "intent": "chore",
                    "message": "chore(core): tidy parser imports",
                },
                {
                    "intent": "chore",
                    "message": "chore(core): rename parser helpers",
                },
            ],
        }
    )

    payload = generate_file_change_diagnostic_payload(
        filename="src/core.py",
        date_range_data={"period": "Last 30 days"},
        focused_intent="all",
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_file_commit_evidence_fn=collect_file_commit_evidence_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )

    assert payload["status"] == "ok"
    assert payload["unique_cochange_neighbors"] == 12
    assert payload["cochange_commit_coverage_percent"] == 100
    assert payload["average_neighbors_per_commit"] == 2.0
    assert payload["coupling_signal_score"] == 3
    assert "coupling_pressure" in payload["advisory_labels"]
    assert "possible_thrash" not in payload["advisory_labels"]
