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
