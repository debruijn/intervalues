from intervalues import BaseInterval, EmptyInterval, IntervalSetFloat, IntervalCounterFloat
import pytest
from random import Random


INTERVAL_MANY = [5, 10, 25, 100, 250, 500, 1000, 10000]


def test_addition_base():
    a = IntervalSetFloat([BaseInterval((0, 1))])
    b = BaseInterval((2, 3))
    c = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_set():
    a = IntervalSetFloat([BaseInterval((0, 1))])
    b = IntervalSetFloat([BaseInterval((2, 3))])
    c = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_overlap():
    a = IntervalSetFloat([BaseInterval((0, 2))])
    b = IntervalSetFloat([BaseInterval((1, 3))])
    c = IntervalSetFloat([BaseInterval((0, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_empty():
    a = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.copy()
    e = EmptyInterval()
    assert a + e == a
    assert e + a == a
    a += e
    assert a == b


def test_subtraction_base():
    a = IntervalSetFloat([BaseInterval((0, 1))])
    b = BaseInterval((2, 3))
    c = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert c - b == a
    assert -b + c == a
    c -= b
    assert a == c


def test_subtraction_set():
    a = IntervalSetFloat([BaseInterval((0, 1))])
    b = IntervalSetFloat([BaseInterval((2, 3))])
    c = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert c - b == a
    c -= b
    assert a == c


def test_subtraction_overlap():
    a = IntervalSetFloat([BaseInterval((0, 1))])
    b = IntervalSetFloat([BaseInterval((1, 3))])
    c = IntervalSetFloat([BaseInterval((0, 3))])
    assert c - b == a
    c -= b
    assert a == c


def test_equality_different_order():
    a = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = IntervalSetFloat([BaseInterval((2, 3)), BaseInterval((0, 1))])
    assert a == b


def test_equality_base():
    a = IntervalSetFloat([BaseInterval((0, 1))])
    b = BaseInterval((0, 1))
    assert a == b
    assert b == a


def test_equality_base_reduced():
    a = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((1, 2))])
    b = BaseInterval((0, 2))
    assert a == b
    assert b == a


def test_comparison():
    interval1 = IntervalSetFloat([BaseInterval((0, 1))])
    interval2 = IntervalSetFloat([BaseInterval((0, 2))])
    interval3 = IntervalSetFloat([BaseInterval((1, 2))])
    interval4 = IntervalSetFloat([BaseInterval((0, 1, 2))])
    interval5 = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((1, 2, 2))])
    assert interval1 < interval3
    assert interval1 < interval2
    assert interval3 > interval2
    assert interval3 > interval1
    assert not interval1 < interval4
    assert not interval1 > interval4
    assert interval1 <= interval4
    assert interval1 >= interval4
    assert interval1 < interval5


def test_comparison_base():
    interval1 = IntervalSetFloat([BaseInterval((0, 1))])
    interval2 = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    base1 = BaseInterval(0, 1)
    base2 = BaseInterval(1, 2)
    base3 = BaseInterval(0, 2)

    # Test in one direction
    assert interval1 <= base1
    assert interval1 >= base1
    assert not interval1 > base1
    assert not interval1 < base1
    assert interval1 < base2
    assert interval1 < base3
    assert interval2 > base1
    assert interval2 < base2
    assert interval2 < base3

    # Test in the other direction
    assert base1 >= interval1
    assert base1 <= interval1
    assert not base1 < interval1
    assert not base1 > interval1
    assert base2 > interval1
    assert base3 > interval1
    assert base1 < interval2
    assert base2 > interval2
    assert base3 > interval2


def test_length():
    a = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((2, 4))*2])
    assert a.get_length() == 3
    assert a.get_length(BaseInterval((0, 1))) == 1
    assert a.get_length(BaseInterval((2, 4))) == 2


def test_find_which_contains():
    a = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((2, 3)) * 2])
    assert [a.find_which_contains(x) for x in [1, 2]] == list(a)


def test_contains():
    a = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert BaseInterval((0, 1)) in a
    assert BaseInterval((1, 3, 2)) in a
    assert 1 in a
    assert 2 in a
    assert 5.0 not in a


def test_contains_as_superset():
    a = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert BaseInterval((1, 2, 2)) in a
    assert BaseInterval((1.5, 2.5)) in a


def test_get_item():
    a = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert a[BaseInterval((0, 1))] == 1
    assert a[BaseInterval((1, 3))] == 1
    assert a[BaseInterval((1, 3, 2))] == 1
    assert a[1] == 1
    assert a[2] == 1
    assert a[5.0] == 0


def test_get_item_as_superset():
    a = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert a[BaseInterval((1.5, 2.5))] == 1
    assert a[BaseInterval((0, 0.5, 2))] == 1


def split_to_pairs(iterable):
    a = iter(iterable)
    return zip(a, a)


def test_min_max():
    a = IntervalSetFloat([BaseInterval((0, 1))])
    b = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])

    assert a.min() == 0
    assert b.min() == 0
    assert a.max() == 1
    assert b.max() == 3


def test_single_interval():
    a = IntervalSetFloat([BaseInterval((0, 1))])
    b = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])

    assert a.as_single_interval() == BaseInterval(0, 1)
    assert b.as_single_interval() == BaseInterval(0, 3)


def test_as_counter():
    a = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_counter()
    c = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert b == c


# TODO: add tests for & | subset, superset, etc (e.g. the set ones that don't apply to Counter)
# Take subset of base intervals into account..
