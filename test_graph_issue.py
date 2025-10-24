#!/usr/bin/env python3
"""
Test script to debug the graph creation with very low affinity thresholds.

This script tests the graph creation with the specific parameters mentioned by the user:
time period="Ever", max_nodes=100, min_affinity=0.05.
"""

import sys
import os
from datetime import datetime
import networkx as nx
from collections import defaultdict
from itertools import combinations
from dash import Dash

# Create a Dash app instance to prevent PageError
app = Dash(__name__, suppress_callback_exceptions=True)

# Set up the repository path
sys.argv = ["app.py", os.getcwd()]  # Use current directory as repository path

# Import project modules
from date_utils import calculate_date_range
import data
from pages.affinity_groups import calculate_affinities, create_file_affinity_network

def test_graph_creation():
    """Test the graph creation with the specific parameters mentioned by the user."""
    print("Testing graph creation with user parameters...")
    
    # Get commit data for "Ever" time period
    starting, ending = calculate_date_range("Ever")
    print(f"Date range: {starting} to {ending}")
    
    # Get commits
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
    max_nodes = 100
    min_affinity = 0.05
    print(f"\nCreating network with max_nodes={max_nodes}, min_affinity={min_affinity}...")
    G, communities = create_file_affinity_network(commits_data, min_affinity=min_affinity, max_nodes=max_nodes)
    
    # Print network statistics
    print(f"Network has {len(G.nodes())} nodes and {len(G.edges())} edges")
    print(f"Number of communities: {len(communities)}")
    
    # If no edges, try with lower affinity thresholds
    if len(G.edges()) == 0:
        print("\nNo edges found with min_affinity=0.05. Trying lower thresholds...")
        
        for threshold in [0.04, 0.03, 0.02, 0.01, 0.005, 0.001]:
            print(f"\nTrying min_affinity={threshold}...")
            G, communities = create_file_affinity_network(commits_data, min_affinity=threshold, max_nodes=max_nodes)
            print(f"Network has {len(G.nodes())} nodes and {len(G.edges())} edges")
            
            if len(G.edges()) > 0:
                print(f"Success with min_affinity={threshold}")
                break
    
    # Print some of the nodes and edges for inspection
    if len(G.nodes()) > 0:
        print("\nSample nodes:")
        for node in list(G.nodes())[:5]:
            print(f"  {node}")
    
    if len(G.edges()) > 0:
        print("\nSample edges with weights:")
        for edge in list(G.edges(data=True))[:5]:
            print(f"  {edge[0]} -- {edge[1]} (weight: {edge[2]['weight']:.4f})")

if __name__ == "__main__":
    test_graph_creation()