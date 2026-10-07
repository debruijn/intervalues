from __future__ import annotations

import abc
import copy
from datetime import datetime, timedelta
from typing import Any, Collection, Generic, Iterator, Optional, TypeVar

import intervalues

Coordinate = int | float | datetime
Length = float | timedelta


def _coordinate_domain(coordinate: object) -> str | None:
    if isinstance(coordinate, datetime):
        return "aware_datetime" if coordinate.utcoffset() is not None else "naive_datetime"
    if isinstance(coordinate, (int, float)):
        return "numeric"
    return None


def _validate_coordinate_domains(intervals: Collection[Any]) -> None:
    domains = {_coordinate_domain(interval.start) for interval in intervals}
    if len(domains) > 1:
        raise TypeError("collection intervals must use the same numeric/datetime domain and timezone awareness")


def _sum_interval_lengths(intervals: Collection[Any], lengths: Iterator[Length]) -> Length:
    _validate_coordinate_domains(intervals)
    if not intervals:
        return 0
    if isinstance(next(iter(intervals)).start, datetime):
        total = timedelta(0)
        for length in lengths:
            if isinstance(length, timedelta):
                total += length
            elif length != 0:
                raise TypeError("datetime interval lengths must be timedeltas")
        return total
    numeric_total: int | float = 0
    for length in lengths:
        if isinstance(length, timedelta):
            raise TypeError("numeric interval lengths must be numeric")
        numeric_total += length
    return numeric_total


CollectionData = TypeVar('CollectionData', bound=Collection[Any])
CollectionType = TypeVar('CollectionType', bound='AbstractIntervalCollection[Any]')


class AbstractInterval(abc.ABC):
    """Common interface for a single interval or a collection of intervals."""

    @abc.abstractmethod
    def as_counter(self) -> 'intervalues.IntervalCounter': pass

    @abc.abstractmethod
    def as_list(self) -> 'intervalues.IntervalList': pass

    @abc.abstractmethod
    def as_meter(self) -> 'intervalues.IntervalMeter': pass

    @abc.abstractmethod
    def as_set(self) -> 'intervalues.IntervalSet': pass

    @abc.abstractmethod
    def as_pdf(self) -> 'intervalues.IntervalPdf': pass

    @abc.abstractmethod
    def get_length(self) -> Length: pass

    @abc.abstractmethod
    def max(self) -> Coordinate: pass

    @abc.abstractmethod
    def min(self) -> Coordinate: pass


class AbstractIntervalCollection(AbstractInterval, Generic[CollectionData]):
    """Base class for interval collections backed by a typed ``data`` container."""

    data: CollectionData

    @property
    def is_empty(self) -> bool:
        """Whether this collection currently contains no intervals."""
        return not self.data

    @property
    def bounds(self) -> Optional[tuple[Coordinate, Coordinate]]:
        """Return the outer coordinate bounds, or ``None`` for an empty collection."""
        intervals = tuple(self)
        if not intervals:
            return None
        _validate_coordinate_domains(intervals)
        from . import base_interval

        start: Coordinate = intervals[0].start
        stop: Coordinate = intervals[0].stop
        for interval in intervals[1:]:
            start = base_interval._coordinate_min(start, interval.start)
            stop = base_interval._coordinate_max(stop, interval.stop)
        return start, stop

    def find_all_containing(
        self, value: float | intervalues.BaseInterval
    ) -> list['intervalues.BaseInterval']:
        """Return all stored intervals that contain a coordinate or interval."""
        if not isinstance(value, (int, float, intervalues.BaseInterval)):
            return []
        return [interval for interval in self if value in interval]

    def get_data(self) -> CollectionData:
        return self.data

    def set_data(self, data: CollectionData) -> None:
        self.data = data

    def deep_copy(self: CollectionType) -> CollectionType:
        """Return a recursive copy of this collection and its stored intervals."""
        return copy.deepcopy(self)

    @abc.abstractmethod
    def get_length(self) -> Length:
        pass

    def __contains__(self, x: object) -> bool:
        return x in self.data

    def __repr__(self) -> str:
        return f"{self.__class__}:{self.data}"

    def __str__(self) -> str:
        return self.__repr__()

    @abc.abstractmethod
    def __getitem__(self, x: object) -> float:
        pass

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and (self.data == other.data)

    def __hash__(self) -> int:
        return hash(tuple(self))

    def __iter__(self) -> Iterator['intervalues.BaseInterval']:
        return iter(self.data)

    @abc.abstractmethod
    def __add__(self, other: 'intervalues.BaseInterval | AbstractIntervalCollection') -> 'AbstractInterval':
        pass

    @abc.abstractmethod
    def __mul__(self, other: float) -> 'AbstractIntervalCollection':
        pass

    def __neg__(self) -> 'AbstractIntervalCollection':
        return self.__mul__(-1)

    def min(self) -> Coordinate:
        bounds = self.bounds
        if bounds is None:
            raise ValueError("min() arg is an empty sequence")
        return bounds[0]

    def max(self) -> Coordinate:
        bounds = self.bounds
        if bounds is None:
            raise ValueError("max() arg is an empty sequence")
        return bounds[1]

    def as_single_interval(self) -> 'intervalues.BaseInterval':
        from .base_interval import BaseInterval

        return BaseInterval(self.min(), self.max())  # type: ignore[arg-type]
