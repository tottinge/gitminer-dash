"""
Weekly Commits Page

Displays a stacked bar chart showing commits per week, with interactive
selection to view commit details for a specific week.
"""

import plotly.graph_objects as go
from dash import html, register_page, dcc, callback, Output, Input, State
from dash.dash_table import DataTable
from dash.exceptions import PreventUpdate

import data
from utils import date_utils
from algorithms.weekly_commits import calculate_weekly_commits, extract_commit_details

register_page(
    module=__name__,
    name="Weekly Commits",
)

layout = html.Div(
    [
        html.H2("Weekly Commits", style={"margin": "10px 0"}),
        html.Div(
            id="id-weekly-commits-graph-holder",
            style={"display": "none"},
            children=[
                dcc.Loading(
                    id="loading-weekly-graph",
                    type="circle",
                    children=[
                        dcc.Graph(id="id-weekly-commits-graph", figure={"data": []}),
                    ],
                ),
            ],
        ),
        html.Div(
            id="id-weekly-stats",
            style={"margin": "20px 0", "fontSize": "16px"},
        ),
        html.H3("Commit Details", style={"margin": "20px 0 10px 0"}),
        html.P(
            id="id-week-selection-message",
            children="Click on a week's bar to see commit details.",
            style={"fontStyle": "italic", "color": "#666"},
        ),
        dcc.Loading(
            id="loading-weekly-table",
            type="circle",
            children=[
                DataTable(
                    id="id-weekly-commits-table",
                    columns=[
                        {"name": "Date", "id": "date"},
                        {"name": "Committer", "id": "committer"},
                        {"name": "Description", "id": "description"},
                        {"name": "Lines Added", "id": "lines_added"},
                        {"name": "Lines Removed", "id": "lines_removed"},
                        {"name": "Lines Modified", "id": "lines_modified"},
                    ],
                    style_table={"maxHeight": "400px", "overflowY": "auto"},
                    style_cell={
                        "textAlign": "left",
                        "padding": "8px",
                    },
                    style_cell_conditional=[
                        {"if": {"column_id": "description"}, "width": "40%"},
                        {"if": {"column_id": "date"}, "width": "15%"},
                        {"if": {"column_id": "committer"}, "width": "15%"},
                    ],
                    data=[],
                )
            ],
        ),
        # Hidden store for weekly data
        dcc.Store(id="id-weekly-data-store"),
    ]
)


@callback(
    [
        Output("id-weekly-commits-graph", "figure"),
        Output("id-weekly-stats", "children"),
        Output("id-weekly-commits-graph-holder", "style"),
        Output("id-weekly-data-store", "data"),
    ],
    Input("global-date-range", "data"),
)
def populate_graph(store_data):
    """Generate the weekly commits graph and statistics."""
    if not store_data or "period" not in store_data:
        raise PreventUpdate

    period_input = store_data["period"]
    if "begin" in store_data and "end" in store_data:
        from datetime import datetime as _dt

        begin = _dt.fromisoformat(store_data["begin"])
        end = _dt.fromisoformat(store_data["end"])
    else:
        begin, end = date_utils.calculate_date_range(period_input)

    commits_data = data.commits_in_period(begin, end)
    weekly_data = calculate_weekly_commits(commits_data, begin, end)

    fig = go.Figure()

    if not weekly_data["weeks"]:
        fig.add_annotation(
            text="No data in selected period",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        stats_text = "No commits in selected period"
        return fig, stats_text, {"display": "block"}, {"weeks": []}

    x_labels = []
    week_data_for_store = []
    
    for week_info in weekly_data["weeks"]:
        week_ending = week_info["week_ending"]
        x_label = week_ending.strftime("%y-%m-%d")
        x_labels.append(x_label)
        
        # Store week info for click handling
        week_data_for_store.append({
            "week_ending": week_ending.isoformat(),
            "x_label": x_label,
            "commits": [c.hexsha for c in week_info["commits"]],
        })
    
    # Add an invisible base trace with all weeks to ensure they all appear on x-axis
    # This trace has y=0 and is not visible, but ensures Plotly shows all x categories
    fig.add_trace(
        go.Bar(
            x=x_labels,
            y=[0] * len(x_labels),
            name="base",
            showlegend=False,
            hoverinfo="skip",
            opacity=0,
        )
    )
    
    # Find the maximum number of commits in any week to determine how many traces we need
    max_commits_in_week = max(len(w["commits"]) for w in weekly_data["weeks"])
    
    # Create one trace per "commit position" (1st commit, 2nd commit, etc.)
    # Each trace spans all weeks but only has data where that position exists
    for commit_index in range(max_commits_in_week):
        x_data = []
        y_data = []
        hover_text = []
        
        for week_info in weekly_data["weeks"]:
            week_ending = week_info["week_ending"]
            x_label = week_ending.strftime("%y-%m-%d")
            commits = week_info["commits"]
            
            # If this week has a commit at this index, add it
            if commit_index < len(commits):
                commit = commits[commit_index]
                x_data.append(x_label)
                y_data.append(1)  # Each commit is one unit tall
                hover_text.append(
                    f"<b>{commit.summary[:50]}</b><br>"
                    f"{commit.committer.name}<br>"
                    f"{commit.committed_datetime.strftime('%Y-%m-%d %H:%M')}"
                )
        
        # Only add the trace if there's data for this commit position
        if x_data:
            fig.add_trace(
                go.Bar(
                    x=x_data,
                    y=y_data,
                    name=f"Commit {commit_index + 1}",
                    showlegend=False,
                    hovertemplate="%{hovertext}<extra></extra>",
                    hovertext=hover_text,
                )
            )

    fig.update_layout(
        barmode="stack",
        xaxis_title="Week Ending",
        yaxis_title="Number of Commits",
        xaxis={
            "type": "category",
            "categoryorder": "array",
            "categoryarray": x_labels,
        },
        hovermode="closest",
        height=500,
    )

    stats_text = html.Div(
        [
            html.Span(f"Minimum: {weekly_data['min_commits']} commits/week", style={"marginRight": "20px"}),
            html.Span(f"Average: {weekly_data['avg_commits']:.1f} commits/week", style={"marginRight": "20px"}),
            html.Span(f"Maximum: {weekly_data['max_commits']} commits/week"),
        ]
    )

    return fig, stats_text, {"display": "block"}, {"weeks": week_data_for_store}


@callback(
    [
        Output("id-weekly-commits-table", "data"),
        Output("id-week-selection-message", "children"),
    ],
    Input("id-weekly-commits-graph", "clickData"),
    [
        State("id-weekly-data-store", "data"),
        State("global-date-range", "data"),
    ],
)
def update_table_on_click(click_data, weekly_store, date_store):
    """Update the table when a week is clicked."""
    if not click_data or not weekly_store or not date_store:
        raise PreventUpdate

    clicked_x = click_data["points"][0]["x"]

    clicked_week = None
    for week in weekly_store["weeks"]:
        if week["x_label"] == clicked_x:
            clicked_week = week
            break

    if not clicked_week or not clicked_week["commits"]:
        return [], f"Week ending {clicked_x}: No commits"

    repo = data.get_repo()
    commit_details = []
    for commit_sha in clicked_week["commits"]:
        commit = repo.commit(commit_sha)
        details = extract_commit_details(commit)
        commit_details.append(details)

    commit_details.sort(key=lambda x: x["date"])

    message = f"Week ending {clicked_x}: {len(commit_details)} commit(s)"

    return commit_details, message
