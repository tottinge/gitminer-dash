"""Tests for `visualization/community_sankey.py`."""

from visualization.community_sankey import create_community_flow_sankey


def test_create_community_flow_sankey_empty_state():
    figure = create_community_flow_sankey(
        flow_rows=[],
        community_sizes={},
        title="Community Flow Test",
    )

    assert figure.layout.title.text == "Community Flow Test"
    assert len(figure.data) == 0
    assert figure.layout.annotations
    assert (
        "No cross-community coupling detected"
        in figure.layout.annotations[0].text
    )


def test_create_community_flow_sankey_builds_expected_links():
    figure = create_community_flow_sankey(
        flow_rows=[
            {
                "source_community": 0,
                "target_community": 1,
                "coupling_strength": 1.25,
                "edge_count": 3,
            },
            {
                "source_community": 1,
                "target_community": 2,
                "coupling_strength": 0.5,
                "edge_count": 2,
            },
        ],
        community_sizes={0: 4, 1: 3, 2: 2},
    )

    assert len(figure.data) == 1
    sankey_trace = figure.data[0]
    assert sankey_trace.type == "sankey"
    assert list(sankey_trace.link.source) == [0, 1]
    assert list(sankey_trace.link.target) == [1, 2]
    assert list(sankey_trace.link.value) == [1.25, 0.5]
    assert list(sankey_trace.link.customdata) == [3, 2]
    assert list(sankey_trace.link.label) == [
        "Community 1 (4 files) ↔ Community 2 (3 files)",
        "Community 2 (3 files) ↔ Community 3 (2 files)",
    ]
    assert "Direction: undirected" in sankey_trace.link.hovertemplate
    assert list(sankey_trace.node.label) == [
        "Community 1 (4 files)",
        "Community 2 (3 files)",
        "Community 3 (2 files)",
    ]
