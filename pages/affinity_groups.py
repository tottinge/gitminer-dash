import plotly.graph_objects as go
from collections import defaultdict
from dash import register_page, html, callback, Output, Input, dcc, State, no_update
from dash.dcc import Dropdown, Slider
from dash.html import Button

import data
import date_utils
from algorithms.affinity_calculator import calculate_affinities
from visualization.network_graph import create_file_affinity_network, create_network_visualization

register_page(__name__, title="Affinity Groups")

layout = html.Div(
    children=[
        html.H1("File Affinity Groups"),
        html.P("Files that frequently change together are grouped by color. Node size indicates how many connections a file has."),
        html.Div(
            style={"display": "flex", "justify-content": "space-between", "align-items": "center", "margin-bottom": "20px"},
            children=[
                html.Div(
                    style={"width": "30%"},
                    children=[
                        html.Label("Time Period:"),
                        Dropdown(
                            id="id-affinity-period-dropdown",
                            options=date_utils.PERIOD_OPTIONS,
                            value=date_utils.PERIOD_OPTIONS[len(date_utils.PERIOD_OPTIONS)//2],
                        ),
                    ]
                ),
                html.Div(
                    style={"width": "30%"},
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
                    style={"width": "30%"},
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
        )
    ]
)


def find_affinity_range(commits, max_nodes=50):
    """
    Find the minimum and maximum affinity values in the dataset.
    
    Args:
        commits: Iterable of commit objects
        max_nodes: Maximum number of nodes to consider (default: 50)
        
    Returns:
        A tuple of (min_affinity, max_affinity, ideal_affinity)
    """
    if not commits:
        return 0.05, 0.5, 0.2  # Default values if no commits
    
    # Reset commits iterator if it was consumed
    if hasattr(commits, 'seek') and callable(getattr(commits, 'seek')):
        commits.seek(0)
    elif not hasattr(commits, '__len__'):
        commits = list(commits)
    
    affinities = calculate_affinities(commits)
    
    if not affinities:
        return 0.05, 0.5, 0.2  # Default values if no affinities
    
    # Get unique files and their total affinities
    file_total_affinity = defaultdict(float)
    for (file1, file2), affinity in affinities.items():
        file_total_affinity[file1] += affinity
        file_total_affinity[file2] += affinity
    
    # Get top files by total affinity
    top_files = sorted(file_total_affinity.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
    top_file_set = {file for file, _ in top_files}
    
    # Get all affinity values between top files
    relevant_affinities = []
    for (file1, file2), affinity in affinities.items():
        if file1 in top_file_set and file2 in top_file_set:
            relevant_affinities.append(affinity)
    
    if not relevant_affinities:
        return 0.05, 0.5, 0.2  # Default values if no relevant affinities
    
    # Find min and max affinity values
    min_affinity = max(0.05, min(relevant_affinities))  # Ensure min is at least 0.05
    max_affinity = min(0.5, max(relevant_affinities))   # Ensure max is at most 0.5
    
    # Calculate ideal affinity
    ideal_affinity, _, _ = calculate_ideal_affinity(commits, target_node_count=15, max_nodes=max_nodes)
    
    # Ensure ideal affinity is within the min-max range
    ideal_affinity = max(min_affinity, min(max_affinity, ideal_affinity))
    
    return min_affinity, max_affinity, ideal_affinity

def calculate_ideal_affinity(commits, target_node_count=15, max_nodes=50):
    """
    Calculate an ideal minimum affinity threshold that will result in approximately
    the target number of connected nodes.
    
    Args:
        commits: Iterable of commit objects
        target_node_count: Target number of nodes in the final graph (default: 15)
        max_nodes: Maximum number of nodes to consider (default: 50)
        
    Returns:
        A tuple of (ideal_min_affinity, estimated_node_count, estimated_edge_count)
    """
    if not commits:
        return 0.2, 0, 0  # Default values if no commits
    
    # Reset commits iterator if it was consumed
    if hasattr(commits, 'seek') and callable(getattr(commits, 'seek')):
        commits.seek(0)
    elif not hasattr(commits, '__len__'):
        commits = list(commits)
    
    affinities = calculate_affinities(commits)

    # Get unique files and their total affinities
    file_total_affinity = defaultdict(float)
    for (file1, file2), affinity in affinities.items():
        file_total_affinity[file1] += affinity
        file_total_affinity[file2] += affinity
    
    # Get top files by total affinity
    top_files = sorted(file_total_affinity.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
    top_file_set = {file for file, _ in top_files}
    
    # Get all affinity values between top files
    relevant_affinities = []
    for (file1, file2), affinity in affinities.items():
        if file1 in top_file_set and file2 in top_file_set:
            relevant_affinities.append(affinity)
    
    if not relevant_affinities:
        return 0.2, 0, 0  # Default if no relevant affinities

    # Try different thresholds to find one that gives us the target node count
    thresholds = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
    best_threshold = 0.2  # Default if we can't find a better one
    best_node_count = 0
    best_edge_count = 0
    
    for threshold in thresholds:
        # Count edges that would be included with this threshold
        edge_count = sum(1 for a in relevant_affinities if a >= threshold)
        
        # Estimate connected nodes (this is an approximation)
        connected_nodes = set()
        for (file1, file2), affinity in affinities.items():
            if file1 in top_file_set and file2 in top_file_set and affinity >= threshold:
                connected_nodes.add(file1)
                connected_nodes.add(file2)
        
        node_count = len(connected_nodes)
        
        # If this threshold gives us a node count in our target range, use it
        if 5 <= node_count <= 20:
            best_threshold = threshold
            best_node_count = node_count
            best_edge_count = edge_count
            break
        
        # If we're below the target range but better than our current best, update
        if node_count > 0 and abs(node_count - target_node_count) < abs(best_node_count - target_node_count):
            best_threshold = threshold
            best_node_count = node_count
            best_edge_count = edge_count
    
    return best_threshold, best_node_count, best_edge_count






@callback(
    Output("id-affinity-min-slider", "min"),
    Output("id-affinity-min-slider", "max"),
    Output("id-affinity-min-slider", "value"),
    Output("id-affinity-min-slider", "marks"),
    Output("id-auto-affinity-info", "children"),
    [Input("id-auto-affinity-button", "n_clicks")],
    [State("id-affinity-period-dropdown", "value"),
     State("id-affinity-node-slider", "value")],
    prevent_initial_call=True
)
def auto_calculate_affinity(n_clicks, period, max_nodes):
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
    [Input("id-affinity-period-dropdown", "value"),
     Input("id-affinity-node-slider", "value"),
     Input("id-affinity-min-slider", "value")]
)
def update_file_affinity_graph(period: str, max_nodes: int, min_affinity: float):
    try:
        starting, ending = date_utils.calculate_date_range(period)
        # Convert commits_data to a list to prevent the iterator from being consumed
        commits_data = list(data.commits_in_period(starting, ending))
        
        # Calculate ideal affinity
        ideal_affinity, _, _ = calculate_ideal_affinity(
            commits_data, target_node_count=15, max_nodes=max_nodes
        )
        
        # Use the provided min_affinity value
        # Note: create_file_affinity_network now returns (G, communities, stats)
        G, communities, stats = create_file_affinity_network(commits_data, min_affinity=min_affinity, max_nodes=max_nodes)
        return create_network_visualization(G, communities)
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
            return fig
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
            return fig
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
        return fig