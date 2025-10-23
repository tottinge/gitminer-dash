import sys
import plotly.graph_objects as go
from datetime import datetime

# Test the callback with and without a repository path
def test_callback_with_repo_path():
    print("Testing callback with repository path...")
    
    # Import after setting sys.argv to simulate command-line argument
    sys.argv = ["app.py", "."]  # Use current directory as repository path
    
    # Now import the modules that use sys.argv
    import date_utils
    import data
    from pages.affinity_groups import update_file_affinity_graph
    
    # Call the callback function with some test values
    period = "Last 30 days"
    max_nodes = 50
    min_affinity = 0.5
    
    try:
        figure = update_file_affinity_graph(period, max_nodes, min_affinity)
        print("Callback succeeded with repository path.")
        print(f"Figure type: {type(figure)}")
        print(f"Is it a Plotly figure? {isinstance(figure, go.Figure)}")
        return True
    except Exception as e:
        print(f"Callback failed with repository path: {str(e)}")
        return False

def test_callback_without_repo_path():
    print("\nTesting callback without repository path...")
    
    # Reset modules to ensure clean import
    for module in list(sys.modules.keys()):
        if module in ['date_utils', 'data', 'pages.affinity_groups']:
            del sys.modules[module]
    
    # Set sys.argv without repository path
    sys.argv = ["app.py"]
    
    # Now import the modules that use sys.argv
    import date_utils
    from pages.affinity_groups import update_file_affinity_graph
    
    # Call the callback function with some test values
    period = "Last 30 days"
    max_nodes = 50
    min_affinity = 0.5
    
    try:
        figure = update_file_affinity_graph(period, max_nodes, min_affinity)
        print("Callback succeeded without repository path.")
        print(f"Figure type: {type(figure)}")
        print(f"Is it a Plotly figure? {isinstance(figure, go.Figure)}")
        
        # Check if the figure contains an error message
        if hasattr(figure, 'layout') and hasattr(figure.layout, 'annotations') and figure.layout.annotations:
            print(f"Figure contains annotation: {figure.layout.annotations[0].text}")
        
        return True
    except Exception as e:
        print(f"Callback failed without repository path: {str(e)}")
        return False

if __name__ == "__main__":
    # Run the tests
    with_path_result = test_callback_with_repo_path()
    without_path_result = test_callback_without_repo_path()
    
    # Print summary
    print("\nTest Summary:")
    print(f"Callback with repository path: {'PASSED' if with_path_result else 'FAILED'}")
    print(f"Callback without repository path: {'PASSED' if without_path_result else 'FAILED'}")