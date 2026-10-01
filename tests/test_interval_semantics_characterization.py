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


def test_continuous_touching_ranges_share_endpoint_across_operations():
    left = BaseInterval(0, 1)
    right = BaseInterval(1, 2)
    touching = IntervalSet(BaseInterval(1, 1))

    assert 1 in left
    assert left.overlaps(right)
    assert not left.is_disjoint_with(right)
    assert IntervalSet(left).intersection(IntervalSet(right)) == touching
    assert IntervalSet(left) & IntervalSet(right) == touching
    assert not IntervalSet(left).isdisjoint(IntervalSet(right))

    result = IntervalSet(left)
    result.intersection_update(IntervalSet(right))
    assert result == touching


def test_continuous_endpoint_operations_include_containment_and_degenerate_ranges():
    containing = BaseInterval(0, 2)
    contained = BaseInterval(1, 1)
    separated_point = BaseInterval(3, 3)

    assert containing.overlaps(contained)
    assert not containing.is_disjoint_with(contained)
    assert not containing.is_disjoint_with(containing)
    assert not contained.is_disjoint_with(BaseInterval(1, 2))
    assert contained.is_disjoint_with(separated_point)
    assert IntervalSet(contained).intersection(IntervalSet(BaseInterval(0, 2))) == IntervalSet(contained)


def test_continuous_interval_intersection_separates_support_from_values():
    left = BaseInterval(0, 2, value=3)
    right = BaseInterval(1, 3, value=4)

    assert left.intersection_support(right) == IntervalSet(BaseInterval(1, 2))
    assert right.intersection_support(left) == left.intersection_support(right)
    assert left.intersection(right) == IntervalMeter(BaseInterval(1, 2, value=12))
    assert right.intersection(left) == left.intersection(right)


def test_continuous_intersection_handles_touching_and_disjoint_intervals():
    left = BaseInterval(0, 1, value=2)
    touching = BaseInterval(1, 2, value=3)
    disjoint = BaseInterval(2, 3)
    point = BaseInterval(0, 0)

    assert left.intersection_support(touching) == IntervalSet(BaseInterval(1, 1))
    assert left.intersection(touching).is_empty
    assert left.intersection_support(disjoint).is_empty
    assert left.intersection(disjoint).is_empty
    assert point.intersection_support(EmptyInterval()) == IntervalSet(EmptyInterval())
    assert point.intersection(EmptyInterval()).is_empty


def test_discrete_interval_intersection_preserves_common_points_and_products():
    left = BaseDiscreteInterval(0, count=5, step=1, value=2)
    right = BaseDiscreteInterval(0, count=3, step=2, value=3)

    assert left.intersection_support(right) == IntervalSet(
        BaseDiscreteInterval(0, count=3, step=2)
    )
    result = left.intersection(right)
    assert isinstance(result, IntervalMeter)
    assert result[0] == 6
    assert result[2] == 6
    assert result[4] == 6
    assert result[1] == 0

    even_lattice = BaseDiscreteInterval(0, count=3, step=2)
    odd_lattice = BaseDiscreteInterval(1, count=3, step=2)
    assert even_lattice.intersection_support(odd_lattice).is_empty
    assert even_lattice.intersection(odd_lattice).is_empty


def test_interval_intersection_rejects_mixed_coordinate_domains():
    with pytest.raises(TypeError, match="Cannot intersect discrete and continuous"):
        BaseInterval(0, 2).intersection_support(BaseDiscreteInterval(0, count=3))
    with pytest.raises(TypeError, match="Cannot intersect discrete and continuous"):
        BaseDiscreteInterval(0, count=3).intersection(BaseInterval(0, 2))


def test_continuous_ordering_uses_start_stop_then_value():
    shorter = BaseInterval(0, 1)
    longer = BaseInterval(0, 2)
    heavier = BaseInterval(0, 1, value=2)

    assert shorter != longer
    assert shorter < longer
    assert shorter <= longer
    assert longer > shorter
    assert not longer <= shorter
    assert shorter < heavier
    assert heavier > shorter
    assert shorter <= shorter.with_value(2)
    assert not shorter.with_value(2) <= shorter


def test_exactly_equal_intervals_have_matching_hashes():
    continuous = BaseInterval(0, 1)
    same_continuous = BaseInterval(0, 1)
    discrete = BaseDiscreteInterval(0, count=3, step=0.5)
    same_discrete = BaseDiscreteInterval(0, count=3, step=0.5)

    assert continuous == same_continuous
    assert hash(continuous) == hash(same_continuous)
    assert discrete == same_discrete
    assert hash(discrete) == hash(same_discrete)


def test_continuous_and_discrete_intervals_are_not_cross_type_equal():
    continuous = BaseInterval(0, 2)
    discrete = BaseDiscreteInterval(0, 2)

    assert continuous != discrete
    assert discrete != continuous


def test_discrete_ordering_distinguishes_step_and_coordinate_domain():
    fine = BaseDiscreteInterval(0, count=5, step=0.5)
    coarse = BaseDiscreteInterval(0, count=3, step=1)
    continuous = BaseInterval(0, 2)

    assert fine != coarse
    assert fine < coarse
    assert coarse > fine
    assert continuous < fine


def test_discrete_tolerance_affects_membership_but_not_interval_equality():
    interval = BaseDiscreteInterval(0, count=3)
    shifted = BaseDiscreteInterval(0.0000001, count=3)

    assert 1.0000001 in interval
    assert interval.index_of(1.0000001) == 1
    assert interval != shifted
    assert len({interval, shifted}) == 2


@pytest.mark.parametrize(
    "collection_factory",
    [
        IntervalList,
        IntervalSet,
        IntervalMeter,
        IntervalCounter,
        lambda interval: interval.as_pdf(),
    ],
)
def test_single_interval_equivalent_collections_are_symmetric_and_hash_equal(collection_factory):
    interval = BaseInterval(0, 1)
    collection = collection_factory(interval)

    assert interval == collection
    assert collection == interval
    assert hash(interval) == hash(collection)
    assert len({interval, collection}) == 1


def test_collection_equality_and_hashing_respect_their_container_semantics():
    left = [BaseInterval(0, 1), BaseInterval(2, 3)]
    right = list(reversed(left))

    assert IntervalList(left) != IntervalList(right)

    set_left, set_right = IntervalSet(left), IntervalSet(right)
    assert set_left == set_right
    assert hash(set_left) == hash(set_right)

    meter_left = IntervalMeter(left)
    meter_right = IntervalMeter(right)
    assert meter_left == meter_right
    assert hash(meter_left) == hash(meter_right)


def test_meter_and_counter_equality_is_symmetric_and_type_specific():
    meter = IntervalMeter(BaseInterval(0, 1))
    counter = IntervalCounter(BaseInterval(0, 1))

    assert meter != counter
    assert counter != meter


def test_meter_ordering_distinguishes_different_values_on_same_bounds():
    lower = IntervalMeter(BaseInterval(0, 1, value=1))
    higher = IntervalMeter(BaseInterval(0, 1, value=2))

    assert lower < higher
    assert higher > lower
    assert lower <= higher
    assert not higher <= lower


@pytest.mark.parametrize(
    "collection_type",
    [IntervalList, IntervalSet, IntervalMeter, IntervalCounter],
)
@pytest.mark.parametrize("method_name", ["min", "max", "as_single_interval"])
def test_empty_collection_aggregates_currently_raise_value_error(collection_type, method_name):
    method = getattr(collection_type(), method_name)

    with pytest.raises(ValueError):
        method()
