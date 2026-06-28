"""Tests for timeline schema ownership in `algorithms/chain_models.py`."""

from datetime import datetime, timezone

from algorithms.chain_models import TIMELINE_COLUMNS, TimelineRow


def test_timeline_row_to_record_matches_declared_columns():
    row = TimelineRow(
        first=datetime(2024, 1, 1, tzinfo=timezone.utc),
        last=datetime(2024, 1, 10, tzinfo=timezone.utc),
        elevation=2,
        commit_counts=7,
        head="head_sha",
        tail="tail_sha",
        duration=9,
        density=1.2857,
    )

    record = row.to_record()

    assert list(record.keys()) == TIMELINE_COLUMNS
    assert record["first"] == row.first
    assert record["last"] == row.last
    assert record["elevation"] == 2
    assert record["commit_counts"] == 7
    assert record["head"] == "head_sha"
    assert record["tail"] == "tail_sha"
    assert record["duration"] == 9
    assert record["density"] == 1.2857
