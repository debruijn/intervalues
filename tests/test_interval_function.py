import math

import pytest

from intervalues.function_interval import FunctionInterval
from intervalues.interval_function import IntervalFunction


def test_interval_function_evaluates_single_function_at_absolute_coordinate():
    seen = []

    def ramp(coordinate: float) -> float:
        seen.append(coordinate)
        return coordinate / 10

    profile = IntervalFunction(FunctionInterval(2, 5, ramp), combine=sum, default=0)

    assert profile(4) == 0.4
    assert seen == [4]


def test_interval_function_returns_default_for_gap_and_empty_collection():
    combine_calls = []

    def combine(values):
        combine_calls.append(values)
        return sum(values)

    profile = IntervalFunction([FunctionInterval(0, 1, abs)], combine=combine, default=7)
    empty = IntervalFunction([], combine=combine, default=3)

    assert profile(2) == 7
    assert empty(0) == 3
    assert combine_calls == []


def test_interval_function_combines_overlaps_in_insertion_order_and_keeps_duplicates():
    seen = []

    def record_and_return(value):
        seen.append(value)
        return value

    first = FunctionInterval(0, 2, lambda coordinate: record_and_return(1))
    second = FunctionInterval(1, 3, lambda coordinate: record_and_return(2))
    combine_inputs = []

    def combine(values):
        combine_inputs.append(values)
        return sum(values)

    profile = IntervalFunction([first, second, first], combine=combine, default=0)

    assert profile(1) == 4
    assert seen == [1, 2, 1]
    assert combine_inputs == [(1, 2, 1)]
    assert type(combine_inputs[0]) is tuple


def test_interval_function_combines_both_closed_shared_boundaries():
    profile = IntervalFunction(
        [
            FunctionInterval(0, 1, lambda coordinate: 2),
            FunctionInterval(1, 2, lambda coordinate: 3),
        ],
        combine=sum,
        default=0,
    )

    assert profile(1) == 5


def test_interval_function_calls_combiner_with_one_result():
    inputs = []

    def combine(values):
        inputs.append(values)
        return values[0]

    profile = IntervalFunction([FunctionInterval(0, 1, lambda coordinate: 9)], combine, default=0)

    assert profile(0.5) == 9
    assert inputs == [(9,)]


@pytest.mark.parametrize(
    ("value", "error", "message"),
    [
        (True, TypeError, "default must be an int or float"),
        ("1", TypeError, "default must be an int or float"),
        (float("nan"), ValueError, "default must be finite"),
        (float("inf"), ValueError, "default must be finite"),
    ],
)
def test_interval_function_validates_default(value, error, message):
    with pytest.raises(error, match=message):
        IntervalFunction([], sum, value)


@pytest.mark.parametrize(
    ("coordinate", "error", "message"),
    [
        (True, TypeError, "coordinate must be an int or float"),
        ("1", TypeError, "coordinate must be an int or float"),
        (float("nan"), ValueError, "coordinate must be finite"),
        (float("inf"), ValueError, "coordinate must be finite"),
    ],
)
def test_interval_function_validates_coordinate(coordinate, error, message):
    profile = IntervalFunction([], sum, 0)

    with pytest.raises(error, match=message):
        profile(coordinate)


@pytest.mark.parametrize(
    ("result", "error", "message"),
    [
        (True, TypeError, "function result must be an int or float"),
        ("1", TypeError, "function result must be an int or float"),
        (float("nan"), ValueError, "function result must be finite"),
        (float("inf"), ValueError, "function result must be finite"),
    ],
)
def test_interval_function_validates_each_callable_result(result, error, message):
    profile = IntervalFunction([FunctionInterval(0, 1, lambda coordinate: result)], sum, 0)

    with pytest.raises(error, match=message):
        profile(0.5)


@pytest.mark.parametrize(
    ("result", "error", "message"),
    [
        (True, TypeError, "combiner result must be an int or float"),
        ("1", TypeError, "combiner result must be an int or float"),
        (float("nan"), ValueError, "combiner result must be finite"),
        (float("inf"), ValueError, "combiner result must be finite"),
    ],
)
def test_interval_function_validates_combiner_result(result, error, message):
    profile = IntervalFunction([FunctionInterval(0, 1, abs)], lambda values: result, 0)

    with pytest.raises(error, match=message):
        profile(0.5)


def test_interval_function_propagates_function_and_combiner_exceptions():
    function_error = RuntimeError("function failed")

    def fail_function(coordinate):
        raise function_error

    def fail_combine(values):
        raise LookupError("combine failed")

    with pytest.raises(RuntimeError) as function_exception:
        IntervalFunction([FunctionInterval(0, 1, fail_function)], sum, 0)(0.5)
    with pytest.raises(LookupError, match="combine failed"):
        IntervalFunction([FunctionInterval(0, 1, abs)], fail_combine, 0)(0.5)
    assert function_exception.value is function_error


def test_interval_function_snapshots_input_iterable_and_exposes_stable_iteration():
    source = [FunctionInterval(0, 1, abs)]
    profile = IntervalFunction(source, sum, 0)
    source.clear()

    assert len(profile) == 1
    assert tuple(profile) == profile.intervals
    assert math.isfinite(profile(0.5))


def test_interval_function_rejects_invalid_members_and_non_callable_combiner():
    with pytest.raises(TypeError, match="only FunctionInterval"):
        IntervalFunction([object()], sum, 0)
    with pytest.raises(TypeError, match="combine must be callable"):
        IntervalFunction([], None, 0)


def test_interval_function_representation_shows_configuration():
    profile = IntervalFunction([FunctionInterval(0, 1, abs)], sum, 0)

    assert "IntervalFunction(intervals=" in repr(profile)
    assert str(profile) == "IntervalFunction(1 intervals, default=0)"
