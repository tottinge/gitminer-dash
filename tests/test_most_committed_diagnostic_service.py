"""Tests for file-change diagnostic helpers in pages.most_committed_service."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pages.most_committed_service import (
    _coupling_signals,
    _diagnostic_labels,
    _filtered_evidence_rows,
    _revisit_signals,
    build_empty_file_change_diagnostic_payload,
    collect_file_commit_evidence,
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


def _mock_commit(
    *,
    sha: str,
    day: int,
    message: str,
    changed_files: list[str],
    no_parents: bool = False,
    diff_items: list[SimpleNamespace] | None = None,
    diff_exception: Exception | None = None,
) -> Mock:
    commit = Mock()
    commit.hexsha = sha
    commit.committed_datetime = datetime(
        2026, 5, day, 12, 0, tzinfo=timezone.utc
    )
    commit.message = message
    commit.stats.files = {path: {} for path in changed_files}
    commit.parents = [] if no_parents else [object()]
    commit.diff = Mock()
    if diff_exception is not None:
        commit.diff.side_effect = diff_exception
    else:
        commit.diff.return_value = diff_items or []
    return commit


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
    assert payload["top_cochange_neighbors"] == [
        {"path": "src/a.py", "count": 3},
        {"path": "src/b.py", "count": 1},
        {"path": "src/c.py", "count": 1},
    ]
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
                sha="aaa1111",
                day=1,
                message="feat(core): add parser",
                neighbors=["src/feat_only.py"],
            ),
            _evidence_row(
                sha="bbb2222",
                day=2,
                message="fix(core): patch parser",
                neighbors=["src/fix.py", "src/shared.py"],
            ),
            _evidence_row(
                sha="ccc3333",
                day=4,
                message="fix(core): adjust parser",
                neighbors=["src/fix.py"],
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
    assert payload["top_cochange_neighbors"] == [
        {"path": "src/fix.py", "count": 2},
        {"path": "src/shared.py", "count": 1},
    ]
    assert len(payload["classifications"]) == 2


def test_generate_file_payload_ranks_and_caps_neighbors_from_filtered_rows():
    period_start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 5, 31, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(period_start, period_end))
    get_repo_fn = Mock(return_value=object())
    collect_file_commit_evidence_fn = Mock(
        return_value=[
            _evidence_row(
                sha="aaa1111",
                day=1,
                message="fix(core): one",
                neighbors=["src/z.py", "src/a.py", "src/b.py"],
            ),
            _evidence_row(
                sha="bbb2222",
                day=2,
                message="fix(core): two",
                neighbors=["src/a.py", "src/c.py"],
            ),
            _evidence_row(
                sha="ccc3333",
                day=3,
                message="fix(core): three",
                neighbors=["src/b.py", "src/d.py"],
            ),
            _evidence_row(
                sha="ddd4444",
                day=4,
                message="fix(core): four",
                neighbors=["src/e.py", "src/f.py"],
            ),
            _evidence_row(
                sha="eee5555",
                day=5,
                message="feat(core): growth",
                neighbors=["src/feat-only.py"],
            ),
        ]
    )
    classify_commit_messages_fn = Mock(
        return_value={
            "message_count": 5,
            "intent_counts": [
                {"intent": "fix", "count": 4},
                {"intent": "feat", "count": 1},
            ],
            "classifications": [
                {"intent": "fix", "message": "fix(core): one"},
                {"intent": "fix", "message": "fix(core): two"},
                {"intent": "fix", "message": "fix(core): three"},
                {"intent": "fix", "message": "fix(core): four"},
                {"intent": "feat", "message": "feat(core): growth"},
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
    assert payload["filtered_message_count"] == 4
    assert payload["top_cochange_neighbors"] == [
        {"path": "src/a.py", "count": 2},
        {"path": "src/b.py", "count": 2},
        {"path": "src/c.py", "count": 1},
        {"path": "src/d.py", "count": 1},
        {"path": "src/e.py", "count": 1},
    ]
    assert all(
        neighbor["path"] != "src/feat-only.py"
        for neighbor in payload["top_cochange_neighbors"]
    )


def test_generate_file_payload_preserves_unknown_focus_and_filters_empty():
    period_start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 5, 31, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(period_start, period_end))
    get_repo_fn = Mock(return_value=object())
    collect_file_commit_evidence_fn = Mock(
        return_value=[
            _evidence_row(
                sha="aaa1111",
                day=1,
                message="fix(core): patch parser",
                neighbors=["src/fix.py"],
            ),
            _evidence_row(
                sha="bbb2222",
                day=2,
                message="feat(core): expand parser",
                neighbors=["src/feat.py"],
            ),
        ]
    )
    classify_commit_messages_fn = Mock(
        return_value={
            "message_count": 2,
            "intent_counts": [
                {"intent": "fix", "count": 1},
                {"intent": "feat", "count": 1},
            ],
            "classifications": [
                {"intent": "fix", "message": "fix(core): patch parser"},
                {"intent": "feat", "message": "feat(core): expand parser"},
            ],
        }
    )

    payload = generate_file_change_diagnostic_payload(
        filename="src/core.py",
        date_range_data={"period": "Last 30 days"},
        focused_intent="not-a-real-intent",
        parse_date_range_fn=parse_date_range_fn,
        get_repo_fn=get_repo_fn,
        collect_file_commit_evidence_fn=collect_file_commit_evidence_fn,
        classify_commit_messages_fn=classify_commit_messages_fn,
    )

    assert payload["status"] == "ok"
    assert payload["focused_intent"] == "not-a-real-intent"
    assert payload["message_count"] == 2
    assert payload["filtered_message_count"] == 0
    assert payload["evidence_rows"] == []
    assert payload["classifications"] == []
    assert payload["top_cochange_neighbors"] == []


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
    assert payload["top_cochange_neighbors"] == [
        {"path": "src/a.py", "count": 1},
        {"path": "src/b.py", "count": 1},
        {"path": "src/c.py", "count": 1},
        {"path": "src/d.py", "count": 1},
        {"path": "src/e.py", "count": 1},
    ]
    assert "coupling_pressure" in payload["advisory_labels"]
    assert "possible_thrash" not in payload["advisory_labels"]


def test_collect_file_commit_evidence_sorts_rows_and_normalizes_summary():
    selected_file = "src/core.py"
    early_commit = _mock_commit(
        sha="aaa1111",
        day=1,
        message="",
        changed_files=[selected_file, "src/alpha.py", "src/beta.py"],
        no_parents=True,
    )
    late_commit = _mock_commit(
        sha="bbb2222",
        day=3,
        message="Fix parser branch\nextra detail",
        changed_files=[selected_file, "src/other.py"],
        diff_items=[
            SimpleNamespace(
                b_path="src/not-target.py",
                a_path="src/not-target.py",
                diff=b"ignored",
            ),
            SimpleNamespace(
                b_path=selected_file,
                a_path=None,
                diff=b"@@ -1 +1 @@",
            ),
        ],
    )
    repo = Mock()
    repo.iter_commits.return_value = [late_commit, early_commit]

    with patch(
        "pages.most_committed_service.hunk_fingerprints_from_patch",
        side_effect=lambda patch_text: (
            [f"fp:{patch_text}"] if patch_text else []
        ),
    ):
        rows = collect_file_commit_evidence(
            repo=repo,
            filename=selected_file,
            period_start=datetime(2026, 5, 1, tzinfo=timezone.utc),
            period_end=datetime(2026, 5, 31, tzinfo=timezone.utc),
        )

    assert [row["hash"] for row in rows] == ["aaa1111", "bbb2222"]
    assert rows[0]["message"] == "(empty commit message)"
    assert rows[0]["cochanged_neighbors"] == ["src/alpha.py", "src/beta.py"]
    assert rows[0]["hunk_fingerprints"] == []
    assert rows[1]["message"] == "Fix parser branch"
    assert rows[1]["cochanged_neighbors"] == ["src/other.py"]
    assert rows[1]["hunk_fingerprints"] == ["fp:@@ -1 +1 @@"]


def test_collect_file_commit_evidence_handles_diff_error_and_string_patch():
    selected_file = "src/core.py"
    error_commit = _mock_commit(
        sha="aaa1111",
        day=1,
        message="fix: fallback",
        changed_files=[selected_file],
        diff_exception=RuntimeError("diff failed"),
    )
    string_patch_commit = _mock_commit(
        sha="bbb2222",
        day=2,
        message="fix: keep string patch",
        changed_files=[selected_file, "src/neighbor.py"],
        diff_items=[
            SimpleNamespace(
                b_path=None,
                a_path=selected_file,
                diff="string patch",
            )
        ],
    )
    repo = Mock()
    repo.iter_commits.return_value = [string_patch_commit, error_commit]

    with patch(
        "pages.most_committed_service.hunk_fingerprints_from_patch",
        side_effect=lambda patch_text: [patch_text],
    ):
        rows = collect_file_commit_evidence(
            repo=repo,
            filename=selected_file,
            period_start=datetime(2026, 5, 1, tzinfo=timezone.utc),
            period_end=datetime(2026, 5, 31, tzinfo=timezone.utc),
        )

    assert rows[0]["hash"] == "aaa1111"
    assert rows[0]["hunk_fingerprints"] == [""]
    assert rows[1]["hash"] == "bbb2222"
    assert rows[1]["hunk_fingerprints"] == ["string patch"]


def test_revisit_signals_handles_short_inputs_and_thresholds():
    empty_signals = _revisit_signals(
        [
            _evidence_row(
                sha="aaa1111",
                day=1,
                message="feat(core): add parser",
                hunk_fingerprints=["hunk-a"],
            )
        ]
    )
    assert empty_signals == {
        "short_gap_followups": 0,
        "short_gap_shared_hunk_followups": 0,
        "fixlike_followups": 0,
        "median_revisit_days": None,
        "rework_episode_count": 0,
        "rework_episodes": [],
    }

    threshold_rows = [
        {
            **_evidence_row(
                sha="aaa1111",
                day=1,
                message="feat(core): add parser",
                hunk_fingerprints=["hunk-a"],
            ),
            "intent": "feat",
        },
        {
            **_evidence_row(
                sha="bbb2222",
                day=10,
                message="fix(core): patch parser",
                hunk_fingerprints=["hunk-b"],
            ),
            "intent": "fix",
        },
        {
            **_evidence_row(
                sha="ccc3333",
                day=11,
                message="fix(core): follow-up parser patch",
                hunk_fingerprints=["hunk-b"],
            ),
            "intent": "fix",
        },
    ]

    signals = _revisit_signals(threshold_rows)
    assert signals["short_gap_followups"] == 1
    assert signals["short_gap_shared_hunk_followups"] == 1
    assert signals["fixlike_followups"] == 1
    assert signals["median_revisit_days"] == 5.0
    assert signals["rework_episode_count"] == 1
    assert signals["rework_episodes"][0]["anchor_hash"] == "bbb2222"
    assert signals["rework_episodes"][0]["rework_signal_score"] == 3


def test_coupling_signals_zero_and_minimum_message_guard():
    zero_signals = _coupling_signals([], message_count=0)
    assert zero_signals == {
        "unique_cochange_neighbors": 0,
        "cochange_commit_coverage_percent": 0,
        "average_neighbors_per_commit": 0.0,
        "coupling_signal_score": 0,
        "top_cochange_neighbors": [],
    }

    dense_rows = [
        {"cochanged_neighbors": ["a.py", "b.py", "c.py"]},
        {"cochanged_neighbors": ["d.py", "e.py", "f.py"]},
        {"cochanged_neighbors": ["g.py", "h.py", "i.py"]},
    ]
    guarded_signals = _coupling_signals(dense_rows, message_count=3)
    assert guarded_signals["unique_cochange_neighbors"] == 9
    assert guarded_signals["cochange_commit_coverage_percent"] == 100
    assert guarded_signals["average_neighbors_per_commit"] == 3.0
    assert guarded_signals["coupling_signal_score"] == 0


def test_diagnostic_labels_cover_all_decision_paths():
    assert _diagnostic_labels(
        message_count=4,
        fixlike_ratio_percent=40,
        feature_ratio_percent=10,
        maintenance_ratio_percent=20,
        short_gap_followups=3,
        short_gap_shared_hunk_followups=2,
        fixlike_followups=2,
        rework_episode_count=2,
        coupling_signal_score=1,
    ) == ["possible_thrash"]

    assert _diagnostic_labels(
        message_count=5,
        fixlike_ratio_percent=10,
        feature_ratio_percent=40,
        maintenance_ratio_percent=20,
        short_gap_followups=0,
        short_gap_shared_hunk_followups=0,
        fixlike_followups=0,
        rework_episode_count=0,
        coupling_signal_score=0,
    ) == ["feature_growth"]

    assert _diagnostic_labels(
        message_count=6,
        fixlike_ratio_percent=20,
        feature_ratio_percent=10,
        maintenance_ratio_percent=45,
        short_gap_followups=0,
        short_gap_shared_hunk_followups=0,
        fixlike_followups=0,
        rework_episode_count=0,
        coupling_signal_score=0,
    ) == ["maintenance_chore"]

    assert _diagnostic_labels(
        message_count=6,
        fixlike_ratio_percent=20,
        feature_ratio_percent=10,
        maintenance_ratio_percent=20,
        short_gap_followups=0,
        short_gap_shared_hunk_followups=0,
        fixlike_followups=0,
        rework_episode_count=0,
        coupling_signal_score=2,
    ) == ["coupling_pressure"]

    assert _diagnostic_labels(
        message_count=3,
        fixlike_ratio_percent=20,
        feature_ratio_percent=20,
        maintenance_ratio_percent=20,
        short_gap_followups=0,
        short_gap_shared_hunk_followups=0,
        fixlike_followups=0,
        rework_episode_count=0,
        coupling_signal_score=1,
    ) == ["mixed_signal"]


def test_filtered_rows_and_empty_payload_focus_normalization():
    evidence_rows = [
        {"intent": "fix", "message": "fix: one"},
        {"intent": "feat", "message": "feat: one"},
    ]
    assert _filtered_evidence_rows(evidence_rows, "all") == evidence_rows
    assert _filtered_evidence_rows(evidence_rows, "FIX") == [
        {"intent": "fix", "message": "fix: one"}
    ]
    assert _filtered_evidence_rows(evidence_rows, "*") == evidence_rows

    empty_payload = build_empty_file_change_diagnostic_payload(
        status="no_file_selected",
        focused_intent="*",
    )
    assert empty_payload["focused_intent"] == "all"
    assert empty_payload["filtered_message_count"] == 0
    assert empty_payload["evidence_rows"] == []


def test_build_empty_payload_preserves_custom_fields_and_zero_metrics():
    payload = build_empty_file_change_diagnostic_payload(
        status="repository_unavailable",
        filename="src/core.py",
        status_detail="Repository selection is required.",
        error_detail="No repository path provided",
        focused_intent="Fix",
    )

    assert payload["status"] == "repository_unavailable"
    assert payload["filename"] == "src/core.py"
    assert payload["status_detail"] == "Repository selection is required."
    assert payload["error_detail"] == "No repository path provided"
    assert payload["focused_intent"] == "fix"

    assert payload["message_count"] == 0
    assert payload["filtered_message_count"] == 0
    assert payload["intent_counts"] == []
    assert payload["classifications"] == []
    assert payload["evidence_rows"] == []
    assert payload["advisory_labels"] == []
    assert payload["confidence_hint"] == ""
    assert payload["intent_leader"] == "unknown"
    assert payload["leader_coverage_percent"] == 0
    assert payload["fixlike_ratio_percent"] == 0
    assert payload["feature_ratio_percent"] == 0
    assert payload["maintenance_ratio_percent"] == 0
    assert payload["short_gap_followups"] == 0
    assert payload["short_gap_shared_hunk_followups"] == 0
    assert payload["median_revisit_days"] is None
    assert payload["unique_cochange_neighbors"] == 0
    assert payload["cochange_commit_coverage_percent"] == 0
    assert payload["average_neighbors_per_commit"] == 0.0
    assert payload["coupling_signal_score"] == 0
    assert payload["top_cochange_neighbors"] == []
    assert payload["rework_episode_count"] == 0
    assert payload["rework_episodes"] == []
