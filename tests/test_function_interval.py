import copy

import pytest

from intervalues.function_interval import FunctionInterval


def test_function_interval_stores_callable_without_evaluating_it():
    calls = []

    def function(coordinate: float) -> float:
        calls.append(coordinate)
        return coordinate

    interval = FunctionInterval(2, 5, function)

    assert interval.start == 2
    assert interval.stop == 5
    assert interval.function is function
    assert calls == []


@pytest.mark.parametrize("coordinate", [1, 1.5, 3, 4.5, 5])
def test_function_interval_contains_coordinates_inclusive_of_bounds(coordinate):
    assert coordinate in FunctionInterval(1, 5, lambda x: x)


@pytest.mark.parametrize("coordinate", [0.99, 5.01, float("-inf"), float("inf"), float("nan"), True, "3"])
def test_function_interval_excludes_outside_or_invalid_coordinates(coordinate):
    assert coordinate not in FunctionInterval(1, 5, lambda x: x)


def test_zero_length_function_interval_contains_its_coordinate():
    interval = FunctionInterval(2, 2, lambda x: x)

    assert 2 in interval
    assert 1 not in interval


@pytest.mark.parametrize(
    ("start", "stop", "error", "message"),
    [
        (True, 1, TypeError, "start must be an int or float"),
        (0, False, TypeError, "stop must be an int or float"),
        (float("nan"), 1, ValueError, "bounds must be finite"),
        (0, float("inf"), ValueError, "bounds must be finite"),
        (2, 1, ValueError, "start must be less than or equal to stop"),
    ],
)
def test_function_interval_rejects_invalid_bounds(start, stop, error, message):
    with pytest.raises(error, match=message):
        FunctionInterval(start, stop, lambda x: x)


def test_function_interval_rejects_non_callable_function():
    with pytest.raises(TypeError, match="function must be callable"):
        FunctionInterval(0, 1, 42)


def test_function_interval_copy_preserves_function_reference_and_identity_semantics():
    def function(x: float) -> float:
        return x

    interval = FunctionInterval(1, 3, function)

    copied = interval.copy()
    copied_with_copy_module = copy.copy(interval)

    assert copied is not interval
    assert copied.start == interval.start
    assert copied.stop == interval.stop
    assert copied.function is function
    assert copied_with_copy_module.function is function
    assert copied != interval
    assert isinstance(hash(interval), int)
    assert isinstance(hash(copied), int)


def test_function_interval_representation_identifies_bounds_and_callable():
    interval = FunctionInterval(1, 3, abs)

    assert repr(interval) == "FunctionInterval(start=1, stop=3, function=<built-in function abs>)"
    assert str(interval) == "[1;3] -> <built-in function abs>"
