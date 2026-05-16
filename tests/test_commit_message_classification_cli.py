"""Tests for `insights/commit_message_classification_cli.py`."""

import json
from unittest.mock import Mock, patch

import pytest

from insights.commit_message_classification_cli import main


def test_main_emits_payload_json_with_named_period(capsys):
    payload = {
        "status": "ok",
        "filename": "src/core.py",
        "message_count": 2,
        "intent_counts": [{"intent": "feat", "count": 2}],
        "classifications": [],
    }

    with (
        patch(
            "insights.commit_message_classification_cli.build_store_payload",
            return_value={
                "period": "Last 7 days",
                "begin": "2026-01-01T00:00:00+00:00",
                "end": "2026-01-07T23:59:59+00:00",
            },
        ) as mock_build_store_payload,
        patch(
            "insights.commit_message_classification_cli.generate_file_commit_classification_payload",
            return_value=payload,
        ) as mock_generate_payload,
    ):
        exit_code = main(
            [
                ".",
                "--file-path",
                "src/core.py",
                "--period",
                "Last 7 days",
            ]
        )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == payload
    mock_build_store_payload.assert_called_once_with("Last 7 days")
    assert mock_generate_payload.call_args.kwargs["filename"] == "src/core.py"


def test_main_uses_custom_range_and_skips_named_period_builder():
    with (
        patch(
            "insights.commit_message_classification_cli.generate_file_commit_classification_payload",
            return_value={"status": "ok"},
        ) as mock_generate_payload,
        patch(
            "insights.commit_message_classification_cli.build_store_payload"
        ) as mock_build_store_payload,
    ):
        exit_code = main(
            [
                ".",
                "--file-path",
                "src/core.py",
                "--from",
                "2026-01-01",
                "--to",
                "2026-01-31",
            ]
        )

    assert exit_code == 0
    mock_build_store_payload.assert_not_called()
    assert mock_generate_payload.call_args.kwargs["date_range_data"] == {
        "period": "Custom",
        "begin": "2026-01-01T00:00:00+00:00",
        "end": "2026-01-31T00:00:00+00:00",
    }


def test_main_passes_collector_that_respects_max_messages():
    sample_repo = Mock()
    with (
        patch(
            "insights.commit_message_classification_cli.build_store_payload",
            return_value={"period": "Last 30 days"},
        ),
        patch(
            "insights.commit_message_classification_cli.collect_commit_messages_for_file",
            return_value=["m1", "m2", "m3"],
        ),
        patch(
            "insights.commit_message_classification_cli.generate_file_commit_classification_payload",
            return_value={"status": "ok"},
        ) as mock_generate_payload,
    ):
        exit_code = main(
            [
                ".",
                "--file-path",
                "src/core.py",
                "--max-messages",
                "2",
            ]
        )

        assert exit_code == 0
        collector = mock_generate_payload.call_args.kwargs[
            "collect_commit_messages_for_file_fn"
        ]
        assert collector(sample_repo, "src/core.py", "start", "end") == [
            "m1",
            "m2",
        ]


def test_main_requires_from_and_to_to_be_provided_together():
    with pytest.raises(SystemExit) as caught:
        main(
            [
                ".",
                "--file-path",
                "src/core.py",
                "--from",
                "2026-01-01",
            ]
        )

    assert caught.value.code == 2


def test_main_rejects_non_positive_max_messages():
    with pytest.raises(SystemExit) as caught:
        main(
            [
                ".",
                "--file-path",
                "src/core.py",
                "--max-messages",
                "0",
            ]
        )

    assert caught.value.code == 2
