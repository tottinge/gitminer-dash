from collections.abc import Iterable

from dash import Input, Output, State, callback, dcc, html, register_page
from dash.dash_table import DataTable
from git import Commit

import repository_context as repo_context
from algorithms.affinity_calculator import calculate_affinities
from algorithms.commit_message_classifier import classify_commit_messages
from utils import date_utils
from utils.git import get_commits_for_file_pair
from visualization.common_pair_intent_pane import (
    CommonPairIntentPanePayload,
    build_common_pair_intent_pane,
)

register_page(__name__)

COMMON_PAIR_INTENT_PANE_PREFIX = "id-strongest-pair-intent-pane"
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
                        dcc.Loading(
                            id="loading-common-pair-intent-pane",
                            type="circle",
                            children=[
                                html.Div(
                                    id="id-common-pair-intent-pane-holder",
                                    children=build_common_pair_intent_pane(
                                        payload=None,
                                        component_id_prefix=COMMON_PAIR_INTENT_PANE_PREFIX,
                                    ),
                                )
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
        repo_context.commits_in_period(starting, ending)
    )
    if not affinity_list:
        return [
            {"Affinity": "-----", "Pairing": "No commits detected in period"}
        ]
    return affinity_list


def _selected_pairing_row(active_cell, table_data):
    if not active_cell or not table_data:
        return None

    row_index = active_cell.get("row")
    if not isinstance(row_index, int) or row_index < 0:
        return None
    if row_index >= len(table_data):
        return None

    return table_data[row_index]


def _selected_pair_file_paths(
    selected_row,
) -> tuple[str, str] | None:
    pairing_text = str(selected_row.get("Pairing", ""))
    files = [
        file_path.strip()
        for file_path in pairing_text.split("\n")
        if file_path.strip()
    ]
    if len(files) != 2:
        return None
    return files[0], files[1]


def _selected_pair_intent_payload(
    selected_row, store_data
) -> CommonPairIntentPanePayload | None:
    selected_files = _selected_pair_file_paths(selected_row)
    if not selected_files:
        return None
    first_file_path, second_file_path = selected_files

    period_start, period_end = date_utils.parse_date_range_from_store(
        store_data
    )
    try:
        repo = repo_context.get_repo()
    except ValueError:
        return None

    pair_commits = get_commits_for_file_pair(
        repo,
        first_file_path,
        second_file_path,
        period_start,
        period_end,
    )
    commit_messages = [
        str(pair_commit.get("message", "")) for pair_commit in pair_commits
    ]
    classification_result = classify_commit_messages(commit_messages)
    evidence_rows = [
        {
            "intent": classification["intent"],
            "message": classification["message"],
            "hash": pair_commit.get("hash", "-"),
            "date": pair_commit.get("date", "-"),
        }
        for pair_commit, classification in zip(
            pair_commits,
            classification_result["classifications"],
            strict=True,
        )
    ]

    return {
        "pairing": f"{first_file_path} ↔ {second_file_path}",
        "affinity": str(selected_row.get("Affinity", "")),
        "message_count": classification_result["message_count"],
        "intent_counts": classification_result["intent_counts"],
        "evidence_rows": evidence_rows,
    }


@callback(
    Output("id-common-pair-intent-pane-holder", "children"),
    [
        Input("id-strongest-pairings-table", "active_cell"),
        Input("global-date-range", "data"),
    ],
    State("id-strongest-pairings-table", "data"),
)
def show_pair_intent_sidebar(active_cell, store_data, table_data):
    """Show pair intent snapshot for the selected pairing."""
    selected_row = _selected_pairing_row(active_cell, table_data)
    payload = None
    if selected_row:
        payload = _selected_pair_intent_payload(selected_row, store_data)
    return build_common_pair_intent_pane(
        payload=payload,
        component_id_prefix=COMMON_PAIR_INTENT_PANE_PREFIX,
    )
