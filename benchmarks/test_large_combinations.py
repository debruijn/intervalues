"""Opt-in stress tests; run with `uv run --group test pytest benchmarks/test_large_combinations.py`."""

from itertools import chain
from random import Random

import pytest
from intervalues import BaseInterval, combine_intervals, combine_via_rust


def split_to_pairs(iterable):
    values = iter(iterable)
    return zip(values, values)


@pytest.mark.parametrize("nr_intervals", [1_000_000])
def test_combine_many(nr_intervals):
    interval_width = 5
    intervals = [BaseInterval((i, i + interval_width)) for i in range(nr_intervals)]
    Random(42).shuffle(intervals)
    meter = combine_intervals(intervals)
    assert meter.total_length() == interval_width * nr_intervals

    middle_interval = BaseInterval((interval_width - 1, nr_intervals))
    assert meter.most_common(1)[0][0] == middle_interval
    sorted_keys = sorted(meter.keys(), key=lambda x: x.start)
    assert tuple(meter[x] for x in sorted_keys) == (1, 2, 3, 4, 5, 4, 3, 2, 1)


@pytest.mark.parametrize("nr_intervals", [1_000_000])
def test_combine_many_varying(nr_intervals):
    nums = list(chain.from_iterable([[2 * x, 2 * x + 1] for x in range(nr_intervals)]))
    Random(42).shuffle(nums)
    intervals = [x if x[0] < x[1] else (x[1], x[0]) for x in split_to_pairs(nums)]
    intervals = [BaseInterval(interval) for interval in intervals]
    meter = combine_intervals(intervals)
    assert meter.total_length() == sum(interval.get_length() for interval in intervals)

    assert meter[0] == 1
    assert meter[2 * nr_intervals - 1] == 1


@pytest.mark.parametrize("nr_intervals", [1_000_000])
def test_combine_many_random(nr_intervals):
    this_random = Random(42)
    nums = [this_random.random() for _ in range(nr_intervals * 2)]
    intervals = [x if x[0] < x[1] else (x[1], x[0]) for x in split_to_pairs(nums)]
    intervals = [BaseInterval(interval) for interval in intervals]
    meter = combine_intervals(intervals)
    assert meter.total_length() == pytest.approx(sum(interval.get_length() for interval in intervals))

    assert meter[min(meter)] == 1
    assert meter[max(meter)] == 1
    assert len(meter.keys()) <= 2 * nr_intervals - 1


@pytest.mark.parametrize("nr_intervals", [1_000_000])
def test_combine_many_randint(nr_intervals):
    this_random = Random(42)
    nums = [this_random.randint(0, 10) for _ in range(nr_intervals * 2)]
    intervals = [x if x[0] < x[1] else (x[1], x[0]) for x in split_to_pairs(nums)]
    intervals = [BaseInterval(interval) for interval in intervals if interval[0] != interval[1]]
    meter = combine_intervals(intervals)
    assert len(meter.keys()) <= 2 * nr_intervals - 1


@pytest.mark.parametrize("nr_intervals", [1_000_000])
def test_combine_rust_to_python(nr_intervals):
    pytest.importorskip("intervalues_pyrust")
    this_random = Random(42)
    nums = [this_random.randint(0, 10) for _ in range(nr_intervals * 2)]
    intervals = [x + (1,) if x[0] < x[1] else (x[1], x[0], 1) for x in split_to_pairs(nums) if x[0] != x[1]]
    intervals = [BaseInterval(interval) for interval in intervals if interval[0] != interval[1]]
    meter_rust = combine_via_rust(intervals)
    meter_py = combine_intervals(intervals)
    assert meter_rust == meter_py
