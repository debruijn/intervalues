from intervalues import BaseInterval
import pytest


@pytest.mark.parametrize("val", [0, 0.5 ** 0.5, 1.42])
def test_number_in_interval(val):
    interval = BaseInterval((0, 1.42))
    assert val in interval


@pytest.mark.parametrize("val", [-0.000001, 2])
def test_number_outside_interval(val):
    interval = BaseInterval((0, 1))
    assert val not in interval


def test_equal():
    interval1 = BaseInterval((0, 1))
    interval2 = BaseInterval((0, 1))
    assert interval1 == interval2


def test_addition():
    interval1 = BaseInterval((0, 1))
    interval2 = BaseInterval((1, 2))
    interval3 = BaseInterval((0, 2))

    assert interval1 + interval2 == interval3
    assert interval2 + interval1 == interval3


def test_comparison():
    interval1 = BaseInterval((0, 1))
    interval2 = BaseInterval((1, 2))
    interval3 = BaseInterval((2, 3))
    assert interval1 <= interval2
    assert interval1 < interval3
    assert interval3 >= interval2
    assert interval3 > interval1
    assert not interval1 < interval2
    assert not interval3 > interval2


def test_bordering():
    interval1 = BaseInterval((0, 1))
    interval2 = BaseInterval((1, 2))
    interval3 = BaseInterval((2, 3))

    assert interval1.borders(interval2)
    assert interval2.borders(interval3)
    assert not interval1.borders(interval3)
    assert interval1.left_borders(interval2)
    assert interval2.right_borders(interval1)
    assert not interval1.right_borders(interval2)


def test_overlap():
    interval1 = BaseInterval((0, 2))
    interval2 = BaseInterval((1, 3))
    interval3 = BaseInterval((2, 4))

    assert interval1.overlaps(interval2)
    assert interval1.left_overlaps(interval2)
    assert not interval1.right_overlaps(interval2)
    assert interval2.right_overlaps(interval1)
    assert not interval1.overlaps(interval3)
    assert not interval1.overlaps(interval1)  # TODO: think about if this is how I want it.


def test_contains():
    interval1 = BaseInterval((0, 3))
    interval2 = BaseInterval((1, 2))
    interval3 = BaseInterval((1, 4))

    assert interval1.contains(interval2)
    assert interval3.contains(interval2)
    assert interval1.contains(interval1)
    assert not interval1.contains(interval3)
    assert not interval2.contains(interval1)


def test_disjoint():
    interval1 = BaseInterval((0, 2))
    interval2 = BaseInterval((0, 1))
    interval3 = BaseInterval((2, 3))

    assert not interval1.is_disjoint_with(interval2)
    assert not interval1.is_disjoint_with(interval3)
    assert interval2.is_disjoint_with(interval3)
    assert not interval1.is_disjoint_with(interval1)


@pytest.mark.parametrize("interval,length", [((0, 1), 1), ((1, 5), 4), ((2.3, 5), 2.7)])
def test_length(interval, length):
    interval = BaseInterval(interval)
    assert interval.length == length


def test_hashable():
    interval1 = BaseInterval((0, 1))
    hash(interval1)
    assert True
