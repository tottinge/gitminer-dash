from tests import setup_path

setup_path()

import sys

import pytest

import repository_context as repo_context


def test_repository_path_with_arg(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["app.py", "."])

    repo_path = repo_context.repository_path()

    assert repo_path is not None


def test_repository_path_without_arg(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["app.py"])

    with pytest.raises(ValueError):
        repo_context.repository_path()


if __name__ == "__main__":
    pytest.main([__file__])
