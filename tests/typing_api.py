"""Static usage examples checked by the configured Mypy command."""

from collections import Counter
from collections.abc import Sequence

from intervalues import (
    AbstractInterval,
    BaseDiscreteInterval,
    BaseInterval,
    IntervalCounter,
    IntervalList,
    IntervalMeter,
    IntervalPdf,
    IntervalSet,
)


def check_public_api(
    interval: BaseInterval,
    discrete: BaseDiscreteInterval,
    intervals: Sequence[BaseInterval],
) -> tuple[AbstractInterval, IntervalCounter, IntervalList, IntervalMeter, IntervalPdf, IntervalSet]:
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
