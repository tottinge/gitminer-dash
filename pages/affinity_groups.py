import plotly.graph_objects as go
from collections import defaultdict
from dash import register_page, html, callback, Output, Input, dcc, State, no_update
from dash.dcc import Dropdown, Slider, Store
from dash.html import Button
from dash.dash_table import DataTable

import data
from utils import date_utils
from algorithms.affinity_calculator import calculate_affinities
from algorithms.affinity_analysis import (
    get_top_files_and_affinities,
    find_affinity_range,
    calculate_ideal_affinity
)
from visualization.network_graph import create_file_affinity_network, create_network_visualization
from utils.git import ensure_list

register_page(__name__, title="Affinity Groups")

layout = html.Div(
    children=[
        html.H1("File Affinity Groups"),
        html.P("Files that frequently change together are grouped by color. Node size indicates how many connections a file has."),
        html.Div(
            style={"display": "flex", "justify-content": "space-between", "align-items": "center", "margin-bottom": "20px"},
            children=[
                html.Div(
                    style={"width": "45%"},
                    children=[
                        html.Label("Maximum Number of Nodes:"),
                        Slider(
                            id="id-affinity-node-slider",
                            min=10,
                            max=100,
                            step=10,
                            value=50,
                            marks={i: str(i) for i in range(10, 101, 10)},
                        ),
                    ]
                ),
                html.Div(
                    style={"width": "45%"},
                    children=[
                        html.Label("Minimum Affinity Factor:"),
                        Slider(
                            id="id-affinity-min-slider",
                            min=0.05,
                            max=0.5,
                            step=0.01,
                            value=0.2,
                            marks={i/100: str(i/100) for i in range(5, 51, 5)},
                        ),
                        html.Div(
                            style={"margin-top": "10px", "display": "flex", "justify-content": "space-between"},
                            children=[
                                Button(
                                    id="id-auto-affinity-button",
                                    children="Auto-calculate Ideal Affinity",
                                    style={"width": "100%"}
                                ),
                            ]
                        ),
                        html.Div(
                            id="id-auto-affinity-info",
                            style={"margin-top": "5px", "font-size": "0.8em", "color": "#666"}
                        )
                    ]
                ),
            ]
        ),
        dcc.Loading(
            id="loading-file-affinity-graph",
            type="circle",
            children=[
                dcc.Graph(
                    id="id-file-affinity-graph",
                    style={'height': '800px'}
                )
            ]
        ),
        html.Div(
            children=[
                html.H3("Interpretation"),
                html.P("Each colored group represents files that tend to change together."),
                html.P("Thicker lines indicate stronger affinity between files."),
                html.P("Larger nodes indicate files that have connections to many other files.")
            ]
        ),
        html.Hr(),
        html.H3("Group Details"),
        html.P("Click on any node in the graph above to see all files in that group, sorted by commit count."),
        dcc.Loading(
            id="loading-node-details-table",
            type="circle",
            children=[
                DataTable(
                    id="id-node-details-table",
                    columns=[
                        {"name": "Node Name", "id": "node_name"},
                        {"name": "Total Commits", "id": "commit_count"},
                        {"name": "Connections", "id": "degree"},
                        {"name": "Group", "id": "group"},
                        {"name": "Connected Groups", "id": "connected_groups"}
                    ],
                    style_cell={'textAlign': 'left'},
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{connected_groups} ne ""'},
                            'backgroundColor': '#ffe6e6',
                            'color': '#cc0000'
                        }
                    ],
                    data=[]
                )
            ]
        ),
        # Hidden store to keep graph data for click handling
        Store(id="id-graph-data-store", data={})
    ]
)



@callback(
    Output("id-affinity-min-slider", "min"),
    Output("id-affinity-min-slider", "max"),
    Output("id-affinity-min-slider", "value"),
    Output("id-affinity-min-slider", "marks"),
    Output("id-auto-affinity-info", "children"),
    [Input("id-auto-affinity-button", "n_clicks")],
    [State("global-date-range", "data"),
     State("id-affinity-node-slider", "value")],
    prevent_initial_call=True
)
def auto_calculate_affinity(n_clicks, store_data, max_nodes):
    """
    Calculate the affinity range and ideal threshold based on the current commit data.
    
    Args:
        n_clicks: Number of button clicks (not used, but required for callback)
        period: Selected time period
        max_nodes: Maximum number of nodes
        
    Returns:
        Tuple of (min_affinity, max_affinity, ideal_affinity, marks, info_text)
    """
    if not n_clicks:
        return no_update, no_update, no_update, no_update, no_update
    
    try:
        # Get commit data for the selected period
        if isinstance(store_data, dict):
            period = store_data.get('period', date_utils.DEFAULT_PERIOD)
        else:
            period = store_data or date_utils.DEFAULT_PERIOD
        if isinstance(store_data, dict) and 'begin' in store_data and 'end' in store_data:
            from datetime import datetime as _dt
            starting = _dt.fromisoformat(store_data['begin'])
            ending = _dt.fromisoformat(store_data['end'])
        else:
            starting, ending = date_utils.calculate_date_range(period)
        commits_data = data.commits_in_period(starting, ending)
        
        # Find affinity range and ideal value
        min_affinity, max_affinity, ideal_affinity = find_affinity_range(
            commits_data, max_nodes=max_nodes
        )
        
        # Round values for display
        min_affinity_rounded = round(min_affinity, 2)
        max_affinity_rounded = round(max_affinity, 2)
        ideal_affinity_rounded = round(ideal_affinity, 2)
        
        # Create marks for the slider
        # Ensure we have at least 3 marks (min, ideal, max)
        marks = {
            min_affinity_rounded: str(min_affinity_rounded),
            ideal_affinity_rounded: str(ideal_affinity_rounded),
            max_affinity_rounded: str(max_affinity_rounded)
        }
        
        # Add intermediate marks if there's enough space
        if max_affinity_rounded - min_affinity_rounded >= 0.1:
            step = round((max_affinity_rounded - min_affinity_rounded) / 5, 2)
            for i in range(1, 5):
                value = round(min_affinity_rounded + i * step, 2)
                if value > min_affinity_rounded and value < max_affinity_rounded and value != ideal_affinity_rounded:
                    marks[value] = str(value)
        
        # Get node and edge counts for info text
        _, node_count, edge_count = calculate_ideal_affinity(
            commits_data, target_node_count=15, max_nodes=max_nodes
        )
        
        # Create info text
        info_text = f"Min: {min_affinity_rounded}, Ideal: {ideal_affinity_rounded}, Max: {max_affinity_rounded} " + \
                   f"(estimated {node_count} nodes, {edge_count} edges)"
        
        return min_affinity_rounded, max_affinity_rounded, ideal_affinity_rounded, marks, info_text
    except Exception as e:
        # Return default values in case of error
        default_min = 0.05
        default_max = 0.5
        default_value = 0.2
        default_marks = {i/100: str(i/100) for i in range(5, 51, 5)}
        return default_min, default_max, default_value, default_marks, f"Error calculating affinity range: {str(e)}"


@callback(
    Output("id-file-affinity-graph", "figure"),
    Output("id-graph-data-store", "data"),
    [Input("global-date-range", "data"),
     Input("id-affinity-node-slider", "value"),
     Input("id-affinity-min-slider", "value")]
)
def update_file_affinity_graph(store_data, max_nodes: int, min_affinity: float):
    try:
        if isinstance(store_data, dict):
            period = store_data.get('period', date_utils.DEFAULT_PERIOD)
        else:
            period = store_data or date_utils.DEFAULT_PERIOD
        if isinstance(store_data, dict) and 'begin' in store_data and 'end' in store_data:
            from datetime import datetime as _dt
            starting = _dt.fromisoformat(store_data['begin'])
            ending = _dt.fromisoformat(store_data['end'])
        else:
            starting, ending = date_utils.calculate_date_range(period)
        # Convert commits_data to a list to prevent the iterator from being consumed
        commits_data = ensure_list(data.commits_in_period(starting, ending))
        
        # Calculate ideal affinity
        ideal_affinity, _, _ = calculate_ideal_affinity(
            commits_data, target_node_count=15, max_nodes=max_nodes
        )
        
        # Use the provided min_affinity value
        # Note: create_file_affinity_network now returns (G, communities, stats)
        G, communities, stats = create_file_affinity_network(commits_data, min_affinity=min_affinity, max_nodes=max_nodes)
        
        # Store graph data for click handling
        graph_data = {
            'nodes': {},
            'communities': {}
        }
        
        for node in G.nodes():
            node_community = G.nodes[node].get('community', 0)
            commit_count = G.nodes[node].get('commit_count', 0)
            degree = G.degree(node)
            
            # Find connected communities (for bridge detection)
            connected_communities = set()
            for neighbor in G.neighbors(node):
                neighbor_community = G.nodes[neighbor].get('community', 0)
                connected_communities.add(neighbor_community)
            
            graph_data['nodes'][node] = {
                'commit_count': commit_count,
                'degree': degree,
                'community': node_community,
                'connected_communities': sorted(list(connected_communities))
            }
        
        # Store community information
        for i, community in enumerate(communities):
            graph_data['communities'][i] = list(community)
        
        return create_network_visualization(G, communities), graph_data
    except ValueError as e:
        # Check if this is the specific error about missing repository path
        if "No repository path provided" in str(e):
            # Create a figure with a helpful message about repository path
            fig = go.Figure()
            fig.add_annotation(
                text="No repository path provided. Please run the application with a repository path as a command-line argument.",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16, color="red")
            )
            fig.add_annotation(
                text="Example: python app.py /path/to/your/git/repository",
                xref="paper", yref="paper",
                x=0.5, y=0.6,
                showarrow=False,
                font=dict(size=14)
            )
            fig.update_layout(
                title='File Affinity Network - Repository Path Required',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
            return fig, {}
        else:
            # Handle other ValueError exceptions
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error with input values: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16, color="red")
            )
            fig.update_layout(
                title='File Affinity Network - Input Error',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
            return fig, {}
    except Exception as e:
        # Create a figure with a general error message
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error generating affinity graph: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(
            title='File Affinity Network - Error',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        return fig, {}


@callback(
    Output("id-node-details-table", "data"),
    [Input("id-file-affinity-graph", "clickData")],
    [State("id-graph-data-store", "data")]
)
def update_node_details_table(click_data, graph_data):
    """
    Handle node clicks and populate the details table with all nodes in the same group.
    
    Args:
        click_data: Click event data from the graph
        graph_data: Stored graph structure data
        
    Returns:
        List of dicts for the DataTable containing all nodes in the selected node's group
    """
    if not click_data or not graph_data or 'nodes' not in graph_data:
        return []
    
    # Extract the clicked node name
    point = click_data.get('points', [{}])[0]
    node_name = point.get('text', '')
    
    # Parse the tooltip text to get the actual file name
    # Tooltip format: "File: {node}<br>Commits: {commit_count}<br>Connections: {degree}"
    if '<br>' in node_name:
        node_name = node_name.split('<br>')[0].replace('File: ', '')
    
    if not node_name or node_name not in graph_data['nodes']:
        return []
    
    # Get the clicked node's community
    clicked_node_data = graph_data['nodes'][node_name]
    node_community = clicked_node_data.get('community', 0)
    
    # Find all nodes in the same community
    table_rows = []
    for node, node_info in graph_data['nodes'].items():
        if node_info.get('community', -1) == node_community:
            # Determine if this is a bridge node
            connected_communities = node_info.get('connected_communities', [])
            is_bridge = len(connected_communities) > 1
            
            # Format connected groups (only show for bridge nodes)
            if is_bridge:
                connected_groups_str = ', '.join([f"Group {c + 1}" for c in connected_communities])
            else:
                connected_groups_str = ''
            
            table_rows.append({
                'node_name': node,
                'commit_count': node_info.get('commit_count', 0),
                'degree': node_info.get('degree', 0),
                'group': f"Group {node_community + 1}",
                'connected_groups': connected_groups_str
            })
    
    # Sort by commit count (descending) for better readability
    table_rows.sort(key=lambda x: x['commit_count'], reverse=True)
    
    return table_rows

