from collections import Counter
from collections.abc import Iterable, Iterator
from typing import Any

ROW_DATE_KEY = "Date"
ROW_NAME_KEY = "Name"
OTHER_CHANGE_KEY = "Other"

change_name = {
    "A": "Files Added",
    "D": "Files Deleted",
    "R": "Files Renamed",
    "M": "Files Modified",
}


def _summarize_change_types(diffs: Iterable[Any]) -> Counter[str]:
    return Counter(
        change_name.get(diff.change_type, OTHER_CHANGE_KEY) for diff in diffs
    )


def _build_change_row(
    commit_ref: Any, change_counts: Counter[str]
) -> dict[str, Any]:
    row = {
        ROW_DATE_KEY: commit_ref.commit.committed_datetime.date(),
        ROW_NAME_KEY: commit_ref.name,
    }
    row.update(change_counts)
    return row


def change_series(
    start: Any, commit_refs: Iterable[Any]
) -> Iterator[dict[str, Any]]:
    """
    Generator: diffs the referenced tags, yielding a summary for each
    detailing the date of commit, the name of the reference, and the
    number of adds, deletes, renames, and modifications in the diff.
    """
    previous_ref = start
    for current_ref in commit_refs:
        diffs = previous_ref.commit.diff(current_ref.commit)
        change_counts = _summarize_change_types(diffs)
        yield _build_change_row(current_ref, change_counts)
        previous_ref = current_ref
