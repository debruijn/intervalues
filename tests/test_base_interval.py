from intervalues import BaseInterval, UnitInterval, EmptyInterval
import pytest


@pytest.mark.parametrize("val", [0, 0.5 ** 0.5, 1.42])
def test_number_in_interval(val):
    interval = BaseInterval((0, 1.42))
    assert val in interval
    assert interval[val] == 1


@pytest.mark.parametrize("val", [-0.000001, 2])
def test_number_outside_interval(val):
    interval = BaseInterval((0, 1))
    assert val not in interval
    assert interval[val] == 0


@pytest.mark.parametrize("val", [1, 2])
def test_interval_in_interval(val):
    interval1 = BaseInterval((0, 1))
    interval2 = BaseInterval((0.4, 0.6), value=val)
    assert interval1[interval2] == 1/val


@pytest.mark.parametrize("val", [1, 2])
def test_interval_out_interval(val):
    interval1 = BaseInterval((0, 1))
    interval2 = BaseInterval((1.4, 1.6), value=val)
    assert interval1[interval2] == 0


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


def test_inplace_addition():
    interval1 = BaseInterval((0, 1))
    interval2 = BaseInterval((1, 2))
    interval3 = BaseInterval((0, 2))
    interval1 += interval2

    assert interval1 == interval3


def test_subtraction():
    interval1 = BaseInterval((0, 1))
    interval2 = BaseInterval((1, 2))
    interval3 = BaseInterval((0, 2))

    assert interval3 - interval2 == interval1
    interval3 -= interval1
    assert interval3 == interval2


def test_negation():
    interval = BaseInterval((0, 1))
    neg_interval = -interval

    assert neg_interval == interval * -1


def test_multiplication():
    interval = BaseInterval((0, 1))
    interval2 = interval * 2
    assert interval == interval2 * 0.5


def test_division():
    interval = BaseInterval((0, 1))
    interval2 = interval * 2
    assert interval2 /2 == interval
    interval2 /= 2
    assert interval2 == interval


def test_comparison():
    interval1 = BaseInterval((0, 1))
    interval2 = BaseInterval((0, 2))
    interval3 = BaseInterval((1, 2))
    interval4 = BaseInterval((0, 1, 2))
    assert interval1 < interval3
    assert interval1 < interval2
    assert interval3 > interval2
    assert interval3 > interval1
    assert not interval1 < interval4
    assert not interval1 > interval4
    assert interval1 <= interval4
    assert interval1 >= interval4


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
    assert interval.get_length() == length


def test_hashable():
    interval1 = BaseInterval((0, 1))
    hash(interval1)
    assert True


def test_shift():
    interval = BaseInterval((0, 1))
    shifted = interval >> 3
    assert shifted == BaseInterval((3, 4))
    assert shifted << 3 == interval


def test_unit_interval():
    interval = UnitInterval()
    assert interval == BaseInterval((0, 1))


def test_empty_interval():
    interval = EmptyInterval()
    assert interval.get_length() == 0


def test_add_empty_interval():
    empty_interval = EmptyInterval()
    unit_interval = UnitInterval()
    assert unit_interval + empty_interval == unit_interval


def test_to_args_and_replace():
    interval = UnitInterval()
    new = BaseInterval(interval.to_args())
    assert interval == new

    interval2 = BaseInterval(0, 2, 4)
    replace = {'stop': 2, 'value': 4}
    new2 = BaseInterval(interval.to_args_and_replace(replace))
    assert interval2 == new2
