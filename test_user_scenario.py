#!/usr/bin/env python3
"""
Test script to simulate the exact user scenario:
- Running the application with a repository path
- Setting the parameters to time period="Ever", max_nodes=100, min_affinity=0.05
"""

import sys
import os
import plotly.graph_objects as go
from dash import Dash

# Create a Dash app instance to prevent PageError
app = Dash(__name__, suppress_callback_exceptions=True)

# Set up the repository path
sys.argv = ["app.py", os.getcwd()]  # Use current directory as repository path

# Import project modules
from date_utils import calculate_date_range
import data
from pages.affinity_groups import (
    update_file_affinity_graph, 
    create_file_affinity_network, 
    calculate_affinities,
    calculate_ideal_affinity,
    create_network_visualization
)

def test_user_scenario():
    """Test the exact user scenario."""
    print("Testing user scenario...")
    
    # Set the parameters to match the user's scenario
    period = "Ever"
    max_nodes = 100
    min_affinity = 0.05
    
    print(f"Parameters: period={period}, max_nodes={max_nodes}, min_affinity={min_affinity}")
    
    # Get the commits data
    starting, ending = calculate_date_range(period)
    print(f"Date range: {starting} to {ending}")
    
    commits_data = list(data.commits_in_period(starting, ending))
    print(f"Retrieved {len(commits_data)} commits")
    
    # Calculate affinities
    affinities = calculate_affinities(commits_data)
    print(f"Calculated {len(affinities)} file pair affinities")
    
    # Print some statistics about the affinities
    if affinities:
        affinity_values = list(affinities.values())
        print(f"Affinity range: {min(affinity_values):.4f} to {max(affinity_values):.4f}")
        print(f"Average affinity: {sum(affinity_values) / len(affinity_values):.4f}")
    
    # Create network with user parameters
    print(f"\nCreating network with max_nodes={max_nodes}, min_affinity={min_affinity}...")
    G, communities = create_file_affinity_network(commits_data, min_affinity=min_affinity, max_nodes=max_nodes)
    
    # Print network statistics
    print(f"Network has {len(G.nodes())} nodes and {len(G.edges())} edges")
    print(f"Number of communities: {len(communities)}")
    
    # Print some of the nodes and edges for inspection
    if len(G.nodes()) > 0:
        print("\nSample nodes:")
        for node in list(G.nodes())[:5]:
            print(f"  {node}")
    
    if len(G.edges()) > 0:
        print("\nSample edges with weights:")
        for edge in list(G.edges(data=True))[:5]:
            print(f"  {edge[0]} -- {edge[1]} (weight: {edge[2]['weight']:.4f})")
    
    # Call the callback function directly
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
    
    # Try with different time periods
    print("\nTrying different time periods...")
    for test_period in ["Last 7 days", "Last 30 days", "Last 90 days", "Last 6 Months", "Last 1 Year", "Last 5 Years", "Ever"]:
        print(f"\nTesting with period={test_period}")
        figure = update_file_affinity_graph(test_period, max_nodes, min_affinity)
        
        # Check if the figure contains data traces
        if hasattr(figure, 'data'):
            node_traces = [trace for trace in figure.data if trace.mode == 'markers']
            edge_traces = [trace for trace in figure.data if trace.mode == 'lines']
            
            has_nodes = any(len(trace.x) > 0 for trace in node_traces) if node_traces else False
            has_edges = any(len(trace.x) > 0 for trace in edge_traces) if edge_traces else False
            
            print(f"Has nodes: {has_nodes}")
            print(f"Has edges: {has_edges}")
        else:
            print("Figure does not contain data traces")
    
    # Try with different min_affinity values
    print("\nTrying different min_affinity values...")
    for test_affinity in [0.5, 0.2, 0.1, 0.05, 0.01]:
        print(f"\nTesting with min_affinity={test_affinity}")
        figure = update_file_affinity_graph("Ever", max_nodes, test_affinity)
        
        # Check if the figure contains data traces
        if hasattr(figure, 'data'):
            node_traces = [trace for trace in figure.data if trace.mode == 'markers']
            edge_traces = [trace for trace in figure.data if trace.mode == 'lines']
            
            has_nodes = any(len(trace.x) > 0 for trace in node_traces) if node_traces else False
            has_edges = any(len(trace.x) > 0 for trace in edge_traces) if edge_traces else False
            
            print(f"Has nodes: {has_nodes}")
            print(f"Has edges: {has_edges}")
        else:
            print("Figure does not contain data traces")

if __name__ == "__main__":
    test_user_scenario()