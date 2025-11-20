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
])
def test_get_repo_name(input_path, expected_name):
    data.get_repo_name.cache_clear()
    data.get_repo.cache_clear()
    with patch('sys.argv', ['script_name', input_path]):
        assert data.get_repo_name() == expected_name
