from collections import Counter

import pytest

from intervalues import (
    BaseInterval,
    IntervalCounter,
    IntervalList,
    IntervalMeter,
    IntervalSet,
)


def _collections_with_one_interval():
    interval = BaseInterval(0, 2)
    return [
        (IntervalList([interval]), interval),
        (IntervalSet(interval), None),
        (IntervalMeter(interval), None),
        (IntervalCounter(interval), None),
    ]


def _stored_interval(collection):
    if isinstance(collection, IntervalList):
        return collection.data[0]
    if isinstance(collection, IntervalSet):
        return next(iter(collection.data))
    return next(iter(collection.data.keys()))


@pytest.mark.parametrize("collection,interval", _collections_with_one_interval())
def test_get_data_returns_live_backing_container(collection, interval):
    data = collection.get_data()

    assert data is collection.data
    if interval is not None:
        assert data[0] is interval


@pytest.mark.parametrize("collection,interval", _collections_with_one_interval())
def test_set_data_replaces_storage_with_the_supplied_container(collection, interval):
    old_data = collection.data
    if isinstance(collection, IntervalList):
        replacement = [BaseInterval(5, 6)]
    elif isinstance(collection, IntervalSet):
        replacement = {BaseInterval(5, 6)}
    else:
        replacement = Counter({BaseInterval(5, 6): 3})

    collection.set_data(replacement)

    assert collection.data is replacement
    assert collection.get_data() is replacement
    assert old_data is not collection.data


@pytest.mark.parametrize("collection,interval", _collections_with_one_interval())
def test_copy_is_shallow_and_deep_copy_recursively_copies_intervals(collection, interval):
    stored_interval = _stored_interval(collection)
    shallow = collection.copy()
    deep = collection.deep_copy()

    assert shallow == collection
    assert deep == collection
    assert shallow.data is not collection.data
    assert deep.data is not collection.data
    assert _stored_interval(shallow) is stored_interval
    assert _stored_interval(deep) is not stored_interval


def test_deep_copy_of_interval_list_is_independent_after_interval_mutation():
    original = IntervalList([BaseInterval(0, 2, value=3)])
    copied = original.deep_copy()

    copied.at(0).set_value(7)

    assert original.at(0).value == 3
    assert copied.at(0).value == 7


def test_set_data_can_bypass_interval_set_normalization():
    interval_set = IntervalSet()
    replacement = {BaseInterval(0, 2), BaseInterval(1, 3)}

    interval_set.set_data(replacement)

    assert interval_set.data is replacement
    assert len(interval_set) == 2

