"""Requirement-based tests for pages.affinity_groups_service."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import networkx as nx
import pytest

from pages.affinity_groups_service import (
    build_graph_data_store,
    extract_clicked_node_name,
    files_in_clicked_community,
    generate_affinity_graph_result,
    generate_node_details_rows,
)


def test_build_graph_data_store_happy_path():
    """Happy path: output shape and key node/community fields are correct."""
    graph = nx.Graph()
    graph.add_node("api/a.py", community=0, commit_count=5)
    graph.add_node("api/b.py", community=0, commit_count=3)
    graph.add_node("ui/c.py", community=1, commit_count=8)
    graph.add_edge("api/a.py", "api/b.py")
    graph.add_edge("api/a.py", "ui/c.py")

    communities = [{"api/a.py", "api/b.py"}, {"ui/c.py"}]

    result = build_graph_data_store(graph, communities)

    assert set(result.keys()) == {"nodes", "communities"}
    assert set(result["nodes"]) == {"api/a.py", "api/b.py", "ui/c.py"}

    a_node = result["nodes"]["api/a.py"]
    assert a_node["commit_count"] == 5
    assert a_node["degree"] == 2
    assert a_node["community"] == 0
    assert a_node["connected_communities"] == [0, 1]

    assert set(result["communities"][0]) == {"api/a.py", "api/b.py"}
    assert set(result["communities"][1]) == {"ui/c.py"}


def test_build_graph_data_store_edge_cases():
    """Edge cases: defaults, deduped connected communities, and empty graph."""
    graph = nx.Graph()
    graph.add_node("no_attrs.py")
    graph.add_node("peer1.py", community=2)
    graph.add_node("peer2.py", community=2)
    graph.add_edge("no_attrs.py", "peer1.py")
    graph.add_edge("no_attrs.py", "peer2.py")

    result = build_graph_data_store(
        graph, [{"no_attrs.py", "peer1.py", "peer2.py"}]
    )

    node_data = result["nodes"]["no_attrs.py"]
    assert node_data["commit_count"] == 0
    assert node_data["community"] == 0
    assert node_data["degree"] == 2
    assert node_data["connected_communities"] == [2]

    empty_result = build_graph_data_store(nx.Graph(), [])
    assert empty_result == {"nodes": {}, "communities": {}}


@pytest.mark.parametrize(
    ("graph", "communities", "expected_exception"),
    [
        (None, [], AttributeError),
        (nx.Graph(), None, TypeError),
    ],
)
def test_build_graph_data_store_invalid_input(
    graph, communities, expected_exception
):
    """Invalid input: non-graph/invalid communities fail explicitly."""
    with pytest.raises(expected_exception):
        build_graph_data_store(graph, communities)


def test_generate_affinity_graph_result_happy_path():
    """Happy path wires parse/load/cache/build collaborators correctly."""
    starting = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ending = datetime(2026, 1, 31, tzinfo=timezone.utc)
    raw_commits = ("commit-a", "commit-b")
    normalized_commits = ["commit-a", "commit-b"]
    affinities = {("a.py", "b.py"): 0.7}
    expected_figure = object()
    expected_graph_data = {"nodes": {"a.py": {"community": 0}}}

    parse_date_range_fn = Mock(return_value=(starting, ending))
    commits_in_period_fn = Mock(return_value=raw_commits)
    ensure_list_fn = Mock(return_value=normalized_commits)
    get_cached_affinities_fn = Mock(return_value=affinities)
    create_network_fn = Mock()
    create_visualization_fn = Mock()
    create_repo_error_figure_fn = Mock()
    create_error_figure_fn = Mock()

    with patch(
        "pages.affinity_groups_service.build_affinity_graph_output",
        return_value=(expected_figure, expected_graph_data),
    ) as build_output_mock:
        result = generate_affinity_graph_result(
            store_data={"period": "Last 30 days"},
            max_nodes=50,
            min_affinity=0.2,
            parse_date_range_fn=parse_date_range_fn,
            commits_in_period_fn=commits_in_period_fn,
            ensure_list_fn=ensure_list_fn,
            get_cached_affinities_fn=get_cached_affinities_fn,
            create_network_fn=create_network_fn,
            create_visualization_fn=create_visualization_fn,
            create_repo_error_figure_fn=create_repo_error_figure_fn,
            create_error_figure_fn=create_error_figure_fn,
        )

    assert result == (expected_figure, expected_graph_data)
    commits_in_period_fn.assert_called_once_with(starting, ending)
    ensure_list_fn.assert_called_once_with(raw_commits)
    get_cached_affinities_fn.assert_called_once_with(
        starting, ending, normalized_commits
    )
    build_output_mock.assert_called_once_with(
        commits_data=normalized_commits,
        min_affinity=0.2,
        max_nodes=50,
        affinities=affinities,
        create_network_fn=create_network_fn,
        create_visualization_fn=create_visualization_fn,
    )
    create_repo_error_figure_fn.assert_not_called()
    create_error_figure_fn.assert_not_called()


def test_generate_affinity_graph_result_invalid_date_returns_error():
    """Date parse error returns invalid-date figure and empty graph data."""
    parse_date_range_fn = Mock(side_effect=ValueError("Bad date range"))
    commits_in_period_fn = Mock()
    ensure_list_fn = Mock()
    get_cached_affinities_fn = Mock()
    create_network_fn = Mock()
    create_visualization_fn = Mock()
    create_repo_error_figure_fn = Mock()
    create_error_figure_fn = Mock(return_value="error-figure")

    result = generate_affinity_graph_result(
        store_data={"period": "Invalid"},
        max_nodes=50,
        min_affinity=0.2,
        parse_date_range_fn=parse_date_range_fn,
        commits_in_period_fn=commits_in_period_fn,
        ensure_list_fn=ensure_list_fn,
        get_cached_affinities_fn=get_cached_affinities_fn,
        create_network_fn=create_network_fn,
        create_visualization_fn=create_visualization_fn,
        create_repo_error_figure_fn=create_repo_error_figure_fn,
        create_error_figure_fn=create_error_figure_fn,
    )

    assert result == ("error-figure", {})
    commits_in_period_fn.assert_not_called()
    ensure_list_fn.assert_not_called()
    get_cached_affinities_fn.assert_not_called()
    create_repo_error_figure_fn.assert_not_called()
    create_error_figure_fn.assert_called_once_with(
        "Invalid date range", "Bad date range"
    )


def test_generate_affinity_graph_result_missing_repo_returns_repo_error():
    """Missing repository path ValueError returns repository-required figure."""
    starting = datetime(2026, 2, 1, tzinfo=timezone.utc)
    ending = datetime(2026, 2, 2, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(starting, ending))
    commits_in_period_fn = Mock(
        side_effect=ValueError("No repository path provided for run")
    )
    ensure_list_fn = Mock()
    get_cached_affinities_fn = Mock()
    create_network_fn = Mock()
    create_visualization_fn = Mock()
    create_repo_error_figure_fn = Mock(return_value="repo-error-figure")
    create_error_figure_fn = Mock()

    result = generate_affinity_graph_result(
        store_data={"period": "Last 7 days"},
        max_nodes=30,
        min_affinity=0.1,
        parse_date_range_fn=parse_date_range_fn,
        commits_in_period_fn=commits_in_period_fn,
        ensure_list_fn=ensure_list_fn,
        get_cached_affinities_fn=get_cached_affinities_fn,
        create_network_fn=create_network_fn,
        create_visualization_fn=create_visualization_fn,
        create_repo_error_figure_fn=create_repo_error_figure_fn,
        create_error_figure_fn=create_error_figure_fn,
    )

    assert result == ("repo-error-figure", {})
    ensure_list_fn.assert_not_called()
    get_cached_affinities_fn.assert_not_called()
    create_error_figure_fn.assert_not_called()
    create_repo_error_figure_fn.assert_called_once_with()


def test_generate_affinity_graph_result_non_repo_error_is_reraised():
    """Non-repository ValueError from commit loader should propagate."""
    starting = datetime(2026, 2, 1, tzinfo=timezone.utc)
    ending = datetime(2026, 2, 2, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(starting, ending))
    commits_in_period_fn = Mock(side_effect=ValueError("Commit load failed"))
    ensure_list_fn = Mock()
    get_cached_affinities_fn = Mock()
    create_network_fn = Mock()
    create_visualization_fn = Mock()
    create_repo_error_figure_fn = Mock()
    create_error_figure_fn = Mock()

    with pytest.raises(ValueError, match="Commit load failed"):
        generate_affinity_graph_result(
            store_data={"period": "Last 7 days"},
            max_nodes=30,
            min_affinity=0.1,
            parse_date_range_fn=parse_date_range_fn,
            commits_in_period_fn=commits_in_period_fn,
            ensure_list_fn=ensure_list_fn,
            get_cached_affinities_fn=get_cached_affinities_fn,
            create_network_fn=create_network_fn,
            create_visualization_fn=create_visualization_fn,
            create_repo_error_figure_fn=create_repo_error_figure_fn,
            create_error_figure_fn=create_error_figure_fn,
        )

    create_repo_error_figure_fn.assert_not_called()
    create_error_figure_fn.assert_not_called()


def test_generate_affinity_graph_result_graph_failure_returns_error():
    """Graph build exception returns graph-generation-failed figure."""
    starting = datetime(2026, 3, 1, tzinfo=timezone.utc)
    ending = datetime(2026, 3, 3, tzinfo=timezone.utc)
    parse_date_range_fn = Mock(return_value=(starting, ending))
    commits_in_period_fn = Mock(return_value=[])
    ensure_list_fn = Mock(return_value=[])
    get_cached_affinities_fn = Mock(return_value={})
    create_network_fn = Mock()
    create_visualization_fn = Mock()
    create_repo_error_figure_fn = Mock()
    create_error_figure_fn = Mock(return_value="graph-error-figure")

    with patch(
        "pages.affinity_groups_service.build_affinity_graph_output",
        side_effect=RuntimeError("Graph exploded"),
    ):
        result = generate_affinity_graph_result(
            store_data={"period": "Last 3 days"},
            max_nodes=20,
            min_affinity=0.15,
            parse_date_range_fn=parse_date_range_fn,
            commits_in_period_fn=commits_in_period_fn,
            ensure_list_fn=ensure_list_fn,
            get_cached_affinities_fn=get_cached_affinities_fn,
            create_network_fn=create_network_fn,
            create_visualization_fn=create_visualization_fn,
            create_repo_error_figure_fn=create_repo_error_figure_fn,
            create_error_figure_fn=create_error_figure_fn,
        )

    assert result == ("graph-error-figure", {})
    create_repo_error_figure_fn.assert_not_called()
    create_error_figure_fn.assert_called_once_with(
        "Graph generation failed", "Graph exploded"
    )


def test_extract_clicked_node_name_handles_missing_and_plain_text():
    """Missing payloads return empty, plain labels are returned as-is."""
    assert extract_clicked_node_name(None) == ""
    assert extract_clicked_node_name({}) == ""
    assert (
        extract_clicked_node_name(
            {"points": [{"text": "src/feature/module.py"}]}
        )
        == "src/feature/module.py"
    )


def test_extract_clicked_node_name_parses_hover_payload_prefix():
    """Hover payload strips File: prefix and metadata suffix."""
    click_data = {
        "points": [{"text": "File: src/feature/module.py<br>Commits: 7"}]
    }
    assert extract_clicked_node_name(click_data) == "src/feature/module.py"


def test_files_in_clicked_community_handles_missing_inputs():
    """Guard clauses return empty list for invalid graph/node inputs."""
    assert files_in_clicked_community({}, "src/a.py") == []
    assert files_in_clicked_community({"nodes": {}}, "src/a.py") == []
    assert files_in_clicked_community({"nodes": {"src/a.py": {}}}, "") == []


def test_files_in_clicked_community_returns_matching_community_members():
    """Only files with the clicked node's community are returned."""
    graph_data = {
        "nodes": {
            "src/a.py": {"community": 1},
            "src/b.py": {"community": 1},
            "src/c.py": {"community": 2},
        }
    }
    assert files_in_clicked_community(graph_data, "src/a.py") == [
        "src/a.py",
        "src/b.py",
    ]


@pytest.mark.parametrize(
    ("click_data", "graph_data"),
    [
        (None, {"nodes": {"src/a.py": {"community": 0}}}),
        ({"points": [{"text": "src/a.py"}]}, None),
        ({"points": [{"text": "src/a.py"}]}, {}),
    ],
)
def test_generate_node_details_rows_returns_empty_for_missing_prerequisites(
    click_data, graph_data
):
    """Missing click or graph prerequisites return empty rows immediately."""
    extract_clicked_node_name_fn = Mock()
    files_in_clicked_community_fn = Mock()
    parse_date_range_fn = Mock()
    commits_in_period_fn = Mock()
    get_commits_for_group_files_fn = Mock()

    result = generate_node_details_rows(
        click_data=click_data,
        graph_data=graph_data,
        date_range_data={"period": "Last 30 days"},
        extract_clicked_node_name_fn=extract_clicked_node_name_fn,
        files_in_clicked_community_fn=files_in_clicked_community_fn,
        parse_date_range_fn=parse_date_range_fn,
        commits_in_period_fn=commits_in_period_fn,
        get_commits_for_group_files_fn=get_commits_for_group_files_fn,
    )

    assert result == []
    extract_clicked_node_name_fn.assert_not_called()
    files_in_clicked_community_fn.assert_not_called()
    parse_date_range_fn.assert_not_called()
    commits_in_period_fn.assert_not_called()
    get_commits_for_group_files_fn.assert_not_called()


def test_generate_node_details_rows_returns_empty_when_group_has_no_files():
    """No files for clicked node community short-circuits to empty rows."""
    click_data = {"points": [{"text": "src/a.py"}]}
    graph_data = {"nodes": {"src/a.py": {"community": 0}}}
    extract_clicked_node_name_fn = Mock(return_value="src/a.py")
    files_in_clicked_community_fn = Mock(return_value=[])
    parse_date_range_fn = Mock()
    commits_in_period_fn = Mock()
    get_commits_for_group_files_fn = Mock()

    result = generate_node_details_rows(
        click_data=click_data,
        graph_data=graph_data,
        date_range_data={"period": "Last 30 days"},
        extract_clicked_node_name_fn=extract_clicked_node_name_fn,
        files_in_clicked_community_fn=files_in_clicked_community_fn,
        parse_date_range_fn=parse_date_range_fn,
        commits_in_period_fn=commits_in_period_fn,
        get_commits_for_group_files_fn=get_commits_for_group_files_fn,
    )

    assert result == []
    extract_clicked_node_name_fn.assert_called_once_with(click_data)
    files_in_clicked_community_fn.assert_called_once_with(
        graph_data, "src/a.py"
    )
    parse_date_range_fn.assert_not_called()
    commits_in_period_fn.assert_not_called()
    get_commits_for_group_files_fn.assert_not_called()


def test_generate_node_details_rows_happy_path():
    """Rows are built from parsed dates, period commits, and group files."""
    click_data = {"points": [{"text": "src/a.py"}]}
    graph_data = {"nodes": {"src/a.py": {"community": 0}}}
    date_range_data = {"period": "Last 7 days"}
    starting = datetime(2026, 4, 1, tzinfo=timezone.utc)
    ending = datetime(2026, 4, 7, tzinfo=timezone.utc)
    commits_in_period = ["c1", "c2"]
    group_files = ["src/a.py", "src/b.py"]
    expected_rows = [{"sha": "c1", "author": "Ada"}]

    extract_clicked_node_name_fn = Mock(return_value="src/a.py")
    files_in_clicked_community_fn = Mock(return_value=group_files)
    parse_date_range_fn = Mock(return_value=(starting, ending))
    commits_in_period_fn = Mock(return_value=commits_in_period)
    get_commits_for_group_files_fn = Mock(return_value=expected_rows)

    result = generate_node_details_rows(
        click_data=click_data,
        graph_data=graph_data,
        date_range_data=date_range_data,
        extract_clicked_node_name_fn=extract_clicked_node_name_fn,
        files_in_clicked_community_fn=files_in_clicked_community_fn,
        parse_date_range_fn=parse_date_range_fn,
        commits_in_period_fn=commits_in_period_fn,
        get_commits_for_group_files_fn=get_commits_for_group_files_fn,
    )

    assert result == expected_rows
    extract_clicked_node_name_fn.assert_called_once_with(click_data)
    files_in_clicked_community_fn.assert_called_once_with(
        graph_data, "src/a.py"
    )
    parse_date_range_fn.assert_called_once_with(date_range_data)
    commits_in_period_fn.assert_called_once_with(starting, ending)
    get_commits_for_group_files_fn.assert_called_once_with(
        commits_in_period, group_files
    )
