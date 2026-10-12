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
    set_data: set[BaseInterval] = interval_set.get_data()
    meter_data: Counter[BaseInterval] = meter.get_data()

    interval_weight: float | None = meter.get(interval)
    interval_length: float = interval.get_length()
    interval_bounds: tuple[float, float] | None = interval_set.bounds
    containing_intervals: list[BaseInterval] = interval_set.find_all_containing(interval)
    high_coverage: IntervalSet = meter.regions_at_least(1)
    changed_value: BaseInterval = interval.with_value(2)
    discrete_coordinate: float = discrete.coordinate_at(discrete.index_of(discrete.start))
    discrete_arguments: tuple[float, ...] = discrete()
    converted: IntervalPdf = interval.as_pdf()
    combined: AbstractInterval = interval + interval_set
    support: IntervalSet = interval.intersection_support(interval)
    product: IntervalMeter = interval.intersection(interval)

    assert list_data and set_data and meter_data
    assert interval_bounds is not None and containing_intervals and high_coverage
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
        IntervalMeter.__init__,
        IntervalMeter.get,
        IntervalMeter.setdefault,
        IntervalMeter.regions_at_least,
        IntervalPdf.__init__,
        IntervalPdf.setdefault,
        intervalues.IntervalPmf.__iter__,
        IntervalSet.__init__,
        IntervalSet.intersection_update,
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
    assert get_type_hints(IntervalPdf.setdefault)["return"] is NoReturn
