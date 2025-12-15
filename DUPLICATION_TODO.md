# Code Duplication to Remediate

Pylint R0801 warnings (duplicate-code) identified on 2025-12-10.
Current code rating: 9.93/10

## Test Fixture Duplication

### High Priority - Large Test Duplicates (90+ lines)
1. **test_ideal_affinity.py:35-128** vs **test_ideal_affinity_algorithm.py:212-305**
   - 93 lines of duplicate test setup/fixtures

2. **test_affinity_network.py:42-94** vs **test_ideal_affinity_algorithm.py:104-202**
   - 52+ lines of duplicate affinity calculation setup

### Medium Priority - Test Helper Duplicates (20-45 lines)
3. **test_affinity_groups.py:20-44** vs **test_affinity_network.py:116-140**
   - Edge iteration pattern

4. **test_commit_messages_for_file.py:12-33** vs **test_git_file_pair.py:13-34**
   - Commit message setup

5. **affinity_analysis.py:126-147** vs **test_ideal_affinity_algorithm.py:74-89**
   - Affinity calculation logic duplicated in tests

6. **affinity_analysis.py:110-125** vs **test_ideal_affinity_algorithm.py:62-73**
   - Threshold configuration duplicated

### Low Priority - Small Test Duplicates (8-12 lines)
7. **test_affinity_network.py:44-52** vs **test_ideal_affinity_algorithm.py:39-47**
   - `defaultdict(float)` affinity initialization

8. **test_affinity_network.py:56-64** vs **test_ideal_affinity_algorithm.py:47-55**
   - `defaultdict(float)` file_total_affinity initialization

9. **test_ideal_affinity_algorithm.py:118-126** vs **test_node_calculation_functions.py:30-38**
   - file_total_affinity setup

10. **test_ideal_affinity.py:137-145** vs **test_ideal_affinity_algorithm.py:315-323**
    - TEST_DATA_DIR mkdir pattern

11. **test_ideal_affinity.py:25-34** vs **test_ideal_affinity_algorithm.py:202-211**
    - test_periods list configuration

## Visualization Duplication

### Network Graph & Word Frequency Overlap
12. **network_graph.py:289-314** vs **word_frequency.py:28-43**
    - xref="paper" layout configuration (15+ lines)

13. **test_affinity_network.py:98-106** vs **word_frequency.py:28-36**
    - xref="paper" annotation setup

14. **test_affinity_network.py:216-227** vs **network_graph.py:366-389**
    - title_font configuration

### Node Trace Duplication
15. **test_affinity_network.py:142-147** vs **network_graph.py:395-400**
    - Empty x/y array initialization

16. **test_affinity_network.py:181-186** vs **network_graph.py:484-490**
    - node_traces.append pattern

17. **test_affinity_network.py:158-163** vs **network_graph.py:509-515**
    - node_x/node_y initialization

18. **test_affinity_network.py:189-194** vs **network_graph.py:539-545**
    - node_x list initialization

19. **test_affinity_network.py:169-174** vs **network_graph.py:525-530**
    - x=node_x trace configuration

20. **test_affinity_network.py:201-206** vs **network_graph.py:555-560**
    - x=node_x trace configuration (duplicate pattern)

## DataFrame Builder Duplication

21. **dataframe_builder.py:56-65** vs **test_figure_builder.py:18-27**
    - Column definition structure

22. **dataframe_builder.py:57-65** vs **test_dataframe_builder.py:22-30**
    - Column names list

23. **test_dataframe_builder.py:22-34** vs **test_figure_builder.py:19-28**
    - Column structure in tests

## Algorithm Duplication

24. **affinity_calculator.py:26-70** vs **test_ideal_affinity_algorithm.py:40-47**
    - Commit iteration logic

25. **test_affinity_network.py:183-189** vs **test_exclude_one_element_communities.py:27-33**
    - Community ID iteration pattern

## Remediation Strategy

1. **Extract shared test fixtures** - Create `tests/fixtures/affinity_fixtures.py` for common setup
2. **Create test helpers** - Move repeated patterns to `tests/helpers/`
3. **Extract layout configs** - Create `visualization/layouts.py` for shared plotly configurations
4. **Refactor node trace logic** - Extract common node trace patterns in network_graph.py
5. **Review algorithm/test overlap** - Ensure test logic doesn't duplicate production code
