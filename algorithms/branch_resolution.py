"""Helpers for resolving representative branch names from commit metadata."""

from __future__ import annotations


def _leaf_ref_name(reference_name: str) -> str:
    """Return the leaf portion of a reference path."""
    if "/" not in reference_name:
        return reference_name
    return reference_name.split("/")[-1]


def branch_from_refs(commit) -> str:
    """Return a branch candidate from commit refs, if available."""
    refs = getattr(commit, "refs", None)
    if not refs:
        return ""

    for ref in refs:
        if not hasattr(ref, "name"):
            continue
        reference_name = ref.name
        if not reference_name:
            continue
        return _leaf_ref_name(reference_name)

    return ""


def branch_from_name_rev(commit) -> str:
    """Return a branch candidate parsed from ``commit.name_rev``."""
    if not hasattr(commit, "name_rev"):
        return ""
    name_rev = commit.name_rev
    if not isinstance(name_rev, str) or not name_rev:
        return ""

    parts = name_rev.split()
    if len(parts) < 2:
        return ""

    return _leaf_ref_name(parts[1])


def branch_for_commit(commit) -> str:
    """Return a representative branch name for a commit, if resolvable."""
    branch_name = branch_from_refs(commit)
    if branch_name:
        return branch_name
    return branch_from_name_rev(commit)
