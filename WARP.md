# Warp Project Rules

## Project Overview
gitminer-dash is a Python Dash application for visualizing git repository metrics and analytics. The project emphasizes test-driven development, incremental changes, and clean architecture.

## Testing Requirements
- **Test Command**: Always run tests from repository root using `uv run pytest`
- **Test-First Development**: 
  - Unit tests must be written and pass for all custom code
  - Tests run after every change (not just once after all changes)
  - No task is complete until all tests pass successfully
  - Cannot commit unless all tests are running and reporting success
- **Test Standards**: 
  - Follow FIRST principles (Fast, Isolated, Repeatable, Self-validating, Timely)
  - Tests must run in suite, not just individually
  - Avoid order-dependent tests:
    - Do not mutate process-global state (e.g. `sys.argv`, `sys.modules`, env vars) unless using `pytest`'s `monkeypatch` (or context-managed `patch`) so changes are automatically restored.
    - Avoid deleting modules from `sys.modules` in tests.
    - When importing Dash page modules in unit tests, stub `dash.register_page` (or instantiate a Dash app) so tests do not depend on page-registry global state or import order.
  - Use smallest possible scope with mocked dependencies
  - Use controlled test data from JSON fixtures
  - Prefer TAP-format reporting (via pytest plugins) for a clear results tree when available

## Development Workflow
- **Small Incremental Changes**: 
  - Keep workload small - make only small changes between commits
  - If scope becomes large, recommend hard reset and restart with smaller units of work
  - Small, frequent commits over large batches
- **Pre-commit Process**: 
  - Run `./prepare` script before commits (pulls, syncs, runs tests)
  - All tests must pass before commit
  - Pre-commit hook automatically synced from `utils/pre-commit`
- **No Auto-commit**: Never commit unless explicitly requested by user

## Code Organization
- **Architecture**: Clean separation of concerns
  - `algorithms/` - Pure computation and analysis logic
  - `pages/` - Dash page components and callbacks
  - `visualization/` - Plotting and visual rendering
  - `utils/` - Shared utilities
  - `tests/` - Comprehensive test coverage
- **Refactoring Pattern**: Extract logic → test → integrate

## Commit Standards
- **Format**: Use conventional commits (feat, fix, refactor, test, optimize, etc.)
- **Style**: 
  - Keep messages concise and to one line when possible
  - Avoid comprehensive multi-line commit messages
- **Prerequisites**: All tests must pass before any commit

## Code Quality Standards
- **Code Virtues**: Follow Industrial Logic's 7 Code Virtues (see CODE_VIRTUES.md)
  - Priority order: Working > Unique > Simple > Clear > Easy > Developed > Brief
- **Language Standards**: 
  - Python 3.10+ with type hints
  - Ruff for linting (line-length: 100)
  - Test files allow assertions and specific lint exceptions
- **Environment**: Use `uv` for package management and virtual environment

## UI Component Development
- **Dash-First UI**: 
  - UI is built as Dash pages and visualization components under `pages/` and `visualization/`.
  - New UI behaviour should have tests in `tests/` (layout, visualization, or interaction) before or alongside integration into the app.
  - Use `uv run pytest` (and the pre-commit hook) to run interaction and visualization tests before any commit.
  - Scripts must never auto-commit UI components or tests; commits are always explicit developer actions.

## Project Scripts
- `./onboard` - Setup environment (Python 3.10+, uv, venv, dependencies)
- `./run <repo-path>` - Run the application with specified git repository
- `./prepare` - Pre-commit preparation (pull, sync, test)
- `./check` - Quick validation checks
- `./run_with_coverage.sh` - Run tests with coverage reporting

## Dependencies
- Core: dash, gitpython, networkx, pandas, plotly
- Testing: pytest with controlled fixtures
- Dev: ruff, mypy, pylint, coverage, bandit

## Performance Considerations
- Application is not turbo-fast; users may need to wait for data loading
- Recent optimizations focus on caching and memory efficiency (slots, trimmed attributes)
