from collections import Counter
from collections.abc import Iterable, Iterator
from typing import Any

ROW_DATE_KEY = "Date"
ROW_NAME_KEY = "Name"
OTHER_CHANGE_KEY = "Other"
CHANGE_NAME_BY_TYPE = {
    "A": "Files Added",
    "D": "Files Deleted",
    "R": "Files Renamed",
    "M": "Files Modified",
}
# Backward compatibility for existing imports.
change_name = CHANGE_NAME_BY_TYPE


def _summarize_change_types(diffs: Iterable[Any]) -> Counter[str]:
    summarized_change_types: list[str] = []
    for diff in diffs:
        diff_change_type = getattr(diff, "change_type", None)
        summarized_change_types.append(
            CHANGE_NAME_BY_TYPE.get(diff_change_type, OTHER_CHANGE_KEY)
        )
    return Counter(summarized_change_types)


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
