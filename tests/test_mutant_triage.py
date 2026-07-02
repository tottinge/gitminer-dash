"""Tests for the `scripts/mutant_triage` clustered triage workflow."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from tests.script_namespace_loader import load_script_namespace


def _load_mutant_triage_namespace() -> dict:
    return load_script_namespace("mutant_triage", start_path=__file__)


def _record(
    *,
    key: str,
    base_key: str,
    module: str,
    function: str,
    status: str,
    source_file: str,
) -> SimpleNamespace:
    return SimpleNamespace(
        key=key,
        base_key=base_key,
        module=module,
        function=function,
        status=status,
        source_path=Path("/repo") / source_file,
        meta_path=Path("/repo/mutants") / f"{source_file}.meta",
    )


def test_select_source_query_prefers_top_survived_source():
    ns = _load_mutant_triage_namespace()
    select_source_query = ns["select_source_query"]
    ranked_sources = [
        {
            "source_file": "pages/no_tests_first.py",
            "no_tests": 40,
            "survived": 0,
            "timeout": 0,
            "total_mutants": 40,
        },
        {
            "source_file": "pages/survivor_target.py",
            "no_tests": 2,
            "survived": 5,
            "timeout": 0,
            "total_mutants": 30,
        },
    ]

    selected_query, selection_mode = select_source_query(ranked_sources, None)

    assert selected_query == "pages/survivor_target.py"
    assert selection_mode == "top-survived"


def test_survivor_clusters_group_by_function_and_mutation_type():
    ns = _load_mutant_triage_namespace()
    clusters_func = ns["survivor_clusters"]
    cluster_globals = clusters_func.__globals__

    records = [
        _record(
            key="pages.target.x_alpha__mutmut_1",
            base_key="pages.target.x_alpha",
            module="pages.target",
            function="alpha",
            status="survived",
            source_file="pages/target.py",
        ),
        _record(
            key="pages.target.x_alpha__mutmut_2",
            base_key="pages.target.x_alpha",
            module="pages.target",
            function="alpha",
            status="survived",
            source_file="pages/target.py",
        ),
        _record(
            key="pages.target.x_beta__mutmut_1",
            base_key="pages.target.x_beta",
            module="pages.target",
            function="beta",
            status="survived",
            source_file="pages/target.py",
        ),
    ]
    mutation_type_by_key = {
        "pages.target.x_alpha__mutmut_1": "comparison-boundary-shift",
        "pages.target.x_alpha__mutmut_2": "comparison-boundary-shift",
        "pages.target.x_beta__mutmut_1": "boolean-operator-swap",
    }
    cluster_globals["mutation_type_for_record"] = (
        lambda record, _cache: mutation_type_by_key[record.key]
    )

    clusters = clusters_func(records, Path("/repo"))

    assert clusters[0]["function_key"] == "pages.target.x_alpha"
    assert clusters[0]["mutation_type"] == "comparison-boundary-shift"
    assert clusters[0]["survivor_count"] == 2
    assert clusters[1]["function_key"] == "pages.target.x_beta"
    assert clusters[1]["mutation_type"] == "boolean-operator-swap"
    assert clusters[1]["survivor_count"] == 1


def test_build_report_emits_parameterized_plan_for_selected_source():
    ns = _load_mutant_triage_namespace()
    build_report = ns["build_report"]
    build_globals = build_report.__globals__

    records = [
        _record(
            key="pages.target.x_alpha__mutmut_1",
            base_key="pages.target.x_alpha",
            module="pages.target",
            function="alpha",
            status="survived",
            source_file="pages/target.py",
        ),
        _record(
            key="pages.target.x_alpha__mutmut_2",
            base_key="pages.target.x_alpha",
            module="pages.target",
            function="alpha",
            status="survived",
            source_file="pages/target.py",
        ),
        _record(
            key="pages.no_tests.x_gamma__mutmut_1",
            base_key="pages.no_tests.x_gamma",
            module="pages.no_tests",
            function="gamma",
            status="no_tests",
            source_file="pages/no_tests.py",
        ),
    ]
    mutation_type_by_key = {
        "pages.target.x_alpha__mutmut_1": "comparison-boundary-shift",
        "pages.target.x_alpha__mutmut_2": "comparison-boundary-shift",
    }

    build_globals["collect_mutants"] = lambda _root: records
    build_globals["load_tests_by_function"] = lambda _root: {
        "pages.target.x_alpha": ["tests/test_target.py::test_alpha_matrix"],
    }
    build_globals["mutation_type_for_record"] = (
        lambda record, _cache: mutation_type_by_key.get(record.key)
    )
    build_globals["surviving_mutant_source_rows"] = lambda _survivors, _root: []

    report = build_report(root=Path("/repo"), source_query=None, top_sources=5)

    assert report["selection_mode"] == "top-survived"
    assert report["selected_query"] == "pages/target.py"
    assert report["surviving_count"] == 2
    assert report["survivor_clusters"][0]["survivor_count"] == 2
    assert report["parameterized_test_plan"][0]["function_key"] == (
        "pages.target.x_alpha"
    )
    assert report["parameterized_test_plan"][0]["survivor_count"] == 2
