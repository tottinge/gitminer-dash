"""
Tests for the node details table callback.

These tests verify that clicking on a node in the affinity graph
populates the details table correctly.
"""

import pytest
from dash import Dash

app = Dash(__name__, suppress_callback_exceptions=True)
from pages.affinity_groups import update_node_details_table


def test_node_details_with_single_community_node():
    """Test details for nodes in a group when one node is clicked."""
    click_data = {
        "points": [{"text": "File: src/main.py<br>Commits: 10<br>Connections: 3"}]
    }
    graph_data = {
        "nodes": {
            "src/main.py": {
                "commit_count": 10,
                "degree": 3,
                "community": 0,
                "connected_communities": [0],
            },
            "src/utils.py": {
                "commit_count": 5,
                "degree": 2,
                "community": 0,
                "connected_communities": [0],
            },
            "src/helper.py": {
                "commit_count": 8,
                "degree": 4,
                "community": 0,
                "connected_communities": [0],
            },
        },
        "communities": {0: ["src/main.py", "src/utils.py", "src/helper.py"]},
    }
    result = update_node_details_table(click_data, graph_data)
    assert len(result) == 3
    assert result[0]["node_name"] == "src/main.py"
    assert result[0]["commit_count"] == 10
    assert result[1]["node_name"] == "src/helper.py"
    assert result[1]["commit_count"] == 8
    assert result[2]["node_name"] == "src/utils.py"
    assert result[2]["commit_count"] == 5
    for row in result:
        assert row["group"] == "Group 1"
        assert row["connected_groups"] == ""


def test_node_details_with_bridge_node():
    """Test details showing all nodes in a group containing a bridge node."""
    click_data = {
        "points": [{"text": "File: src/bridge.py<br>Commits: 15<br>Connections: 5"}]
    }
    graph_data = {
        "nodes": {
            "src/bridge.py": {
                "commit_count": 15,
                "degree": 5,
                "community": 0,
                "connected_communities": [0, 1, 2],
            },
            "src/main.py": {
                "commit_count": 10,
                "degree": 3,
                "community": 0,
                "connected_communities": [0],
            },
        },
        "communities": {
            0: ["src/bridge.py", "src/main.py"],
            1: ["src/other.py"],
            2: ["src/third.py"],
        },
    }
    result = update_node_details_table(click_data, graph_data)
    assert len(result) == 2
    assert result[0]["node_name"] == "src/bridge.py"
    assert result[0]["commit_count"] == 15
    assert result[0]["degree"] == 5
    assert result[0]["group"] == "Group 1"
    assert "Group 1" in result[0]["connected_groups"]
    assert "Group 2" in result[0]["connected_groups"]
    assert "Group 3" in result[0]["connected_groups"]
    assert result[1]["node_name"] == "src/main.py"
    assert result[1]["commit_count"] == 10
    assert result[1]["connected_groups"] == ""


def test_node_details_with_no_click():
    """Test that no data is returned when nothing is clicked."""
    click_data = None
    graph_data = {"nodes": {}, "communities": {}}
    result = update_node_details_table(click_data, graph_data)
    assert result == []


def test_node_details_with_invalid_node():
    """Test handling of clicks on nodes not in the graph data."""
    click_data = {
        "points": [{"text": "File: nonexistent.py<br>Commits: 0<br>Connections: 0"}]
    }
    graph_data = {
        "nodes": {
            "src/main.py": {
                "commit_count": 10,
                "degree": 3,
                "community": 0,
                "connected_communities": [0],
            }
        },
        "communities": {0: ["src/main.py"]},
    }
    result = update_node_details_table(click_data, graph_data)
    assert result == []


def test_node_details_with_empty_graph_data():
    """Test handling of clicks when graph data is empty."""
    click_data = {
        "points": [{"text": "File: src/main.py<br>Commits: 10<br>Connections: 3"}]
    }
    graph_data = {}
    result = update_node_details_table(click_data, graph_data)
    assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
