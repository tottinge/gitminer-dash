"""Shared models and helpers for mutmut analysis scripts in `scripts/`.

This module centralizes artifact discovery, mutant parsing, grouping, and
status weighting so command scripts can share one implementation.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Collection
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

DEFAULT_RANK_TARGET_STATUSES = frozenset({"survived"})
DEFAULT_TRIAGE_TARGET_STATUSES = frozenset({"no_tests", "survived", "timeout"})
MUTANT_NAME_PATTERN = re.compile(r"^(?P<base>.+)__mutmut_(?P<suffix>orig|\d+)$")
DEF_PATTERN = re.compile(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)
PARAMETERIZED_DIMENSIONS_BY_MUTATION_TYPE = {
    "comparison-boundary-shift": [
        "inputs exactly at, below, and above each boundary",
        "zero, one, and many-item boundary cardinalities",
    ],
    "boolean-operator-swap": [
        "truth-table combinations for each predicate input",
        "cases where only one predicate flips the outcome",
    ],
    "lookup-argument-mutation": [
        "canonical keys plus casing/alias variants",
        "missing key fallback behavior",
    ],
    "arithmetic-operator-swap": [
        "positive, zero, and negative value combinations",
        "known exact totals from representative fixtures",
    ],
    "return-value-mutation": [
        "exact return values for canonical and edge inputs",
        "shape and type invariants on returned payloads",
    ],
    "statement-deletion-or-simplification": [
        "required fields are present and populated",
        "multi-step behavior where dropping logic changes outcome",
    ],
    "statement-addition-or-expansion": [
        "minimal inputs that should not trigger extra behavior",
        "assert no accidental extra side effects/fields",
    ],
    "assignment-or-expression-mutation": [
        "cross-check derived values against known-good fixtures",
        "orthogonal combinations of inputs affecting the expression",
    ],
    "string-literal-mutation": [
        "canonical label/token values from user-visible contract",
    ],
    "no-text-change": [
        "no additional parameterization needed; inspect for equivalence",
    ],
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


def parse_target_statuses(
    raw_statuses: str | None,
    default_statuses: Collection[str],
    include_crash: bool = False,
) -> set[str]:
    if raw_statuses:
        statuses = {
            value.strip() for value in raw_statuses.split(",") if value.strip()
        }
    else:
        statuses = set(default_statuses)
    if include_crash:
        statuses.add("crash")
    return statuses


def candidate_test_file_for_module(module_name: str) -> str:
    return f"tests/test_{module_name.split('.')[-1]}.py"


def classify_mutation(original_source: str, mutant_source: str) -> str:
    if original_source == mutant_source:
        return "no-text-change"
    if "XXXX" in mutant_source or "XX" in mutant_source:
        return "string-literal-mutation"

    if (
        ".get(" in original_source
        and ".get(" in mutant_source
        and original_source != mutant_source
    ):
        return "lookup-argument-mutation"

    if (" and " in original_source and " or " in mutant_source) or (
        " or " in original_source and " and " in mutant_source
    ):
        return "boolean-operator-swap"

    if (
        (" >= " in original_source and " > " in mutant_source)
        or (" > " in original_source and " >= " in mutant_source)
        or (" <= " in original_source and " < " in mutant_source)
        or (" < " in original_source and " <= " in mutant_source)
    ):
        return "comparison-boundary-shift"

    if (
        (" + " in original_source and " - " in mutant_source)
        or (" - " in original_source and " + " in mutant_source)
        or (" * " in original_source and " / " in mutant_source)
        or (" / " in original_source and " * " in mutant_source)
    ):
        return "arithmetic-operator-swap"

    original_returns = [
        line.strip()
        for line in original_source.splitlines()
        if line.strip().startswith("return ")
    ]
    mutant_returns = [
        line.strip()
        for line in mutant_source.splitlines()
        if line.strip().startswith("return ")
    ]
    if (
        original_returns
        and mutant_returns
        and original_returns != mutant_returns
    ):
        return "return-value-mutation"

    if len(mutant_source) < len(original_source):
        return "statement-deletion-or-simplification"
    if len(mutant_source) > len(original_source):
        return "statement-addition-or-expansion"
    return "assignment-or-expression-mutation"


def load_function_sources(mutants_py_file: Path) -> dict[str, str]:
    source_text = mutants_py_file.read_text()
    matches = list(DEF_PATTERN.finditer(source_text))
    function_sources: dict[str, str] = {}
    for index, match in enumerate(matches):
        function_name = match.group(1)
        start = match.start()
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(source_text)
        )
        function_sources[function_name] = source_text[start:end]
    return function_sources


def mutation_type_for_record(
    record: MutantRecord, source_cache: dict[Path, dict[str, str]]
) -> str | None:
    mutants_py_file = record.meta_path.with_suffix("")
    if mutants_py_file not in source_cache:
        try:
            source_cache[mutants_py_file] = load_function_sources(
                mutants_py_file
            )
        except (FileNotFoundError, OSError, SyntaxError):
            source_cache[mutants_py_file] = {}
    function_sources = source_cache[mutants_py_file]

    mutant_function_name = record.key.rsplit(".", 1)[-1]
    match = MUTANT_NAME_PATTERN.match(mutant_function_name)
    if not match:
        return None
    base_name = match.group("base")
    original_function_name = f"{base_name}__mutmut_orig"
    if (
        original_function_name not in function_sources
        or mutant_function_name not in function_sources
    ):
        return None

    return classify_mutation(
        function_sources[original_function_name],
        function_sources[mutant_function_name],
    )


def parameterized_dimensions_for_mutation_type(
    mutation_type: str,
) -> list[str]:
    return PARAMETERIZED_DIMENSIONS_BY_MUTATION_TYPE.get(
        mutation_type,
        [
            "cover happy-path, edge-case, and invalid-input variants "
            "with exact assertions"
        ],
    )


def split_mutant_key(key: str) -> tuple[str, str, str]:
    base_key = key.split("__mutmut_")[0]
    module, mangled_function = base_key.rsplit(".", 1)
    function = normalize_function_name(mangled_function)
    return base_key, module, function


def source_path_for_module(root: Path, module: str) -> Path:
    return root / f"{module.replace('.', '/')}.py"


def _is_project_mutation_artifact(path: Path, root: Path) -> bool:
    root_abs = root.resolve()
    path_abs = path.resolve()
    try:
        relative_path = path_abs.relative_to(root_abs)
    except ValueError:
        return False
    return bool(relative_path.parts) and relative_path.parts[0] == "mutants"


def find_meta_files(root: Path) -> list[Path]:
    return [
        path
        for path in sorted(root.rglob("*.py.meta"))
        if _is_project_mutation_artifact(path, root)
    ]


def find_stats_files(root: Path) -> list[Path]:
    return [
        path
        for path in sorted(root.rglob("mutmut-stats.json"))
        if _is_project_mutation_artifact(path, root)
    ]


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


def group_by_module(
    records: list[MutantRecord],
) -> dict[str, list[MutantRecord]]:
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


def relative_path_str(path: Path, root: Path) -> str:
    root_abs = root.resolve()
    path_abs = path.resolve()
    try:
        return path_abs.relative_to(root_abs).as_posix()
    except ValueError:
        return path_abs.as_posix()


def normalize_source_query(source_query: str) -> str:
    return source_query.strip().replace("\\", "/")


def source_matches_query(
    source_path: Path, root: Path, source_query: str
) -> bool:
    query = normalize_source_query(source_query)
    if not query:
        return False

    source_rel = relative_path_str(source_path, root)
    source_name = Path(source_rel).name
    query_path = Path(query)
    query_name = query_path.name

    if query_path.is_absolute():
        return source_path.resolve() == query_path.resolve()

    normalized_query = query.lstrip("./")
    if "/" in normalized_query:
        return source_rel == normalized_query or source_rel.endswith(
            f"/{normalized_query}"
        )

    return source_name == query_name or source_rel == normalized_query


def filter_mutants_for_source(
    records: list[MutantRecord], root: Path, source_query: str
) -> list[MutantRecord]:
    return [
        record
        for record in records
        if source_matches_query(record.source_path, root, source_query)
    ]


def surviving_mutants_for_source(
    records: list[MutantRecord], root: Path, source_query: str
) -> list[MutantRecord]:
    return [
        record
        for record in filter_mutants_for_source(records, root, source_query)
        if record.status == "survived"
    ]
