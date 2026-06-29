"""Shared page navigation ordering and sorting configuration."""

from __future__ import annotations

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
    module_name: index for index, module_name in enumerate(WORKFLOW_PAGE_ORDER)
}
WORKFLOW_PAGE_FALLBACK_INDEX = len(WORKFLOW_PAGE_ORDER)


def page_sort_key(page) -> tuple[int, str]:
    """Sort page registry entries by workflow order then page name."""
    module_name = str(page.get("module", ""))
    workflow_index = WORKFLOW_PAGE_ORDER_INDEX.get(
        module_name,
        WORKFLOW_PAGE_FALLBACK_INDEX,
    )
    page_name = str(page.get("name", "")).lower()
    return workflow_index, page_name
