"""Unit tests for interval disjointness in `algorithms/stacking.py`."""

from algorithms.stacking import is_disjoint


def test_is_disjoint_false_when_intervals_touch_on_first_upper_bound():
    assert is_disjoint((3, 6), (1, 3)) is False


def test_is_disjoint_false_when_intervals_touch_on_second_upper_bound():
    assert is_disjoint((1, 3), (3, 6)) is False


def test_is_disjoint_true_when_intervals_are_separated():
    assert is_disjoint((1, 2), (4, 5)) is True
