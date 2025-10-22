# Git Miner Dashboard Visualizations

This document provides an overview of the various visualizations available in the Git Miner Dashboard application.

## Most Committed

This visualization shows the most frequently committed files in your repository over different time periods (30, 60, or 90 days). It displays a bar chart of the files that have been modified most often, helping you identify which parts of your codebase are changing most frequently. This can be useful for identifying areas that might need refactoring or more attention.

## Change Types By Tag

This visualization shows information about tagged versions in your repository, if there are tags present. It provides insights into the types of changes that occurred between tagged versions. Note that this visualization may not be useful for repositories without tags.

## Codelines

Codelines attempts to visualize how many change sets are ongoing at a time, and whether they are branched or not. This visualization has proven helpful for understanding the parallel development activities in a repository.

## Conventional

This visualization displays stacked bars of change types, assuming that contributors are using conventional commits. It categorizes commits based on their types (e.g., feat, fix, docs, etc.) and shows their distribution. This visualization is only useful if the repository follows conventional commit practices; otherwise, it provides little value.

## Diff Summary

Diff Summary provides a visualization of code churn or "thrash" in the repository. It helps identify areas of the codebase that experience frequent changes, which might indicate design issues or areas that need refactoring.

## Merges

The Merges visualization shows all merges in your repository. Each merge is represented visually with size and color indicating:
- The number of lines changed
- The number of files affected

This helps identify significant integration points in your development history.

## Strongest Pairings

Strongest Pairings shows files that have the strongest affinity to each other, where affinity is based on how often they are committed together. The strength of the pairing is inversely proportional to the total number of files in those commits.

For example:
- Committing just files A & B together creates a strong pairing
- Committing 1000 files (e.g., after reformatting everything) creates weak pairings between all files

The visualization aggregates these pairings over a period to help identify:
- Potential "shotgun surgery" (changes scattered across the codebase)
- Files that frequently change together, suggesting they might be tightly coupled

Positive case: A source file and its test file (e.g., X and test_X) having strong affinity, indicating good test coverage.

Negative case: Files from different modules (e.g., moduleA/X and moduleB/Y) changing together frequently without tests, suggesting problematic cross-module dependencies.