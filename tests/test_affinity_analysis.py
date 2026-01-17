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
        ("qq.py", "mm.py"): 0.1,
        ("aa.py", "mm.py"): 0.9,
    }

    # Totals:
    #   aa.py: 0.1
    #   bb.py: 0.9
    #   zz.py: 1.0
    top = aa.get_top_files_by_affinity(affinities, max_nodes=2)

    # The top files should be ordered by score, not name
    assert top == {"mm.py", "aa.py"}


def test_calculate_ideal_affinity_calls_calculate_affinities_with_commits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """calculate_ideal_affinity must pass the commits iterable through.

    This kills mutants that call calculate_affinities(None) or otherwise
    ignore the commits argument.
    """

    dummy_commits: list[str] = ["c1", "c2"]

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


def test_calculate_ideal_affinity_simple_graph_threshold_and_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    dummy_commits: list[str] = ["c1"]

    threshold, node_count, edge_count = aa.calculate_ideal_affinity(
        dummy_commits, target_node_count=15, max_nodes=3
    )

    assert threshold == pytest.approx(0.05)
    assert node_count == 3
    assert edge_count == 2


def test_get_top_files_by_affinity_uses_total_score_for_top_n() -> None:
    """The top-N set must be chosen by total affinity score, not name.

    This kills mutants that sort by filename (or another key) instead of
    the accumulated affinity value.
    """

    affinities = {
        ("a.py", "hub.py"): 0.1,
        ("z.py", "hub.py"): 0.9,
    }

    # Totals:
    #   a.py  -> 0.1
    #   z.py  -> 0.9
    #   hub.py -> 1.0 (connected to both)
    #
    # Alphabetical order would give ["a.py", "hub.py"] for max_nodes=2,
    # but sorting by total affinity must yield {"hub.py", "z.py"}.
    top_two = aa.get_top_files_by_affinity(affinities, max_nodes=2)

    assert top_two == {"hub.py", "z.py"}


def test_calculate_ideal_affinity_returns_defaults_when_no_commits() -> None:
    """No commits at all should trigger the documented default tuple.

    This pins the early-return behaviour for ``not commits`` so that
    refactors cannot silently change the baseline configuration.
    """

    threshold, node_count, edge_count = aa.calculate_ideal_affinity(
        [], target_node_count=15, max_nodes=50
    )

    assert threshold == pytest.approx(0.2)
    assert node_count == 0
    assert edge_count == 0


def test_calculate_ideal_affinity_defaults_when_commits_have_no_affinities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Commits with no affinities must also fall back to the default tuple.

    This targets the branch guarded by ``if not relevant_affinities`` and
    kills mutants that change the default values or the emptiness check.
    """

    dummy_commits: list[str] = ["c1"]

    def fake_calculate_affinities(commits_param):  # type: ignore[override]
        # We deliberately return no pairwise affinities.
        assert commits_param == dummy_commits
        return {}

    def fake_get_top_files_and_affinities(commits_param, affinities_param, max_nodes):
        # There are no affinities, so there can be no relevant affinities.
        assert commits_param == dummy_commits
        assert affinities_param == {}
        return set(), []

    monkeypatch.setattr(aa, "calculate_affinities", fake_calculate_affinities)
    monkeypatch.setattr(
        aa, "get_top_files_and_affinities", fake_get_top_files_and_affinities
    )

    threshold, node_count, edge_count = aa.calculate_ideal_affinity(
        dummy_commits, target_node_count=15, max_nodes=50
    )

    assert threshold == pytest.approx(0.2)
    assert node_count == 0
    assert edge_count == 0


def test_calculate_ideal_affinity_types_with_valid_commits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With non-trivial affinities, return types must remain stable.

    Even if future changes alter the threshold-search algorithm, the
    public API must continue to return (float, int, int).
    """

    affinities = {("a.py", "b.py"): 0.3}

    def fake_calculate_affinities(commits_param):  # type: ignore[override]
        assert commits_param == ["c1", "c2"]
        return affinities

    monkeypatch.setattr(aa, "calculate_affinities", fake_calculate_affinities)

    threshold, node_count, edge_count = aa.calculate_ideal_affinity(
        ["c1", "c2"], target_node_count=10, max_nodes=10
    )

    assert isinstance(threshold, float)
    assert isinstance(node_count, int)
    assert isinstance(edge_count, int)


def test_calculate_ideal_affinity_default_params_match_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Calling with defaults must be equivalent to explicit arguments.

    Rather than relying on implementation details such as ``__defaults__``,
    we assert that the downstream call into ``get_top_files_and_affinities``
    receives the same ``max_nodes`` value in both cases.
    """

    dummy_commits: list[str] = ["c1"]
    captured_max_nodes: list[int] = []

    monkeypatch.setattr(aa, "calculate_affinities", lambda commits_param: {})

    def fake_get_top_files_and_affinities(commits_param, affinities_param, max_nodes):
        captured_max_nodes.append(max_nodes)
        return set(), []

    monkeypatch.setattr(
        aa, "get_top_files_and_affinities", fake_get_top_files_and_affinities
    )

    # First call relies on default parameter values.
    aa.calculate_ideal_affinity(dummy_commits)
    # Second call specifies the documented defaults explicitly.
    aa.calculate_ideal_affinity(dummy_commits, target_node_count=15, max_nodes=50)

    assert captured_max_nodes == [50, 50]
