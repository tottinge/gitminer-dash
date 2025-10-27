
# Import from tests package to set up path
from tests import setup_path
setup_path()  # This ensures we can import modules from the project root
"""
Test script to verify that Dash imports work correctly with the new version.
This script imports the same Dash components used in the application.
"""

# Test basic Dash imports
try:
    from dash import html, dcc, Dash, page_container, page_registry
    from dash import register_page, callback, Output, Input
    from dash.dash_table import DataTable
    from dash.dcc import Dropdown, Graph
    
    print("All Dash imports successful!")
    
    # Print the Dash version
    import dash
    print(f"Dash version: {dash.__version__}")
    
    # Create a simple Dash app to test initialization
    app = Dash(__name__)
    app.layout = html.Div([
        html.H1("Test App"),
        dcc.Graph(id='test-graph')
    ])
    
    print("Dash app initialization successful!")
    
except Exception as e:
    print(f"Error importing Dash components: {e}")