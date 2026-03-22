"""Community-to-community coupling Sankey report page."""

from __future__ import annotations

import re
from collections import defaultdict

from dash import Input, Output, callback, dcc, html, register_page
from dash.dash_table import DataTable
from dash.exceptions import PreventUpdate

import data
from algorithms.community_flow import (
    community_flow_rows,
    count_nodes_by_community,
)
from utils import date_utils
from utils.plotly_utils import create_empty_figure
from visualization.community_sankey import create_community_flow_sankey
from visualization.network_graph import create_file_affinity_network

register_page(
    module=__name__,
    name="Community Flows",
)

SANKEY_TITLE = "Community-to-Community Coupling"  # pragma: no mutate
_CONTROL_GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "1fr 1fr",
    "columnGap": "16px",
    "rowGap": "8px",
    "marginBottom": "12px",
}


def _stats_text(
    flow_rows: list[dict[str, float | int]], graph_stats: dict[str, float | int]
) -> str:
    if not flow_rows:
        return "No cross-community coupling detected in selected period."
    total_strength = sum(float(row["coupling_strength"]) for row in flow_rows)
    return (
        f"{len(flow_rows)} cross-community links across "
        f"{int(graph_stats.get('communities', 0))} communities "
        f"(total coupling strength: {total_strength:.3f})."
    )


def _table_row(
    flow_row: dict[str, float | int],
) -> dict[str, float | int | str]:
    return {
        "source_group": f"Group {int(flow_row['source_community']) + 1}",
        "target_group": f"Group {int(flow_row['target_community']) + 1}",
        "coupling_strength": round(float(flow_row["coupling_strength"]), 3),
        "cross_community_edges": int(flow_row["edge_count"]),
    }


_GROUP_LABEL_PATTERN = re.compile(r"Group\s+(\d+)")


def _repo_error_message() -> str:
    return (
        "No repository path provided. Please run the application with a "
        "repository path as a command-line argument."
    )


def _community_composition_store(graph) -> dict[str, object]:
    grouped_rows: defaultdict[int, list[dict[str, int | str]]] = defaultdict(
        list
    )

    for file_path in graph.nodes():
        community = int(graph.nodes[file_path].get("community", 0))
        commit_count = int(graph.nodes[file_path].get("commit_count", 0))
        total_connections = int(graph.degree(file_path))
        cross_community_connections = sum(
            1
            for neighbor in graph.neighbors(file_path)
            if int(graph.nodes[neighbor].get("community", 0)) != community
        )
        grouped_rows[community].append(
            {
                "file_path": file_path,
                "commit_count": commit_count,
                "total_connections": total_connections,
                "cross_community_connections": cross_community_connections,
            }
        )

    communities: dict[str, dict[str, object]] = {}
    for community, rows in grouped_rows.items():
        sorted_rows = sorted(
            rows,
            key=lambda row: (
                -int(row["cross_community_connections"]),
                -int(row["total_connections"]),
                -int(row["commit_count"]),
                str(row["file_path"]),
            ),
        )
        communities[str(community)] = {
            "group_label": f"Group {community + 1}",
            "file_count": len(sorted_rows),
            "files": sorted_rows,
        }
    return {"communities": communities}


def _is_link_click(click_data: dict[str, object] | None) -> bool:
    if not click_data:
        return False
    points = click_data.get("points", [])
    if not points:
        return False
    point = points[0]
    return (
        isinstance(point, dict)
        and point.get("source") is not None
        and point.get("target") is not None
    )


def _selected_community_from_click(
    click_data: dict[str, object] | None,
) -> int | None:
    if not click_data:
        return None
    points = click_data.get("points", [])
    if not points:
        return None
    point = points[0]
    if not isinstance(point, dict):
        return None
    label = str(point.get("label", ""))
    matched = _GROUP_LABEL_PATTERN.search(label)
    if not matched:
        return None
    return int(matched.group(1)) - 1


def _node_count_slider() -> dcc.Slider:
    node_marks = {
        node_count: str(node_count) for node_count in range(10, 101, 10)
    }
    return dcc.Slider(
        id="id-community-flow-node-slider",
        min=10,
        max=100,
        step=10,
        value=50,
        marks=node_marks,
    )


def _min_affinity_slider() -> dcc.Slider:
    affinity_marks = {
        affinity / 100: str(affinity / 100) for affinity in range(5, 51, 5)
    }
    return dcc.Slider(
        id="id-community-flow-min-affinity-slider",
        min=0.05,
        max=0.5,
        step=0.01,
        value=0.2,
        marks=affinity_marks,
    )


layout = html.Div(
    [
        html.H2(SANKEY_TITLE, style={"margin": "10px 0"}),
        html.Div(
            style=_CONTROL_GRID_STYLE,
            children=[
                html.Div(
                    children=[
                        html.Label("Maximum Number of Nodes:"),
                        _node_count_slider(),
                    ]
                ),
                html.Div(
                    children=[
                        html.Label("Minimum Affinity Factor:"),
                        _min_affinity_slider(),
                    ]
                ),
            ],
        ),
        html.P(
            id="id-community-flow-status",
            style={"fontStyle": "italic", "color": "#666"},
        ),
        dcc.Loading(
            id="loading-community-flow-sankey",
            type="circle",
            children=[
                dcc.Graph(
                    id="id-community-flow-sankey-graph",
                    style={"height": "640px"},
                )
            ],
        ),
        dcc.Store(id="id-community-flow-table", data=[]),
        dcc.Store(id="id-community-flow-composition-store", data={}),
        html.H3("Selected Group Composition", style={"margin": "16px 0 8px 0"}),
        html.P(
            id="id-community-flow-composition-status",
            style={"fontStyle": "italic", "color": "#666"},
        ),
        DataTable(
            id="id-community-flow-composition-table",
            columns=[
                {"name": "File", "id": "file_path"},
                {"name": "Commit Count", "id": "commit_count"},
                {"name": "Connections", "id": "total_connections"},
                {
                    "name": "Cross-Community Connections",
                    "id": "cross_community_connections",
                },
            ],
            style_table={"maxHeight": "280px", "overflowY": "auto"},
            style_cell={"textAlign": "left", "padding": "8px"},
            style_cell_conditional=[
                {"if": {"column_id": "file_path"}, "width": "50%"},
                {"if": {"column_id": "commit_count"}, "width": "12%"},
                {"if": {"column_id": "total_connections"}, "width": "14%"},
                {
                    "if": {"column_id": "cross_community_connections"},
                    "width": "24%",
                },
            ],
            data=[],
        ),
    ]
)


@callback(
    [
        Output("id-community-flow-sankey-graph", "figure"),
        Output("id-community-flow-status", "children"),
        Output("id-community-flow-table", "data"),
        Output("id-community-flow-composition-store", "data"),
    ],
    [
        Input("global-date-range", "data"),
        Input("id-community-flow-node-slider", "value"),
        Input("id-community-flow-min-affinity-slider", "value"),
    ],
)
def populate_community_flow_sankey(store_data, max_nodes, min_affinity):
    """Populate community-to-community Sankey figure and details table."""
    if not store_data or "period" not in store_data:
        raise PreventUpdate

    try:
        begin, end = date_utils.parse_date_range_from_store(store_data)
    except ValueError as error:
        message = f"Invalid date range: {error}"
        return (
            create_empty_figure(message=message, title=SANKEY_TITLE),
            message,
            [],
            {"communities": {}},
        )

    try:
        commits_data = data.commits_in_period(begin, end)
        graph, _, graph_stats = create_file_affinity_network(
            commits=commits_data,
            min_affinity=float(min_affinity),
            max_nodes=int(max_nodes),
        )
    except ValueError as error:
        if "No repository path provided" in str(error):
            message = _repo_error_message()
            return (
                create_empty_figure(message=message, title=SANKEY_TITLE),
                message,
                [],
                {"communities": {}},
            )
        raise
    except Exception as error:
        message = f"Graph generation failed: {error}"
        return (
            create_empty_figure(message=message, title=SANKEY_TITLE),
            message,
            [],
            {"communities": {}},
        )

    flow_rows = community_flow_rows(graph)
    community_sizes = count_nodes_by_community(graph)
    figure = create_community_flow_sankey(
        flow_rows=flow_rows,
        community_sizes=community_sizes,
        title=SANKEY_TITLE,
    )
    table_rows = [_table_row(flow_row) for flow_row in flow_rows]
    return (
        figure,
        _stats_text(flow_rows, graph_stats),
        table_rows,
        _community_composition_store(graph),
    )


@callback(
    [
        Output("id-community-flow-composition-status", "children"),
        Output("id-community-flow-composition-table", "data"),
    ],
    Input("id-community-flow-sankey-graph", "clickData"),
    Input("id-community-flow-composition-store", "data"),
)
def reveal_group_composition(click_data, composition_store):
    """Reveal group composition when a Sankey group node is selected."""
    if not composition_store or "communities" not in composition_store:
        return "No community composition available for selected period.", []

    communities = composition_store["communities"]
    if not communities:
        return "No community composition available for selected period.", []
    if not click_data:
        return "Click a group node in the Sankey chart to reveal files.", []
    if _is_link_click(click_data):
        return "Select a group node (not a link) to reveal composition.", []

    selected_community = _selected_community_from_click(click_data)
    if selected_community is None:
        return "Could not determine selected group from chart click.", []

    community_payload = communities.get(str(selected_community))
    if community_payload is None:
        return "Selected group is not available in current results.", []

    group_label = str(community_payload["group_label"])
    file_count = int(community_payload["file_count"])
    status = f"{group_label}: {file_count} files"
    return status, list(community_payload["files"])
