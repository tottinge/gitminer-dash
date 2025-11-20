from unittest.mock import patch

import pytest

import data


@pytest.mark.parametrize("input_path,expected_name", [
    ("/path/to/stand_up/", "Stand Up"),
    ("/path/to/stand_up", "Stand Up"),
    ("/path/to/poo/", "Poo"),
    ("/path/to/Poo/", "Poo"),
    ("/path/to/my-project/", "My Project"),
    ("/path/to/my-project", "My Project"),
    ("/path/to/my.project/", "My Project"),
    ("/path/to/my.project", "My Project"),
    # Multiple separators and empty components
    ("/path//to///my_repo//", "My Repo"),
    ("/path/to//empty//components/test-repo", "Test Repo"),
    # No separators (single directory name)
    ("single-repo", "Single Repo"),
    ("standalone_project", "Standalone Project"),
    # Path ending with separator
    ("/usr/local/projects/cool-app/", "Cool App"),
    ("/home/user/repos/data.analysis/", "Data Analysis"),
])
def test_get_repo_name(input_path, expected_name):
    data.get_repo_name.cache_clear()
    data.get_repo.cache_clear()
    with patch('sys.argv', ['script_name', input_path]):
        assert data.get_repo_name() == expected_name
