"""Persistence helpers for versioned analysis snapshots."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from insights.models import AnalysisSnapshot
from insights.schema_version import ANALYSIS_SCHEMA_VERSION


def _canonical_time(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def snapshot_path_for_inputs(
    snapshot_dir: Path,
    repo_path: str,
    period_start: datetime,
    period_end: datetime,
    schema_version: str = ANALYSIS_SCHEMA_VERSION,
) -> Path:
    """Return deterministic snapshot path for a repo/date/schema tuple."""
    raw_key = "|".join(
        [
            schema_version,
            repo_path,
            _canonical_time(period_start),
            _canonical_time(period_end),
        ]
    )
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]
    return snapshot_dir / f"{digest}.json"


def save_snapshot(snapshot: AnalysisSnapshot, snapshot_dir: Path) -> Path:
    """Persist a snapshot artifact and return its path."""
    period_start = datetime.fromisoformat(snapshot.period_start)
    period_end = datetime.fromisoformat(snapshot.period_end)
    snapshot_path = snapshot_path_for_inputs(
        snapshot_dir=snapshot_dir,
        repo_path=snapshot.repo_path,
        period_start=period_start,
        period_end=period_end,
        schema_version=snapshot.schema_version,
    )
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(
        json.dumps(snapshot.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return snapshot_path


def load_snapshot(
    snapshot_dir: Path,
    repo_path: str,
    period_start: datetime,
    period_end: datetime,
    schema_version: str = ANALYSIS_SCHEMA_VERSION,
) -> AnalysisSnapshot | None:
    """Load snapshot for a repo/date tuple if it exists."""
    snapshot_path = snapshot_path_for_inputs(
        snapshot_dir=snapshot_dir,
        repo_path=repo_path,
        period_start=period_start,
        period_end=period_end,
        schema_version=schema_version,
    )
    if not snapshot_path.exists():
        return None

    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != schema_version:
        return None
    return AnalysisSnapshot(
        schema_version=payload["schema_version"],
        repo_path=payload["repo_path"],
        period_start=payload["period_start"],
        period_end=payload["period_end"],
        total_commits=payload["total_commits"],
        file_commit_counts=payload["file_commit_counts"],
        file_recent_commits=payload["file_recent_commits"],
    )
