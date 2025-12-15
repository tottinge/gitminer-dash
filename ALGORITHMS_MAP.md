# Algorithms Directory Map

Quick reference for finding and reusing code in `algorithms/`. Organized by functionality to help avoid duplication.

## File Affinity Analysis
**Purpose**: Identify files that change together frequently

- `affinity_calculator.py` - Core algorithm: calculates affinity scores for file pairs based on co-occurrence in commits
  - `calculate_affinities()` - Main entry point, returns dict of (file1, file2) → affinity score
  - `_calculate_affinities_from_commits()` - Inner loop logic, reusable for custom affinity calculations
  
- `affinity_analysis.py` - Advanced analysis and threshold optimization
  - `get_file_total_affinities()` - Aggregate affinity scores per file
  - `get_top_files_by_affinity()` - Filter to N most connected files
  - `calculate_ideal_affinity()` - Auto-tune threshold for target node count

## Commit Chain Analysis
**Purpose**: Analyze sequences of related commits and their temporal patterns

- `chain_models.py` - Data models (ChainData, ClampedChain, TimelineRow)
- `chain_analyzer.py` - Extract chain metadata from NetworkX graphs
- `chain_traversal.py` - Build commit chains following parent relationships
- `chain_clamper.py` - Constrain chains to specific time periods
- `chain_layout.py` - Position chains for visualization (vertical stacking)
- `commit_graph.py` - Build NetworkX graphs from commit data

## File Change Statistics
**Purpose**: Calculate metrics about file modifications over time

- `file_changes.py` - Core file change analysis
  - `file_changes_over_period()` - Stats for single file: commits, avg changes, size deltas
  - `files_changes_over_period()` - Batch version, returns dict[filename → FileChangeStats]
  - `FileChangeStats` - NamedTuple with structured results

## Commit Frequency & Top Files
**Purpose**: Find most-changed files and their statistics

- `commit_frequency.py` - Identify frequently modified files
  - `calculate_file_commit_frequency()` - Returns top N files with commit counts and change stats
  - Internally uses `file_changes.py` for enrichment

## Conventional Commits
**Purpose**: Parse and categorize commit messages by intent

- `conventional_commits.py` - Parse conventional commit format (feat:, fix:, etc.)
  - `normalize_intent()` - Map commit prefix to standard category
  - `prepare_changes_by_date()` - Group commits by date and type
  - Standard categories: feat, fix, refactor, test, docs, chore, perf, etc.

## Time-Based Analysis
**Purpose**: Aggregate commits by time periods

- `weekly_commits.py` - Group commits by week
  - `get_week_ending()` - Calculate week boundary (Monday-Sunday)
  - `calculate_weekly_commits()` - Full weekly aggregation with stats
  - `extract_commit_details()` - Format single commit for display

- `diff_analysis.py` - Daily diff statistics
  - `get_diffs_in_period()` - Break down insertions/deletions into modifications vs net changes

## Text Analysis
**Purpose**: Analyze text content of commits

- `word_frequency.py` - Count word occurrences in commit messages
  - `calculate_word_frequency()` - With stop word filtering and min length
  - `STOP_WORDS` - Configurable exclusion list

## Data Transformation
**Purpose**: Convert analysis results to visualization-ready formats

- `dataframe_builder.py` - Build pandas DataFrames
  - `create_timeline_dataframe()` - Convert TimelineRows to typed DataFrame with datetime handling
  - Handles timezone-aware datetime → pandas datetime64[ns] conversion

- `figure_builder.py` - Build Plotly figures (check for visualization helpers)

## Utility Patterns
**Purpose**: Small reusable utilities

- `change_series.py` - Generate change series between commits
- `sorted_tags.py` - Retrieve recent tags from repository
- `stacking.py` - Generic stacking/layout algorithms

## Common Patterns to Reuse

### Iterator Safety
Many functions use `ensure_list()` from `utils.git` to handle iterators safely for re-use

### Date Range Filtering
Most functions accept `begin`/`end` or `start`/`end` datetime parameters with sensible defaults

### Repository Access
Functions accept optional `repo` parameter, defaulting to `get_repo()` from `utils.git`

### Error Handling
File operations typically have try/except with logging and return zero/empty defaults

### Named Tuples for Results
`FileChangeStats`, `ChainData`, `ClampedChain`, `TimelineRow` - prefer immutable results with slots

## Before Implementing New Features

1. **Check affinity/frequency modules** if analyzing file relationships
2. **Check chain modules** if working with commit sequences or timelines
3. **Check file_changes.py** if calculating any file-level statistics
4. **Check weekly_commits.py or diff_analysis.py** if aggregating by time
5. **Check dataframe_builder.py** if converting to pandas for visualization
