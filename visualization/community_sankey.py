"""Plotly Sankey builder for community-to-community coupling flows."""

from __future__ import annotations

import plotly.graph_objects as go

from utils.plotly_utils import create_empty_figure


def _community_label(community: int, community_sizes: dict[int, int]) -> str:
    size = community_sizes.get(community, 0)  # pragma: no mutate
    return f"Community {community + 1} ({size} files)"  # pragma: no mutate


def _sankey_layout_style(title: str) -> dict[str, object]:
    """Return cosmetic layout style for community sankey diagrams."""
    return {
        "title": title,  # pragma: no mutate
        "font_size": 12,  # pragma: no mutate
        "margin": dict(l=10, r=10, t=50, b=10),  # pragma: no mutate
    }


def create_community_flow_sankey(
    flow_rows: list[dict[str, float | int]],
    community_sizes: dict[int, int],
    title: str = "Community-to-Community Coupling",  # pragma: no mutate
) -> go.Figure:
    """Build Sankey chart from cross-community coupling rows."""
    if not flow_rows:
        return create_empty_figure(
            message="No cross-community coupling detected in selected period.",  # pragma: no mutate
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
            f"{_community_label(int(row['source_community']), community_sizes)}"  # pragma: no mutate
            f" ↔ "  # pragma: no mutate
            f"{_community_label(int(row['target_community']), community_sizes)}"  # pragma: no mutate
        )
        for row in flow_rows
    ]

    figure = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    label=community_labels,
                ),
                link=dict(
                    source=link_source,
                    target=link_target,
                    value=link_value,
                    customdata=link_edge_counts,
                    label=link_labels,
                    hovertemplate=(
                        "%{label}<br>"  # pragma: no mutate
                        "Coupling Strength: %{value:.3f}<br>"  # pragma: no mutate
                        "Cross-community edges: %{customdata}<br>"  # pragma: no mutate
                        "Direction: undirected<extra></extra>"  # pragma: no mutate
                    ),
                ),
            )
        ]
    )
    figure.update_layout(**_sankey_layout_style(title))  # pragma: no mutate
    return figure
