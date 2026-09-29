from collections import Counter
from collections.abc import Sequence
from typing import get_type_hints

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
    discrete_arguments: tuple[float, ...] = discrete()
    converted: IntervalPdf = interval.as_pdf()
    combined: AbstractInterval = interval + interval_set

    assert list_data and set_data and meter_data
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
        AbstractIntervalCollection.as_single_interval,
        BaseInterval.as_meter,
        BaseInterval.as_pdf,
        BaseInterval.__add__,
        BaseDiscreteInterval.__call__,
        IntervalCounter.__init__,
        IntervalList.__init__,
        IntervalMeter.__init__,
        IntervalMeter.get,
        IntervalPdf.__init__,
        IntervalSet.__init__,
        combine_intervals,
    ]

    for callable_api in api:
        assert get_type_hints(callable_api), callable_api.__qualname__

    assert get_type_hints(AbstractInterval.as_counter)["return"] is intervalues.IntervalCounter
    assert get_type_hints(BaseInterval.as_pdf)["return"] is intervalues.IntervalPdf
    assert get_type_hints(IntervalMeter.get)["return"] == float | None
