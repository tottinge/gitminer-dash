"""Focused helper-level tests for `pages/community_flows.py`."""

from __future__ import annotations

from unittest.mock import patch

import networkx as nx


@patch("dash.register_page")
def test_stats_text_variants(_):
    import pages.community_flows as module

    assert (
        module._stats_text([], {"communities": 4})
        == "No cross-community coupling detected in selected period."
    )

    flow_rows = [
        {"coupling_strength": 1.2},
        {"coupling_strength": 0.3},
    ]
    stats_text = module._stats_text(flow_rows, {"communities": 2})
    assert (
        stats_text
        == "2 cross-community links across 2 communities (total coupling strength: 1.500)."
    )

    default_communities_text = module._stats_text(flow_rows, {})
    assert (
        default_communities_text
        == "2 cross-community links across 0 communities (total coupling strength: 1.500)."
    )


@patch("dash.register_page")
def test_table_row_variants(_):
    import pages.community_flows as module

    row = module._table_row(
        {
            "source_community": 1,
            "target_community": 3,
            "coupling_strength": 1.23456,
            "edge_count": 4,
        },
        total_coupling_strength=2.46912,
    )
    assert row == {
        "source_group": "Community 2",
        "target_group": "Community 4",
        "coupling_strength": 1.235,
        "cross_community_edges": 4,
        "coupling_share_pct": 50.0,
    }

    zero_total = module._table_row(
        {
            "source_community": 0,
            "target_community": 1,
            "coupling_strength": 3.0,
            "edge_count": 2,
        },
        total_coupling_strength=0.0,
    )
    assert zero_total["coupling_share_pct"] == 0.0
    precision_sensitive = module._table_row(
        {
            "source_community": 1,
            "target_community": 2,
            "coupling_strength": 1.0,
            "edge_count": 1,
        },
        total_coupling_strength=3.0,
    )
    assert precision_sensitive["coupling_share_pct"] == 33.3


@patch("dash.register_page")
def test_repo_error_message(_):
    import pages.community_flows as module

    assert module._repo_error_message() == (
        "No repository path provided. Please run the application with a "
        "repository path as a command-line argument."
    )


@patch("dash.register_page")
def test_community_composition_store_sorting_and_counts(_):
    import pages.community_flows as module

    graph = nx.Graph()
    graph.add_node("src/a.py", community=0, commit_count=8)
    graph.add_node("src/b.py", community=0, commit_count=4)
    graph.add_node("src/c.py", community=1, commit_count=7)
    graph.add_node("src/d.py", commit_count=2)
    graph.add_edge("src/a.py", "src/b.py")
    graph.add_edge("src/a.py", "src/c.py")
    graph.add_edge("src/b.py", "src/c.py")
    graph.add_edge("src/d.py", "src/c.py")

    composition = module._community_composition_store(graph)
    communities = composition["communities"]

    assert set(communities.keys()) == {"0", "1"}
    assert communities["0"]["community_label"] == "Community 1"
    assert communities["0"]["file_count"] == 3
    assert communities["1"]["community_label"] == "Community 2"
    assert communities["1"]["file_count"] == 1

    first_file = communities["0"]["files"][0]
    assert first_file["file_path"] == "src/a.py"
    assert first_file["cross_community_connections"] == 1
    assert first_file["total_connections"] == 2
    assert first_file["commit_count"] == 8

    # default community fallback for node without explicit community attribute
    default_community_files = [
        row["file_path"] for row in communities["0"]["files"]
    ]
    assert "src/d.py" in default_community_files
    ranking_graph = nx.Graph()
    ranking_graph.add_node("src/z.py", community=1, commit_count=5)
    ranking_graph.add_node("src/a.py", community=1, commit_count=5)
    ranking_graph.add_node("src/hub.py", community=0, commit_count=20)
    ranking_graph.add_node("src/other.py", community=2, commit_count=20)
    ranking_graph.add_edge("src/z.py", "src/hub.py")
    ranking_graph.add_edge("src/a.py", "src/hub.py")
    ranking_graph.add_edge("src/a.py", "src/other.py")
    ranking_store = module._community_composition_store(ranking_graph)
    ranked_files = ranking_store["communities"]["1"]["files"]
    assert [row["file_path"] for row in ranked_files] == [
        "src/a.py",
        "src/z.py",
    ]
    assert ranked_files[0]["cross_community_connections"] == 2
    assert ranked_files[1]["cross_community_connections"] == 1
    tie_break_graph = nx.Graph()
    tie_break_graph.add_node("src/z.py", community=1, commit_count=5)
    tie_break_graph.add_node("src/a.py", community=1, commit_count=5)
    tie_break_graph.add_node("src/hub.py", community=0, commit_count=20)
    tie_break_graph.add_edge("src/z.py", "src/hub.py")
    tie_break_graph.add_edge("src/a.py", "src/hub.py")
    tie_break_store = module._community_composition_store(tie_break_graph)
    tie_break_files = tie_break_store["communities"]["1"]["files"]
    assert [row["file_path"] for row in tie_break_files] == [
        "src/a.py",
        "src/z.py",
    ]
    default_neighbor_graph = nx.Graph()
    default_neighbor_graph.add_node("src/owned.py", community=1, commit_count=1)
    default_neighbor_graph.add_node("src/missing.py", commit_count=1)
    default_neighbor_graph.add_edge("src/owned.py", "src/missing.py")
    default_neighbor_store = module._community_composition_store(
        default_neighbor_graph
    )
    owned_row = default_neighbor_store["communities"]["1"]["files"][0]
    assert owned_row["cross_community_connections"] == 1


@patch("dash.register_page")
def test_is_link_click_variants(_):
    import pages.community_flows as module

    assert module._is_link_click(None) is False
    assert module._is_link_click({}) is False
    assert module._is_link_click({"points": []}) is False
    assert module._is_link_click({"points": ["not-a-dict"]}) is False
    assert (
        module._is_link_click(
            {"points": [{"source": 0, "target": 1, "label": "x"}]}
        )
        is True
    )
    assert (
        module._is_link_click({"points": [{"source": 0, "label": "x"}]})
        is False
    )
    assert (
        module._is_link_click({"points": [{"target": 1, "label": "x"}]})
        is False
    )


@patch("dash.register_page")
def test_selected_community_from_click_variants(_):
    import pages.community_flows as module

    assert module._selected_community_from_click(None) is None
    assert module._selected_community_from_click({}) is None
    assert module._selected_community_from_click({"points": []}) is None
    assert module._selected_community_from_click({"points": ["bad"]}) is None
    assert (
        module._selected_community_from_click(
            {"points": [{"label": "Community 3 (4 files)"}]}
        )
        == 2
    )
    assert (
        module._selected_community_from_click(
            {"points": [{"label": "Group 2"}]}
        )
        == 1
    )
    assert (
        module._selected_community_from_click(
            {"points": [{"label": "No Community Label"}]}
        )
        is None
    )


@patch("dash.register_page")
def test_node_count_slider_contract(_):
    import pages.community_flows as module

    slider = module._node_count_slider()
    assert slider.id == "id-community-flow-node-slider"
    assert slider.min == 10
    assert slider.max == 100
    assert slider.step == 10
    assert slider.value == 50
    assert slider.marks[10] == "10"
    assert slider.marks[100] == "100"
    assert len(slider.marks) == 10
    assert 11 not in slider.marks


@patch("dash.register_page")
def test_min_affinity_slider_contract(_):
    import pages.community_flows as module

    slider = module._min_affinity_slider()
    assert slider.id == "id-community-flow-min-affinity-slider"
    assert slider.min == 0.05
    assert slider.max == 0.5
    assert slider.step == 0.01
    assert slider.value == 0.2
    assert slider.marks[0.05] == "0.05"
    assert slider.marks[0.5] == "0.50"
    assert len(slider.marks) == 10
    assert 0.06 not in slider.marks


@patch("dash.register_page")
def test_interpretation_guidance_contract(_):
    import pages.community_flows as module

    guidance = module._interpretation_guidance()
    assert guidance.style == module._INTERPRETATION_GUIDANCE_STYLE
    assert len(guidance.children) == 2
    assert guidance.children[0].children == "How to read this chart"

    bullet_list = guidance.children[1]
    assert bullet_list.style == {"margin": "6px 0 0 18px", "padding": "0"}
    assert len(bullet_list.children) == 3
    assert (
        bullet_list.children[0].children
        == "Each node is a community of files that frequently change together."
    )
    assert (
        bullet_list.children[1].children
        == "Thicker links indicate stronger cross-community coupling."
    )
    assert (
        bullet_list.children[2].children
        == "Links are undirected coupling summaries, not source-to-target causality."
    )
