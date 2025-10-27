# Git Miner Dashboard Algorithms

This directory contains algorithm implementations for the Git Miner Dashboard project.

## File Change Statistics

The `file_changes.py` module provides functions for calculating statistics about changes to files in a Git repository over a period of time.

### FileChangeStats

A named tuple that represents statistics about changes to a file:

- `file_path`: Path to the file
- `commits`: Number of commits that modified the file
- `avg_changes`: Average number of lines changed per commit
- `total_change`: Absolute difference between original and final file size
- `percent_change`: Percentage change in file size

### file_changes_over_period

Calculates statistics about changes to a single file over a period of time.

```python
from datetime import datetime, timedelta
from algorithms.file_changes import file_changes_over_period

# Calculate statistics for a file over the last 30 days
commits, avg_changes, total_change, percent_change = file_changes_over_period(
    target_file='path/to/file.py',
    start=datetime.now() - timedelta(days=30),
    end=datetime.now()
)

print(f"Number of commits: {commits}")
print(f"Average lines changed per commit: {avg_changes:.2f}")
print(f"Total change in file size: {total_change} bytes")
print(f"Percentage change in file size: {percent_change:.2f}%")
```

### files_changes_over_period

Calculates statistics about changes to multiple files over a period of time.

```python
from datetime import datetime, timedelta
from algorithms.file_changes import files_changes_over_period

# Calculate statistics for multiple files over the last 30 days
results = files_changes_over_period(
    target_files=['path/to/file1.py', 'path/to/file2.py', 'path/to/file3.py'],
    start=datetime.now() - timedelta(days=30),
    end=datetime.now()
)

# Process the results
for file_path, stats in results.items():
    print(f"\nFile: {file_path}")
    print(f"Number of commits: {stats.commits}")
    print(f"Average lines changed per commit: {stats.avg_changes:.2f}")
    print(f"Total change in file size: {stats.total_change} bytes")
    print(f"Percentage change in file size: {stats.percent_change:.2f}%")
```

## Other Algorithms

### change_series

The `change_series.py` module provides a function for generating a series of changes between Git commits.

### sorted_tags

The `sorted_tags.py` module provides a function for retrieving the most recent tags from a Git repository.