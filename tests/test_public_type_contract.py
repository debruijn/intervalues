from collections import Counter
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Iterator, NoReturn, Sequence as TypingSequence, get_type_hints
from zoneinfo import ZoneInfo

import intervalues
from intervalues import (
    AbstractInterval,
    AbstractIntervalCollection,
    BaseDiscreteInterval,
    BaseInterval,
    Coordinate,
    IntervalCounter,
    IntervalFunction,
    IntervalList,
    IntervalMap,
    IntervalMeter,
    IntervalPdf,
    IntervalSet,
    Length,
    FunctionInterval,
    PriorityIntervalMap,
    PriorityLookupResult,
    PriorityResolutionExplanation,
    PrioritySourceHandle,
    combine_maps,
    combine_intervals,
    resolve_maps,
)


def check_temporal_type_api() -> tuple[Length, Coordinate, Coordinate]:
    """Static temporal examples checked by Mypy; pytest calls this helper."""
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    stop = start + timedelta(hours=1)
    interval = BaseInterval(start, stop)
    discrete = BaseDiscreteInterval(start, count=3, step=timedelta(minutes=5))

    elapsed: Length = interval.get_length()
    coordinate: Coordinate = discrete.coordinate_at(1)
    bounds: tuple[Coordinate, Coordinate] | None = IntervalSet(interval).bounds
    converted: BaseInterval = interval.to_timezone(ZoneInfo("America/Kralendijk"))
    shifted: BaseInterval = interval >> timedelta(minutes=30)

    assert bounds is not None
    return elapsed, coordinate, converted.start if converted.start else shifted.start


def check_temporal_attribute_types() -> tuple[Coordinate, float | timedelta, list[tuple[Coordinate, float]]]:
    """Static checks for public temporal bounds, steps, and point iteration."""
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    interval = BaseInterval(start, start + timedelta(hours=1))
    discrete = BaseDiscreteInterval(start, count=3, step=timedelta(minutes=5))

    coordinate: Coordinate = interval.start
    step: float | timedelta = discrete.step
    points: list[tuple[Coordinate, float]] = list(discrete)
    return coordinate, step, points


def check_public_api(
    interval: BaseInterval,
    discrete: BaseDiscreteInterval,
    intervals: Sequence[BaseInterval],
) -> tuple[AbstractInterval, IntervalCounter, IntervalList, IntervalMeter, IntervalPdf, IntervalSet]:
    """Static usage examples checked by Mypy; pytest does not call this helper."""
    meter = IntervalMeter(intervals)
    counter = IntervalCounter(intervals)
    interval_list = IntervalList(intervals)
    interval_set = IntervalSet(intervals)
    pdf = IntervalPdf(intervals)

    list_data: list[BaseInterval] = interval_list.get_data()
    independent_list: IntervalList = interval_list.deep_copy()
    first_interval: BaseInterval = interval_list.at(0)
    matching_records: IntervalList = interval_list.filter_by_coordinate(interval.start)
    overlapping_records: IntervalList = interval_list.filter_by_range(interval)
    set_data: set[BaseInterval] = interval_set.get_data()
    meter_data: Counter[BaseInterval] = meter.get_data()

    interval_weight: float | None = meter.get(interval)
    interval_length: Length = interval.get_length()
    interval_bounds: tuple[Coordinate, Coordinate] | None = interval_set.bounds
    containing_intervals: list[BaseInterval] = interval_set.find_all_containing(interval)
    clipped_coverage: IntervalSet = interval_set.clip(interval)
    contained_segments: tuple[BaseInterval, ...] = interval_set.contained_intervals(interval)
    high_coverage: IntervalSet = meter.regions_at_least(1)
    low_coverage: IntervalSet = meter.regions_below(1, within=interval)
    meter_support: IntervalSet = meter.support
    covered_length: Length = meter.coverage_length()
    point_count: int = discrete.as_counter().support_point_count()
    average: float = meter.average_value(interval)
    minimum: float = meter.minimum_value(interval)
    maximum: float = meter.maximum_value(interval)
    median: float = meter.median_value(interval)
    modes: tuple[float, ...] = meter.mode_value(interval)
    changed_value: BaseInterval = interval.with_value(2)
    discrete_coordinate: Coordinate = discrete.coordinate_at(discrete.index_of(discrete.start))
    discrete_arguments: tuple[Coordinate | timedelta, ...] = discrete()
    converted: IntervalPdf = interval.as_pdf()
    combined: AbstractInterval = interval + interval_set
    support: IntervalSet = interval.intersection_support(interval)
    product: IntervalMeter = interval.intersection(interval)

    assert list_data and independent_list and first_interval and matching_records and overlapping_records
    assert set_data and meter_data
    assert interval_bounds is not None and containing_intervals and high_coverage
    assert not isinstance(interval_bounds[0], datetime) and not isinstance(interval_bounds[1], datetime)
    assert clipped_coverage and contained_segments
    assert isinstance(interval_length, float) and isinstance(covered_length, float)
    assert low_coverage and meter_support and covered_length >= 0 and point_count >= 0
    assert isinstance(average, float) and minimum <= maximum and median >= minimum and modes
    assert changed_value.value == 2 and discrete_coordinate == discrete.start
    assert not isinstance(discrete_coordinate, datetime)
    assert support and product
    assert interval_weight is None or isinstance(interval_weight, float)
    assert interval_length >= 0
    assert discrete_arguments
    assert converted.total_length() == 1
    return combined, counter, interval_list, meter, pdf, interval_set


def check_function_interval_api() -> int | float:
    """Static examples for the public piecewise-function API."""
    ramp = FunctionInterval(0, 10, lambda coordinate: coordinate / 10)
    bias = FunctionInterval(5, 15, lambda coordinate: 2)
    profile = IntervalFunction([ramp, bias], combine=sum, default=0)
    return profile(7)


def check_interval_map_api() -> tuple[IntervalMap[float | None], float | None]:
    """Static examples for generic interval-map construction and composition."""
    first: IntervalMap[float] = IntervalMap(default=0.0)
    first.assign(0.0, 60.0, 1.0)
    first.assign(BaseInterval(20.0, 40.0), value=2.0)

    second: IntervalMap[float] = IntervalMap(default=0.0)
    second.assign(0.0, 30.0, 3.0)
    fleet = combine_maps([first, second], combine=sum_values, absent=0.0)
    return fleet, fleet[25.0]


def check_priority_interval_map_api() -> tuple[str | None, tuple[str | None, ...]]:
    """Static examples for the public mutable priority resolver."""
    high: IntervalMap[str] = IntervalMap()
    high.assign(2, 4, "high")
    low: IntervalMap[str] = IntervalMap()
    low.assign(0, 6, "low")

    resolver: PriorityIntervalMap[str] = PriorityIntervalMap(default=None)
    low_handle: PrioritySourceHandle
    low_handle, _ = resolver.add(low, 1)
    resolver.add(high, 2)
    resolved: str | None = resolver[3]
    active_bounds: tuple[BaseInterval, ...] = resolver.active_regions(low_handle)
    batch: tuple[str | None, ...] = resolver.lookup_many([1, 3, 7])
    provenance = resolver.lookup(3, with_priority=True)
    explanation: PriorityResolutionExplanation[str] = resolver.explain(3)
    resolved_snapshot: IntervalMap[str | None] = resolve_maps([high, low])
    current_snapshot: IntervalMap[str | None] = resolver.snapshot()
    payload_result: PriorityLookupResult[str] = provenance

    assert active_bounds and explanation.source is not None
    assert payload_result.priority == 2 and resolved_snapshot[3] == "high"
    assert current_snapshot[3] == "high"
    return resolved, batch


def sum_values(values: tuple[float | None, ...]) -> float:
    return sum(value if value is not None else 0.0 for value in values)


def test_exported_api_annotations_resolve_at_runtime():
    api = [
        AbstractInterval.as_counter,
        AbstractInterval.as_list,
        AbstractInterval.as_meter,
        AbstractInterval.as_set,
        AbstractInterval.as_pdf,
        AbstractIntervalCollection.get_data,
        AbstractIntervalCollection.set_data,
        AbstractIntervalCollection.deep_copy,
        AbstractIntervalCollection.find_all_containing,
        AbstractIntervalCollection.bounds.fget,
        AbstractIntervalCollection.as_single_interval,
        BaseInterval.as_meter,
        BaseInterval.as_pdf,
        BaseInterval.intersection_support,
        BaseInterval.intersection,
        BaseInterval.with_value,
        BaseInterval.__add__,
        BaseDiscreteInterval.__call__,
        BaseDiscreteInterval.coordinate_at,
        BaseDiscreteInterval.index_of,
        FunctionInterval.__init__,
        FunctionInterval.contains,
        FunctionInterval.copy,
        IntervalFunction.__init__,
        IntervalFunction.__call__,
        IntervalFunction.__iter__,
        IntervalFunction.__len__,
        IntervalMap.__init__,
        IntervalMap.assign,
        IntervalMap.reset,
        IntervalMap.items,
        IntervalMap.__getitem__,
        IntervalMap.__contains__,
        IntervalMap.__iter__,
        IntervalMap.copy,
        PriorityIntervalMap.__init__,
        PriorityIntervalMap.add,
        PriorityIntervalMap.remove,
        PriorityIntervalMap.replace,
        PriorityIntervalMap.update_priority,
        PriorityIntervalMap.active_regions,
        PriorityIntervalMap.lookup,
        PriorityIntervalMap.lookup_many,
        PriorityIntervalMap.explain,
        PriorityIntervalMap.snapshot,
        PriorityLookupResult.used_default.fget,
        PriorityResolutionExplanation.used_default.fget,
        combine_maps,
        resolve_maps,
        IntervalCounter.__init__,
        IntervalList.__init__,
        IntervalList.__iter__,
        IntervalList.deep_copy,
        IntervalList.at,
        IntervalList.filter_by_coordinate,
        IntervalList.filter_by_range,
        IntervalMeter.__init__,
        IntervalMeter.get,
        IntervalMeter.setdefault,
        IntervalMeter.regions_at_least,
        IntervalMeter.regions_below,
        IntervalMeter.average_value,
        IntervalMeter.minimum_value,
        IntervalMeter.maximum_value,
        IntervalMeter.median_value,
        IntervalMeter.mode_value,
        IntervalMeter.coverage_length,
        IntervalMeter.support_point_count,
        IntervalMeter.support.fget,
        IntervalPdf.__init__,
        IntervalPdf.setdefault,
        intervalues.IntervalPmf.__iter__,
        IntervalSet.__init__,
        IntervalSet.deep_copy,
        IntervalSet.intersection_update,
        IntervalSet.clip,
        IntervalSet.contained_intervals,
        IntervalSet.update_set,
        combine_intervals,
    ]

    for callable_api in api:
        assert get_type_hints(callable_api), callable_api.__qualname__

    assert get_type_hints(AbstractInterval.as_counter)["return"] is intervalues.IntervalCounter
    assert intervalues.Coordinate == int | float | datetime
    assert intervalues.Length == float | timedelta
    assert get_type_hints(BaseInterval.__init__)["loc"] == TypingSequence[Coordinate] | Coordinate
    assert get_type_hints(BaseDiscreteInterval.__init__)["step"] == float | timedelta | None
    assert get_type_hints(BaseInterval.as_pdf)["return"] is intervalues.IntervalPdf
    assert get_type_hints(BaseInterval.intersection_support)["return"] is intervalues.IntervalSet
    assert get_type_hints(BaseInterval.intersection)["return"] is intervalues.IntervalMeter
    assert get_type_hints(IntervalMeter.get)["return"] == float | None
    assert get_type_hints(IntervalMeter.setdefault)["return"] == float | None
    assert get_type_hints(IntervalMeter.support.fget)["return"] is intervalues.IntervalSet
    assert get_type_hints(IntervalMeter.regions_below)["return"] is intervalues.IntervalSet
    assert get_type_hints(IntervalMeter.average_value)["return"] is float
    assert get_type_hints(IntervalMeter.minimum_value)["return"] is float
    assert get_type_hints(IntervalMeter.maximum_value)["return"] is float
    assert get_type_hints(IntervalMeter.median_value)["return"] is float
    assert get_type_hints(IntervalMeter.mode_value)["return"] == tuple[float, ...]
    assert get_type_hints(IntervalPdf.setdefault)["return"] is NoReturn
    assert get_type_hints(IntervalList.at)["return"] is BaseInterval
    assert get_type_hints(IntervalList.filter_by_coordinate)["return"] is IntervalList
    assert get_type_hints(IntervalList.filter_by_range)["return"] is IntervalList
    assert get_type_hints(IntervalSet.clip)["return"] is IntervalSet
    assert get_type_hints(IntervalSet.contained_intervals)["return"] == tuple[BaseInterval, ...]
    assert get_type_hints(BaseInterval.get_length)["return"] == float | timedelta
    assert get_type_hints(BaseInterval.to_timezone)["return"] is get_type_hints(BaseInterval.copy)["return"]
    assert get_type_hints(BaseDiscreteInterval.coordinate_at)["return"] == Coordinate
    assert get_type_hints(AbstractIntervalCollection.bounds.fget)["return"] == (
        tuple[Coordinate, Coordinate] | None
    )


def test_temporal_public_type_contract():
    elapsed, coordinate, bound = check_temporal_type_api()

    assert elapsed == timedelta(hours=1)
    assert coordinate == datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc)
    assert bound == datetime(2024, 1, 1, 0, tzinfo=timezone.utc)


def test_temporal_attribute_type_contract():
    coordinate, step, points = check_temporal_attribute_types()

    assert coordinate == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert step == timedelta(minutes=5)
    assert points[1] == (datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc), 1)
    assert get_type_hints(BaseInterval)["start"] == Coordinate
    assert get_type_hints(BaseInterval)["stop"] == Coordinate
    assert get_type_hints(BaseDiscreteInterval)["step"] == float | timedelta
    assert get_type_hints(BaseInterval.__iter__)["return"] == Iterator[tuple[Coordinate, float]]
    assert get_type_hints(BaseDiscreteInterval.__iter__)["return"] == Iterator[tuple[Coordinate, float]]


def test_function_types_and_classes_are_exported():
    assert intervalues.FunctionInterval is FunctionInterval
    assert intervalues.IntervalFunction is IntervalFunction
    assert check_function_interval_api() == 2.7


def test_interval_map_types_and_functions_are_exported():
    fleet, value = check_interval_map_api()

    assert intervalues.IntervalMap is IntervalMap
    assert intervalues.combine_maps is combine_maps
    assert value == 5.0
    assert fleet[60.0] == 0.0
    assert 60.0 not in fleet


def test_priority_interval_map_types_and_functions_are_exported():
    resolved, batch = check_priority_interval_map_api()

    assert intervalues.PriorityIntervalMap is PriorityIntervalMap
    assert intervalues.PrioritySourceHandle is PrioritySourceHandle
    assert intervalues.PriorityLookupResult is PriorityLookupResult
    assert intervalues.PriorityResolutionExplanation is PriorityResolutionExplanation
    assert intervalues.resolve_maps is resolve_maps
    assert resolved == "high"
    assert batch == ("low", "high", None)
