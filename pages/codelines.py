from datetime import datetime, timedelta

import networkx as nx
import plotly.express as px
from dash import html, register_page, callback, Output, Input, dcc
from pandas import DataFrame

from data import commits_in_period
from algorithms.stacking import SequenceStacker
from algorithms.commit_graph import build_commit_graph
from algorithms.chain_analyzer import analyze_commit_chains
from algorithms.chain_clamper import clamp_chains_to_period
from utils import date_utils

register_page(module=__name__, title="Concurrent Efforts")

layout = html.Div(
    [
        html.H2("Concurrent Effort", style={"margin": "10px 0"}),
        html.Button(id="code-lines-refresh-button", children=["Refresh"]),
        html.Div(
            id="id-code-lines-container",
            style={"display": "none"},
            children=[
                dcc.Loading(
                    id="loading-code-lines-graph",
                    type="circle",
                    children=[
                        dcc.Graph(
                            id="code-lines-graph",
                            figure={"data": []},
                            style={"height": "500px"},
                        ),
                    ],
                ),
            ],
        ),
    ]
)


@callback(
    [Output("code-lines-graph", "figure"), Output("id-code-lines-container", "style")],
    Input("code-lines-refresh-button", "n_clicks"),
    Input("global-date-range", "data"),
    running=[(Output("code-lines-refresh-button", "disabled"), True, False)],
)
def update_code_lines_graph(_: int, store_data):
    show = {"display": "block"}

    # Determine range from global store
    start_date, end_date = date_utils.parse_date_range_from_store(store_data)

    # Build commit graph
    commits = commits_in_period(start_date, end_date)
    graph = build_commit_graph(commits)

    # Analyze chains
    chains = analyze_commit_chains(graph)

    # Clamp chains to the selected period
    clamped_chains = clamp_chains_to_period(chains, start_date, end_date)

    # Convert chains to timeline rows
    rows = []
    stacker = SequenceStacker()

    for clamped in clamped_chains:
        height = stacker.height_for([clamped.clamped_first, clamped.clamped_last])
        rows.append(
            dict(
                first=clamped.clamped_first,
                last=clamped.clamped_last,
                elevation=height,
                commit_counts=clamped.commit_count,
                head=clamped.earliest_sha,
                tail=clamped.latest_sha,
                duration=clamped.clamped_duration.days,
                density=(clamped.clamped_duration.days / clamped.commit_count) if clamped.commit_count else 0,
            )
        )

    df = DataFrame(
        rows,
        columns=[
            "first",
            "last",
            "elevation",
            "commit_counts",
            "head",
            "tail",
            "duration",
            "density",
        ],
    )
    # Convert datetime columns to pandas datetime type
    df["first"] = df["first"].astype("datetime64[ns]")
    df["last"] = df["last"].astype("datetime64[ns]")
    
    figure = px.timeline(
        data_frame=df,
        x_start="first",
        x_end="last",
        y="elevation",
        color="density",
        title="Code Lines (selected period)",
        labels={
            "elevation": "",
            "density": "Commit Sparsity",
            "first": "Begun",
            "last": "Ended",
            "duration": "Days",
        },
        hover_data={
            "first": True,
            "head": True,
            "last": True,
            "tail": True,
            "commit_counts": True,
            "duration": True,
            "elevation": False,
            "density": True,
        },
    )
    return figure, show
