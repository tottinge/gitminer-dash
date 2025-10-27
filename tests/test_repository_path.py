
# Import from tests package to set up path
from tests import setup_path
setup_path()  # This ensures we can import modules from the project root
import sys

import pytest


def test_repository_path_with_arg():
    print("Testing repository_path() with command-line argument...")

    # Set sys.argv with a repository path
    sys.argv = ["app.py", "."]  # Use current directory as repository path

    # Import data module after setting sys.argv
    import data

    repo_path = data.repository_path()
    print(f"Repository path: {repo_path}")
    print("Test PASSED: repository_path() returned a value with command-line argument")
    assert repo_path is not None


def test_repository_path_without_arg():
    print("\nTesting repository_path() without command-line argument...")

    # Reset modules to ensure clean import
    if 'data' in sys.modules:
        del sys.modules['data']

    # Set sys.argv without a repository path
    sys.argv = ["app.py"]

    # Import data module after setting sys.argv
    import data

    with pytest.raises(ValueError):
        repo_path = data.repository_path()


if __name__ == "__main__":
    pytest.main([__file__])
