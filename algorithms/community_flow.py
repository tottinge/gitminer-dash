"""Community flow helpers for cross-community coupling analysis."""

from __future__ import annotations

from collections import defaultdict

import networkx as nx


def _normalized_community_pair(
    first_community: int, second_community: int
) -> tuple[int, int]:
    return tuple(sorted((first_community, second_community)))


def count_nodes_by_community(graph: nx.Graph) -> dict[int, int]:
    """Count nodes in each community from graph node attributes."""
    sizes: defaultdict[int, int] = defaultdict(int)
    for _, node_data in graph.nodes(data=True):
        community = int(node_data.get("community", 0))
        sizes[community] += 1
    return {community: sizes[community] for community in sorted(sizes)}


def community_flow_rows(graph: nx.Graph) -> list[dict[str, float | int]]:
    """Aggregate cross-community edge weights into community flow rows."""
    flows: defaultdict[tuple[int, int], dict[str, float | int]] = defaultdict(
        lambda: {"coupling_strength": 0.0, "edge_count": 0}
    )

    for file_one, file_two, edge_data in graph.edges(data=True):
        first_community = int(graph.nodes[file_one].get("community", 0))
        second_community = int(graph.nodes[file_two].get("community", 0))
        if first_community == second_community:
            continue

        pair = _normalized_community_pair(
            first_community=first_community,
            second_community=second_community,
        )
        row = flows[pair]
        row["coupling_strength"] += float(edge_data.get("weight", 0.0))
        row["edge_count"] += 1

    rows: list[dict[str, float | int]] = []
    for (source_community, target_community), aggregate in flows.items():
        rows.append(
            {
                "source_community": source_community,
                "target_community": target_community,
                "coupling_strength": round(
                    float(aggregate["coupling_strength"]), 6
                ),
                "edge_count": int(aggregate["edge_count"]),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            -float(row["coupling_strength"]),
            -int(row["edge_count"]),
            int(row["source_community"]),
            int(row["target_community"]),
        ),
    )
