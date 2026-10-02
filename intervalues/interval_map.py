"""Replacement-oriented mappings over numeric intervals."""

import math
from collections.abc import Iterator
from typing import Any, Generic, Literal, TypeVar, overload

from .base_interval import BaseInterval


Payload = TypeVar("Payload")
_UNSET = object()


class IntervalMap(Generic[Payload]):
    """A piecewise mapping with half-open numeric ranges and replacement writes.

    Segments are stored as sorted ``(BaseInterval, payload)`` pairs. Although
    ``BaseInterval`` itself has closed-bound semantics, this map interprets
    each stored segment as ``[start, stop)``.
    """

    def __init__(self, default: Payload | None = None) -> None:
        """Create an empty map whose uncovered coordinates resolve to default."""
        self.default = default
        self._segments: list[tuple[BaseInterval, Payload]] = []
    @overload
    def assign(
        self,
        start: BaseInterval,
        *,
        conflict: Literal["replace"] = "replace",
    ) -> None: ...

    @overload
    def assign(
        self,
        start: BaseInterval,
        *,
        value: Payload,
        conflict: Literal["replace"] = "replace",
    ) -> None: ...

    @overload
    def assign(
        self,
        start: float,
        stop: float,
        value: Payload,
        *,
        conflict: Literal["replace"] = "replace",
    ) -> None: ...

    def assign(
        self,
        start: float | BaseInterval,
        stop: object = _UNSET,
        value: object = _UNSET,
        *,
        conflict: str = "replace",
    ) -> None:
        """Replace mappings on a half-open range, merging adjacent equal values.

        Pass either ``start, stop, value`` or a ``BaseInterval``. For the
        interval form, omitting ``value`` uses ``interval.value``.
        """
        if conflict != "replace":
            raise ValueError("conflict must be 'replace'")

        if isinstance(start, BaseInterval):
            if stop is not _UNSET:
                raise TypeError("interval payload must be passed with the value keyword")
            if value is not _UNSET:
                payload = value
            else:
                payload = start.value
            interval_start, interval_stop = start.start, start.stop
        else:
            if stop is _UNSET or value is _UNSET:
                raise TypeError("assign(start, stop, value) requires all three arguments")
            interval_start, interval_stop, payload = *self._validate_range(start, stop), value

        interval_start, interval_stop = self._validate_range(interval_start, interval_stop)
        if interval_start == interval_stop:
            raise ValueError("assignment range must have positive length")

        replacement: list[tuple[BaseInterval, Any]] = []
        for interval, existing_payload in self._segments:
            if interval.stop <= interval_start or interval.start >= interval_stop:
                replacement.append((interval, existing_payload))
                continue

            if interval.start < interval_start:
                replacement.append((BaseInterval(interval.start, interval_start), existing_payload))
            if interval.stop > interval_stop:
                replacement.append((BaseInterval(interval_stop, interval.stop), existing_payload))

        replacement.append((BaseInterval(interval_start, interval_stop), payload))
        replacement.sort(key=lambda entry: (entry[0].start, entry[0].stop))
        self._segments = self._merge_adjacent(replacement)

    def reset(self, interval: BaseInterval) -> None:
        """Remove mappings in ``interval``, restoring the default on that range."""
        if not isinstance(interval, BaseInterval):
            raise TypeError("interval must be a BaseInterval")
        reset_start, reset_stop = self._validate_range(interval.start, interval.stop)
        if reset_start == reset_stop:
            raise ValueError("reset range must have positive length")

        replacement: list[tuple[BaseInterval, Payload]] = []
        for existing, payload in self._segments:
            if existing.stop <= reset_start or existing.start >= reset_stop:
                replacement.append((existing, payload))
                continue

            if existing.start < reset_start:
                replacement.append((BaseInterval(existing.start, reset_start), payload))
            if existing.stop > reset_stop:
                replacement.append((BaseInterval(reset_stop, existing.stop), payload))

        self._segments = replacement

    @staticmethod
    def _validate_range(start: object, stop: object) -> tuple[int | float, int | float]:
        validated_start = IntervalMap._validate_coordinate("start", start)
        validated_stop = IntervalMap._validate_coordinate("stop", stop)
        if validated_start > validated_stop:
            raise ValueError("start must be less than or equal to stop")
        return validated_start, validated_stop

    @staticmethod
    def _validate_coordinate(name: str, coordinate: object) -> int | float:
        if isinstance(coordinate, bool) or not isinstance(coordinate, (int, float)):
            raise TypeError(f"{name} must be an int or float")
        if not math.isfinite(coordinate):
            raise ValueError(f"{name} must be finite")
        return coordinate

    @staticmethod
    def _merge_adjacent(
        segments: list[tuple[BaseInterval, Payload]],
    ) -> list[tuple[BaseInterval, Payload]]:
        merged: list[tuple[BaseInterval, Payload]] = []
        for interval, payload in segments:
            if merged and merged[-1][0].stop == interval.start:
                previous_interval, previous_payload = merged[-1]
                if bool(previous_payload == payload):
                    merged[-1] = (BaseInterval(previous_interval.start, interval.stop), previous_payload)
                    continue
            merged.append((interval, payload))
        return merged

    def items(self) -> tuple[tuple[BaseInterval, Payload], ...]:
        """Return an immutable snapshot of sorted interval/payload pairs."""
        return tuple(self._segments)

    def __iter__(self) -> Iterator[BaseInterval]:
        return (interval for interval, _ in self._segments)

    def __len__(self) -> int:
        return len(self._segments)

    def clear(self) -> None:
        """Remove all assigned segments."""
        self._segments.clear()

    def copy(self) -> "IntervalMap[Payload]":
        """Return a shallow copy that shares payload objects."""
        copied = self.__class__(self.default)
        copied._segments = self._segments.copy()
        return copied

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(items={self.items()!r}, default={self.default!r})"
