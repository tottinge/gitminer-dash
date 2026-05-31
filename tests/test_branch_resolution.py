"""Unit tests for branch parsing helpers in algorithms.branch_resolution."""

from algorithms.branch_resolution import (
    _leaf_ref_name,
    branch_for_commit,
    branch_from_name_rev,
    branch_from_refs,
)


class DummyRef:
    def __init__(self, name):
        self.name = name


def test_leaf_ref_name_returns_original_without_slash():
    assert _leaf_ref_name("main") == "main"


def test_leaf_ref_name_returns_last_segment_for_nested_path():
    assert _leaf_ref_name("refs/remotes/origin/feature/cool") == "cool"


def test_branch_from_refs_returns_empty_when_refs_missing():
    class CommitWithoutRefs:
        pass

    assert branch_from_refs(CommitWithoutRefs()) == ""


def test_branch_from_refs_returns_empty_for_empty_refs():
    class CommitWithEmptyRefs:
        def __init__(self):
            self.refs = []

    assert branch_from_refs(CommitWithEmptyRefs()) == ""


def test_branch_from_refs_uses_first_named_ref():
    class CommitWithRefs:
        def __init__(self):
            self.refs = [DummyRef("origin/main"), DummyRef("origin/dev")]

    assert branch_from_refs(CommitWithRefs()) == "main"


def test_branch_from_refs_skips_blank_name_and_uses_next():
    class CommitWithMixedRefs:
        def __init__(self):
            self.refs = [DummyRef(""), DummyRef("heads/feature/x")]

    assert branch_from_refs(CommitWithMixedRefs()) == "x"


def test_branch_from_refs_returns_empty_when_ref_lacks_name():
    class RefWithoutName:
        pass

    class CommitWithUnnamedRef:
        def __init__(self):
            self.refs = [RefWithoutName()]

    assert branch_from_refs(CommitWithUnnamedRef()) == ""


def test_branch_from_refs_skips_unnamed_ref_and_continues_to_next():
    class RefWithoutName:
        pass

    class CommitWithUnnamedThenNamedRef:
        def __init__(self):
            self.refs = [RefWithoutName(), DummyRef("origin/main")]

    assert branch_from_refs(CommitWithUnnamedThenNamedRef()) == "main"


def test_branch_from_name_rev_returns_empty_when_missing():
    class CommitWithoutNameRev:
        pass

    assert branch_from_name_rev(CommitWithoutNameRev()) == ""


def test_branch_from_name_rev_returns_empty_for_non_string():
    class CommitWithNonString:
        def __init__(self):
            self.name_rev = 123

    assert branch_from_name_rev(CommitWithNonString()) == ""


def test_branch_from_name_rev_returns_empty_for_single_token():
    class CommitWithSingleToken:
        def __init__(self):
            self.name_rev = "deadbeef"

    assert branch_from_name_rev(CommitWithSingleToken()) == ""


def test_branch_from_name_rev_extracts_leaf_from_second_token():
    class CommitWithNameRev:
        def __init__(self):
            self.name_rev = "deadbeef refs/remotes/origin/main"

    assert branch_from_name_rev(CommitWithNameRev()) == "main"


def test_branch_for_commit_prefers_refs_over_name_rev():
    class CommitWithBoth:
        def __init__(self):
            self.refs = [DummyRef("origin/release")]
            self.name_rev = "deadbeef refs/remotes/origin/main"

    assert branch_for_commit(CommitWithBoth()) == "release"


def test_branch_for_commit_falls_back_to_name_rev():
    class CommitWithFallback:
        def __init__(self):
            self.refs = []
            self.name_rev = "deadbeef refs/remotes/origin/main"

    assert branch_for_commit(CommitWithFallback()) == "main"


def test_branch_for_commit_returns_empty_when_unresolvable():
    class CommitWithoutBranchData:
        def __init__(self):
            self.refs = []
            self.name_rev = ""

    assert branch_for_commit(CommitWithoutBranchData()) == ""
