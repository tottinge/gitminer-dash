from pathlib import Path

from utils.dependency_policy import (
    collect_policy_violations,
    normalize_dependency_name,
    validate_dependency_policy,
)


def test_normalize_dependency_name_with_extras_and_markers():
    spec = "Foo_Bar[dev]>=1.2; python_version < '3.11'"
    assert normalize_dependency_name(spec) == "foo-bar"


def test_collect_policy_violations_flags_optional_dev_and_overlap():
    pyproject_data = {
        "project": {
            "dependencies": ["dash>=3.2.0", "ruff>=0.14.2"],
            "optional-dependencies": {"dev": ["ruff>=0.14.2"]},
        },
        "dependency-groups": {
            "dev": ["ruff>=0.14.2", "black>=25.9.0"],
        },
    }

    violations = collect_policy_violations(pyproject_data)

    assert len(violations) == 2
    assert any("optional-dependencies.dev" in message for message in violations)
    assert any("Duplicate packages" in message for message in violations)


def test_collect_policy_violations_accepts_single_dev_source():
    pyproject_data = {
        "project": {
            "dependencies": ["dash>=3.2.0", "networkx>=3.4.2"],
        },
        "dependency-groups": {
            "dev": ["ruff>=0.14.2", "black>=25.9.0"],
        },
    }

    violations = collect_policy_violations(pyproject_data)

    assert violations == []


def test_validate_dependency_policy_reads_pyproject_file(tmp_path: Path):
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        "\n".join(
            [
                "[project]",
                "name = 'example'",
                "version = '0.1.0'",
                "dependencies = ['dash>=3.2.0', 'networkx>=3.4.2']",
                "",
                "[dependency-groups]",
                "dev = ['ruff>=0.14.2']",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assert validate_dependency_policy(pyproject_path) == []
