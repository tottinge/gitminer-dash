#!/usr/bin/env python3
"""
Test script to verify if the "no data available" issue is related to the repository path.
"""

import sys
import os
from datetime import datetime
from pathlib import Path
import networkx as nx
from collections import defaultdict
from itertools import combinations

# Function to calculate affinities (copied from affinity_groups.py to avoid import issues)
def calculate_affinities(commits):
    """Calculate file affinities based on commit data."""
    affinities = defaultdict(float)
    for commit in commits:
        files_in_commit = len(commit.stats.files)
        if files_in_commit < 2:
            continue
        for combo in combinations(commit.stats.files, 2):
            ordered_key = tuple(sorted(combo))
            affinities[ordered_key] += 1 / files_in_commit
    return affinities

# Function to create network (simplified version from affinity_groups.py)
def create_simple_network(commits, min_affinity=0.2, max_nodes=50):
    """Create a simplified network graph for testing."""
    if not commits:
        return nx.Graph()
    
    affinities = calculate_affinities(commits)
    G = nx.Graph()
    
    # Calculate total affinity for each file
    file_total_affinity = defaultdict(float)
    for (file1, file2), affinity in affinities.items():
        file_total_affinity[file1] += affinity
        file_total_affinity[file2] += affinity
    
    # Get top files
    top_files = sorted(file_total_affinity.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
    top_file_set = {file for file, _ in top_files}
    
    # Add nodes
    for file in top_file_set:
        G.add_node(file)
    
    # Add edges
    for (file1, file2), affinity in affinities.items():
        if file1 in top_file_set and file2 in top_file_set and affinity >= min_affinity:
            G.add_edge(file1, file2, weight=affinity)
    
    return G

# First, test without a repository path
print("Testing without repository path...")
sys.argv = ["app.py"]  # Simulate running without a repository path

try:
    import data
    from date_utils import calculate_date_range
    
    # Try to get commits
    starting, ending = calculate_date_range("Last 30 days")
    commits_data = list(data.commits_in_period(starting, ending))
    
    print(f"Retrieved {len(commits_data)} commits")
    
    # Try to create a network
    G = create_simple_network(commits_data, min_affinity=0.2, max_nodes=50)
    
    # Check if we have any nodes
    print(f"Graph has {len(G.nodes())} nodes and {len(G.edges())} edges")
    
except Exception as e:
    print(f"Error: {str(e)}")

# Reset modules to ensure clean state
for module in list(sys.modules.keys()):
    if module in ['data', 'date_utils']:
        del sys.modules[module]

# Now test with a repository path (current directory)
print("\nTesting with repository path...")
sys.argv = ["app.py", os.getcwd()]  # Use current directory as repository path

try:
    import data
    from date_utils import calculate_date_range
    
    # Try to get commits
    starting, ending = calculate_date_range("Last 30 days")
    commits_data = list(data.commits_in_period(starting, ending))
    
    print(f"Retrieved {len(commits_data)} commits")
    
    # Try to create a network
    G = create_simple_network(commits_data, min_affinity=0.2, max_nodes=50)
    
    # Check if we have any nodes
    print(f"Graph has {len(G.nodes())} nodes and {len(G.edges())} edges")
    
except Exception as e:
    print(f"Error: {str(e)}")