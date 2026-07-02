"""Shared helpers for loading executable script namespaces in tests."""

from __future__ import annotations

import runpy
from pathlib import Path

from git import InvalidGitRepositoryError, Repo


def repository_root_for_path(start_path: str | Path) -> Path:
    """Resolve repository root using GitPython parent-directory search."""
    search_path = Path(start_path).resolve()
    try:
        repo = Repo(search_path, search_parent_directories=True)
    except InvalidGitRepositoryError as exc:
        msg = f"Could not locate git repository for {search_path}"
        raise FileNotFoundError(msg) from exc

    working_tree_dir = repo.working_tree_dir
    if not working_tree_dir:
        msg = f"Resolved repository has no working tree: {search_path}"
        raise FileNotFoundError(msg)
    return Path(working_tree_dir).resolve()


def load_script_namespace(script_name: str, *, start_path: str | Path) -> dict:
    """Load a scripts/<name> executable file as a Python namespace dict."""
    repo_root = repository_root_for_path(start_path)
    script_path = repo_root / "scripts" / script_name
    if not script_path.exists():
        msg = f"Could not locate scripts/{script_name} at {script_path}"
        raise FileNotFoundError(msg)
    return runpy.run_path(str(script_path))
