#!/usr/bin/env python3
"""Validate dependency policy conventions in `pyproject.toml`."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    from utils.dependency_policy import run_dependency_policy_check

    return run_dependency_policy_check(PROJECT_ROOT / "pyproject.toml")


if __name__ == "__main__":
    raise SystemExit(main())
