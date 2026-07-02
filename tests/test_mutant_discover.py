"""Tests for the `scripts/mutant_discover` reporting script."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from tests.script_namespace_loader import load_script_namespace


def _load_mutant_discover_namespace() -> dict:
    return load_script_namespace("mutant_discover", start_path=__file__)


def _record(module: str, status: str) -> SimpleNamespace:
    return SimpleNamespace(module=module, status=status)


def test_build_report_tracks_total_and_surviving_top_modules():
    ns = _load_mutant_discover_namespace()
    root = Path("/repo")

    records = [
        *[_record("module.alpha", "killed") for _ in range(6)],
        _record("module.alpha", "survived"),
        *[_record("module.beta", "no_tests") for _ in range(4)],
        _record("module.beta", "killed"),
        *[_record("module.gamma", "survived") for _ in range(2)],
    ]

    build_report_globals = ns["build_report"].__globals__
    build_report_globals["collect_mutants"] = lambda _: records
    build_report_globals["find_meta_files"] = lambda _: [root / "one.py.meta"]
    build_report_globals["find_stats_files"] = lambda _: [
        root / "mutmut-stats.json"
    ]

    report = ns["build_report"](root=root, top=2)

    assert report["top_modules"] == [
        {"module": "module.alpha", "count": 7},
        {"module": "module.beta", "count": 5},
    ]
    assert report["top_surviving_modules"] == [
        {"module": "module.beta", "count": 4},
        {"module": "module.gamma", "count": 2},
    ]


def test_print_text_report_survivors_only_uses_surviving_module_counts(capsys):
    ns = _load_mutant_discover_namespace()
    report = {
        "root": "/repo",
        "meta_files": [],
        "stats_files": [],
        "mutant_count": 100,
        "status_counts": {"killed": 95, "survived": 3, "no_tests": 2},
        "top_modules": [{"module": "module.total", "count": 100}],
        "top_surviving_modules": [{"module": "module.survivor", "count": 5}],
    }

    ns["print_text_report"](report, survivors_only=True)
    output = capsys.readouterr().out

    assert "Top modules by surviving mutant count:" in output
    assert "module.survivor: 5" in output
    assert "module.total: 100" not in output
