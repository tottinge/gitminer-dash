#!/usr/bin/env python3
"""
Test script to verify that the callback function displays the appropriate message
when no repository path is provided.
"""

import sys
import os
from dash import Dash

# Create a Dash app instance to prevent PageError
app = Dash(__name__, suppress_callback_exceptions=True)

# First, test without a repository path
print("Testing callback without repository path...")
sys.argv = ["app.py"]  # Simulate running without a repository path

try:
    # Import the callback function
    from pages.affinity_groups import update_file_affinity_graph
    
    # Call the callback function with some test values
    period = "Last 30 days"
    max_nodes = 50
    min_affinity = 0.2
    
    figure = update_file_affinity_graph(period, max_nodes, min_affinity)
    
    # Check if the figure contains the expected message
    if hasattr(figure, 'layout') and hasattr(figure.layout, 'annotations') and figure.layout.annotations:
        message = figure.layout.annotations[0].text
        print(f"Message displayed: {message}")
        
        if "No repository path provided" in message:
            print("✓ Test passed: Correct message displayed when no repository path is provided")
        else:
            print("✗ Test failed: Incorrect message displayed")
    else:
        print("✗ Test failed: No message displayed")
    
except Exception as e:
    print(f"Error: {str(e)}")

# Reset modules to ensure clean state
for module in list(sys.modules.keys()):
    if module in ['data', 'date_utils', 'pages.affinity_groups']:
        del sys.modules[module]

# Now test with a repository path
print("\nTesting callback with repository path...")
sys.argv = ["app.py", os.getcwd()]  # Use current directory as repository path

try:
    # Import the callback function
    from pages.affinity_groups import update_file_affinity_graph
    
    # Call the callback function with some test values
    period = "Last 30 days"
    max_nodes = 50
    min_affinity = 0.2
    
    figure = update_file_affinity_graph(period, max_nodes, min_affinity)
    
    # Check if the figure contains a graph (no error message)
    if hasattr(figure, 'layout') and hasattr(figure.layout, 'annotations') and figure.layout.annotations:
        message = figure.layout.annotations[0].text
        if "Error" in message or "No repository path provided" in message:
            print(f"✗ Test failed: Error message displayed: {message}")
        else:
            print("✓ Test passed: No error message displayed when repository path is provided")
    else:
        print("✓ Test passed: No error message displayed when repository path is provided")
    
except Exception as e:
    print(f"Error: {str(e)}")