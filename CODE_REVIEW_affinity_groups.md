# Code Review: pages/affinity_groups.py

## Critical Issue: update_file_affinity_graph (lines 113-182)

### Problem: Overly Broad Try/Except Block
The function wraps 70 lines of logic in a single try/except, forcing the exception handlers to inspect error messages to determine what went wrong. This violates the principle of narrow, focused error handling.

**Current structure:**
- Lines 114-159: All business logic in one try block
- Lines 160-168: ValueError handler that inspects error message strings
- Lines 169-175: Different ValueError handler 
- Lines 176-182: Generic Exception handler

### Root Cause: Single Callback Doing Multiple Jobs

The callback has at least 4 distinct responsibilities:
1. **Data retrieval**: Parse date range, fetch commits
2. **Affinity calculation**: Cache lookup/computation
3. **Graph construction**: Create network with communities
4. **Data transformation**: Build graph_data structure for storage

### Recommended Refactoring

#### Option A: Extract Pure Functions (Preferred)

Break into testable, focused functions:

```python
def _get_cached_affinities(starting, ending, commits_data):
    """Get or compute affinities for date range."""
    cache_key = (starting.isoformat(), ending.isoformat())
    affinities = _AFFINITY_CACHE.get(cache_key)
    if affinities is None:
        affinities = calculate_affinities(commits_data)
        _AFFINITY_CACHE[cache_key] = affinities
    return affinities


def _build_graph_data_store(G, communities):
    """Transform graph into serializable store format."""
    graph_data = {"nodes": {}, "communities": {}}
    
    for node in G.nodes():
        node_community = G.nodes[node].get("community", 0)
        commit_count = G.nodes[node].get("commit_count", 0)
        degree = G.degree(node)
        
        connected_communities = set()
        for neighbor in G.neighbors(node):
            neighbor_community = G.nodes[neighbor].get("community", 0)
            connected_communities.add(neighbor_community)
        
        graph_data["nodes"][node] = {
            "commit_count": commit_count,
            "degree": degree,
            "community": node_community,
            "connected_communities": sorted(list(connected_communities)),
        }
    
    for i, community in enumerate(communities):
        graph_data["communities"][i] = list(community)
    
    return graph_data


@callback(
    Output("id-file-affinity-graph", "figure"),
    Output("id-graph-data-store", "data"),
    [
        Input("global-date-range", "data"),
        Input("id-affinity-node-slider", "value"),
        Input("id-affinity-min-slider", "value"),
    ],
)
def update_file_affinity_graph(store_data, max_nodes: int, min_affinity: float):
    try:
        starting, ending = date_utils.parse_date_range_from_store(store_data)
    except ValueError as e:
        return _create_error_figure("Invalid date range", str(e)), {}
    
    try:
        commits_data = ensure_list(data.commits_in_period(starting, ending))
    except ValueError as e:
        if "No repository path provided" in str(e):
            return _create_repo_error_figure(), {}
        raise
    
    affinities = _get_cached_affinities(starting, ending, commits_data)
    
    try:
        G, communities, stats = create_file_affinity_network(
            commits_data,
            min_affinity=min_affinity,
            max_nodes=max_nodes,
            precomputed_affinities=affinities,
        )
    except Exception as e:
        return _create_error_figure("Graph generation failed", str(e)), {}
    
    graph_data = _build_graph_data_store(G, communities)
    figure = create_network_visualization(G, communities)
    
    return figure, graph_data


def _create_repo_error_figure():
    """Create figure for missing repository path."""
    return create_empty_figure(
        "No repository path provided. Please run the application with a repository path as a command-line argument.\\n\\nExample: python app.py /path/to/your/git/repository",
        title="File Affinity Network - Repository Path Required",
    )


def _create_error_figure(context: str, error_msg: str):
    """Create figure for general errors."""
    return create_empty_figure(
        f"{context}: {error_msg}",
        title="File Affinity Network - Error",
    )
```

**Benefits:**
- Each function has one clear purpose
- Try/except blocks are narrow and focused
- Error handlers don't need to inspect error messages
- Functions are independently testable
- No conditional logic in exception handlers

#### Option B: Split into Multiple Callbacks

Create separate callbacks for different concerns:
- One for date range validation
- One for data fetching
- One for graph generation

**Trade-off:** More callbacks mean more Dash complexity and potential re-rendering issues.

## Secondary Issues

### 1. get_commits_for_group_files (lines 185-229)

**Issues:**
- Complex nested logic mixing iteration, filtering, and transformation
- Direct git operations in presentation layer
- No error handling for git operations

**Recommendation:** Extract to `algorithms/commit_filter.py` as domain logic, not UI code.

### 2. Cache Management

**Current:** Module-level dict with no eviction policy
```python
_AFFINITY_CACHE: dict[tuple[str, str], dict[tuple[str, str], float]] = {}
```

**Issues:**
- Unbounded growth
- No cache invalidation
- Thread-unsafe (if Dash uses multiple workers)

**Recommendation:** Use `functools.lru_cache` or `cachetools.TTLCache` with size limits.

### 3. Magic String Parsing (lines 256-259)

```python
if "<br>" in node_name:
    node_name = node_name.split("<br>")[0].replace("File: ", "")
```

Parsing HTML from tooltip text is brittle. Better: use `customdata` in plotly traces.

### 4. Direct Git Operations in Callbacks

Lines 200-208 perform git diff operations synchronously in the callback. This blocks the UI thread.

**Recommendation:** Precompute commit metadata or move to background task.

## Structural Recommendation

Consider this organization:

```
pages/affinity_groups.py
├── Layout definition (lines 25-101) ✓ Good
├── Callback: update_file_affinity_graph
│   ├── Parse inputs (narrow try/except)
│   ├── Call: _get_cached_affinities()
│   ├── Call: _create_network_graph()
│   ├── Call: _build_graph_data_store()
│   └── Return results
├── Callback: update_node_details_table
│   ├── Parse click data
│   ├── Call: algorithms.commit_filter.get_group_commits()
│   └── Return table data
└── Helper functions (private, testable)
```

## Testing Gap

No tests exist for this file. After refactoring, add:
- `test_get_cached_affinities()` - cache behavior
- `test_build_graph_data_store()` - data transformation
- `test_error_handling()` - each error path separately

## Priority

**High**: Refactor `update_file_affinity_graph` 
**Medium**: Extract git operations from `get_commits_for_group_files`
**Low**: Replace magic string parsing with customdata
