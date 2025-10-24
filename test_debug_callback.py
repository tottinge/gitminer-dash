#!/usr/bin/env python3
"""
Test script to debug the callback function.

This script directly calls the update_file_affinity_graph function with debug prints
to trace what's happening inside it.
"""

import sys
import os
import inspect
import plotly.graph_objects as go
from dash import Dash

# Create a Dash app instance to prevent PageError
app = Dash(__name__, suppress_callback_exceptions=True)

# Set up the repository path
sys.argv = ["app.py", os.getcwd()]  # Use current directory as repository path

# Import project modules
from date_utils import calculate_date_range
import data
from pages.affinity_groups import update_file_affinity_graph

def test_debug_callback():
    """Debug the callback function."""
    print("Debugging callback function...")
    
    # Set the parameters to match the user's scenario
    period = "Ever"
    max_nodes = 100
    min_affinity = 0.05
    
    print(f"Parameters: period={period}, max_nodes={max_nodes}, min_affinity={min_affinity}")
    
    # Add debug prints to the update_file_affinity_graph function
    original_function = update_file_affinity_graph
    
    # Get the source code of the function
    source_code = inspect.getsource(update_file_affinity_graph)
    print("\nOriginal function source code:")
    print(source_code)
    
    # Call the function with debug prints
    print("\nCalling update_file_affinity_graph...")
    try:
        # Call the function
        figure = update_file_affinity_graph(period, max_nodes, min_affinity)
        
        # Check if the figure is a valid Plotly figure
        print(f"Figure type: {type(figure)}")
        print(f"Is it a Plotly figure? {isinstance(figure, go.Figure)}")
        
        # Check if the figure contains an error message
        if hasattr(figure, 'layout') and hasattr(figure.layout, 'annotations') and figure.layout.annotations:
            print(f"Figure contains annotation: {figure.layout.annotations[0].text}")
            if "No data available" in figure.layout.annotations[0].text:
                print("ERROR: Figure shows 'No data available' message")
            elif "Error" in figure.layout.annotations[0].text:
                print(f"ERROR: Figure shows error message: {figure.layout.annotations[0].text}")
        else:
            print("Figure does not contain annotations (this is good)")
        
        # Check if the figure contains data traces
        if hasattr(figure, 'data'):
            print(f"Figure contains {len(figure.data)} data traces")
            
            # Count node and edge traces
            node_traces = [trace for trace in figure.data if trace.mode == 'markers']
            edge_traces = [trace for trace in figure.data if trace.mode == 'lines']
            
            print(f"Node traces: {len(node_traces)}")
            print(f"Edge traces: {len(edge_traces)}")
            
            # Check if there are any nodes or edges
            has_nodes = any(len(trace.x) > 0 for trace in node_traces) if node_traces else False
            has_edges = any(len(trace.x) > 0 for trace in edge_traces) if edge_traces else False
            
            print(f"Has nodes: {has_nodes}")
            print(f"Has edges: {has_edges}")
            
            if not has_nodes and not has_edges:
                print("ERROR: Figure does not contain any nodes or edges")
        else:
            print("ERROR: Figure does not contain data traces")
    
    except Exception as e:
        print(f"Error calling update_file_affinity_graph: {str(e)}")
    
    # Try with a modified version of the function
    print("\nTrying with a modified version of the function...")
    
    # Define a modified version of the function
    def modified_update_file_affinity_graph(period, max_nodes, min_affinity):
        print("Inside modified_update_file_affinity_graph...")
        try:
            print(f"Calculating date range for period={period}")
            starting, ending = calculate_date_range(period)
            print(f"Date range: {starting} to {ending}")
            
            print(f"Getting commits data")
            commits_data = list(data.commits_in_period(starting, ending))
            print(f"Retrieved {len(commits_data)} commits")
            
            # Import here to avoid circular imports
            from pages.affinity_groups import calculate_ideal_affinity, create_file_affinity_network, create_network_visualization
            
            print(f"Calculating ideal affinity")
            ideal_affinity, node_count, edge_count = calculate_ideal_affinity(
                commits_data, target_node_count=15, max_nodes=max_nodes
            )
            print(f"Ideal affinity: {ideal_affinity}, node_count: {node_count}, edge_count: {edge_count}")
            
            print(f"Creating network with min_affinity={min_affinity}, max_nodes={max_nodes}")
            G, communities = create_file_affinity_network(commits_data, min_affinity=min_affinity, max_nodes=max_nodes)
            print(f"Network has {len(G.nodes())} nodes and {len(G.edges())} edges")
            print(f"Number of communities: {len(communities)}")
            
            print(f"Creating network visualization")
            figure = create_network_visualization(G, communities)
            print(f"Visualization created")
            
            return figure
        except ValueError as e:
            print(f"ValueError: {str(e)}")
            raise
        except Exception as e:
            print(f"Exception: {str(e)}")
            raise
    
    # Call the modified function
    try:
        figure = modified_update_file_affinity_graph(period, max_nodes, min_affinity)
        
        # Check if the figure is a valid Plotly figure
        print(f"Figure type: {type(figure)}")
        print(f"Is it a Plotly figure? {isinstance(figure, go.Figure)}")
        
        # Check if the figure contains an error message
        if hasattr(figure, 'layout') and hasattr(figure.layout, 'annotations') and figure.layout.annotations:
            print(f"Figure contains annotation: {figure.layout.annotations[0].text}")
            if "No data available" in figure.layout.annotations[0].text:
                print("ERROR: Figure shows 'No data available' message")
            elif "Error" in figure.layout.annotations[0].text:
                print(f"ERROR: Figure shows error message: {figure.layout.annotations[0].text}")
        else:
            print("Figure does not contain annotations (this is good)")
        
        # Check if the figure contains data traces
        if hasattr(figure, 'data'):
            print(f"Figure contains {len(figure.data)} data traces")
            
            # Count node and edge traces
            node_traces = [trace for trace in figure.data if trace.mode == 'markers']
            edge_traces = [trace for trace in figure.data if trace.mode == 'lines']
            
            print(f"Node traces: {len(node_traces)}")
            print(f"Edge traces: {len(edge_traces)}")
            
            # Check if there are any nodes or edges
            has_nodes = any(len(trace.x) > 0 for trace in node_traces) if node_traces else False
            has_edges = any(len(trace.x) > 0 for trace in edge_traces) if edge_traces else False
            
            print(f"Has nodes: {has_nodes}")
            print(f"Has edges: {has_edges}")
            
            if not has_nodes and not has_edges:
                print("ERROR: Figure does not contain any nodes or edges")
        else:
            print("ERROR: Figure does not contain data traces")
    
    except Exception as e:
        print(f"Error calling modified_update_file_affinity_graph: {str(e)}")

if __name__ == "__main__":
    test_debug_callback()