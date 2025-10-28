from typing import Iterable

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
        html.H1("Strongest Commit Affinities"),
        Dropdown(
            id="id-pairings-period-dropdown",
            options=date_utils.PERIOD_OPTIONS,
            value=date_utils.PERIOD_OPTIONS[0],  # 'Last 7 days'
        ),
        dcc.Loading(
            id="loading-strongest-pairings-table",
            type="circle",
            children=[
                DataTable(
                    id="id-strongest-pairings-table",
                    columns=[
                        {"name": i, "id": i, 'presentation': 'markdown'}
                        for i in ['Affinity', 'Pairing']
                    ],
                    style_cell={'textAlign': 'left'},
                    data=[]
                )
            ]
        )
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
    # Use shared affinity calculator
    affinities = calculate_affinities(dataset)
    
    # Format for display
    affinity_first_list = [
        dict(Affinity=f"{value:6.2f}", Pairing="\n\n".join(key))
        for key, value in affinities.items()
    ]
    sorted_by_strength = sorted(affinity_first_list, reverse=True, key=lambda x: x['Affinity'])
    return sorted_by_strength[:50]


@callback(
    Output("id-strongest-pairings-table", "data"),
    Input("id-pairings-period-dropdown", "value"),
)
def handle_period_selection(period: str):
    # Use the shared date_utils module to calculate begin and end dates
    starting, ending = date_utils.calculate_date_range(period)
    
    affinity_list = create_affinity_list(data.commits_in_period(starting, ending))
    if not affinity_list:
        return [{"Affinity": "-----",
                 "Pairing": "No commits detected in period"}]
    return affinity_list
