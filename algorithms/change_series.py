from collections import Counter

change_name = {
    "A": "Files Added",
    "D": "Files Deleted",
    "R": "Files Renamed",
    "M": "Files Modified"
}


def change_series(start, commit_refs):
    """
    Generator: diffs the referenced tags, yielding a summary for each
    detailing the date of commit, the name of the reference, and the
    number of adds, deletes, renames, and modifications in the diff.
    """
    earlier_commit = start
    for latter_commit in commit_refs:
        diffs = earlier_commit.commit.diff(latter_commit.commit)
        yield {
            'Date': latter_commit.commit.committed_datetime.date(),
            'Name': latter_commit.name,
            **Counter(change_name[x.change_type] for x in diffs)
        }
        earlier_commit = latter_commit
