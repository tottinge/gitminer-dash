# Contract tests to ensure pages use the global store's begin/end when querying commits

# Ensure project imports work
from tests import setup_path
setup_path()

from datetime import datetime
import types
import pytest

# Build a fixed store payload
STORE = {
    "period": "Last 60 days",
    "begin": "2025-09-01T00:00:00+00:00",
    "end":   "2025-10-31T23:59:59+00:00",
}

@pytest.fixture
def capture_commits_call(monkeypatch):
    import data
    called = {}
    def _capture(begin, end):
        called["begin"] = begin
        called["end"] = end
        return []
    monkeypatch.setattr(data, "commits_in_period", _capture)
    # Some pages access repo; stub safely
    monkeypatch.setattr(data, "get_repo", lambda: types.SimpleNamespace())
    return called

@pytest.mark.parametrize("target, build_args", [
    ("pages.most_committed.populate_graph", lambda: (STORE,)),
    ("pages.conventional.update_conventional_table", lambda: (None, STORE)),
    ("pages.diff_summary.update_graph", lambda: (None, STORE)),
    ("pages.merges.update_merge_graph", lambda: (1, STORE)),
    ("pages.codelines.update_code_lines_graph", lambda: (1, STORE)),
    ("pages.strongest_pairings.handle_period_selection", lambda: (STORE,)),
])
def test_page_uses_store_begin_end(target, build_args, capture_commits_call, monkeypatch):
    # Import target function dynamically
    module_name, func_name = target.rsplit(".", 1)
    mod = __import__(module_name, fromlist=[func_name])
    fn = getattr(mod, func_name)

    # Extra stubs per page where needed
    if module_name == "pages.most_committed":
        monkeypatch.setattr(mod, "calculate_file_commit_frequency", lambda *a, **k: [
            {"filename": "(none)", "count": 0, "avg_changes": 0, "total_change": 0, "percent_change": 0}
        ])

    # Call function
    args = build_args()
    fn(*args)

    # Assert captured begin/end match store exactly
    assert capture_commits_call["begin"].isoformat() == STORE["begin"]
    assert capture_commits_call["end"].isoformat() == STORE["end"]


def test_affinity_groups_uses_store_begin_end(capture_commits_call, monkeypatch):
    # Patch heavy functions to no-op figure
    from pages import affinity_groups as ag
    monkeypatch.setattr(ag, "calculate_ideal_affinity", lambda commits_data, **kw: (0.2, 0, 0))
    monkeypatch.setattr(ag, "create_file_affinity_network", lambda commits_data, **kw: (None, None, {}))
    import plotly.graph_objects as go
    monkeypatch.setattr(ag, "create_network_visualization", lambda G, communities: go.Figure())

    # Call
    ag.update_file_affinity_graph(STORE, 50, 0.2)

    # Assert store begin/end were used
    assert capture_commits_call["begin"].isoformat() == STORE["begin"]
    assert capture_commits_call["end"].isoformat() == STORE["end"]
