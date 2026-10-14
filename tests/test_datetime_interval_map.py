from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from intervalues import BaseInterval, IntervalMap, PriorityIntervalMap, combine_maps, resolve_maps


def utc_bounds(interval_map):
    return [
        (interval.start.astimezone(timezone.utc), interval.stop.astimezone(timezone.utc), value)
        for interval, value in interval_map.items()
    ]


def test_datetime_map_assignment_lookup_and_reset_use_half_open_ranges():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    interval_map = IntervalMap(default="off")
    interval_map.assign(start, start + timedelta(hours=1), "on")
    interval_map.assign(start + timedelta(minutes=15), start + timedelta(minutes=30), "curtail")

    assert utc_bounds(interval_map) == [
        (start, start + timedelta(minutes=15), "on"),
        (start + timedelta(minutes=15), start + timedelta(minutes=30), "curtail"),
        (start + timedelta(minutes=30), start + timedelta(hours=1), "on"),
    ]
    assert interval_map[start] == "on"
    assert interval_map[start + timedelta(minutes=15)] == "curtail"
    assert interval_map[start + timedelta(minutes=30)] == "on"
    assert interval_map[start + timedelta(hours=1)] == "off"
    assert start + timedelta(minutes=15) in interval_map
    assert start + timedelta(hours=1) not in interval_map

    interval_map.reset(BaseInterval(start + timedelta(minutes=15), start + timedelta(minutes=30)))
    assert utc_bounds(interval_map) == [
        (start, start + timedelta(minutes=15), "on"),
        (start + timedelta(minutes=30), start + timedelta(hours=1), "on"),
    ]


def test_aware_datetime_maps_compare_instants_across_timezones():
    start_utc = datetime(2024, 1, 1, tzinfo=timezone.utc)
    local_zone = ZoneInfo("America/Los_Angeles")
    start_local = start_utc.astimezone(local_zone)
    interval_map = IntervalMap()
    interval_map.assign(start_utc, start_utc + timedelta(hours=1), "base")
    interval_map.assign(
        start_local + timedelta(minutes=15),
        start_local + timedelta(minutes=30),
        "override",
    )

    assert interval_map[start_utc + timedelta(minutes=20)] == "override"
    assert interval_map[(start_utc + timedelta(minutes=20)).astimezone(local_zone)] == "override"
    assert len(interval_map) == 3


def test_aware_datetime_maps_keep_both_dst_fold_occurrences_distinct():
    new_york = ZoneInfo("America/New_York")
    first_hour = datetime(2024, 11, 3, 1, 0, tzinfo=new_york, fold=0)
    second_hour = datetime(2024, 11, 3, 1, 0, tzinfo=new_york, fold=1)
    end = datetime(2024, 11, 3, 2, 0, tzinfo=new_york)
    interval_map = IntervalMap()
    interval_map.assign(first_hour, second_hour, "first occurrence")
    interval_map.assign(second_hour, end, "second occurrence")

    first_midpoint = datetime(2024, 11, 3, 1, 30, tzinfo=new_york, fold=0)
    second_midpoint = datetime(2024, 11, 3, 1, 30, tzinfo=new_york, fold=1)
    assert utc_bounds(interval_map) == [
        (first_hour.astimezone(timezone.utc), second_hour.astimezone(timezone.utc), "first occurrence"),
        (second_hour.astimezone(timezone.utc), end.astimezone(timezone.utc), "second occurrence"),
    ]
    assert interval_map[first_midpoint] == "first occurrence"
    assert interval_map[second_midpoint] == "second occurrence"
    assert second_hour in interval_map


def test_priority_map_resolution_keeps_dst_fold_occurrences_distinct():
    new_york = ZoneInfo("America/New_York")
    first_hour = datetime(2024, 11, 3, 1, 0, tzinfo=new_york, fold=0)
    second_hour = datetime(2024, 11, 3, 1, 0, tzinfo=new_york, fold=1)
    end = datetime(2024, 11, 3, 2, 0, tzinfo=new_york)

    baseline = IntervalMap()
    baseline.assign(first_hour, end, "available")
    curtailment = IntervalMap()
    curtailment.assign(second_hour, end, "curtailed")
    resolver = PriorityIntervalMap(default="unconfigured")
    baseline_handle, _ = resolver.add(baseline, priority=10)
    curtailment_handle, _ = resolver.add(curtailment, priority=20)

    first_midpoint = datetime(2024, 11, 3, 1, 30, tzinfo=new_york, fold=0)
    second_midpoint = datetime(2024, 11, 3, 1, 30, tzinfo=new_york, fold=1)
    assert resolver[first_midpoint] == "available"
    assert resolver[second_midpoint] == "curtailed"
    assert resolver.active_regions(curtailment_handle)[0].start.astimezone(timezone.utc) == (
        second_hour.astimezone(timezone.utc)
    )
    assert resolver.active_regions(baseline_handle)[0].stop.astimezone(timezone.utc) == (
        second_hour.astimezone(timezone.utc)
    )


def test_datetime_map_rejects_mixed_domains_without_changing_existing_segments():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    numeric = IntervalMap()
    numeric.assign(0, 1, "numeric")
    before = numeric.items()

    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        numeric.assign(start, start + timedelta(hours=1), "datetime")
    assert numeric.items() == before
    assert start not in numeric
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        numeric[start]

    naive = IntervalMap()
    naive.assign(datetime(2024, 1, 1), datetime(2024, 1, 2), "naive")
    naive_before = naive.items()
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        naive.assign(start, start + timedelta(hours=1), "aware")
    assert naive.items() == naive_before


def test_map_rejects_naive_aware_bounds_and_invalid_datetime_coordinates():
    interval_map = IntervalMap()
    aware = datetime(2024, 1, 1, tzinfo=timezone.utc)
    naive = datetime(2024, 1, 2)
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        interval_map.assign(aware, naive, "mixed")
    with pytest.raises(TypeError, match="int, float, or datetime"):
        interval_map.assign("2024-01-01", "2024-01-02", "string")


def test_combine_and_resolve_maps_partition_datetime_ranges_across_timezones():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    local_zone = ZoneInfo("America/Los_Angeles")
    first = IntervalMap()
    first.assign(start, start + timedelta(hours=1), 1)
    second = IntervalMap()
    second.assign(
        (start + timedelta(minutes=15)).astimezone(local_zone),
        (start + timedelta(minutes=45)).astimezone(local_zone),
        2,
    )

    combined = combine_maps([first, second], combine=sum, absent=0)
    assert utc_bounds(combined) == [
        (start, start + timedelta(minutes=15), 1),
        (start + timedelta(minutes=15), start + timedelta(minutes=45), 3),
        (start + timedelta(minutes=45), start + timedelta(hours=1), 1),
    ]

    resolved = resolve_maps([second, first], default=0)
    assert utc_bounds(resolved) == [
        (start, start + timedelta(minutes=15), 1),
        (start + timedelta(minutes=15), start + timedelta(minutes=45), 2),
        (start + timedelta(minutes=45), start + timedelta(hours=1), 1),
    ]


def test_priority_map_supports_datetime_lookups_provenance_batches_and_regions():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    baseline = IntervalMap()
    baseline.assign(start, start + timedelta(hours=1), "available")
    local_zone = ZoneInfo("America/Los_Angeles")
    curtailment = IntervalMap()
    curtailment.assign(
        (start + timedelta(minutes=15)).astimezone(local_zone),
        (start + timedelta(minutes=30)).astimezone(local_zone),
        "curtailed",
    )
    resolver = PriorityIntervalMap(default="unconfigured")
    baseline_handle, _ = resolver.add(baseline, priority=10)
    curtailment_handle, _ = resolver.add(curtailment, priority=20)

    first_slot = start + timedelta(minutes=15)
    second_slot = start + timedelta(minutes=20)
    assert resolver.lookup_many([start, second_slot, first_slot]) == (
        "available",
        "curtailed",
        "curtailed",
    )
    assert resolver.lookup(second_slot, with_priority=True).source is curtailment_handle
    explanation = resolver.explain(second_slot)
    assert explanation.value == "curtailed"
    assert explanation.priority == 20
    assert explanation.source is curtailment_handle
    assert resolver.active_regions(curtailment_handle)[0].start == first_slot
    assert resolver.active_regions(baseline_handle)
    assert utc_bounds(resolver.snapshot()) == [
        (start, first_slot, "available"),
        (first_slot, start + timedelta(minutes=30), "curtailed"),
        (start + timedelta(minutes=30), start + timedelta(hours=1), "available"),
    ]


def test_priority_and_map_composition_reject_mixed_domains_atomically():
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    numeric = IntervalMap()
    numeric.assign(0, 2, "numeric")
    temporal = IntervalMap()
    temporal.assign(start, start + timedelta(hours=1), "datetime")

    resolver = PriorityIntervalMap(default="gap")
    resolver.add(numeric, 1)
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        resolver.add(temporal, 2)
    assert resolver[1] == "numeric"
    assert start not in resolver
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        resolver.lookup(start)

    handle, _ = resolver.add(IntervalMap(), 2)
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        resolver.replace(handle, temporal)
    assert resolver[1] == "numeric"

    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        combine_maps([numeric, temporal], combine=lambda values: values, absent=None)
    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        resolve_maps([numeric, temporal])


def test_priority_lookup_many_rejects_mixed_coordinate_domains():
    resolver = PriorityIntervalMap(default="gap")
    numeric = datetime(2024, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(TypeError, match="same numeric/datetime domain"):
        resolver.lookup_many([0, numeric])
