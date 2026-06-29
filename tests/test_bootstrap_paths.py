"""Tests for `scripts/bootstrap_paths.py`."""

import sys
from pathlib import Path

from scripts.bootstrap_paths import (
    add_project_root,
    add_script_dir,
    ensure_on_sys_path,
)


def test_ensure_on_sys_path_inserts_missing_path_at_front(
    monkeypatch, tmp_path: Path
):
    target = tmp_path / "example" / "path"
    monkeypatch.setattr(sys, "path", ["/existing/entry"])

    resolved_target = ensure_on_sys_path(target)

    assert resolved_target == target.resolve()
    assert sys.path[0] == str(target.resolve())


def test_ensure_on_sys_path_does_not_duplicate_existing_path(
    monkeypatch, tmp_path: Path
):
    target = tmp_path / "example" / "path"
    resolved_target = str(target.resolve())
    monkeypatch.setattr(sys, "path", [resolved_target, "/existing/entry"])

    ensure_on_sys_path(target)

    assert sys.path.count(resolved_target) == 1


def test_add_script_dir_uses_invoking_script_directory(
    monkeypatch, tmp_path: Path
):
    script_file = tmp_path / "repo" / "scripts" / "tool.py"
    expected_script_dir = script_file.parent.resolve()
    monkeypatch.setattr(sys, "path", ["/existing/entry"])

    script_dir = add_script_dir(str(script_file))

    assert script_dir == expected_script_dir
    assert sys.path[0] == str(expected_script_dir)


def test_add_project_root_uses_script_parent_repository(
    monkeypatch, tmp_path: Path
):
    script_file = tmp_path / "repo" / "scripts" / "tool.py"
    expected_project_root = script_file.parents[1].resolve()
    monkeypatch.setattr(sys, "path", ["/existing/entry"])

    project_root = add_project_root(str(script_file))

    assert project_root == expected_project_root
    assert sys.path[0] == str(expected_project_root)
