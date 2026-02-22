"""Unit tests for algorithms.affinity_analysis.

These tests exercise the production implementations of:
- get_file_total_affinities
- get_top_files_by_affinity

The goal is to pin down core affinity behaviour for the helpers that are
used by the network graph visualisation code.
"""

from tests import setup_path

setup_path()

import pytest

import algorithms.affinity_analysis as aa


def test_get_file_total_affinities_sums_across_all_pairs() -> None:
    """Totals must accumulate affinity over all pairs for each file."""

    affinities = {
        ("a.py", "b.py"): 0.5,
        ("a.py", "c.py"): 0.3,
        ("b.py", "c.py"): 0.2,
    }

    totals = aa.get_file_total_affinities(affinities)

    assert totals["a.py"] == pytest.approx(0.8)
    assert totals["b.py"] == pytest.approx(0.7)
    assert totals["c.py"] == pytest.approx(0.5)


def test_get_top_files_by_affinity_ranks_by_total_score_not_name() -> None:
    """Top files must be selected by total affinity, not alphabetically."""

    affinities = {
        ("qq.py", "mm.py"): 0.1,
        ("aa.py", "mm.py"): 0.9,
    }

    top = aa.get_top_files_by_affinity(affinities, max_nodes=2)

    # The top files should be chosen by score, not name
    assert top == {"mm.py", "aa.py"}


def test_get_top_files_by_affinity_uses_total_score_for_top_n() -> None:
    """The top-N set must be chosen by total affinity score, not name."""

    affinities = {
        ("a.py", "hub.py"): 0.1,
        ("z.py", "hub.py"): 0.9,
    }

    # Totals:
    #   a.py   -> 0.1
    #   z.py   -> 0.9
    #   hub.py -> 1.0 (connected to both)
    #
    # Alphabetical order would give ["a.py", "hub.py"] for max_nodes=2,
    # but sorting by total affinity must yield {"hub.py", "z.py"}.
    top_two = aa.get_top_files_by_affinity(affinities, max_nodes=2)

    assert top_two == {"hub.py", "z.py"}
