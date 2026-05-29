"""Unit tests for algorithms.affinity_analysis.

These tests exercise the production implementations of:
- get_file_total_affinities
- get_top_files_by_affinity
- get_top_files_and_affinities

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


def test_get_top_files_and_affinities_filters_to_edges_inside_top_set() -> None:
    """Relevant affinities must only include pairs where both files are in top-N."""

    affinities = {
        ("a.py", "b.py"): 0.9,
        ("a.py", "c.py"): 0.8,
        ("b.py", "c.py"): 0.1,
        ("c.py", "d.py"): 0.7,
    }

    top_files, relevant_affinities = aa.get_top_files_and_affinities(
        commits=[],
        affinities=affinities,
        max_nodes=2,
    )

    assert top_files == {"a.py", "c.py"}
    assert relevant_affinities == [0.8]


def test_get_top_files_and_affinities_returns_all_pairs_when_all_files_selected() -> None:
    """When max_nodes covers all files, every affinity value is relevant."""

    affinities = {
        ("a.py", "b.py"): 0.4,
        ("b.py", "c.py"): 0.3,
        ("a.py", "c.py"): 0.2,
    }

    top_files, relevant_affinities = aa.get_top_files_and_affinities(
        commits=[],
        affinities=affinities,
        max_nodes=10,
    )

    assert top_files == {"a.py", "b.py", "c.py"}
    assert sorted(relevant_affinities) == [0.2, 0.3, 0.4]


def test_get_top_files_and_affinities_returns_empty_outputs_for_empty_input() -> None:
    """With no affinities, top files and relevant affinities must both be empty."""

    top_files, relevant_affinities = aa.get_top_files_and_affinities(
        commits=[],
        affinities={},
        max_nodes=5,
    )

    assert top_files == set()
    assert relevant_affinities == []


def test_get_top_files_and_affinities_honors_zero_max_nodes() -> None:
    """A zero max_nodes limit should return no selected files or affinities."""

    affinities = {
        ("a.py", "b.py"): 0.9,
        ("a.py", "c.py"): 0.8,
    }

    top_files, relevant_affinities = aa.get_top_files_and_affinities(
        commits=[],
        affinities=affinities,
        max_nodes=0,
    )

    assert top_files == set()
    assert relevant_affinities == []
