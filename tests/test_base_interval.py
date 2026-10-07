from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from intervalues import BaseInterval, EmptyInterval, IntervalMeter, IntervalSet, UnitInterval


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


def test_datetime_interval_requires_explicit_stop():
    with pytest.raises(TypeError, match="require an explicit stop"):
        BaseInterval(datetime(2024, 1, 1))


def test_datetime_interval_preserves_bounds():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    stop = start + timedelta(hours=3)

    interval = BaseInterval(start, stop)

    assert interval.min() is start
    assert interval.max() is stop


def test_datetime_interval_rejects_mixed_coordinate_domains_and_awareness():
    naive = datetime(2024, 1, 1)
    aware = datetime(2024, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(TypeError, match="same coordinate domain"):
        BaseInterval(naive, aware)
    with pytest.raises(TypeError, match="same coordinate domain"):
        BaseInterval(0, aware)
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        BaseInterval(naive, naive + timedelta(hours=1)).overlaps(
            BaseInterval(aware, aware + timedelta(hours=1))
        )


def test_aware_datetime_comparison_uses_absolute_instants_and_hashes_consistently():
    amsterdam = ZoneInfo("Europe/Amsterdam")
    first_fold = datetime(2023, 10, 29, 2, 30, tzinfo=amsterdam, fold=0)
    second_fold = datetime(2023, 10, 29, 2, 30, tzinfo=amsterdam, fold=1)
    second_fold_stop = datetime(2023, 10, 29, 2, 45, tzinfo=amsterdam, fold=1)
    equivalent_instant = first_fold.astimezone(ZoneInfo("America/Kralendijk"))

    first = BaseInterval(first_fold, first_fold + timedelta(minutes=15))
    same_instant = BaseInterval(
        equivalent_instant,
        (first_fold + timedelta(minutes=15)).astimezone(ZoneInfo("America/Kralendijk")),
    )
    second = BaseInterval(second_fold, second_fold_stop)

    assert first == same_instant
    assert hash(first) == hash(same_instant)
    assert first != second
    assert first < second
    assert first.overlaps(same_instant)
    assert not first.overlaps(second)
    assert len({first: "first", same_instant: "same"}) == 1


def test_datetime_containment_overlap_borders_and_point_lookup():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    middle = start + timedelta(hours=1)
    stop = start + timedelta(hours=2)
    interval = BaseInterval(start, middle)
    touching = BaseInterval(middle, stop)

    assert start in interval
    assert middle in interval
    assert BaseInterval(start, middle) in interval
    assert interval[middle] == 1
    assert interval.overlaps(touching)
    assert interval.left_borders(touching)
    assert not interval.left_overlaps(touching)


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
    assert interval1 < interval4
    assert interval4 > interval1
    assert interval1 <= interval4
    assert not interval1 >= interval4


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
    assert interval1.overlaps(interval3)
    assert interval1.overlaps(interval1)


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


def test_intersection_support_ignores_values_and_includes_touching_point():
    left = BaseInterval(0, 2, value=3)
    right = BaseInterval(1, 3, value=4)
    touching = BaseInterval(2, 4)

    assert left.intersection_support(right) == IntervalSet(BaseInterval(1, 2))
    assert left.intersection_support(touching) == IntervalSet(BaseInterval(2, 2))
    assert left.intersection_support(BaseInterval(3, 4)).is_empty


def test_intersection_returns_value_product_over_positive_length_support():
    left = BaseInterval(0, 2, value=3)
    right = BaseInterval(1, 3, value=4)

    assert left.intersection(right) == IntervalMeter(BaseInterval(1, 2, value=12))
    assert left.intersection(BaseInterval(2, 3)).is_empty
    assert left.intersection(BaseInterval(3, 4)).is_empty


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


def test_distance_to():
    interval = BaseInterval(0, 2)

    assert interval.distance_to(BaseInterval(4, 5)) == 2
    assert interval.distance_to(BaseInterval(2, 3)) == 0
    assert interval.distance_to(BaseInterval(1, 3)) == 0


def test_datetime_distance_returns_elapsed_timedelta():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    interval = BaseInterval(start, start + timedelta(hours=2))

    assert interval.distance_to(BaseInterval(start + timedelta(hours=5), start + timedelta(hours=6))) == timedelta(hours=3)
    assert interval.distance_to(BaseInterval(start + timedelta(hours=2), start + timedelta(hours=3))) == timedelta(0)
    assert interval.distance_to(BaseInterval(start + timedelta(hours=1), start + timedelta(hours=3))) == timedelta(0)


def test_datetime_length_and_distance_use_elapsed_time_across_dst_fold():
    amsterdam = ZoneInfo("Europe/Amsterdam")
    before_fold = datetime(2023, 10, 29, 2, 30, tzinfo=amsterdam, fold=0)
    after_fold = datetime(2023, 10, 29, 2, 30, tzinfo=amsterdam, fold=1)
    interval = BaseInterval(before_fold, after_fold)
    later = BaseInterval(after_fold + timedelta(hours=1), after_fold + timedelta(hours=2))

    assert interval.get_length() == timedelta(hours=1)
    assert interval.distance_to(later) == timedelta(hours=1)


def test_naive_datetime_operations_use_timezone_free_coordinates():
    start = datetime(2024, 1, 1, 9)
    stop = datetime(2024, 1, 1, 11)
    interval = BaseInterval(start, stop)
    shifted = interval >> timedelta(minutes=30)

    assert interval.get_length() == timedelta(hours=2)
    assert interval.distance_to(BaseInterval(stop + timedelta(hours=1), stop + timedelta(hours=2))) == timedelta(hours=1)
    assert interval.clamp(start - timedelta(minutes=1)) == start
    assert interval.split_at([start + timedelta(hours=1)]) == (
        BaseInterval(start, start + timedelta(hours=1)),
        BaseInterval(start + timedelta(hours=1), stop),
    )
    assert shifted.start == datetime(2024, 1, 1, 9, 30)
    assert shifted.stop == datetime(2024, 1, 1, 11, 30)


def test_fractionally_weighted_datetime_length_uses_timedelta_scaling():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    stop = start + timedelta(microseconds=1)
    interval = BaseInterval(start, stop, value=0.5)

    assert interval.get_length() == timedelta(microseconds=1) * 0.5


def test_datetime_clamp_and_rejects_mixed_coordinate_domains():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    middle = start + timedelta(hours=1)
    stop = start + timedelta(hours=2)
    interval = BaseInterval(start, stop)

    assert interval.clamp(start - timedelta(minutes=1)) == start
    assert interval.clamp(middle) == middle
    assert interval.clamp(stop + timedelta(minutes=1)) == stop
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        interval.clamp(0)
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        BaseInterval(0, 2).clamp(start)


def test_datetime_split_at_orders_and_deduplicates_by_instant():
    amsterdam = ZoneInfo("Europe/Amsterdam")
    kralendijk = ZoneInfo("America/Kralendijk")
    start = datetime(2023, 10, 29, 2, 15, tzinfo=amsterdam, fold=0)
    first_split = datetime(2023, 10, 29, 2, 30, tzinfo=amsterdam, fold=0)
    second_split = datetime(2023, 10, 29, 2, 30, tzinfo=amsterdam, fold=1)
    stop = datetime(2023, 10, 29, 2, 45, tzinfo=amsterdam, fold=1)
    interval = BaseInterval(start, stop, value=2)

    pieces = interval.split_at([second_split, first_split, second_split.astimezone(kralendijk)])

    assert len(pieces) == 3
    assert [piece.get_length() for piece in pieces] == [
        timedelta(minutes=30),
        timedelta(hours=2),
        timedelta(minutes=30),
    ]
    assert all(piece.value == 2 for piece in pieces)
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        interval.split_at([1])
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        BaseInterval(0, 10).split_at([start])


def test_datetime_shift_uses_elapsed_timedelta_across_dst():
    amsterdam = ZoneInfo("Europe/Amsterdam")
    start = datetime(2023, 10, 29, 1, 30, tzinfo=amsterdam)
    stop = datetime(2023, 10, 29, 2, 15, tzinfo=amsterdam, fold=0)
    interval = BaseInterval(start, stop)
    shift = timedelta(hours=2)

    shifted = interval >> shift

    assert shifted.start.astimezone(timezone.utc) == start.astimezone(timezone.utc) + shift
    assert shifted.stop.astimezone(timezone.utc) == stop.astimezone(timezone.utc) + shift
    assert (shifted << shift) == interval
    with pytest.raises(TypeError, match="timedelta shift"):
        interval >> 2
    with pytest.raises(TypeError, match="timedelta shifts"):
        BaseInterval(0, 2) >> shift


@pytest.mark.parametrize(("value", "expected"), [(-1, 0), (0.5, 0.5), (3, 2)])
def test_clamp(value, expected):
    assert BaseInterval(0, 2).clamp(value) == expected


def test_clamp_rejects_nan():
    with pytest.raises(ValueError, match="must not be NaN"):
        BaseInterval(0, 2).clamp(float("nan"))


def test_split_at_preserves_value_and_covers_input():
    interval = BaseInterval(0, 10, value=2)

    assert interval.split_at([7, 3, 3, -1, 10]) == (
        BaseInterval(0, 3, value=2),
        BaseInterval(3, 7, value=2),
        BaseInterval(7, 10, value=2),
    )


def test_split_at_without_interior_points_returns_a_copy():
    interval = BaseInterval(0, 2)

    pieces = interval.split_at([-1, 0, 2, 3])

    assert pieces == (interval,)
    assert pieces[0] is not interval


def test_split_at_rejects_non_finite_points():
    with pytest.raises(ValueError, match="split points must be finite numbers"):
        BaseInterval(0, 2).split_at([float("inf")])


def test_with_value_returns_a_copy_without_mutating_original():
    interval = BaseInterval(0, 2, value=3)

    changed = interval.with_value(5)

    assert changed == BaseInterval(0, 2, value=5)
    assert interval == BaseInterval(0, 2, value=3)


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
