"""Tests for the `scripts/mutant_type_report` mutation-type analyzer."""

from __future__ import annotations

import json
from pathlib import Path

from tests.script_namespace_loader import load_script_namespace


def _load_mutant_type_report_namespace() -> dict:
    return load_script_namespace("mutant_type_report", start_path=__file__)


def test_classify_mutation_detects_lookup_argument_changes():
    ns = _load_mutant_type_report_namespace()
    classify_mutation = ns["classify_mutation"]

    original_source = "def x__mutmut_orig():\n    row = payload.get('row')\n"
    mutant_source = "def x__mutmut_1():\n    row = payload.get('ROW')\n"

    assert (
        classify_mutation(original_source, mutant_source)
        == "lookup-argument-mutation"
    )


def test_build_report_summarizes_types_and_cosmetic_hotspots(tmp_path):
    ns = _load_mutant_type_report_namespace()
    build_report = ns["build_report"]

    mutants_py_file = tmp_path / "mutants" / "sample.py"
    mutants_py_file.parent.mkdir(parents=True)
    mutants_py_file.write_text(
        "\n".join(
            [
                "def x_story__mutmut_orig():",
                "    token = payload.get('row')",
                "    return token",
                "",
                "def x_story__mutmut_1():",
                "    token = payload.get('ROW')",
                "    return token",
                "",
                "def x_story__mutmut_2():",
                "    token = payload.get('row')",
                "    return 'XXXX'",
            ]
        )
    )
    meta_path = mutants_py_file.with_suffix(".py.meta")
    meta_path.write_text(
        json.dumps(
            {
                "exit_code_by_key": {
                    "visualization.storybook_demo.x_story__mutmut_1": 0,
                    "visualization.storybook_demo.x_story__mutmut_2": 0,
                }
            }
        )
    )

    report = build_report(root=tmp_path, target_statuses={"survived"}, top=5)

    mutation_type_counts = {
        row["mutation_type"]: row["count"] for row in report["mutation_types"]
    }
    assert mutation_type_counts["lookup-argument-mutation"] == 1
    assert mutation_type_counts["string-literal-mutation"] == 1

    assert report["source_type_hotspots"][0]["source_file"] == (
        "visualization/storybook_demo.py"
    )
    assert report["likely_cosmetic_hotspots"] != []
