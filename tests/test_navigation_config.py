"""Tests for pages.navigation_config page sort behavior."""

from pages.navigation_config import page_sort_key


def test_page_sort_key_respects_workflow_order_before_name():
    weekly_page = {"module": "pages.weekly_commits", "name": "ZZZ"}
    most_committed_page = {"module": "pages.most_committed", "name": "AAA"}

    assert page_sort_key(weekly_page) < page_sort_key(most_committed_page)


def test_page_sort_key_falls_back_to_lowercase_name_for_unknown_modules():
    alpha_page = {"module": "pages.custom_alpha", "name": "Alpha"}
    beta_page = {"module": "pages.custom_beta", "name": "beta"}

    assert page_sort_key(alpha_page) < page_sort_key(beta_page)
