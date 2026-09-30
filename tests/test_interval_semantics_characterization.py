"""Characterize current interval semantics; these tests do not prescribe future changes."""

import math

import pytest

from intervalues import (
    BaseDiscreteInterval,
    BaseInterval,
    EmptyInterval,
    IntervalCounter,
    IntervalList,
    IntervalMeter,
    IntervalSet,
)


def test_continuous_constructor_currently_accepts_degenerate_and_unusual_bounds():
    zero_length = BaseInterval(0, 0)
    reversed_interval = BaseInterval(2, 1)
    nan_interval = BaseInterval(float("nan"), 1)
    infinite_interval = BaseInterval(0, float("inf"))

    assert zero_length.get_length() == 0
    assert 0 in zero_length
    assert reversed_interval.get_length() == -1
    assert math.isnan(nan_interval.get_length())
    assert math.isinf(infinite_interval.get_length())
    assert zero_length == EmptyInterval()
    assert hash(zero_length) == hash(EmptyInterval())


def test_continuous_endpoint_operations_have_distinct_touching_behavior():
    left = BaseInterval(0, 1)
    right = BaseInterval(1, 2)

    assert 1 in left
    assert not left.overlaps(right)
    assert not left.is_disjoint_with(right)
    assert IntervalSet(left).intersection(IntervalSet(right)) == IntervalSet()
    assert not IntervalSet(left).isdisjoint(IntervalSet(right))


def test_continuous_ordering_can_report_both_same_start_intervals_as_less_equal():
    shorter = BaseInterval(0, 1)
    longer = BaseInterval(0, 2)

    assert shorter != longer
    assert shorter <= longer
    assert longer <= shorter


def test_exactly_equal_intervals_have_matching_hashes():
    continuous = BaseInterval(0, 1)
    same_continuous = BaseInterval(0, 1)
    discrete = BaseDiscreteInterval(0, count=3, step=0.5)
    same_discrete = BaseDiscreteInterval(0, count=3, step=0.5)

    assert continuous == same_continuous
    assert hash(continuous) == hash(same_continuous)
    assert discrete == same_discrete
    assert hash(discrete) == hash(same_discrete)


def test_discrete_tolerance_affects_membership_but_not_interval_equality():
    interval = BaseDiscreteInterval(0, count=3)
    shifted = BaseDiscreteInterval(0.0000001, count=3)

    assert 1.0000001 in interval
    assert interval.index_of(1.0000001) == 1
    assert interval != shifted
    assert len({interval, shifted}) == 2


@pytest.mark.parametrize(
    "collection_type",
    [IntervalList, IntervalSet, IntervalMeter, IntervalCounter],
)
@pytest.mark.parametrize("method_name", ["min", "max", "as_single_interval"])
def test_empty_collection_aggregates_currently_raise_value_error(collection_type, method_name):
    method = getattr(collection_type(), method_name)

    with pytest.raises(ValueError):
        method()
