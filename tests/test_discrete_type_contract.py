import pytest

from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

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


def test_datetime_discrete_interval_requires_stop_or_count_and_explicit_timedelta_step():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(TypeError, match="explicit stop or count"):
        BaseDiscreteInterval(start, step=timedelta(hours=1))
    with pytest.raises(TypeError, match="explicit timedelta step"):
        BaseDiscreteInterval(start, count=2)
    with pytest.raises(TypeError, match="explicit timedelta step"):
        BaseDiscreteInterval(start, stop=start + timedelta(hours=1))
    with pytest.raises(TypeError, match="explicit timedelta step"):
        BaseDiscreteInterval(start, count=1, step=1)


@pytest.mark.parametrize("step", [timedelta(0), -timedelta(seconds=1)])
def test_datetime_discrete_interval_rejects_non_positive_step(step):
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="step must be greater than zero"):
        BaseDiscreteInterval(start, count=2, step=step)


def test_datetime_discrete_interval_truncates_stop_and_uses_exact_microseconds():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    interval = BaseDiscreteInterval(
        start,
        stop=start + timedelta(seconds=10, microseconds=5),
        step=timedelta(seconds=3),
    )

    assert interval.count == 4
    assert interval.stop == start + timedelta(seconds=9)
    assert list(interval) == [
        (start, 1),
        (start + timedelta(seconds=3), 1),
        (start + timedelta(seconds=6), 1),
        (start + timedelta(seconds=9), 1),
    ]


def test_datetime_discrete_interval_count_construction_and_argument_round_trip():
    start = datetime(2024, 1, 1, 9, tzinfo=timezone.utc)
    interval = BaseDiscreteInterval(start, count=3, step=timedelta(minutes=15), value=2)
    copied = BaseDiscreteInterval(interval.to_args())

    assert interval.point_count == 3
    assert interval.coordinate_at(2) == start + timedelta(minutes=30)
    assert copied == interval
    assert hash(copied) == hash(interval)


def test_datetime_discrete_interval_uses_absolute_elapsed_steps_across_dst_fold():
    amsterdam = ZoneInfo("Europe/Amsterdam")
    start = datetime(2023, 10, 29, 1, 30, tzinfo=amsterdam)
    interval = BaseDiscreteInterval(start, count=4, step=timedelta(hours=1))
    expected_utc = [
        (start.astimezone(timezone.utc) + timedelta(hours=index))
        for index in range(4)
    ]

    assert [point.astimezone(timezone.utc) for point, _ in interval] == expected_utc
    assert interval.get_length() == 0
    assert interval.coordinate_at(1).fold == 0


def test_datetime_discrete_membership_and_indexing_require_exact_alignment():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    interval = BaseDiscreteInterval(start, count=4, step=timedelta(seconds=3))
    aligned = start + timedelta(seconds=6)

    assert aligned in interval
    assert start + timedelta(seconds=7) not in interval
    assert interval.index_of(aligned) == 2
    with pytest.raises(ValueError, match="not a point"):
        interval.index_of(start + timedelta(seconds=7))
    with pytest.raises(TypeError, match="datetime interval"):
        interval.index_of(0)
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        0 in interval


def test_datetime_discrete_membership_of_runs_is_exact():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    whole = BaseDiscreteInterval(start, count=7, step=timedelta(minutes=5))
    contained = BaseDiscreteInterval(
        start + timedelta(minutes=10),
        count=3,
        step=timedelta(minutes=10),
    )
    misaligned = BaseDiscreteInterval(
        start + timedelta(minutes=11),
        count=2,
        step=timedelta(minutes=10),
    )

    assert contained in whole
    assert misaligned not in whole
    assert BaseDiscreteInterval(start, count=2, step=timedelta(minutes=5)) in whole


def test_datetime_discrete_clamp_chooses_nearest_and_prefers_earlier_on_ties():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    interval = BaseDiscreteInterval(start, count=3, step=timedelta(hours=1))

    assert interval.clamp(start - timedelta(minutes=1)) == start
    assert interval.clamp(start + timedelta(minutes=30)) == start
    assert interval.clamp(start + timedelta(minutes=31)) == start + timedelta(hours=1)
    assert interval.clamp(start + timedelta(hours=2, minutes=1)) == interval.stop
    with pytest.raises(TypeError, match="datetime coordinates"):
        interval.clamp(1)


def test_datetime_discrete_split_assigns_points_at_or_before_boundary_left():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    interval = BaseDiscreteInterval(start, count=5, step=timedelta(hours=1), value=3)

    pieces = interval.split_at([
        start + timedelta(minutes=90),
        start + timedelta(hours=2),
        start + timedelta(minutes=90),
    ])

    assert [piece.count for piece in pieces] == [2, 1, 2]
    assert [point for piece in pieces for point, _ in piece] == [point for point, _ in interval]
    assert all(piece.value == 3 for piece in pieces)
    with pytest.raises(TypeError, match="datetime split points"):
        interval.split_at([1])


def test_datetime_discrete_adjacency_compares_elapsed_steps():
    amsterdam = ZoneInfo("Europe/Amsterdam")
    start = datetime(2023, 10, 29, 1, 30, tzinfo=amsterdam)
    left = BaseDiscreteInterval(start, count=2, step=timedelta(hours=1))
    next_start = (
        left.stop.astimezone(timezone.utc) + timedelta(hours=1)
    ).astimezone(amsterdam)
    right = BaseDiscreteInterval(next_start, count=2, step=timedelta(hours=1))

    assert left.left_borders(right)
    assert right.right_borders(left)


def test_datetime_discrete_intervals_reject_mixed_domains_and_awareness():
    naive = datetime(2024, 1, 1)
    aware = datetime(2024, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        BaseDiscreteInterval(naive, stop=aware, step=timedelta(hours=1))
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        BaseDiscreteInterval(0, stop=2, step=timedelta(hours=1))
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        BaseDiscreteInterval(naive, count=2, step=timedelta(hours=1)).overlaps(
            BaseDiscreteInterval(aware, count=2, step=timedelta(hours=1))
        )


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


def test_discrete_set_algebra_uses_exact_coordinates_not_membership_tolerance():
    original = IntervalSet(BaseDiscreteInterval(0, count=3))
    shifted = IntervalSet(BaseDiscreteInterval(1e-7, count=3))

    assert 1.0000001 in original
    assert original.intersection(shifted).is_empty
    assert original.isdisjoint(shifted)
    assert original - shifted == original
    assert not original.issubset(shifted)


def test_discrete_unaligned_step_intersection_uses_compact_integer_runs(monkeypatch):
    def fail_if_iterated(self):
        raise AssertionError("integer-multiple step intersection must not enumerate points")

    monkeypatch.setattr(BaseDiscreteInterval, "__iter__", fail_if_iterated)
    fine = IntervalSet(BaseDiscreteInterval(0, count=10_000_001, step=1))
    offset_coarse = IntervalSet(BaseDiscreteInterval(1, count=5_000_000, step=2))
    wider_coarse = IntervalSet(BaseDiscreteInterval(1, count=1_666_667, step=6))

    assert fine.intersection(offset_coarse) == offset_coarse
    assert offset_coarse.intersection(wider_coarse) == wider_coarse


def test_discrete_unaligned_step_difference_compacts_periodic_holes(monkeypatch):
    def fail_if_iterated(self):
        raise AssertionError("integer-multiple step difference must not enumerate points")

    monkeypatch.setattr(BaseDiscreteInterval, "__iter__", fail_if_iterated)
    every_point = IntervalSet(BaseDiscreteInterval(0, count=1_000_001, step=1))
    every_third = IntervalSet(BaseDiscreteInterval(0, count=333_334, step=3))

    difference = every_point - every_third

    assert difference == IntervalSet([
        BaseDiscreteInterval(1, count=333_333, step=3),
        BaseDiscreteInterval(2, count=333_333, step=3),
        BaseDiscreteInterval(1_000_000, count=1),
    ])


@pytest.mark.parametrize(
    ("left_points", "right_points"),
    [
        ((0, 2, 4, 6, 8, 10), (2, 8)),
        ((1, 4, 7, 10), (4, 10)),
        ((0, 3, 6, 9, 12), (3, 9)),
        ((0, 1, 2, 3, 4, 5), (1, 4)),
    ],
)
def test_integer_step_operations_match_exact_point_set_oracle(left_points, right_points):
    left_interval = BaseDiscreteInterval(left_points[0], stop=left_points[-1],
                                         step=left_points[1] - left_points[0] if len(left_points) > 1 else 1)
    right_interval = BaseDiscreteInterval(right_points[0], stop=right_points[-1],
                                          step=right_points[1] - right_points[0] if len(right_points) > 1 else 1)
    left = IntervalSet(left_interval)
    right = IntervalSet(right_interval)
    expected_left, expected_right = set(left_points), set(right_points)

    intersection = left.intersection(right)
    difference = left - right

    assert {point for interval in intersection for point, _ in interval} == expected_left & expected_right
    assert {point for interval in difference for point, _ in interval} == expected_left - expected_right


def test_integer_step_set_algebra_matches_exhaustive_small_point_oracle():
    runs = [
        BaseDiscreteInterval(start, count=count, step=step)
        for start in range(-2, 3)
        for step in range(1, 5)
        for count in range(1, 5)
    ]

    for left_run in runs:
        left = IntervalSet(left_run)
        left_points = {point for point, _ in left_run}
        for right_run in runs:
            right = IntervalSet(right_run)
            right_points = {point for point, _ in right_run}

            actual_intersection = {
                point for interval in left.intersection(right) for point, _ in interval
            }
            actual_difference = {point for interval in left - right for point, _ in interval}

            assert actual_intersection == left_points & right_points
            assert actual_difference == left_points - right_points
