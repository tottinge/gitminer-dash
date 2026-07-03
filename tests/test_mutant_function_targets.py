"""Tests for `scripts/mutant_function_targets`."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from tests.script_namespace_loader import load_script_namespace


def _load_mutant_function_targets_namespace() -> dict:
    return load_script_namespace("mutant_function_targets", start_path=__file__)


def _record(
    *,
    key: str,
    base_key: str,
    module: str,
    mangled_function: str,
    function: str,
    status: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        key=key,
        base_key=base_key,
        module=module,
        mangled_function=mangled_function,
        function=function,
        status=status,
        source_path=Path("/repo/visualization/common_pair_intent_pane.py"),
        meta_path=Path(
            "/repo/mutants/visualization/common_pair_intent_pane.py.meta"
        ),
    )


def test_function_query_matches_supports_base_mangled_and_normalized_names():
    ns = _load_mutant_function_targets_namespace()
    function_query_matches = ns["function_query_matches"]
    record = _record(
        key="visualization.common_pair_intent_pane.x_build_common_pair_intent_pane__mutmut_1",
        base_key="visualization.common_pair_intent_pane.x_build_common_pair_intent_pane",
        module="visualization.common_pair_intent_pane",
        mangled_function="x_build_common_pair_intent_pane",
        function="build_common_pair_intent_pane",
        status="survived",
    )

    assert function_query_matches(record, "build_common_pair_intent_pane")
    assert function_query_matches(record, "x_build_common_pair_intent_pane")
    assert function_query_matches(
        record,
        "visualization.common_pair_intent_pane.x_build_common_pair_intent_pane",
    )
    assert not function_query_matches(record, "build_evidence_preview_items")


def test_build_report_groups_mutants_and_emits_target_keys_and_dimensions():
    ns = _load_mutant_function_targets_namespace()
    build_report = ns["build_report"]
    build_globals = build_report.__globals__

    records = [
        _record(
            key="visualization.common_pair_intent_pane.x_build_common_pair_intent_pane__mutmut_1",
            base_key="visualization.common_pair_intent_pane.x_build_common_pair_intent_pane",
            module="visualization.common_pair_intent_pane",
            mangled_function="x_build_common_pair_intent_pane",
            function="build_common_pair_intent_pane",
            status="survived",
        ),
        _record(
            key="visualization.common_pair_intent_pane.x_build_common_pair_intent_pane__mutmut_2",
            base_key="visualization.common_pair_intent_pane.x_build_common_pair_intent_pane",
            module="visualization.common_pair_intent_pane",
            mangled_function="x_build_common_pair_intent_pane",
            function="build_common_pair_intent_pane",
            status="no_tests",
        ),
        _record(
            key="visualization.common_pair_intent_pane.x_build_common_pair_intent_pane__mutmut_3",
            base_key="visualization.common_pair_intent_pane.x_build_common_pair_intent_pane",
            module="visualization.common_pair_intent_pane",
            mangled_function="x_build_common_pair_intent_pane",
            function="build_common_pair_intent_pane",
            status="killed",
        ),
        _record(
            key="visualization.common_pair_intent_pane.x_build_evidence_preview_items__mutmut_1",
            base_key="visualization.common_pair_intent_pane.x_build_evidence_preview_items",
            module="visualization.common_pair_intent_pane",
            mangled_function="x_build_evidence_preview_items",
            function="build_evidence_preview_items",
            status="survived",
        ),
    ]
    mutation_type_by_key = {
        "visualization.common_pair_intent_pane.x_build_common_pair_intent_pane__mutmut_1": "lookup-argument-mutation",
        "visualization.common_pair_intent_pane.x_build_common_pair_intent_pane__mutmut_2": "string-literal-mutation",
        "visualization.common_pair_intent_pane.x_build_common_pair_intent_pane__mutmut_3": "lookup-argument-mutation",
        "visualization.common_pair_intent_pane.x_build_evidence_preview_items__mutmut_1": "lookup-argument-mutation",
    }

    build_globals["collect_mutants"] = lambda _root: records
    build_globals["filter_mutants_for_source"] = (
        lambda all_records, _root, source_query: (
            all_records
            if source_query == "visualization/common_pair_intent_pane.py"
            else []
        )
    )
    build_globals["mutation_type_for_record"] = (
        lambda record, _cache: mutation_type_by_key[record.key]
    )

    report = build_report(
        root=Path("/repo"),
        source_query="visualization/common_pair_intent_pane.py",
        function_query="build_common_pair_intent_pane",
        target_statuses={"survived", "no_tests"},
    )

    assert report["matched_source_count"] == 4
    assert report["matched_function_count"] == 3
    assert report["matched_function_keys"] == [
        "visualization.common_pair_intent_pane.x_build_common_pair_intent_pane"
    ]
    assert report["status_counts"] == {
        "survived": 1,
        "no_tests": 1,
        "killed": 1,
    }
    assert report["mutation_type_counts"] == {
        "lookup-argument-mutation": 2,
        "string-literal-mutation": 1,
    }
    assert report["target_mutant_count"] == 2
    assert report["target_mutant_keys"] == [
        "visualization.common_pair_intent_pane.x_build_common_pair_intent_pane__mutmut_1",
        "visualization.common_pair_intent_pane.x_build_common_pair_intent_pane__mutmut_2",
    ]
    assert report["mutmut_run_command"] == (
        "uv run mutmut run "
        "visualization.common_pair_intent_pane.x_build_common_pair_intent_pane__mutmut_1 "
        "visualization.common_pair_intent_pane.x_build_common_pair_intent_pane__mutmut_2"
    )
    assert report["parameterized_dimensions"] == [
        "canonical keys plus casing/alias variants",
        "missing key fallback behavior",
        "canonical label/token values from user-visible contract",
    ]
