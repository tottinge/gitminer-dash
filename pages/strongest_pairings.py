from collections.abc import Iterable

from dash import Input, Output, State, callback, dcc, html, register_page
from dash.dash_table import DataTable
from git import Commit

import data
from algorithms.affinity_calculator import calculate_affinities
from utils import date_utils
from utils.git import get_commits_for_file_pair

register_page(__name__)

layout = html.Div(
    children=[
        html.H1("Strongest Commit Affinities", style={"margin": "10px 0"}),
        html.Div(
            style={"display": "flex", "gap": "20px"},
            children=[
                # Left side: Pairings table
                html.Div(
                    style={"flex": "1", "minWidth": "300px"},
                    children=[
                        dcc.Loading(
                            id="loading-strongest-pairings-table",
                            type="circle",
                            children=[
                                DataTable(
                                    id="id-strongest-pairings-table",
                                    columns=[
                                        {"name": i, "id": i}
                                        for i in ["Affinity", "Pairing"]
                                    ],
                                    style_cell={
                                        "textAlign": "left",
                                        "padding": "3px 8px",
                                        "whiteSpace": "pre-line",
                                        "height": "auto",
                                        "lineHeight": "1.3",
                                        "cursor": "pointer",
                                    },
                                    style_data={
                                        "whiteSpace": "pre-line",
                                        "height": "auto",
                                    },
                                    style_data_conditional=[
                                        {
                                            "if": {"state": "active"},
                                            "backgroundColor": "#e6f3ff",
                                            "border": "1px solid #0066cc",
                                        }
                                    ],
                                    style_table={
                                        "maxHeight": "600px",
                                        "overflowY": "auto",
                                    },
                                    data=[],
                                )
                            ],
                        ),
                    ],
                ),
                # Right side: Commit details
                html.Div(
                    style={"flex": "1", "minWidth": "400px"},
                    children=[
                        html.Div(
                            id="id-commit-details-container",
                            style={"display": "none"},
                            children=[
                                html.H3(
                                    id="id-commit-details-title",
                                    style={"margin": "0 0 10px 0"},
                                ),
                                dcc.Loading(
                                    id="loading-commit-details-table",
                                    type="circle",
                                    children=[
                                        DataTable(
                                            id="id-commit-details-table",
                                            columns=[
                                                {"name": "Hash", "id": "hash"},
                                                {"name": "Date", "id": "date"},
                                                {
                                                    "name": "Message",
                                                    "id": "message",
                                                },
                                            ],
                                            style_cell={
                                                "textAlign": "left",
                                                "padding": "3px 8px",
                                            },
                                            style_table={
                                                "maxHeight": "600px",
                                                "overflowY": "auto",
                                            },
                                            data=[],
                                        )
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ]
)


def create_affinity_list(dataset: Iterable[Commit]) -> list[dict[str, str]]:
    """
    This method should be called with a series of commits, and will provide pairings
    that occur together frequently (other than in massive merge checkins).

    > a = create_affinity_list([commit_with('a','b','c'), commit_with('b','a')])


    Called with an empty list, returns an empty list.
    > create_affinity_list([])
    []

    > create_affinity_list([commit_with(['a','b']), commit_with(['b','c'])])\

    """
    affinities = calculate_affinities(dataset)

    # Sort by numeric affinity value, then format for display
    sorted_pairs = sorted(
        affinities.items(), key=lambda kv: kv[1], reverse=True
    )
    return [
        dict(Affinity=f"{value:6.2f}", Pairing="\n".join(key))
        for key, value in sorted_pairs[:50]
    ]


@callback(
    Output("id-strongest-pairings-table", "data"),
    Input("global-date-range", "data"),
)
def handle_period_selection(store_data):
    # Use the shared store's explicit begin/end when available
    period = (store_data or {}).get("period", date_utils.DEFAULT_PERIOD)
    if (
        isinstance(store_data, dict)
        and "begin" in store_data
        and "end" in store_data
    ):
        from datetime import datetime as _dt

        starting = _dt.fromisoformat(store_data["begin"])
        ending = _dt.fromisoformat(store_data["end"])
    else:
        starting, ending = date_utils.calculate_date_range(period)

    affinity_list = create_affinity_list(
        data.commits_in_period(starting, ending)
    )
    if not affinity_list:
        return [
            {"Affinity": "-----", "Pairing": "No commits detected in period"}
        ]
    return affinity_list


@callback(
    [
        Output("id-commit-details-container", "style"),
        Output("id-commit-details-title", "children"),
        Output("id-commit-details-table", "data"),
    ],
    [
        Input("id-strongest-pairings-table", "active_cell"),
        Input("global-date-range", "data"),
    ],
    State("id-strongest-pairings-table", "data"),
)
def show_commit_details(active_cell, store_data, table_data):
    """Show commit details for the selected pairing."""
    if not active_cell or not table_data:
        return {"display": "none"}, "", []

    # Get the selected row data
    row_index = active_cell["row"]
    selected_row = table_data[row_index]
    pairing_text = selected_row.get("Pairing", "")

    # Extract the two files from the pairing (they're separated by newline)
    files = [f.strip() for f in pairing_text.split("\n") if f.strip()]
    if len(files) != 2:
        return {"display": "none"}, "", []

    file1, file2 = files

    # Get date range
    if (
        isinstance(store_data, dict)
        and "begin" in store_data
        and "end" in store_data
    ):
        from datetime import datetime as _dt

        starting = _dt.fromisoformat(store_data["begin"])
        ending = _dt.fromisoformat(store_data["end"])
    else:
        period = (store_data or {}).get("period", date_utils.DEFAULT_PERIOD)
        starting, ending = date_utils.calculate_date_range(period)

    # Get commits involving both files
    repo = data.get_repo()
    commits = get_commits_for_file_pair(repo, file1, file2, starting, ending)

    # Create title and show container
    title = f"Commits for: {file1} & {file2}"
    if not commits:
        commits = [{"hash": "-", "date": "-", "message": "No commits found"}]

    return {"display": "block"}, title, commits
