import pytest

from collections import Counter

from intervalues import (
    BaseDiscreteInterval,
    BaseInterval,
    IntervalCounter,
    IntervalList,
    IntervalMeter,
    IntervalSet,
)


@pytest.mark.parametrize("count", [1.5, True])
def test_discrete_interval_rejects_non_integer_count(count):
    with pytest.raises(TypeError, match="count must be an integer"):
        BaseDiscreteInterval(0, count=count)


@pytest.mark.parametrize("count", [0, -1])
def test_discrete_interval_rejects_non_positive_count(count):
    with pytest.raises(ValueError, match="count must be at least 1"):
        BaseDiscreteInterval(0, count=count)


@pytest.mark.parametrize("step", [0, -1, float("inf"), float("nan")])
def test_discrete_interval_rejects_invalid_step(step):
    with pytest.raises(ValueError, match="step must be greater than zero"):
        BaseDiscreteInterval(0, count=3, step=step)


def test_discrete_interval_rejects_stop_before_start():
    with pytest.raises(ValueError, match="stop must be greater than or equal to start"):
        BaseDiscreteInterval(2, stop=1)


def test_discrete_interval_accepts_positive_integer_count():
    interval = BaseDiscreteInterval(1, count=3, step=0.5)

    assert interval.count == 3
    assert interval.stop == 2
    assert list(interval) == [(1, 1), (1.5, 1), (2, 1)]


def test_discrete_point_count_and_coordinate_index_helpers():
    interval = BaseDiscreteInterval(1, count=4, step=0.5)

    assert interval.point_count == 4
    assert [interval.coordinate_at(index) for index in range(interval.point_count)] == [
        1, 1.5, 2, 2.5
    ]
    assert interval.index_of(2) == 2
    assert interval.index_of(2 + 1e-8) == 2


@pytest.mark.parametrize("index", [-1, 3])
def test_discrete_coordinate_at_rejects_out_of_range_indices(index):
    with pytest.raises(IndexError, match="index out of range"):
        BaseDiscreteInterval(1, count=3).coordinate_at(index)


def test_discrete_coordinate_index_helpers_reject_invalid_inputs():
    interval = BaseDiscreteInterval(1, count=3)

    with pytest.raises(TypeError, match="index must be an integer"):
        interval.coordinate_at(1.0)
    with pytest.raises(ValueError, match="not a point"):
        interval.index_of(1.5)
    with pytest.raises(ValueError, match="not a point"):
        interval.index_of(float("nan"))


@pytest.mark.parametrize(("value", "expected"), [(0, 1), (1.5, 1), (2.5, 2), (5, 3)])
def test_discrete_clamp_selects_nearest_point_and_prefers_lower_on_ties(value, expected):
    interval = BaseDiscreteInterval(1, count=3)

    assert interval.clamp(value) == expected


def test_discrete_split_at_partitions_points_without_overlap():
    interval = BaseDiscreteInterval(0, count=6, step=2, value=3)

    pieces = interval.split_at([4, 7])

    assert pieces == (
        BaseDiscreteInterval(0, count=3, step=2, value=3),
        BaseDiscreteInterval(6, count=1, step=2, value=3),
        BaseDiscreteInterval(8, count=2, step=2, value=3),
    )
    assert [point for piece in pieces for point, _ in piece] == [0, 2, 4, 6, 8, 10]


def test_interval_set_discrete_reflects_current_contents():
    interval_set = IntervalSet()
    assert interval_set.discrete is False
    assert IntervalSet([]).discrete is False

    interval_set.update(BaseDiscreteInterval(0, count=2))
    assert interval_set.discrete is True

    with pytest.raises(TypeError, match="Cannot mix discrete and continuous"):
        interval_set.update(BaseInterval(3, 4))
    with pytest.raises(TypeError, match="Cannot mix discrete and continuous"):
        interval_set.update(IntervalSet([BaseInterval(3, 4)]))

    interval_set.clear()
    assert interval_set.discrete is False

    interval_set.update(BaseInterval(3, 4))
    assert interval_set.discrete is False


def test_collection_data_uses_the_documented_container_types():
    interval = BaseInterval(0, 1)

    assert isinstance(IntervalList([interval]).get_data(), list)
    assert isinstance(IntervalSet([interval]).get_data(), set)
    assert isinstance(IntervalMeter([interval]).get_data(), Counter)


def test_collection_helpers_are_consistent_for_each_collection_type():
    interval = BaseInterval(2, 4)
    collections = [
        IntervalList(interval),
        IntervalSet(interval),
        IntervalMeter(interval),
        IntervalCounter(interval),
    ]

    assert all(not collection.is_empty for collection in collections)
    assert all(collection.bounds == (2, 4) for collection in collections)
    assert all(collection.find_all_containing(3) for collection in collections)

    empty_collections = [IntervalList(), IntervalSet(), IntervalMeter(), IntervalCounter()]
    assert all(collection.is_empty for collection in empty_collections)
    assert all(collection.bounds is None for collection in empty_collections)
    assert all(collection.find_all_containing(3) == [] for collection in empty_collections)


def test_single_discrete_interval_is_supported_by_all_collections():
    interval = BaseDiscreteInterval(0, count=3)

    assert list(IntervalList(interval)) == [interval]
    assert IntervalSet(interval).discrete
    assert IntervalMeter(interval).data[interval.as_index()] == 1
    assert IntervalCounter(interval).data[interval.as_index()] == 1
    assert IntervalMeter(interval, skip_combine=True).data[interval.as_index()] == 1


def test_discrete_sequences_use_discrete_combiners():
    intervals = [BaseDiscreteInterval(0, count=3), BaseDiscreteInterval(1, count=3)]

    meter = IntervalMeter(intervals)
    counter = IntervalCounter(intervals)

    assert all(isinstance(key, BaseDiscreteInterval) for key in meter.data)
    assert all(isinstance(key, BaseDiscreteInterval) for key in counter.data)
    assert meter[BaseDiscreteInterval(1, count=1)] == 2
    assert counter[BaseDiscreteInterval(1, count=1)] == 2


def test_discrete_combiners_preserve_non_unit_steps():
    intervals = [
        BaseDiscreteInterval(0, count=2, step=2),
        BaseDiscreteInterval(4, count=2, step=2),
    ]
    expected = BaseDiscreteInterval(0, count=4, step=2)

    interval_set = IntervalSet(intervals)
    meter = IntervalMeter(intervals)
    counter = IntervalCounter(intervals)

    assert interval_set == IntervalSet(expected)
    assert set(meter.keys()) == {expected}
    assert set(counter.keys()) == {expected}


def test_discrete_interval_intersection_returns_shared_points_with_product_values():
    left = BaseDiscreteInterval(0, count=5, step=1, value=2)
    right = BaseDiscreteInterval(0, count=3, step=2, value=3)

    assert left.intersection_support(right) == IntervalSet(BaseDiscreteInterval(0, count=3, step=2))
    intersection = left.intersection(right)

    assert isinstance(intersection, IntervalMeter)
    assert intersection[0] == 6
    assert intersection[2] == 6
    assert intersection[4] == 6
    assert intersection[1] == 0


def test_discrete_set_union_intersection_and_difference_keep_large_runs_compact(monkeypatch):
    def fail_if_iterated(self):
        raise AssertionError("compact aligned-run operations must not enumerate points")

    monkeypatch.setattr(BaseDiscreteInterval, "__iter__", fail_if_iterated)
    whole = BaseDiscreteInterval(0, count=10_000_000)
    middle = BaseDiscreteInterval(2_000_000, count=2_000_000)
    tail = BaseDiscreteInterval(4_000_000, count=2_000_000)
    whole_set = IntervalSet(whole)

    union = whole_set | IntervalSet(tail)
    intersection = whole_set.intersection(IntervalSet(middle))
    difference = whole_set - IntervalSet(middle)
    overlapping = whole_set | IntervalSet(BaseDiscreteInterval(9_000_000, count=2_000_001))

    assert union == whole_set
    assert intersection == IntervalSet(middle)
    assert overlapping == IntervalSet(BaseDiscreteInterval(0, count=11_000_001))
    assert difference == IntervalSet([
        BaseDiscreteInterval(0, count=2_000_000),
        BaseDiscreteInterval(4_000_000, count=6_000_000),
    ])


def test_discrete_set_union_retains_compact_partially_overlapping_sequences():
    fine = BaseDiscreteInterval(0, count=11)
    coarse = BaseDiscreteInterval(0, count=6, step=2)

    combined = IntervalSet(fine) | IntervalSet(coarse)

    assert combined == IntervalSet(fine)
    assert len(combined) == 1
    assert 10 in combined

    offset_sequence = BaseDiscreteInterval(1, count=6, step=2)
    distinct = IntervalSet(fine) | IntervalSet(offset_sequence)
    assert len(distinct) == 2
    assert all(isinstance(interval, BaseDiscreteInterval) for interval in distinct)
    assert 11 in distinct


def test_discrete_set_normalization_keeps_nearby_points_exactly_distinct():
    original = BaseDiscreteInterval(0, count=2)
    shifted = BaseDiscreteInterval(1e-7, count=2)

    normalized = IntervalSet([original, shifted])

    assert len(normalized) == 2
    assert {interval.start for interval in normalized} == {0, 1e-7}
