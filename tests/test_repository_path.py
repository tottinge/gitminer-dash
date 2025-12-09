from tests import setup_path

setup_path()
import sys

import pytest


def test_repository_path_with_arg():
    sys.argv = ["app.py", "."]
    import data

    repo_path = data.repository_path()
    assert repo_path is not None


def test_repository_path_without_arg():
    if "data" in sys.modules:
        del sys.modules["data"]
    sys.argv = ["app.py"]
    import data

    with pytest.raises(ValueError):
        repo_path = data.repository_path()


if __name__ == "__main__":
    pytest.main([__file__])
