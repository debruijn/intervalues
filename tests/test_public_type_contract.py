from collections import Counter
from collections.abc import Sequence
from typing import NoReturn, get_type_hints

import intervalues
from intervalues import (
    AbstractInterval,
    AbstractIntervalCollection,
    BaseDiscreteInterval,
    BaseInterval,
    IntervalCounter,
    IntervalList,
    IntervalMeter,
    IntervalPdf,
    IntervalSet,
    combine_intervals,
)


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
    interval_length: float = interval.get_length()
    interval_bounds: tuple[float, float] | None = interval_set.bounds
    containing_intervals: list[BaseInterval] = interval_set.find_all_containing(interval)
    clipped_coverage: IntervalSet = interval_set.clip(interval)
    contained_segments: tuple[BaseInterval, ...] = interval_set.contained_intervals(interval)
    high_coverage: IntervalSet = meter.regions_at_least(1)
    low_coverage: IntervalSet = meter.regions_below(1, within=interval)
    meter_support: IntervalSet = meter.support
    covered_length: float = meter.coverage_length()
    point_count: int = discrete.as_counter().support_point_count()
    average: float = meter.average_value(interval)
    minimum: float = meter.minimum_value(interval)
    maximum: float = meter.maximum_value(interval)
    median: float = meter.median_value(interval)
    modes: tuple[float, ...] = meter.mode_value(interval)
    changed_value: BaseInterval = interval.with_value(2)
    discrete_coordinate: float = discrete.coordinate_at(discrete.index_of(discrete.start))
    discrete_arguments: tuple[float, ...] = discrete()
    converted: IntervalPdf = interval.as_pdf()
    combined: AbstractInterval = interval + interval_set
    support: IntervalSet = interval.intersection_support(interval)
    product: IntervalMeter = interval.intersection(interval)

    assert list_data and independent_list and first_interval and matching_records and overlapping_records
    assert set_data and meter_data
    assert interval_bounds is not None and containing_intervals and high_coverage
    assert clipped_coverage and contained_segments
    assert low_coverage and meter_support and covered_length >= 0 and point_count >= 0
    assert isinstance(average, float) and minimum <= maximum and median >= minimum and modes
    assert changed_value.value == 2 and discrete_coordinate == discrete.start
    assert support and product
    assert interval_weight is None or isinstance(interval_weight, float)
    assert interval_length >= 0
    assert discrete_arguments
    assert converted.total_length() == 1
    return combined, counter, interval_list, meter, pdf, interval_set


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
