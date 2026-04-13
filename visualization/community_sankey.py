"""Plotly Sankey builder for community-to-community coupling flows."""

from __future__ import annotations

import plotly.graph_objects as go

from utils.plotly_utils import create_empty_figure


def _community_label(community: int, community_sizes: dict[int, int]) -> str:
    size = community_sizes.get(community, 0)
    return f"Community {community + 1} ({size} files)"


def create_community_flow_sankey(
    flow_rows: list[dict[str, float | int]],
    community_sizes: dict[int, int],
    title: str = "Community-to-Community Coupling",
) -> go.Figure:
    """Build Sankey chart from cross-community coupling rows."""
    if not flow_rows:
        return create_empty_figure(
            message="No cross-community coupling detected in selected period.",
            title=title,
        )

    community_ids = sorted(
        {int(row["source_community"]) for row in flow_rows}
        | {int(row["target_community"]) for row in flow_rows}
    )
    indices_by_community = {
        community_id: index for index, community_id in enumerate(community_ids)
    }
    community_labels = [
        _community_label(
            community=community_id, community_sizes=community_sizes
        )
        for community_id in community_ids
    ]

    link_source = [
        indices_by_community[int(row["source_community"])] for row in flow_rows
    ]
    link_target = [
        indices_by_community[int(row["target_community"])] for row in flow_rows
    ]
    link_value = [float(row["coupling_strength"]) for row in flow_rows]
    link_edge_counts = [int(row["edge_count"]) for row in flow_rows]
    link_labels = [
        (
            f"{_community_label(int(row['source_community']), community_sizes)}"
            f" ↔ "
            f"{_community_label(int(row['target_community']), community_sizes)}"
        )
        for row in flow_rows
    ]

    figure = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=18,
                    thickness=20,
                    line=dict(color="black", width=0.4),
                    label=community_labels,
                ),
                link=dict(
                    source=link_source,
                    target=link_target,
                    value=link_value,
                    customdata=link_edge_counts,
                    label=link_labels,
                    hovertemplate=(
                        "%{label}<br>"
                        "Coupling Strength: %{value:.3f}<br>"
                        "Cross-community edges: %{customdata}<br>"
                        "Direction: undirected<extra></extra>"
                    ),
                ),
            )
        ]
    )
    figure.update_layout(
        title=title,
        font_size=12,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return figure
