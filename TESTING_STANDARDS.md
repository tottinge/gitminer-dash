# Testing Standards for Git Miner Dashboard

This document establishes the testing standards for the Git Miner Dashboard project. These standards ensure that tests are reliable, maintainable, and effective at catching issues early.

## Core Testing Principles

### The FIRST Principles

Our testing approach follows the FIRST principles, as described by Tim Ottinger and Jeff Langr in their article ["Unit Tests are FIRST"](https://pragprog.com/magazines/2012-01/unit-tests-are-first):

- **Fast**: Tests should run quickly to provide immediate feedback and encourage developers to run them frequently. Fast tests allow developers to run them often during development, ensuring issues are caught early.

- **Isolated/Independent**: Tests should not depend on each other and should be able to run in any order. Each test should set up its own test data and assertions, and should not rely on side effects from other tests.

- **Repeatable**: Tests should produce the same results regardless of the environment or when they are run. They should not depend on specific environmental conditions, network availability, or time-dependent factors.

- **Self-validating**: Tests should automatically determine if they pass or fail without requiring human interpretation. Each test should have clear assertions that unambiguously indicate success or failure.

- **Timely**: Tests should be written at the appropriate time (usually before or alongside the production code). Writing tests early helps design more testable code and ensures functionality is verified from the start.

These principles guide our specific testing standards described below.

### 1. Tests Must Run in Suite

All tests must be designed to run and pass as part of the full test suite. This means:

- Tests should run successfully when executed with `pytest` from the project root directory
- Tests should not depend on being run in a specific order
- Tests should clean up after themselves and not leave side effects that could affect other tests

**Why this matters**: Tests that only run individually but fail in the suite are not reliable for continuous integration and can hide issues that only appear when components interact.

**Example of good practice**: The tests in `tests/test_date_utils.py` use pytest fixtures to mock dependencies, allowing them to run both individually and as part of the suite:

```python
@pytest.fixture
def mock_datetime(monkeypatch):
    """Fixture to mock datetime.today() to return a fixed date."""
    class MockDatetime:
        @classmethod
        def today(cls):
            return MOCK_DATE
        
        @staticmethod
        def astimezone(dt):
            return dt
    
    # Apply the monkeypatch to replace datetime in date_utils
    monkeypatch.setattr(date_utils, 'datetime', MockDatetime)
    
    return MockDatetime
```

### 2. Tests Should Have the Smallest Possible Scope

Tests should be focused on testing a specific piece of functionality with minimal dependencies. This means:

- Each test function should test one specific behavior or aspect
- Tests should mock or stub external dependencies when possible
- Tests should be independent of each other

**Why this matters**: Small, focused tests make it easier to:
- Identify what's broken when a test fails
- Understand what functionality a test is verifying
- Maintain tests as the codebase evolves

**Example of good practice**: The tests in `tests/test_date_utils.py` are small and focused, with each test function testing a specific aspect of the `calculate_date_range` function:

```python
def test_calculate_date_range_7_days(mock_datetime):
    """Test calculate_date_range with 'Last 7 days'."""
    # Call function under test
    begin, end = date_utils.calculate_date_range('Last 7 days')
    
    # Assertions
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 10, 15).date()
    assert (end.date() - begin.date()).days == 7
```

### 3. Tests Should Use Controlled Data

Tests should use controlled, predictable data rather than depending on external systems or repositories. This means:

- Use mock objects or fixtures to simulate external dependencies
- Store test data in the repository (e.g., in JSON files) rather than generating it dynamically
- Make tests deterministic by controlling random factors and time-dependent behavior

**Why this matters**: Tests with controlled data are:
- Repeatable, producing the same results each time they run
- Isolated from external changes that could break the tests
- Faster and more reliable, as they don't depend on external systems

**Example of good practice**: The tests in `tests/test_affinity_callback.py` use controlled test data from JSON files:

```python
def load_commits_data(period):
    """
    Load commit data from a file.
    
    Args:
        period: Time period string
        
    Returns:
        List of simplified commit objects
    """
    filename = f"commits_{period.replace(' ', '_').lower()}.json"
    filepath = TEST_DATA_DIR / filename
    
    if not filepath.exists():
        print(f"No saved data found for {period}")
        return []
    
    with open(filepath, 'r') as f:
        commits = json.load(f)
    
    print(f"Loaded {len(commits)} commits from {filepath}")
    return [create_mock_commit(commit) for commit in commits]
```

## Best Practices

### Use pytest Fixtures for Setup and Teardown

Pytest fixtures provide a clean, modular way to set up test dependencies and clean up afterward. They are more flexible and maintainable than traditional setup/teardown methods.

```python
@pytest.fixture
def mock_commits():
    """Fixture to provide mock commit data."""
    return [
        create_mock_commit({
            'hash': '123456',
            'message': 'Test commit',
            'date': '2025-10-23T13:53:00',
            'files': ['file1.py', 'file2.py']
        })
    ]
```

### Use Descriptive Test Names and Docstrings

Test names should clearly describe what they're testing, and docstrings should provide additional context if needed.

```python
def test_calculate_date_range_with_empty_string_uses_default_period(mock_datetime):
    """Test that calculate_date_range uses the default period (30 days) when given an empty string."""
    # Test implementation...
```

### Mock External Dependencies

Use mocking to isolate the code under test from external dependencies. This makes tests faster, more reliable, and focused on the specific functionality being tested.

```python
@patch('data.commits_in_period')
def test_callback_with_mock_data(mock_commits_in_period):
    # Configure the mock
    mock_commits_in_period.return_value = mock_commits
    
    # Test implementation...
```

### Test Edge Cases and Error Conditions

Don't just test the happy path. Include tests for edge cases, boundary conditions, and error handling.

```python
def test_calculate_date_range_with_invalid_period_uses_default():
    """Test that calculate_date_range handles invalid period strings gracefully."""
    # Test implementation...
```

## Implementing These Standards

When writing new tests or modifying existing ones:

1. Ensure they run successfully with `pytest` from the project root
2. Keep tests focused on specific functionality
3. Use controlled test data rather than depending on external repositories
4. Follow the best practices outlined in this document
5. Apply the FIRST principles (Fast, Isolated, Repeatable, Self-validating, Timely)

By adhering to these standards, we can maintain a reliable, maintainable test suite that helps catch issues early and supports the ongoing development of the Git Miner Dashboard.

## References

- Ottinger, T., & Langr, J. (2012). Unit Tests are FIRST. PragPub Magazine, January 2012. Retrieved from https://pragprog.com/magazines/2012-01/unit-tests-are-first