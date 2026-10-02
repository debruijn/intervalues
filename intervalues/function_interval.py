"""A bounded numeric coordinate range associated with a callable."""

import math
from typing import Callable, TypeVar


FunctionIntervalType = TypeVar("FunctionIntervalType", bound="FunctionInterval")


class FunctionInterval:
    """Associate a callable with finite, inclusive numeric bounds.

    The callable is stored, not evaluated, by this class. Evaluation is
    performed by :class:`IntervalFunction` when a coordinate is requested.
    """

    def __init__(self, start: float, stop: float, function: Callable[[float], float]) -> None:
        """Create a function interval over the closed range ``[start, stop]``."""
        self._validate_bound("start", start)
        self._validate_bound("stop", stop)
        if start > stop:
            raise ValueError("interval start must be less than or equal to stop")
        if not callable(function):
            raise TypeError("function must be callable")

        self.start = start
        self.stop = stop
        self.function = function

    @staticmethod
    def _validate_bound(name: str, value: object) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be an int or float")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("interval bounds must be finite")

    def contains(self, coordinate: object) -> bool:
        """Return whether a finite numeric coordinate lies within the closed bounds."""
        if isinstance(coordinate, bool) or not isinstance(coordinate, (int, float)):
            return False
        if isinstance(coordinate, float) and not math.isfinite(coordinate):
            return False
        return self.start <= coordinate <= self.stop

    def __contains__(self, coordinate: object) -> bool:
        return self.contains(coordinate)

    def copy(self: FunctionIntervalType) -> FunctionIntervalType:
        """Return a shallow copy, preserving the original callable reference."""
        return self.__copy__()

    def __copy__(self: FunctionIntervalType) -> FunctionIntervalType:
        return self.__class__(self.start, self.stop, self.function)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(start={self.start!r}, stop={self.stop!r}, function={self.function!r})"

    def __str__(self) -> str:
        return f"[{self.start};{self.stop}] -> {self.function!r}"
