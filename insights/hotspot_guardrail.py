"""Guardrail checks for hotspot and bridge-metrics regression trends."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from git import Repo

from insights.bridge_metrics_report import build_bridge_metrics_report
from insights.report_builder import build_insight_report
from insights.snapshot_builder import build_analysis_snapshot


@dataclass(frozen=True)
class WindowMetrics:
    """Hotspot and bridge metrics for one rolling window."""

    period_start: datetime
    period_end: datetime
    hotspot_rank: int | None
    hotspot_score: float
    bridge_rank: int | None
    bridge_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "hotspot_rank": self.hotspot_rank,
            "hotspot_score": self.hotspot_score,
            "bridge_rank": self.bridge_rank,
            "bridge_score": self.bridge_score,
        }


@dataclass(frozen=True)
class GuardrailResult:
    """Evaluation result for hotspot/bridge regression guardrail."""

    file_path: str
    window_days: int
    previous_window: WindowMetrics
    current_window: WindowMetrics
    hotspot_rank_threshold: int
    min_bridge_score_increase: float
    sustained_top_rank: bool
    bridge_score_delta: float
    regression_detected: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "window_days": self.window_days,
            "hotspot_rank_threshold": self.hotspot_rank_threshold,
            "min_bridge_score_increase": self.min_bridge_score_increase,
            "sustained_top_rank": self.sustained_top_rank,
            "bridge_score_delta": self.bridge_score_delta,
            "regression_detected": self.regression_detected,
            "previous_window": self.previous_window.to_dict(),
            "current_window": self.current_window.to_dict(),
        }


def _as_utc(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _window_bounds(
    *, now: datetime, window_days: int, offset_days: int
) -> tuple[datetime, datetime]:
    end = now - timedelta(days=offset_days)
    start = end - timedelta(days=window_days)
    return start, end


def _hotspot_rank_and_score(report, file_path: str) -> tuple[int | None, float]:
    for index, hotspot in enumerate(report.hotspots, start=1):
        if hotspot.file_path == file_path:
            return index, hotspot.score
    return None, 0.0


def _bridge_rank_and_score(
    bridge_report, file_path: str
) -> tuple[int | None, float]:
    for index, bridge in enumerate(bridge_report.bridges, start=1):
        if bridge.file_path == file_path:
            return index, bridge.bridge_score
    return None, 0.0


def collect_window_metrics(
    repo: Any,
    file_path: str,
    period_start: datetime,
    period_end: datetime,
    top_n: int,
) -> WindowMetrics:
    """Collect hotspot and bridge metrics for one period window."""
    snapshot = build_analysis_snapshot(
        repo=repo,
        period_start=period_start,
        period_end=period_end,
    )
    hotspot_report = build_insight_report(snapshot=snapshot, top_n=top_n)
    hotspot_rank, hotspot_score = _hotspot_rank_and_score(
        report=hotspot_report,
        file_path=file_path,
    )

    bridge_report = build_bridge_metrics_report(
        repo=repo,
        period_start=period_start,
        period_end=period_end,
        top_n=top_n,
    )
    bridge_rank, bridge_score = _bridge_rank_and_score(
        bridge_report=bridge_report,
        file_path=file_path,
    )
    return WindowMetrics(
        period_start=period_start,
        period_end=period_end,
        hotspot_rank=hotspot_rank,
        hotspot_score=hotspot_score,
        bridge_rank=bridge_rank,
        bridge_score=bridge_score,
    )


def evaluate_hotspot_guardrail(
    *,
    repo_path: str | Path,
    file_path: str,
    window_days: int = 90,
    top_n: int = 500,
    hotspot_rank_threshold: int = 1,
    min_bridge_score_increase: float = 0.1,
    reference_time: datetime | None = None,
    metrics_loader: Callable[..., WindowMetrics] = collect_window_metrics,
    repo_loader: Callable[[Path], Any] = Repo,
) -> GuardrailResult:
    """Check for sustained top-rank hotspot status and rising bridge score."""
    if window_days <= 0:
        raise ValueError("window_days must be positive")
    if top_n <= 0:
        raise ValueError("top_n must be positive")
    if hotspot_rank_threshold <= 0:
        raise ValueError("hotspot_rank_threshold must be positive")

    repo = repo_loader(Path(repo_path))
    now = _as_utc(reference_time)

    previous_start, previous_end = _window_bounds(
        now=now, window_days=window_days, offset_days=window_days
    )
    current_start, current_end = _window_bounds(
        now=now, window_days=window_days, offset_days=0
    )

    previous_window = metrics_loader(
        repo=repo,
        file_path=file_path,
        period_start=previous_start,
        period_end=previous_end,
        top_n=top_n,
    )
    current_window = metrics_loader(
        repo=repo,
        file_path=file_path,
        period_start=current_start,
        period_end=current_end,
        top_n=top_n,
    )

    sustained_top_rank = (
        previous_window.hotspot_rank is not None
        and current_window.hotspot_rank is not None
        and previous_window.hotspot_rank <= hotspot_rank_threshold
        and current_window.hotspot_rank <= hotspot_rank_threshold
    )
    bridge_score_delta = (
        current_window.bridge_score - previous_window.bridge_score
    )
    regression_detected = (
        sustained_top_rank and bridge_score_delta >= min_bridge_score_increase
    )

    return GuardrailResult(
        file_path=file_path,
        window_days=window_days,
        previous_window=previous_window,
        current_window=current_window,
        hotspot_rank_threshold=hotspot_rank_threshold,
        min_bridge_score_increase=min_bridge_score_increase,
        sustained_top_rank=sustained_top_rank,
        bridge_score_delta=bridge_score_delta,
        regression_detected=regression_detected,
    )
