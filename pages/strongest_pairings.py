from collections.abc import Iterable

from dash import register_page, html, callback, Output, Input, dcc
from dash.dash_table import DataTable
from dash.dcc import Dropdown
from git import Commit

import data
from utils import date_utils
from algorithms.affinity_calculator import calculate_affinities

register_page(__name__)

layout = html.Div(
    children=[
        html.H1("Strongest Commit Affinities", style={"margin": "10px 0"}),
        dcc.Loading(
            id="loading-strongest-pairings-table",
            type="circle",
            children=[
                DataTable(
                    id="id-strongest-pairings-table",
                    columns=[{"name": i, "id": i} for i in ["Affinity", "Pairing"]],
                    style_cell={
                        "textAlign": "left",
                        "padding": "3px 8px",
                        "whiteSpace": "pre-line",
                        "height": "auto",
                        "lineHeight": "1.3",
                    },
                    style_data={"whiteSpace": "pre-line", "height": "auto"},
                    style_table={"maxHeight": "600px", "overflowY": "auto"},
                    data=[],
                )
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
    sorted_pairs = sorted(affinities.items(), key=lambda kv: kv[1], reverse=True)
    return [
        dict(Affinity=f"{value:6.2f}", Pairing="\n".join(key)) for key, value in sorted_pairs[:50]
    ]


@callback(
    Output("id-strongest-pairings-table", "data"),
    Input("global-date-range", "data"),
)
def handle_period_selection(store_data):
    # Use the shared store's explicit begin/end when available
    period = (store_data or {}).get("period", date_utils.DEFAULT_PERIOD)
    if isinstance(store_data, dict) and "begin" in store_data and "end" in store_data:
        from datetime import datetime as _dt

        starting = _dt.fromisoformat(store_data["begin"])
        ending = _dt.fromisoformat(store_data["end"])
    else:
        starting, ending = date_utils.calculate_date_range(period)

    affinity_list = create_affinity_list(data.commits_in_period(starting, ending))
    if not affinity_list:
        return [{"Affinity": "-----", "Pairing": "No commits detected in period"}]
    return affinity_list
