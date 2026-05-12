from pathlib import Path

from utils.dependency_policy import (
    collect_policy_violations,
    normalize_dependency_name,
    run_dependency_policy_check,
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


def test_run_dependency_policy_check_reports_success(
    monkeypatch, capsys, tmp_path: Path
):
    pyproject_path = tmp_path / "pyproject.toml"
    captured_paths: list[Path] = []

    def fake_validate_dependency_policy(path: Path) -> list[str]:
        captured_paths.append(path)
        return []

    monkeypatch.setattr(
        "utils.dependency_policy.validate_dependency_policy",
        fake_validate_dependency_policy,
    )

    exit_code = run_dependency_policy_check(pyproject_path)
    output = capsys.readouterr().out

    assert exit_code == 0
    assert captured_paths == [pyproject_path]
    assert output.strip() == "Dependency policy check passed."


def test_run_dependency_policy_check_reports_violations(
    monkeypatch, capsys, tmp_path: Path
):
    pyproject_path = tmp_path / "pyproject.toml"
    violations = [
        "first policy violation",
        "second policy violation",
    ]

    monkeypatch.setattr(
        "utils.dependency_policy.validate_dependency_policy",
        lambda _path: violations,
    )

    exit_code = run_dependency_policy_check(pyproject_path)
    output_lines = capsys.readouterr().out.strip().splitlines()

    assert exit_code == 1
    assert output_lines[0] == "Dependency policy check failed:"
    assert output_lines[1] == "- first policy violation"
    assert output_lines[2] == "- second policy violation"
