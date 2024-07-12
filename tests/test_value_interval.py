from intervalues import BaseInterval, _ValueInterval as ValueInterval, IntervalMeter
import pytest


# Note: ValueInterval is no longer directly used, but can be indirectly be used like this. In principle, all ValueInterval
# does is now supported by BaseInterval instead.

@pytest.mark.parametrize("val", [0, 0.5 ** 0.5, 1.42])
def test_number_in_interval(val):
    interval = ValueInterval((0, 1.42))
    assert val in interval
    assert interval[val] == 1


@pytest.mark.parametrize("val", [-0.000001, 2])
def test_number_outside_interval(val):
    interval = ValueInterval((0, 1))
    assert val not in interval
    assert interval[val] == 0


def test_equal():
    interval1 = ValueInterval((0, 1), value=2)
    interval2 = ValueInterval((0, 1), value=2)
    assert interval1 == interval2


def test_unequal():
    interval1 = ValueInterval((0, 1), value=2)
    interval2 = ValueInterval((0, 1), value=3)
    assert interval1 != interval2

    interval3 = BaseInterval((0, 1))
    assert interval1 != interval3
    assert interval3 != interval1


def test_addition():
    interval1 = BaseInterval((0, 1))
    interval2 = BaseInterval((1, 2))
    interval3 = BaseInterval((0, 2))
    interval4 = ValueInterval((0, 2), value=2)
    interval5 = ValueInterval((0, 2), value=4)

    assert interval1 + interval2 + interval3 == interval4
    assert interval4 + interval4 == interval5


def test_addition_unequal_value():
    interval1 = ValueInterval((0, 1), value=2)
    interval2 = ValueInterval((1, 2), value=3)
    interval3 = BaseInterval((0, 1))
    interval4 = BaseInterval((1, 2))
    interval5 = IntervalMeter([interval3, interval3, interval4, interval4, interval4])

    assert interval1 + interval2 == interval5


def test_inplace_addition():
    interval1 = BaseInterval((0, 1))
    interval2 = BaseInterval((1, 2))
    interval3 = BaseInterval((0, 2))
    interval1 += interval2
    interval1 += interval3
    interval4 = ValueInterval((0, 2), value=2)
    interval5 = ValueInterval((0, 2), value=4)

    assert interval1 == interval4
    interval4 += interval4
    assert interval4 == interval5


def test_subtraction_equal_value():
    interval1 = ValueInterval((0, 1), value=2)
    interval2 = ValueInterval((1, 2), value=2)
    interval3 = ValueInterval((0, 2), value=2)

    assert interval3 - interval2 == interval1
    interval3 -= interval1
    assert interval3 == interval2


def test_subtraction_unequal_value():
    interval1 = ValueInterval((0, 1), value=1)
    interval2 = ValueInterval((0, 2), value=1)
    interval3 = ValueInterval((0, 2), value=2)
    interval4 = BaseInterval((0, 2))
    interval5 = BaseInterval((0, 1)) + BaseInterval((1, 2)) * 2

    assert interval3 - interval2 == interval4  # It returns a BaseInterval ..
    assert interval3 - interval2 == interval2  # .. but this BaseInterval is equal to a ValueInterval((...), 1)
    interval3 -= interval1
    assert interval3 == interval5


def test_negation():
    interval = ValueInterval((0, 1), value=2)
    neg_interval = -interval

    assert neg_interval == interval * -1


def test_multiplication():
    interval = ValueInterval((0, 1), value=2)
    interval2 = interval * 2
    assert interval2.value == 4


@pytest.mark.parametrize("interval,value,length", [((0, 1), 2, 2), ((1, 5), 2, 8), ((2.3, 5), 2, 5.4)])
def test_length(interval, value, length):
    interval = ValueInterval(interval, value=value)
    assert interval.get_length() == length


def test_hashable():
    interval1 = ValueInterval((0, 1), value=2)
    hash(interval1)
    assert True


def test_shift():
    interval = ValueInterval((0, 1), value=2)
    shifted = interval >> 3
    assert shifted == ValueInterval((3, 4), value=2)
    assert shifted << 3 == interval
