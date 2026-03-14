from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

DEPENDENCY_NAME_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")


def normalize_dependency_name(spec: str) -> str:
    """Extract and normalize the package name from a dependency spec."""
    raw_spec = spec.strip()
    if not raw_spec:
        return ""

    match = DEPENDENCY_NAME_RE.match(raw_spec)
    if not match:
        return ""

    return match.group(1).lower().replace("_", "-")


def _dependency_names(raw_dependencies: list[str] | None) -> set[str]:
    if not raw_dependencies:
        return set()

    names = set()
    for dependency in raw_dependencies:
        name = normalize_dependency_name(dependency)
        if name:
            names.add(name)
    return names


def load_pyproject_data(pyproject_path: Path) -> dict[str, Any]:
    """Load `pyproject.toml` as a dictionary."""
    with pyproject_path.open("rb") as pyproject_file:
        return tomllib.load(pyproject_file)


def collect_policy_violations(pyproject_data: dict[str, Any]) -> list[str]:
    """Return dependency policy violations found in pyproject data."""
    project = pyproject_data.get("project", {})
    dependency_groups = pyproject_data.get("dependency-groups", {})
    optional_dependencies = project.get("optional-dependencies", {})

    violations: list[str] = []

    if (
        isinstance(optional_dependencies, dict)
        and "dev" in optional_dependencies
    ):
        violations.append(
            "Use `dependency-groups.dev` only; "
            "`project.optional-dependencies.dev` is not allowed."
        )

    runtime_dependencies = _dependency_names(project.get("dependencies"))
    dev_dependencies = _dependency_names(dependency_groups.get("dev"))
    overlap = sorted(runtime_dependencies & dev_dependencies)
    if overlap:
        violations.append(
            "Duplicate packages across `project.dependencies` and "
            f"`dependency-groups.dev`: {', '.join(overlap)}"
        )

    return violations


def validate_dependency_policy(pyproject_path: Path) -> list[str]:
    """Validate dependency policy rules for `pyproject.toml`."""
    pyproject_data = load_pyproject_data(pyproject_path)
    return collect_policy_violations(pyproject_data)


def run_dependency_policy_check(pyproject_path: Path) -> int:
    """Run dependency policy validation and print a concise report."""
    violations = validate_dependency_policy(pyproject_path)
    if not violations:
        print("Dependency policy check passed.")
        return 0

    print("Dependency policy check failed:")
    for violation in violations:
        print(f"- {violation}")
    return 1
