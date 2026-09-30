"""Characterize current interval semantics without changing them implicitly."""

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


def test_continuous_constructor_rejects_invalid_bounds_but_allows_zero_length():
    zero_length = BaseInterval(0, 0)

    assert zero_length.get_length() == 0
    assert 0 in zero_length
    assert zero_length == EmptyInterval()
    assert hash(zero_length) == hash(EmptyInterval())

    with pytest.raises(ValueError, match="start must be less than or equal to stop"):
        BaseInterval(2, 1)
    with pytest.raises(ValueError, match="bounds must be finite"):
        BaseInterval(float("nan"), 1)
    with pytest.raises(ValueError, match="bounds must be finite"):
        BaseInterval(0, float("inf"))


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
