# Mocking in Pytest: Fixing the date_utils Tests

## The Problem

The tests in `test_date_utils.py` were failing when run with pytest as part of the full test suite, but passing when run individually with `python test_date_utils.py`. The error message was:

```
ImportError: module date_utils not in sys.modules
```

This error occurred because the tests were using unittest's `@patch('date_utils.datetime')` decorator to mock the datetime module, but when pytest was collecting and running the tests as part of the full suite, the module import paths were different, causing the patching to fail.

## Root Cause Analysis

The issue stemmed from several factors:

1. **String-based patching**: The unittest.mock `@patch` decorator was using a string path `'date_utils.datetime'` to specify what to patch. This approach is fragile because it depends on how the module is imported and the context in which the tests are run.

2. **Module import order**: When pytest runs the full test suite, it imports modules in a different order than when running a single test file directly. This can cause issues with patching, especially when using string-based paths.

3. **Module reloading**: The test was trying to reload the `date_utils` module in the `setUp` method, but this approach doesn't work well with pytest's test collection and execution model.

## The Solution

We rewrote the tests to use pytest's native fixtures and monkeypatching approach instead of unittest.mock. The key changes were:

1. **Use pytest fixtures**: We created a custom fixture called `mock_datetime` that uses pytest's `monkeypatch` fixture to replace `date_utils.datetime` with a mock object.

2. **Direct attribute patching**: Instead of using string-based patching, we directly patched the attribute on the module object: `monkeypatch.setattr(date_utils, 'datetime', MockDatetime)`.

3. **Simplified test structure**: We converted the unittest.TestCase class to individual pytest test functions, which work better with pytest's test discovery and execution.

4. **Special handling for edge cases**: We added special handling for the 'Ever' test case, which needed to mock the datetime constructor.

## Best Practices for Mocking in Pytest

Based on this experience, here are some best practices for mocking in pytest:

1. **Use pytest's monkeypatch fixture**: Instead of unittest.mock's `@patch` decorator, use pytest's `monkeypatch` fixture, which is designed to work with pytest's test collection and execution model.

2. **Patch objects directly**: Instead of using string-based patching, patch objects directly using `monkeypatch.setattr(object, attribute, value)`.

3. **Create custom fixtures**: Create custom fixtures for complex mocking scenarios to make your tests more readable and maintainable.

4. **Be careful with module reloading**: Avoid reloading modules in tests, as it can cause issues with pytest's test collection and execution.

5. **Test both individually and as part of the suite**: Make sure your tests pass both when run individually and as part of the full test suite.

## Example: Before and After

### Before (using unittest.mock):

```python
@patch('date_utils.datetime')
def test_calculate_date_range_7_days(self, mock_datetime):
    # Configure mock
    mock_datetime.today.return_value = MOCK_DATE
    mock_datetime.astimezone = lambda x: x
    
    # Call function under test
    begin, end = date_utils.calculate_date_range('Last 7 days')
    
    # Assertions
    self.assertEqual(end.date(), MOCK_DATE.date())
    self.assertEqual(begin.date(), datetime(2025, 10, 15).date())
    self.assertEqual((end.date() - begin.date()).days, 7)
```

### After (using pytest fixtures):

```python
def test_calculate_date_range_7_days(mock_datetime):
    # Call function under test
    begin, end = date_utils.calculate_date_range('Last 7 days')
    
    # Assertions
    assert end.date() == MOCK_DATE.date()
    assert begin.date() == datetime(2025, 10, 15).date()
    assert (end.date() - begin.date()).days == 7
```

With the fixture defined as:

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
    
    # Return the mock for use in tests that need special handling
    return MockDatetime
```

## Conclusion

When working with pytest, it's best to use pytest's native fixtures and monkeypatching approach instead of unittest.mock, especially for complex mocking scenarios. This approach is more reliable and works better with pytest's test collection and execution model.

By following these best practices, we were able to fix the failing tests and ensure they pass both when run individually and as part of the full test suite.