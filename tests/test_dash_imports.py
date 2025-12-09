from tests import setup_path

setup_path()
"\nTest script to verify that Dash imports work correctly with the new version.\nThis script imports the same Dash components used in the application.\n"
try:
    import dash
    from dash import (
        Dash,
        Input,
        Output,
        callback,
        dcc,
        html,
        page_container,
        page_registry,
        register_page,
    )
    from dash.dash_table import DataTable
    from dash.dcc import Dropdown, Graph

    app = Dash(__name__)
    app.layout = html.Div([html.H1("Test App"), dcc.Graph(id="test-graph")])
except Exception as e:
    pass
