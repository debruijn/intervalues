"""Replacement-oriented mappings over numeric intervals."""

import math
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from numbers import Rational, Real
from typing import Any, Callable, Generic, Literal, TypeVar, overload

from .base_interval import BaseInterval


Payload = TypeVar("Payload")
Result = TypeVar("Result")
Absent = TypeVar("Absent")
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
        if isinstance(coordinate, float) and not math.isfinite(coordinate):
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
        """Return a snapshot of sorted pairs, copying intervals but sharing payloads."""
        return tuple((interval.copy(), payload) for interval, payload in self._segments)

    def __getitem__(self, coordinate: float) -> Payload | None:
        """Return the payload at a coordinate, or the configured default."""
        coordinate = self._validate_coordinate("coordinate", coordinate)
        for interval, payload in self._segments:
            if interval.start <= coordinate < interval.stop:
                return payload
            if interval.start > coordinate:
                break
        return self.default

    def __contains__(self, coordinate: object) -> bool:
        """Return whether a coordinate has an explicitly assigned payload."""
        if isinstance(coordinate, bool) or not isinstance(coordinate, (int, float)):
            return False
        if isinstance(coordinate, float) and not math.isfinite(coordinate):
            return False
        return any(interval.start <= coordinate < interval.stop for interval, _ in self._segments)

    def __iter__(self) -> Iterator[BaseInterval]:
        return (interval.copy() for interval, _ in self._segments)

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


TiePolicy = Literal["error", "first", "last", "key"]


class PrioritySourceHandle:
    """Opaque identity for one registration in a :class:`PriorityIntervalMap`."""

    __slots__ = ()


@dataclass(frozen=True)
class PriorityLookupResult(Generic[Payload]):
    """Resolved payload and the source metadata responsible for it."""

    value: Payload | None
    source: PrioritySourceHandle | None
    priority: Real | None

    @property
    def used_default(self) -> bool:
        """Whether no source covered the lookup coordinate."""
        return self.source is None


@dataclass(frozen=True)
class PriorityResolutionExplanation(Generic[Payload]):
    """Resolution result and the higher-precedence sources skipped as gaps."""

    coordinate: int | float
    value: Payload | None
    source: PrioritySourceHandle | None
    priority: Real | None
    uncovered_sources: tuple[PrioritySourceHandle, ...]

    @property
    def used_default(self) -> bool:
        """Whether no source covered the lookup coordinate."""
        return self.source is None


class _PrioritySource(Generic[Payload]):
    def __init__(
        self,
        handle: PrioritySourceHandle,
        interval_map: IntervalMap[Payload],
        priority: Real,
        tie_break_key: Any,
        order: int,
    ) -> None:
        self.handle = handle
        self.interval_map = interval_map
        self.priority = priority
        self.tie_break_key = tie_break_key
        self.order = order


class PriorityIntervalMap(Generic[Payload]):
    """Resolve live interval maps by numeric priority, falling back through gaps.

    Larger finite real priorities win. Equal priorities are handled according
    to ``tie_policy``: reject duplicates, prefer the first or last registration,
    or compare explicit per-source keys (larger keys win, with earlier
    registration breaking equal-key ties).
    """

    def __init__(
        self,
        default: Payload | None = None,
        *,
        tie_policy: TiePolicy = "first",
    ) -> None:
        if tie_policy not in ("error", "first", "last", "key"):
            raise ValueError("tie_policy must be 'error', 'first', 'last', or 'key'")
        self.default = default
        self.tie_policy = tie_policy
        self._sources: dict[PrioritySourceHandle, _PrioritySource[Payload]] = {}
        self._next_order = 0

    def add(
        self,
        interval_map: IntervalMap[Payload],
        priority: Real,
        *,
        tie_break_key: object = _UNSET,
    ) -> tuple[PrioritySourceHandle, bool]:
        """Register a live source and return its handle and current active status."""
        self._validate_map(interval_map)
        self._validate_priority(priority)
        self._validate_tie_break_key(tie_break_key)
        self._validate_priority_tie(priority)

        handle = PrioritySourceHandle()
        source = _PrioritySource(handle, interval_map, priority, tie_break_key, self._next_order)
        proposed_sources = [*self._sources.values(), source]
        is_active = self._has_winning_coverage(handle, proposed_sources)
        self._sources[handle] = source
        self._next_order += 1
        return handle, is_active

    def remove(self, handle: PrioritySourceHandle) -> None:
        """Remove a source, permanently invalidating its handle."""
        self._get_source(handle)
        del self._sources[handle]

    def replace(self, handle: PrioritySourceHandle, interval_map: IntervalMap[Payload]) -> None:
        """Replace a source map while preserving the registration and priority."""
        self._validate_map(interval_map)
        self._get_source(handle).interval_map = interval_map

    def update_priority(
        self,
        handle: PrioritySourceHandle,
        priority: Real,
        *,
        tie_break_key: object = _UNSET,
    ) -> bool:
        """Change priority and return whether the source wins any region afterward."""
        source = self._get_source(handle)
        self._validate_priority(priority)
        self._validate_priority_tie(priority, excluding=handle)

        if tie_break_key is _UNSET:
            updated_key = source.tie_break_key
        else:
            self._validate_tie_break_key(tie_break_key)
            updated_key = tie_break_key

        proposed = _PrioritySource(
            source.handle,
            source.interval_map,
            priority,
            updated_key,
            source.order,
        )
        proposed_sources = [
            proposed if registered.handle is handle else registered
            for registered in self._sources.values()
        ]
        is_active = bool(self._winning_regions(handle, proposed_sources))
        source.priority = priority
        source.tie_break_key = updated_key
        return is_active

    def active_regions(self, handle: PrioritySourceHandle) -> tuple[BaseInterval, ...]:
        """Return a snapshot of a source's explicitly covered winning regions.

        Returned intervals use the map's half-open ``[start, stop)`` semantics,
        like source-map segments, even though ``BaseInterval`` itself is closed.
        """
        self._get_source(handle)
        return tuple(
            BaseInterval(interval.start, interval.stop)
            for interval in self._winning_regions(handle, self._sources.values())
        )

    def __getitem__(self, coordinate: float) -> Payload | None:
        """Return the highest-priority explicit payload, or the resolver default."""
        return self.lookup(coordinate)

    @overload
    def lookup(
        self,
        coordinate: float,
        *,
        with_priority: Literal[False] = False,
    ) -> Payload | None: ...

    @overload
    def lookup(
        self,
        coordinate: float,
        *,
        with_priority: Literal[True],
    ) -> PriorityLookupResult[Payload]: ...

    def lookup(
        self,
        coordinate: float,
        *,
        with_priority: bool = False,
    ) -> Payload | None | PriorityLookupResult[Payload]:
        """Look up a coordinate, optionally returning source and priority."""
        coordinate = IntervalMap._validate_coordinate("coordinate", coordinate)
        result = self._lookup_result(coordinate)
        if with_priority:
            return result
        return result.value

    def explain(self, coordinate: float) -> PriorityResolutionExplanation[Payload]:
        """Explain the winner and higher-precedence sources skipped as gaps."""
        coordinate = IntervalMap._validate_coordinate("coordinate", coordinate)
        uncovered: list[PrioritySourceHandle] = []
        for source in self._ordered_sources():
            if coordinate in source.interval_map:
                return PriorityResolutionExplanation(
                    coordinate=coordinate,
                    value=source.interval_map[coordinate],
                    source=source.handle,
                    priority=source.priority,
                    uncovered_sources=tuple(uncovered),
                )
            uncovered.append(source.handle)
        return PriorityResolutionExplanation(
            coordinate=coordinate,
            value=self.default,
            source=None,
            priority=None,
            uncovered_sources=tuple(uncovered),
        )

    @overload
    def lookup_many(
        self,
        coordinates: Iterable[float],
        *,
        with_priority: Literal[False] = False,
    ) -> tuple[Payload | None, ...]: ...

    @overload
    def lookup_many(
        self,
        coordinates: Iterable[float],
        *,
        with_priority: Literal[True],
    ) -> tuple[PriorityLookupResult[Payload], ...]: ...

    def lookup_many(
        self,
        coordinates: Iterable[float],
        *,
        with_priority: bool = False,
    ) -> tuple[Payload | None, ...] | tuple[PriorityLookupResult[Payload], ...]:
        """Resolve coordinates in input order, validating all before lookup.

        Duplicate coordinates are preserved. Invalid coordinates raise before
        any result is returned.
        """
        coordinate_tuple = tuple(
            IntervalMap._validate_coordinate("coordinate", coordinate)
            for coordinate in coordinates
        )
        results = tuple(self._lookup_result(coordinate) for coordinate in coordinate_tuple)
        if with_priority:
            return results
        return tuple(result.value for result in results)

    def _lookup_result(self, coordinate: int | float) -> PriorityLookupResult[Payload]:
        for source in self._ordered_sources():
            if coordinate in source.interval_map:
                return PriorityLookupResult(
                    value=source.interval_map[coordinate],
                    source=source.handle,
                    priority=source.priority,
                )
        return PriorityLookupResult(value=self.default, source=None, priority=None)

    def __contains__(self, coordinate: object) -> bool:
        """Return whether any registered source explicitly covers a coordinate."""
        if isinstance(coordinate, bool) or not isinstance(coordinate, (int, float)):
            return False
        if isinstance(coordinate, float) and not math.isfinite(coordinate):
            return False
        return any(coordinate in source.interval_map for source in self._sources.values())

    def _ordered_sources(
        self,
        sources: Iterable[_PrioritySource[Payload]] | None = None,
    ) -> list[_PrioritySource[Payload]]:
        by_priority = sorted(
            self._sources.values() if sources is None else sources,
            key=lambda source: source.priority,
            reverse=True,
        )
        ordered: list[_PrioritySource[Payload]] = []
        offset = 0
        while offset < len(by_priority):
            end = offset + 1
            priority = by_priority[offset].priority
            while end < len(by_priority) and by_priority[end].priority == priority:
                end += 1
            group = by_priority[offset:end]
            if self.tie_policy == "last":
                group.reverse()
            elif self.tie_policy == "key":
                group.sort(key=lambda source: source.tie_break_key, reverse=True)
            ordered.extend(group)
            offset = end
        return ordered

    def _has_winning_coverage(
        self,
        handle: PrioritySourceHandle,
        sources: Iterable[_PrioritySource[Payload]],
    ) -> bool:
        return bool(self._winning_regions(handle, sources))

    def _winning_regions(
        self,
        handle: PrioritySourceHandle,
        sources: Iterable[_PrioritySource[Payload]],
    ) -> list[BaseInterval]:
        source_list = tuple(sources)
        boundaries = sorted({
            boundary
            for source in source_list
            for interval, _ in source.interval_map.items()
            for boundary in (interval.start, interval.stop)
        })
        ordered = self._ordered_sources(source_list)
        winning: list[BaseInterval] = []
        for start, stop in zip(boundaries, boundaries[1:]):
            if start == stop:
                continue
            for source in ordered:
                if start in source.interval_map:
                    if source.handle is handle:
                        if winning and winning[-1].stop == start:
                            winning[-1].stop = stop
                        else:
                            winning.append(BaseInterval(start, stop))
                    break
        return winning

    def _validate_priority_tie(
        self,
        priority: Real,
        *,
        excluding: PrioritySourceHandle | None = None,
    ) -> None:
        if self.tie_policy == "error" and any(
            source.priority == priority and source.handle is not excluding
            for source in self._sources.values()
        ):
            raise ValueError("priority values must be unique when tie_policy='error'")

    def _validate_tie_break_key(self, key: object) -> None:
        if self.tie_policy == "key":
            if key is _UNSET:
                raise TypeError("tie_break_key is required when tie_policy='key'")
        elif key is not _UNSET:
            raise TypeError("tie_break_key is only supported when tie_policy='key'")

    @staticmethod
    def _validate_map(interval_map: object) -> None:
        if not isinstance(interval_map, IntervalMap):
            raise TypeError("source must be an IntervalMap")

    @staticmethod
    def _validate_priority(priority: object) -> None:
        if isinstance(priority, bool) or not isinstance(priority, Real):
            raise TypeError("priority must be a finite real number")
        if not isinstance(priority, Rational) and not math.isfinite(priority):
            raise ValueError("priority must be finite")

    def _get_source(self, handle: PrioritySourceHandle) -> _PrioritySource[Payload]:
        if not isinstance(handle, PrioritySourceHandle):
            raise TypeError("handle must be a PrioritySourceHandle")
        try:
            return self._sources[handle]
        except KeyError:
            raise KeyError("source handle is not registered with this resolver") from None


def combine_maps(
    maps: Iterable[IntervalMap[Payload]],
    combine: Callable[[tuple[Payload | Absent | None, ...]], Result],
    absent: Absent | None,
) -> IntervalMap[Result | Absent | None]:
    """Combine resolved maps into a new map over their covered coordinate union.

    Each partition receives one value per input map in input order. The
    explicit ``absent`` value is used for gaps regardless of each map's own
    default. Spans uncovered by every input are omitted.
    """
    map_tuple = tuple(maps)
    if any(not isinstance(interval_map, IntervalMap) for interval_map in map_tuple):
        raise TypeError("maps must contain only IntervalMap instances")
    if not callable(combine):
        raise TypeError("combine must be callable")

    result: IntervalMap[Result | Absent | None] = IntervalMap(default=absent)
    boundaries = sorted({
        boundary
        for interval_map in map_tuple
        for interval, _ in interval_map.items()
        for boundary in (interval.start, interval.stop)
    })

    segments_by_map = tuple(interval_map.items() for interval_map in map_tuple)
    for start, stop in zip(boundaries, boundaries[1:]):
        values: list[Payload | Absent | None] = []
        covered = False
        for segments in segments_by_map:
            matching_payload: Payload | Absent | None = absent
            for interval, payload in segments:
                if interval.start <= start and stop <= interval.stop:
                    matching_payload = payload
                    covered = True
                    break
            values.append(matching_payload)
        if covered:
            result.assign(start, stop, combine(tuple(values)))

    return result
