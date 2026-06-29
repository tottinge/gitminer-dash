#!/usr/bin/env python3
"""Validate dependency policy conventions in `pyproject.toml`."""

try:
    from bootstrap_paths import add_project_root
except ModuleNotFoundError:  # pragma: no cover
    from scripts.bootstrap_paths import add_project_root

PROJECT_ROOT = add_project_root(__file__)


def main() -> int:
    from utils.dependency_policy import run_dependency_policy_check

    return run_dependency_policy_check(PROJECT_ROOT / "pyproject.toml")


if __name__ == "__main__":
    raise SystemExit(main())
