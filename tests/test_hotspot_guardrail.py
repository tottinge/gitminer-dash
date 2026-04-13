from datetime import datetime, timezone

import pytest

from insights.hotspot_guardrail import WindowMetrics, evaluate_hotspot_guardrail


def _window_metrics(
    *,
    hotspot_rank: int | None,
    hotspot_score: float,
    bridge_rank: int | None,
    bridge_score: float,
) -> WindowMetrics:
    return WindowMetrics(
        period_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 1, 2, tzinfo=timezone.utc),
        hotspot_rank=hotspot_rank,
        hotspot_score=hotspot_score,
        bridge_rank=bridge_rank,
        bridge_score=bridge_score,
    )


def test_guardrail_triggers_for_sustained_top_rank_and_bridge_rise():
    windows = iter(
        [
            _window_metrics(
                hotspot_rank=1,
                hotspot_score=8.0,
                bridge_rank=3,
                bridge_score=0.05,
            ),
            _window_metrics(
                hotspot_rank=1,
                hotspot_score=12.0,
                bridge_rank=1,
                bridge_score=0.20,
            ),
        ]
    )

    result = evaluate_hotspot_guardrail(
        repo_path="/example/repo",
        file_path="visualization/network_graph.py",
        reference_time=datetime(2026, 4, 13, tzinfo=timezone.utc),
        window_days=90,
        hotspot_rank_threshold=1,
        min_bridge_score_increase=0.1,
        metrics_loader=lambda **_kwargs: next(windows),
        repo_loader=lambda _path: object(),
    )

    assert result.sustained_top_rank is True
    assert result.bridge_score_delta == pytest.approx(0.15)
    assert result.regression_detected is True


def test_guardrail_does_not_trigger_without_sustained_top_rank():
    windows = iter(
        [
            _window_metrics(
                hotspot_rank=2,
                hotspot_score=6.0,
                bridge_rank=6,
                bridge_score=0.01,
            ),
            _window_metrics(
                hotspot_rank=1,
                hotspot_score=10.0,
                bridge_rank=1,
                bridge_score=0.30,
            ),
        ]
    )

    result = evaluate_hotspot_guardrail(
        repo_path="/example/repo",
        file_path="visualization/network_graph.py",
        reference_time=datetime(2026, 4, 13, tzinfo=timezone.utc),
        window_days=90,
        hotspot_rank_threshold=1,
        min_bridge_score_increase=0.1,
        metrics_loader=lambda **_kwargs: next(windows),
        repo_loader=lambda _path: object(),
    )

    assert result.sustained_top_rank is False
    assert result.bridge_score_delta == pytest.approx(0.29)
    assert result.regression_detected is False


def test_guardrail_does_not_trigger_when_bridge_rise_is_too_small():
    windows = iter(
        [
            _window_metrics(
                hotspot_rank=1,
                hotspot_score=8.0,
                bridge_rank=3,
                bridge_score=0.12,
            ),
            _window_metrics(
                hotspot_rank=1,
                hotspot_score=10.0,
                bridge_rank=2,
                bridge_score=0.18,
            ),
        ]
    )

    result = evaluate_hotspot_guardrail(
        repo_path="/example/repo",
        file_path="visualization/network_graph.py",
        reference_time=datetime(2026, 4, 13, tzinfo=timezone.utc),
        window_days=90,
        hotspot_rank_threshold=1,
        min_bridge_score_increase=0.1,
        metrics_loader=lambda **_kwargs: next(windows),
        repo_loader=lambda _path: object(),
    )

    assert result.sustained_top_rank is True
    assert result.bridge_score_delta == pytest.approx(0.06)
    assert result.regression_detected is False
