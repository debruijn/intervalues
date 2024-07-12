from intervalues import BaseInterval, IntervalMeter, EmptyInterval, IntervalSet, IntervalList, IntervalCounter
import pytest
from random import Random


INTERVAL_MANY = [5, 10, 25, 100, 250, 500, 1000, 10000]


def test_addition_base():
    a = IntervalMeter([BaseInterval((0, 1))])
    b = BaseInterval((2, 3))
    c = IntervalMeter([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_base_value():
    a = IntervalMeter([BaseInterval((0, 1))])
    b = BaseInterval((2, 3, 2))
    c = IntervalMeter([BaseInterval((0, 1)), BaseInterval((2, 3, 2))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_meter():
    a = IntervalMeter([BaseInterval((0, 1))])
    b = IntervalMeter([BaseInterval((2, 3))])
    c = IntervalMeter([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_overlap():
    a = IntervalMeter([BaseInterval((0, 2))])
    b = IntervalMeter([BaseInterval((1, 3))])
    c = IntervalMeter([BaseInterval((0, 1)), BaseInterval((1, 2)) * 2, BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_empty():
    a = IntervalMeter([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.copy()
    e = EmptyInterval()
    assert a + e == a
    assert e + a == a
    a += e
    assert a == b


def test_subtraction_base():
    a = IntervalMeter([BaseInterval((0, 1))])
    b = BaseInterval((2, 3))
    c = IntervalMeter([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert c - b == a
    assert -b + c == a
    c -= b
    assert a == c


def test_subtraction_meter():
    a = IntervalMeter([BaseInterval((0, 1))])
    b = IntervalMeter([BaseInterval((2, 3))])
    c = IntervalMeter([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert c - b == a
    c -= b
    assert a == c


def test_subtraction_overlap():
    a = IntervalMeter([BaseInterval((0, 2))])
    b = IntervalMeter([BaseInterval((1, 3))])
    c = IntervalMeter([BaseInterval((0, 1)), BaseInterval((1, 2)) * 2, BaseInterval((2, 3))])
    assert c - b == a
    c -= b
    assert a == c


@pytest.mark.parametrize("mult",(2, -2, 0))
def test_multiplication(mult):
    a = IntervalMeter([BaseInterval((0, 2))]) * mult
    b = IntervalMeter([BaseInterval((0, 2)) * mult])
    assert a == b
    a *= mult
    assert a == b*mult


def test_equality_different_order():
    a = IntervalMeter([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = IntervalMeter([BaseInterval((2, 3)), BaseInterval((0, 1))])
    assert a == b


def test_equality_base():
    a = IntervalMeter([BaseInterval((0, 1))])
    b = BaseInterval((0, 1))
    assert a == b
    assert b == a


def test_equality_base_reduced():
    a = IntervalMeter([BaseInterval((0, 1)), BaseInterval((1, 2))])
    b = BaseInterval((0, 2))
    assert a == b
    assert b == a


def test_comparison():
    interval1 = IntervalMeter([BaseInterval((0, 1))])
    interval2 = IntervalMeter([BaseInterval((0, 2))])
    interval3 = IntervalMeter([BaseInterval((1, 2))])
    interval4 = IntervalMeter([BaseInterval((0, 1, 2))])
    interval5 = IntervalMeter([BaseInterval((0, 1)), BaseInterval((1, 2, 2))])
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
    interval1 = IntervalMeter([BaseInterval((0, 1))])
    interval2 = IntervalMeter([BaseInterval((0, 1)), BaseInterval((2, 3))])
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
    a = IntervalMeter([BaseInterval((0, 1)), BaseInterval((1, 3)) * 2])
    assert a.get_length() == a.total_length()
    assert [a.get_length(v) for v in a.keys()] == [1, 4]


def test_find_which_contains():
    a = IntervalMeter([BaseInterval((0, 1)), BaseInterval((1, 3)) * 2])
    assert [a.find_which_contains(x) for x in [1, 2]] == list(a.keys())


def test_contains():
    a = IntervalMeter([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert BaseInterval((0, 1)) in a
    assert BaseInterval((1, 3, 2)) in a
    assert 1 in a
    assert 2 in a
    assert 5.0 not in a


def test_contains_as_superset():
    a = IntervalMeter([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert BaseInterval((1, 2, 2)) in a
    assert BaseInterval((1.5, 2.5)) in a


def test_get_item():
    a = IntervalMeter([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert a[BaseInterval((0, 1))] == 1
    assert a[BaseInterval((1, 3))] == 2
    assert a[BaseInterval((1, 3, 2))] == 1
    assert a[1] == 1
    assert a[2] == 2
    assert a[5.0] == 0


def test_get_item_as_superset():
    a = IntervalMeter([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert a[BaseInterval((1.5, 2.5))] == 2
    assert a[BaseInterval((0, 0.5, 2))] == 0.5


def split_to_pairs(iterable):
    a = iter(iterable)
    return zip(a, a)


@pytest.mark.parametrize("nr_intervals", INTERVAL_MANY)
def test_combine_many_randint(nr_intervals):
    nums = [Random().randint(0, 10) for _ in range(nr_intervals * 2)]
    intervals = [x if x[0] < x[1] else (x[1], x[0]) for x in split_to_pairs(nums)]
    intervals = [BaseInterval(interval) for interval in intervals if interval[0] != interval[1]]

    meter1 = IntervalMeter(intervals[:int(nr_intervals / 2)])
    meter2 = IntervalMeter(intervals[int(nr_intervals / 2):] * 2)
    meter3 = IntervalMeter(intervals)

    assert meter1 * 2 + meter2 == meter3 * 2


def test_min_max():
    a = IntervalMeter([BaseInterval((0, 4))])
    b = IntervalMeter([BaseInterval((0, 4)), BaseInterval((2, 3))])

    assert a.min() == 0
    assert b.min() == 0
    assert a.max() == 4
    assert b.max() == 4


def test_single_interval():
    a = IntervalMeter([BaseInterval((0, 1))])
    b = IntervalMeter([BaseInterval((0, 1)), BaseInterval((2, 3))])

    assert a.as_single_interval() == BaseInterval(0, 1)
    assert b.as_single_interval() == BaseInterval(0, 3)


def test_as_set():
    a = IntervalMeter([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_set()
    c = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert b == c


def test_as_set_value():
    a = IntervalMeter([BaseInterval((0, 1, 2)), BaseInterval((2, 3, 3))])
    b = a.as_set()
    c = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert b == c


def test_as_list():
    a = IntervalMeter([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_list()
    c = IntervalList([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert b == c


def test_as_list_value():
    a = IntervalMeter([BaseInterval((0, 1, 2)), BaseInterval((2, 3, 3))])
    b = a.as_list()
    c = IntervalList([BaseInterval((0, 1, 2)), BaseInterval((2, 3, 3))])
    assert b == c


def test_as_counter():
    a = IntervalMeter([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_counter()
    c = IntervalCounter([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert b == c


def test_as_counter_value():
    a = IntervalMeter([BaseInterval((0, 1, 2)), BaseInterval((2, 3, -3))])
    b = a.as_counter()
    c = IntervalCounter([BaseInterval((0, 1, 2))])
    assert b == c
