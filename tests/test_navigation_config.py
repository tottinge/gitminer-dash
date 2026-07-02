"""Tests for pages.navigation_config page sort behavior."""

from pages.navigation_config import WORKFLOW_PAGE_FALLBACK_INDEX, page_sort_key


def test_page_sort_key_respects_workflow_order_before_name():
    weekly_page = {"module": "pages.weekly_commits", "name": "ZZZ"}
    most_committed_page = {"module": "pages.most_committed", "name": "AAA"}

    assert page_sort_key(weekly_page) < page_sort_key(most_committed_page)


def test_page_sort_key_falls_back_to_lowercase_name_for_unknown_modules():
    alpha_page = {"module": "pages.custom_alpha", "name": "Alpha"}
    beta_page = {"module": "pages.custom_beta", "name": "beta"}

    assert page_sort_key(alpha_page) < page_sort_key(beta_page)


def test_page_sort_key_uses_numeric_fallback_index_for_unknown_module():
    unknown_page = {"module": "pages.custom_unknown", "name": "Page"}

    workflow_index, _ = page_sort_key(unknown_page)

    assert workflow_index == WORKFLOW_PAGE_FALLBACK_INDEX


def test_page_sort_key_defaults_missing_name_to_empty_string():
    unnamed_page = {"module": "pages.custom_unknown"}

    _, page_name = page_sort_key(unnamed_page)

    assert page_name == ""


def test_page_sort_key_normalizes_name_to_lowercase():
    mixed_case_page = {"module": "pages.custom_unknown", "name": "MiXeD"}

    _, page_name = page_sort_key(mixed_case_page)

    assert page_name == "mixed"
