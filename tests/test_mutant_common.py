"""Tests for shared mutation helper policies in `scripts/mutant_common.py`."""

from scripts.mutant_common import (
    DEFAULT_RANK_TARGET_STATUSES,
    DEFAULT_TRIAGE_TARGET_STATUSES,
    candidate_test_file_for_module,
    parse_target_statuses,
)


def test_parse_target_statuses_uses_rank_defaults_when_statuses_not_provided():
    statuses = parse_target_statuses(None, DEFAULT_RANK_TARGET_STATUSES)

    assert statuses == {"survived"}


def test_parse_target_statuses_uses_triage_defaults_when_statuses_not_provided():
    statuses = parse_target_statuses(None, DEFAULT_TRIAGE_TARGET_STATUSES)

    assert statuses == {"no_tests", "survived", "timeout"}


def test_parse_target_statuses_parses_csv_values_with_whitespace():
    statuses = parse_target_statuses(
        " no_tests, survived , timeout ", DEFAULT_RANK_TARGET_STATUSES
    )

    assert statuses == {"no_tests", "survived", "timeout"}


def test_parse_target_statuses_adds_crash_when_requested():
    statuses = parse_target_statuses(
        None,
        DEFAULT_RANK_TARGET_STATUSES,
        include_crash=True,
    )

    assert statuses == {"survived", "crash"}


def test_candidate_test_file_for_module_uses_leaf_module_name():
    suggested_path = candidate_test_file_for_module("insights.some_module")

    assert suggested_path == "tests/test_some_module.py"


def test_candidate_test_file_for_module_handles_single_segment_module_name():
    suggested_path = candidate_test_file_for_module("summarize")

    assert suggested_path == "tests/test_summarize.py"
