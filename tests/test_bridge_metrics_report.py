"""Tests for `insights/bridge_metrics_report.py`."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import networkx as nx
import pytest

from insights.bridge_metrics_report import (
    build_bridge_metrics_report,
    rank_bridge_metrics,
)


def _sample_graph() -> nx.Graph:
    graph = nx.Graph()
    graph.add_node("src/core.py", community=0, commit_count=9)
    graph.add_node("src/ui.py", community=0, commit_count=4)
    graph.add_node("src/api.py", community=1, commit_count=7)
    graph.add_node("src/db.py", community=2, commit_count=5)
    graph.add_edge("src/core.py", "src/ui.py", weight=0.2)
    graph.add_edge("src/core.py", "src/api.py", weight=0.7)
    graph.add_edge("src/core.py", "src/db.py", weight=0.5)
    graph.add_edge("src/api.py", "src/db.py", weight=0.1)
    return graph


def test_rank_bridge_metrics_prioritizes_cross_community_connectors():
    ranked = rank_bridge_metrics(graph=_sample_graph(), top_n=2)

    assert [item.file_path for item in ranked] == [
        "src/core.py",
        "src/api.py",
    ]
    assert ranked[0].cross_community_edges == 2
    assert ranked[0].total_edges == 3
    assert ranked[0].connected_communities == [1, 2]
    assert ranked[0].bridge_ratio == pytest.approx(1.2 / 1.4, rel=1e-6)


def test_rank_bridge_metrics_handles_empty_or_non_positive_inputs():
    assert rank_bridge_metrics(graph=nx.Graph(), top_n=5) == []
    assert rank_bridge_metrics(graph=_sample_graph(), top_n=0) == []


def test_build_bridge_metrics_report_emits_contract_from_graph_stats():
    period_start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    period_end = datetime(2026, 1, 31, tzinfo=timezone.utc)
    commits = [MagicMock(), MagicMock(), MagicMock()]
    graph = nx.Graph()
    graph.add_node("src/a.py", community=0, commit_count=5)
    graph.add_node("src/b.py", community=1, commit_count=3)
    graph.add_edge("src/a.py", "src/b.py", weight=0.6)
    mock_repo = MagicMock()
    mock_repo.working_tree_dir = "/example/repo"

    with (
        patch(
            "insights.bridge_metrics_report.get_commits_for_period",
            return_value=commits,
        ) as mock_get_commits,
        patch(
            "insights.bridge_metrics_report.create_file_affinity_network",
            return_value=(
                graph,
                [],
                {"communities": 2, "edges_after_filtering": 1},
            ),
        ) as mock_create_network,
    ):
        report = build_bridge_metrics_report(
            repo=mock_repo,
            period_start=period_start,
            period_end=period_end,
            top_n=5,
        )

    assert report.report_type == "bridge-metrics"
    assert report.total_commits == 3
    assert report.graph_stats["communities"] == 2
    assert [item.file_path for item in report.bridges] == [
        "src/a.py",
        "src/b.py",
    ]
    mock_get_commits.assert_called_once_with(
        repo=mock_repo, period_start=period_start, period_end=period_end
    )
    mock_create_network.assert_called_once_with(
        commits=commits,
        min_affinity=0.2,
        max_nodes=50,
        min_edge_count=1,
    )
