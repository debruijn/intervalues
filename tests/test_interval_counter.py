from intervalues import BaseInterval, IntervalCounterFloat
import pytest
from random import Random


INTERVAL_MANY = [5, 10, 25, 100, 250, 500, 1000, 10000]


def test_addition_base():
    a = IntervalCounterFloat([BaseInterval((0, 1))])
    b = BaseInterval((2, 3))
    c = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_counter():
    a = IntervalCounterFloat([BaseInterval((0, 1))])
    b = IntervalCounterFloat([BaseInterval((2, 3))])
    c = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_overlap():
    a = IntervalCounterFloat([BaseInterval((0, 2))])
    b = IntervalCounterFloat([BaseInterval((1, 3))])
    c = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((1,2))*2, BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_subtraction_base():
    a = IntervalCounterFloat([BaseInterval((0, 1))])
    b = BaseInterval((2, 3))
    c = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert c - b == a
    c -= b
    assert a == c


def test_subtraction_counter():
    a = IntervalCounterFloat([BaseInterval((0, 1))])
    b = IntervalCounterFloat([BaseInterval((2, 3))])
    c = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert c - b == a
    c -= b
    assert a == c


def test_subtraction_overlap():
    a = IntervalCounterFloat([BaseInterval((0, 2))])
    b = IntervalCounterFloat([BaseInterval((1, 3))])
    c = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((1,2))*2, BaseInterval((2, 3))])
    assert c - b == a
    c -= b
    assert a == c


@pytest.mark.parametrize("mult",(2, -2, 0))
def test_multiplication(mult):
    a = IntervalCounterFloat([BaseInterval((0, 2))])*mult
    b = IntervalCounterFloat([BaseInterval((0, 2))*mult])
    assert a == b
    a *= mult
    assert a == b*mult

def test_equality_different_order():
    a = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = IntervalCounterFloat([BaseInterval((2, 3)), BaseInterval((0, 1))])
    assert a == b


def test_equality_base():
    a = IntervalCounterFloat([BaseInterval((0, 1))])
    b = BaseInterval((0, 1))
    assert a == b
    assert b == a


def test_equality_base_reduced():
    a = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((1, 2))])
    b = BaseInterval((0, 2))
    assert a == b
    assert b == a


def test_length():
    a = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((1, 3))*2])
    assert a.get_length() == a.total_length()
    assert [a.get_length(v) for v in a.keys()] == [1, 4]


def test_find_which_contains():
    a = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((1, 3)) * 2])
    assert [a.find_which_contains(x) for x in [1, 2]] == list(a.keys())


def test_contains():
    a = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((1, 3)) * 2])
    assert BaseInterval((0, 1)) in a
    assert 1 in a
    assert 2 in a
    assert 5.0 not in a


def test_get_item():
    a = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((1, 3)) * 2])
    assert a[BaseInterval((0, 1))] == 1
    assert a[1] == 1
    assert a[2] == 2
    assert a[5.0] == 0


def split_to_pairs(iterable):
    a = iter(iterable)
    return zip(a, a)


@pytest.mark.parametrize("nr_intervals", INTERVAL_MANY)
def test_combine_many_randint(nr_intervals):
    nums = [Random().randint(0, 10) for _ in range(nr_intervals * 2)]
    intervals = [x if x[0] < x[1] else (x[1], x[0]) for x in split_to_pairs(nums)]
    intervals = [BaseInterval(interval) for interval in intervals if interval[0] != interval[1]]

    counter1 = IntervalCounterFloat(intervals[:int(nr_intervals/2)])
    counter2 = IntervalCounterFloat(intervals[int(nr_intervals/2):] * 2)
    counter3 = IntervalCounterFloat(intervals)

    assert counter1 * 2 + counter2 == counter3 * 2
