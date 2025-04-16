import sys

from dash import html, dcc, Dash, page_container, page_registry

import data

if len(sys.argv) < 2:
    print("Usage: app.py <repo_name>")
    exit(1)

app = Dash(__name__, use_pages=True)

app.layout = html.Div([
    html.H1(f"The Git Miner: {data.get_repo_name()}", style={"text-align": "center"}),
    html.Div([
        dcc.Link(page['name'], href=page['path'])
        for page in page_registry.values()
    ], style={
        "display": "flex",
        "justify-content": "space-between"
    }),
    page_container
])

if __name__ == '__main__':
    app.run(debug=True)
