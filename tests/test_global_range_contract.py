from tests import setup_path

setup_path()
import types

import networkx as nx
import pytest

STORE = {
    "period": "Last 60 days",
    "begin": "2025-09-01T00:00:00+00:00",
    "end": "2025-10-31T23:59:59+00:00",
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
    monkeypatch.setattr(data, "get_repo", lambda: types.SimpleNamespace())
    return called


@pytest.mark.parametrize(
    "target, build_args",
    [
        ("pages.most_committed.populate_graph", lambda: (STORE,)),
        ("pages.conventional.update_conventional_table", lambda: (None, STORE)),
        ("pages.diff_summary.update_graph", lambda: (None, STORE)),
        ("pages.merges.update_merge_graph", lambda: (1, STORE)),
        ("pages.codelines.update_code_lines_graph", lambda: (1, STORE)),
        ("pages.strongest_pairings.handle_period_selection", lambda: (STORE,)),
    ],
)
def test_page_uses_store_begin_end(
    target, build_args, capture_commits_call, monkeypatch
):
    # Page modules call `dash.register_page` at import-time; make this test
    # independent of Dash app instantiation / page registry global state.
    import dash

    monkeypatch.setattr(dash, "register_page", lambda *a, **k: None)

    (module_name, func_name) = target.rsplit(".", 1)
    mod = __import__(module_name, fromlist=[func_name])
    fn = getattr(mod, func_name)
    if module_name == "pages.most_committed":
        monkeypatch.setattr(
            mod,
            "calculate_file_commit_frequency",
            lambda *a, **k: [
                {
                    "filename": "(none)",
                    "count": 0,
                    "avg_changes": 0,
                    "total_change": 0,
                    "percent_change": 0,
                }
            ],
        )
    args = build_args()
    fn(*args)
    assert capture_commits_call["begin"].isoformat() == STORE["begin"]
    assert capture_commits_call["end"].isoformat() == STORE["end"]


def test_affinity_groups_uses_store_begin_end(
    capture_commits_call, monkeypatch
):
    """Ensure affinity_groups uses the store's begin/end when querying commits.

    This test is intentionally focused on the contract that
    `update_file_affinity_graph` passes the correct date range from the
    global store into `data.commits_in_period`. The heavy computation and
    visualization functions are stubbed out to avoid expensive work.
    """
    import dash

    monkeypatch.setattr(dash, "register_page", lambda *a, **k: None)

    from pages import affinity_groups as ag

    mock_graph = nx.Graph()
    monkeypatch.setattr(
        ag,
        "create_file_affinity_network",
        lambda commits_data, **kw: (mock_graph, [], {}),
    )

    import plotly.graph_objects as go

    monkeypatch.setattr(
        ag,
        "create_network_visualization",
        lambda G, communities: go.Figure(),
    )

    ag.update_file_affinity_graph(STORE, 50, 0.2)
    assert capture_commits_call["begin"].isoformat() == STORE["begin"]
    assert capture_commits_call["end"].isoformat() == STORE["end"]
