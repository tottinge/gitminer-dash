"""Unit tests for algorithms.affinity_analysis.

These tests exercise the production implementations of:
- get_file_total_affinities
- get_top_files_by_affinity
- calculate_ideal_affinity

The goal is to pin down core affinity behaviour so that
mutation-test survivors in this module represent real
behavioural changes, not just untested logic.
"""

from tests import setup_path

setup_path()

from typing import List

import pytest

import algorithms.affinity_analysis as aa


def test_get_file_total_affinities_sums_across_all_pairs() -> None:
    """Totals must accumulate affinity over all pairs for each file.

    This kills mutants that overwrite instead of accumulating
    per-file affinity.
    """

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
    """Top files must be selected by total affinity, not alphabetically.

    This kills mutants that change the sort key away from the
    affinity value.
    """

    affinities = {
        ("aa.py", "zz.py"): 0.1,
        ("bb.py", "zz.py"): 0.9,
    }

    # Totals:
    #   aa.py: 0.1
    #   bb.py: 0.9
    #   zz.py: 1.0
    top = aa.get_top_files_by_affinity(affinities, max_nodes=2)

    # The top files by score should be zz.py and bb.py, not e.g. aa.py
    assert top == {"zz.py", "bb.py"}


def test_calculate_ideal_affinity_calls_calculate_affinities_with_commits(monkeypatch: pytest.MonkeyPatch) -> None:
    """calculate_ideal_affinity must pass the commits iterable through.

    This kills mutants that call calculate_affinities(None) or otherwise
    ignore the commits argument.
    """

    dummy_commits: List[str] = ["c1", "c2"]

    called = {"value": False}

    def fake_calculate_affinities(commits_param):  # type: ignore[override]
        assert commits_param is dummy_commits
        called["value"] = True
        # No affinities -> early default path in calculate_ideal_affinity
        return {}

    monkeypatch.setattr(aa, "calculate_affinities", fake_calculate_affinities)

    threshold, node_count, edge_count = aa.calculate_ideal_affinity(
        dummy_commits, target_node_count=15, max_nodes=10
    )

    assert called["value"] is True
    # With no affinities, we expect the documented default tuple
    assert threshold == pytest.approx(0.2)
    assert node_count == 0
    assert edge_count == 0


def test_calculate_ideal_affinity_simple_graph_threshold_and_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    """For a tiny graph we can predict threshold, node_count and edge_count.

    Affinities:
      a-b: 0.3
      a-c: 0.3

    All three nodes are connected together for thresholds <= 0.3.
    With the built-in thresholds [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, ...]
    and target_node_count=15, the search should pick 0.05 as the
    best threshold, with node_count=3 and edge_count=2.

    This kills mutants that:
    - Change the first threshold value dramatically
    - Change the edge-counting logic (e.g. counting 2 per edge)
    """

    affinities = {
        ("a.py", "b.py"): 0.3,
        ("a.py", "c.py"): 0.3,
    }

    def fake_calculate_affinities(commits_param):  # type: ignore[override]
        # We don't care about commits here, just return the tiny graph.
        return affinities

    monkeypatch.setattr(aa, "calculate_affinities", fake_calculate_affinities)

    dummy_commits: List[str] = ["c1"]

    threshold, node_count, edge_count = aa.calculate_ideal_affinity(
        dummy_commits, target_node_count=15, max_nodes=3
    )

    assert threshold == pytest.approx(0.05)
    assert node_count == 3
    assert edge_count == 2
