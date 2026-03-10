"""Shared models and helpers for mutmut analysis scripts in `scripts/`.

This module centralizes artifact discovery, mutant parsing, grouping, and
status weighting so command scripts can share one implementation.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

EXIT_CODE_STATUS = {
    1: "killed",
    0: "survived",
    2: "timeout",
    33: "no_tests",
    -9: "timeout",
    -11: "crash",
}

DEFAULT_STATUS_WEIGHTS = {
    "no_tests": 5,
    "survived": 4,
    "timeout": 3,
    "crash": 1,
    "killed": 0,
}

DEFAULT_STATUS_SEVERITY = {
    "killed": 0,
    "crash": 1,
    "timeout": 2,
    "survived": 3,
    "no_tests": 4,
}


@dataclass(frozen=True)
class MutantRecord:
    key: str
    base_key: str
    module: str
    mangled_function: str
    function: str
    status: str
    exit_code: int
    meta_path: Path
    source_path: Path


def status_for_exit_code(exit_code: int) -> str:
    return EXIT_CODE_STATUS.get(exit_code, f"code_{exit_code}")


def weight_for_status(
    status: str, weights: dict[str, int] | None = None
) -> int:
    mapping = weights or DEFAULT_STATUS_WEIGHTS
    if status in mapping:
        return mapping[status]
    if status.startswith("code_"):
        return 2
    return 1


def severity_for_status(
    status: str, mapping: dict[str, int] | None = None
) -> int:
    severity = mapping or DEFAULT_STATUS_SEVERITY
    if status in severity:
        return severity[status]
    if status.startswith("code_"):
        return 2
    return 2


def normalize_function_name(mangled_name: str) -> str:
    cleaned = mangled_name
    if cleaned.startswith("x_"):
        cleaned = cleaned[2:]
    return cleaned.replace("ǁ", ".")


def split_mutant_key(key: str) -> tuple[str, str, str]:
    base_key = key.split("__mutmut_")[0]
    module, mangled_function = base_key.rsplit(".", 1)
    function = normalize_function_name(mangled_function)
    return base_key, module, function


def source_path_for_module(root: Path, module: str) -> Path:
    return root / f"{module.replace('.', '/')}.py"


def find_meta_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.py.meta"))


def find_stats_files(root: Path) -> list[Path]:
    return sorted(root.rglob("mutmut-stats.json"))


def parse_meta_file(meta_path: Path, root: Path) -> list[MutantRecord]:
    try:
        payload = json.loads(meta_path.read_text())
    except (OSError, json.JSONDecodeError):
        return []

    exit_code_by_key = payload.get("exit_code_by_key", {})
    records: list[MutantRecord] = []
    for key, exit_code in exit_code_by_key.items():
        base_key, module, function = split_mutant_key(key)
        records.append(
            MutantRecord(
                key=key,
                base_key=base_key,
                module=module,
                mangled_function=base_key.rsplit(".", 1)[1],
                function=function,
                status=status_for_exit_code(exit_code),
                exit_code=exit_code,
                meta_path=meta_path,
                source_path=source_path_for_module(root, module),
            )
        )
    return records


def collect_mutants(root: Path) -> list[MutantRecord]:
    records: list[MutantRecord] = []
    for meta_path in find_meta_files(root):
        records.extend(parse_meta_file(meta_path, root))
    return records


def summarize_statuses(records: list[MutantRecord]) -> Counter:
    return Counter(record.status for record in records)


def group_by_function(
    records: list[MutantRecord],
) -> dict[str, list[MutantRecord]]:
    grouped: dict[str, list[MutantRecord]] = defaultdict(list)
    for record in records:
        grouped[record.base_key].append(record)
    return dict(grouped)


def group_by_module(records: list[MutantRecord]) -> dict[str, list[MutantRecord]]:
    grouped: dict[str, list[MutantRecord]] = defaultdict(list)
    for record in records:
        grouped[record.module].append(record)
    return dict(grouped)


def load_tests_by_function(root: Path) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)

    for stats_path in find_stats_files(root):
        try:
            payload = json.loads(stats_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue

        tests_by_function = payload.get("tests_by_mangled_function_name", {})
        for function_key, tests in tests_by_function.items():
            for test_name in tests:
                if test_name not in seen[function_key]:
                    merged[function_key].append(test_name)
                    seen[function_key].add(test_name)
    return dict(merged)
