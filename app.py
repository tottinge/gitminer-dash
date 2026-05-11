import sys

from dash import (
    Dash,
    Input,
    Output,
    callback,
    dcc,
    html,
    page_container,
    page_registry,
)

import repository_context as repo_context
from utils import date_utils
from utils.global_date_store import build_store_payload

if len(sys.argv) < 2:
    print("Usage: app.py <repo_name>")
    sys.exit(1)

app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
NAV_CONTAINER_STYLE = {
    "display": "flex",
    "flexWrap": "wrap",
    "gap": "8px",
    "alignItems": "center",
    "margin": "8px 0 12px",
    "padding": "10px",
    "border": "1px solid #d9dee8",
    "borderRadius": "10px",
    "backgroundColor": "#f8fafc",
    "boxShadow": "0 1px 2px rgba(15, 23, 42, 0.08)",
}

NAV_LINK_STYLE = {
    "display": "inline-block",
    "padding": "6px 12px",
    "borderRadius": "999px",
    "textDecoration": "none",
    "fontWeight": "600",
    "fontSize": "0.9rem",
    "letterSpacing": "0.01em",
    "color": "#334155",
    "backgroundColor": "#e2e8f0",
    "border": "1px solid #cbd5e1",
}
WORKFLOW_PAGE_ORDER = [
    "pages.ai_insights",
    "pages.weekly_commits",
    "pages.merges",
    "pages.diff_summary",
    "pages.change_types",
    "pages.conventional",
    "pages.codelines",
    "pages.community_flows",
    "pages.affinity_groups",
    "pages.strongest_pairings",
    "pages.most_committed",
]
WORKFLOW_PAGE_ORDER_INDEX = {
    module_name: idx for idx, module_name in enumerate(WORKFLOW_PAGE_ORDER)
}


def _page_sort_key(page):
    module_name = str(page.get("module", ""))
    workflow_index = WORKFLOW_PAGE_ORDER_INDEX.get(
        module_name, len(WORKFLOW_PAGE_ORDER)
    )
    page_name = str(page.get("name", "")).lower()
    return workflow_index, page_name


app.layout = html.Div(
    [
        # Memory-scoped date range store (cleared on page refresh)
        dcc.Store(id="global-date-range", storage_type="memory"),
        html.H1(
            f"The Git Miner: {repo_context.format_repository_display_name()}",
            style={"text-align": "center", "margin": "10px 0"},
        ),
        # Global period selector
        html.Div(
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "10px",
                "margin": "5px 0",
            },
            children=[
                html.Label("Period:"),
                dcc.Dropdown(
                    id="global-period-dropdown",
                    options=date_utils.PERIOD_OPTIONS,
                    value=date_utils.DEFAULT_PERIOD,
                    style={"minWidth": "240px"},
                ),
            ],
        ),
        # Navigation
        html.Div(
            [
                dcc.Link(
                    page["name"],
                    href=page["path"],
                    style=NAV_LINK_STYLE,
                )
                for page in sorted(
                    page_registry.values(),
                    key=_page_sort_key,
                )
            ],
            style=NAV_CONTAINER_STYLE,
        ),
        page_container,
    ]
)


# Compute store from dropdown only (no URL syncing)
@callback(
    Output("global-date-range", "data"),
    Input("global-period-dropdown", "value"),
)
def compute_store(period_label: str):
    return build_store_payload(period_label)


if __name__ == "__main__":
    import os

    # Disable debug mode when running under coverage to avoid reloader issues
    debug_mode = os.environ.get("COVERAGE_RUN") != "true"
    app.run(debug=debug_mode)
