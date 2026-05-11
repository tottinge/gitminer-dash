"""Tests for `pages/community_flows.py`."""

from datetime import datetime
from unittest.mock import patch

import networkx as nx
import pytest
from dash.exceptions import PreventUpdate


@pytest.fixture
def populate_community_flow_sankey():
    with patch("dash.register_page"):
        from pages.community_flows import (
            populate_community_flow_sankey as callback_fn,
        )

        return callback_fn


@pytest.fixture
def reveal_group_composition():
    with patch("dash.register_page"):
        from pages.community_flows import (
            reveal_group_composition as callback_fn,
        )

        return callback_fn


@patch("pages.community_flows.create_file_affinity_network")
@patch("pages.community_flows.repo_context.commits_in_period")
@patch("pages.community_flows.date_utils.parse_date_range_from_store")
def test_populate_community_flow_sankey_returns_sankey_and_table(
    mock_parse_date_range,
    mock_commits_in_period,
    mock_create_file_affinity_network,
    populate_community_flow_sankey,
):
    mock_parse_date_range.return_value = (
        datetime(2026, 1, 1),
        datetime(2026, 1, 31),
    )
    mock_commits_in_period.return_value = []
    graph = nx.Graph()
    graph.add_node("a.py", community=0)
    graph.add_node("b.py", community=1)
    graph.add_edge("a.py", "b.py", weight=0.8)
    mock_create_file_affinity_network.return_value = (
        graph,
        [{0}, {1}],
        {"communities": 2},
    )

    figure, status, table_rows, composition_store = (
        populate_community_flow_sankey({"period": "Last 30 days"}, 50, 0.2)
    )

    assert len(figure.data) == 1
    assert figure.data[0].type == "sankey"
    assert "cross-community links across 2 communities" in status
    assert table_rows == [
        {
            "source_group": "Community 1",
            "target_group": "Community 2",
            "coupling_strength": 0.8,
            "cross_community_edges": 1,
            "coupling_share_pct": 100.0,
        }
    ]
    assert composition_store == {
        "communities": {
            "0": {
                "community_label": "Community 1",
                "file_count": 1,
                "files": [
                    {
                        "file_path": "a.py",
                        "commit_count": 0,
                        "total_connections": 1,
                        "cross_community_connections": 1,
                    }
                ],
            },
            "1": {
                "community_label": "Community 2",
                "file_count": 1,
                "files": [
                    {
                        "file_path": "b.py",
                        "commit_count": 0,
                        "total_connections": 1,
                        "cross_community_connections": 1,
                    }
                ],
            },
        }
    }


@patch("pages.community_flows.date_utils.parse_date_range_from_store")
def test_populate_community_flow_sankey_invalid_date_range(
    mock_parse_date_range,
    populate_community_flow_sankey,
):
    mock_parse_date_range.side_effect = ValueError("bad-date")

    figure, status, table_rows, composition_store = (
        populate_community_flow_sankey({"period": "custom"}, 50, 0.2)
    )

    assert "Invalid date range" in status
    assert table_rows == []
    assert composition_store == {"communities": {}}
    assert figure.layout.annotations
    assert "bad-date" in figure.layout.annotations[0].text


@patch("pages.community_flows.create_file_affinity_network")
@patch("pages.community_flows.repo_context.commits_in_period")
@patch("pages.community_flows.date_utils.parse_date_range_from_store")
def test_populate_community_flow_sankey_repository_path_error(
    mock_parse_date_range,
    mock_commits_in_period,
    mock_create_file_affinity_network,
    populate_community_flow_sankey,
):
    mock_parse_date_range.return_value = (
        datetime(2026, 1, 1),
        datetime(2026, 1, 31),
    )
    mock_commits_in_period.return_value = []
    mock_create_file_affinity_network.side_effect = ValueError(
        "No repository path provided"
    )

    figure, status, table_rows, composition_store = (
        populate_community_flow_sankey({"period": "Last 30 days"}, 50, 0.2)
    )

    assert "No repository path provided" in status
    assert table_rows == []
    assert composition_store == {"communities": {}}
    assert figure.layout.annotations


def test_populate_community_flow_sankey_prevent_update_without_store_data(
    populate_community_flow_sankey,
):
    with pytest.raises(PreventUpdate):
        populate_community_flow_sankey(None, 50, 0.2)


def test_reveal_group_composition_for_selected_group(reveal_group_composition):
    status, table_rows = reveal_group_composition(
        {"points": [{"label": "Community 1 (3 files)"}]},
        {
            "communities": {
                "0": {
                    "community_label": "Community 1",
                    "file_count": 2,
                    "files": [
                        {
                            "file_path": "src/a.py",
                            "commit_count": 10,
                            "total_connections": 3,
                            "cross_community_connections": 2,
                        },
                        {
                            "file_path": "src/b.py",
                            "commit_count": 7,
                            "total_connections": 2,
                            "cross_community_connections": 1,
                        },
                    ],
                }
            }
        },
    )

    assert status == "Community 1: 2 files"
    assert table_rows[0]["file_path"] == "src/a.py"
    assert table_rows[1]["file_path"] == "src/b.py"


def test_reveal_group_composition_requires_node_selection(
    reveal_group_composition,
):
    status, table_rows = reveal_group_composition(
        {
            "points": [
                {
                    "label": "Community 1 (2 files) ↔ Community 2 (4 files)",
                    "source": 0,
                    "target": 1,
                }
            ]
        },
        {
            "communities": {
                "0": {"community_label": "Community 1", "file_count": 0}
            }
        },
    )

    assert "Select a community node (not a link)" in status
    assert table_rows == []
