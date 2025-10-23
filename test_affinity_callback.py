import sys

import plotly.graph_objects as go
import pytest
from dash import Dash

app = Dash(__name__, suppress_callback_exceptions=True)


# Test the callback with and without a repository path
def test_callback_with_repo_path():
    print("Testing callback with repository path...")

    sys.argv = ["app.py", "."]

    from pages.affinity_groups import update_file_affinity_graph

    period = "Last 30 days"
    max_nodes = 50
    min_affinity = 0.5

    try:
        figure = update_file_affinity_graph(period, max_nodes, min_affinity)
        print("Callback succeeded with repository path.")
        print(f"Figure type: {type(figure)}")
        print(f"Is it a Plotly figure? {isinstance(figure, go.Figure)}")
        assert isinstance(figure, go.Figure)
    except Exception as e:
        print(f"Callback failed with repository path: {str(e)}")
        pytest.fail(f"Test failed with exception: {str(e)}")


def test_callback_without_repo_path():
    print("\nTesting callback without repository path...")

    for module in list(sys.modules.keys()):
        if module in ['date_utils', 'data', 'pages.affinity_groups']:
            del sys.modules[module]

    sys.argv = ["app.py"]

    from pages.affinity_groups import update_file_affinity_graph

    period = "Last 30 days"
    max_nodes = 50
    min_affinity = 0.5

    try:
        figure = update_file_affinity_graph(period, max_nodes, min_affinity)
        print("Callback succeeded without repository path.")
        print(f"Figure type: {type(figure)}")
        print(f"Is it a Plotly figure? {isinstance(figure, go.Figure)}")

        assert isinstance(figure, go.Figure)

        # Check if the figure contains an error message
        if hasattr(figure, 'layout') and hasattr(figure.layout, 'annotations') and figure.layout.annotations:
            print(f"Figure contains annotation: {figure.layout.annotations[0].text}")
            assert figure.layout.annotations[0].text != ""

    except Exception as e:
        print(f"Callback failed without repository path: {str(e)}")
        pytest.fail(f"Test failed with exception: {str(e)}")


if __name__ == "__main__":
    test_callback_with_repo_path()
    test_callback_without_repo_path()
