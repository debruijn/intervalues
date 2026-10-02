"""Piecewise evaluation of numeric functions over closed intervals."""

import math
from collections.abc import Iterable, Iterator
from typing import Callable, TypeAlias

from .function_interval import FunctionInterval


NumericValue: TypeAlias = int | float
Combiner: TypeAlias = Callable[[tuple[NumericValue, ...]], NumericValue]


class IntervalFunction:
    """Evaluate bounded functions and combine all values at a coordinate.

    Function intervals are evaluated in insertion order. Their bounds are
    inclusive, so intervals sharing an endpoint both contribute there.
    """

    def __init__(
        self,
        intervals: FunctionInterval | Iterable[FunctionInterval],
        combine: Combiner,
        default: NumericValue,
    ) -> None:
        """Create an evaluator from one interval or an ordered iterable."""
        self.intervals: tuple[FunctionInterval, ...]
        if isinstance(intervals, FunctionInterval):
            self.intervals = (intervals,)
        else:
            self.intervals = tuple(intervals)
        if any(not isinstance(interval, FunctionInterval) for interval in self.intervals):
            raise TypeError("intervals must contain only FunctionInterval instances")
        if not callable(combine):
            raise TypeError("combine must be callable")

        self._validate_numeric("default", default)
        self.combine = combine
        self.default = default

    @staticmethod
    def _validate_numeric(name: str, value: object) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be an int or float")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"{name} must be finite")

    def __call__(self, coordinate: NumericValue) -> NumericValue:
        """Evaluate all matching functions and combine their results."""
        self._validate_numeric("coordinate", coordinate)
        results: list[NumericValue] = []
        for interval in self.intervals:
            if coordinate in interval:
                result = interval.function(coordinate)
                self._validate_numeric("function result", result)
                results.append(result)

        if not results:
            return self.default

        combined = self.combine(tuple(results))
        self._validate_numeric("combiner result", combined)
        return combined

    def __iter__(self) -> Iterator[FunctionInterval]:
        return iter(self.intervals)

    def __len__(self) -> int:
        return len(self.intervals)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(intervals={self.intervals!r}, "
            f"combine={self.combine!r}, default={self.default!r})"
        )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({len(self)} intervals, default={self.default!r})"
