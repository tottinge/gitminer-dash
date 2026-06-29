"""Shared path bootstrap helpers for executable scripts in this directory."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_on_sys_path(path: Path) -> Path:
    """Ensure a resolved path is present on ``sys.path``."""
    resolved_path = path.resolve()
    path_text = str(resolved_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)
    return resolved_path


def add_script_dir(script_file: str) -> Path:
    """Ensure the invoking script directory is on ``sys.path``."""
    script_path = Path(script_file).resolve()
    return ensure_on_sys_path(script_path.parent)


def add_project_root(script_file: str) -> Path:
    """Ensure the repository root for the invoking script is on ``sys.path``."""
    script_path = Path(script_file).resolve()
    return ensure_on_sys_path(script_path.parents[1])
