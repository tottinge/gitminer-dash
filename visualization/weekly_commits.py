"""
Weekly Commits Visualization Module

This module provides visualization functions for weekly commits data.
"""

import plotly.graph_objects as go
from dash import html


def create_weekly_commits_figure(
    weekly_data: dict,
) -> tuple[go.Figure, html.Div]:
    """
    Create a Plotly figure for weekly commits visualization.

    Args:
        weekly_data: Dictionary containing weekly commit data with structure:
            - weeks: List of week data with week_ending, commits, and count
            - min_commits: Minimum commits in any week
            - max_commits: Maximum commits in any week
            - avg_commits: Average commits per week

    Returns:
        A tuple of (figure, stats_html) where:
        - figure is a Plotly Figure object with the stacked bar chart
        - stats_html is a Dash html.Div with statistics
    """
    fig = go.Figure()

    x_labels = []
    for week_info in weekly_data["weeks"]:
        week_ending = week_info["week_ending"]
        x_label = week_ending.strftime("%y-%m-%d")
        x_labels.append(x_label)

    # Add an invisible base trace with all weeks to ensure they all appear on x-axis
    # This trace has y=0 and is not visible, but ensures Plotly shows all x categories
    fig.add_trace(
        go.Bar(
            x=x_labels,
            y=[0] * len(x_labels),
            name="base",
            showlegend=False,
            hoverinfo="skip",  # pragma: no mutate
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
                    f"{commit.committed_datetime.strftime('%Y-%m-%d %H:%M')}"  # pragma: no mutate
                )

        # Only add the trace if there's data for this commit position
        if x_data:
            fig.add_trace(
                go.Bar(
                    x=x_data,
                    y=y_data,
                    name=f"Commit {commit_index + 1}",
                    showlegend=False,
                    hovertemplate="%{hovertext}<extra></extra>",  # pragma: no mutate
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

    stats_html = html.Div(
        [
            html.Span(
                f"Minimum: {weekly_data['min_commits']} commits/week",
                style={"marginRight": "20px"},  # pragma: no mutate
            ),
            html.Span(
                f"Average: {weekly_data['avg_commits']:.1f} commits/week",
                style={"marginRight": "20px"},  # pragma: no mutate
            ),
            html.Span(f"Maximum: {weekly_data['max_commits']} commits/week"),
        ]
    )

    return fig, stats_html
