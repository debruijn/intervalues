from typing import Iterable, Sequence, Iterator, Mapping, Optional, TypeVar
import collections
import math
from datetime import datetime, timedelta, timezone, tzinfo

from . import abstract_interval, interval_list, interval_meter, interval_set
import intervalues


T = TypeVar('T', bound='BaseInterval')
Coordinate = int | float | datetime


def _coordinate_domain(coordinate: object) -> str | None:
    if isinstance(coordinate, datetime):
        return "aware_datetime" if coordinate.utcoffset() is not None else "naive_datetime"
    if isinstance(coordinate, (int, float)):
        return "numeric"
    return None


def _compare_coordinates(left: object, right: object) -> int:
    if isinstance(left, datetime) and isinstance(right, datetime):
        left_aware = left.utcoffset() is not None
        right_aware = right.utcoffset() is not None
        if left_aware != right_aware:
            raise TypeError("coordinates must use the same numeric/datetime domain and timezone awareness")
        if left_aware:
            left = left.astimezone(timezone.utc)
            right = right.astimezone(timezone.utc)
        return (left > right) - (left < right)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return (left > right) - (left < right)
    else:
        raise TypeError("coordinates must use the same numeric/datetime domain and timezone awareness")


def _coordinates_equal(left: object, right: object) -> bool:
    return _compare_coordinates(left, right) == 0


def _ordering_coordinate(coordinate: Coordinate) -> Coordinate:
    if isinstance(coordinate, datetime) and coordinate.utcoffset() is not None:
        return coordinate.astimezone(timezone.utc)
    return coordinate


def _coordinate_min(left: Coordinate, right: Coordinate) -> Coordinate:
    return left if _compare_coordinates(left, right) <= 0 else right


def _coordinate_max(left: Coordinate, right: Coordinate) -> Coordinate:
    return left if _compare_coordinates(left, right) >= 0 else right


def _interval_length(start: object, stop: object) -> float | timedelta:
    if isinstance(start, datetime) and isinstance(stop, datetime):
        if (start.utcoffset() is None) != (stop.utcoffset() is None):
            raise TypeError("interval bounds must use the same timezone awareness")
        if start.utcoffset() is not None:
            start = start.astimezone(timezone.utc)
            stop = stop.astimezone(timezone.utc)
        return stop - start
    if isinstance(start, (int, float)) and isinstance(stop, (int, float)):
        return stop - start
    raise TypeError("interval bounds must both be numeric or both be datetimes")


def _shift_coordinate(coordinate: object, shift: object) -> object:
    if isinstance(coordinate, datetime) and isinstance(shift, timedelta):
        if coordinate.utcoffset() is None:
            return coordinate + shift
        return (coordinate.astimezone(timezone.utc) + shift).astimezone(coordinate.tzinfo)
    if isinstance(coordinate, (int, float)) and isinstance(shift, (int, float)):
        return coordinate + shift
    if isinstance(coordinate, datetime):
        raise TypeError("datetime coordinates require a timedelta shift")
    if isinstance(shift, timedelta):
        raise TypeError("timedelta shifts require datetime coordinates")
    raise TypeError("shift and coordinate must use compatible numeric or datetime domains")


def _convert_datetime_timezone(
    coordinate: datetime,
    target_timezone: Optional[tzinfo],
    *,
    remove_timezone: bool,
    fold: Optional[int],
) -> datetime:
    if fold is not None and (isinstance(fold, bool) or fold not in (0, 1)):
        raise ValueError("fold must be 0 or 1")

    is_aware = coordinate.utcoffset() is not None
    if target_timezone is None:
        if not remove_timezone:
            raise ValueError("target_timezone=None requires remove_timezone=True")
        if not is_aware:
            raise TypeError("cannot remove timezone information from a naive datetime")
        if fold is not None:
            raise ValueError("fold is only applicable when converting naive datetimes")
        return coordinate.replace(tzinfo=None)

    if remove_timezone:
        raise ValueError("remove_timezone=True cannot be used with a target timezone")
    if is_aware:
        if fold is not None:
            raise ValueError("fold is only applicable when converting naive datetimes")
        return coordinate.astimezone(target_timezone)

    candidates = [
        coordinate.replace(tzinfo=target_timezone, fold=candidate_fold)
        for candidate_fold in (0, 1)
    ]
    valid_candidates = [
        candidate
        for candidate in candidates
        if candidate.astimezone(timezone.utc).astimezone(target_timezone).replace(tzinfo=None)
        == coordinate
    ]
    by_instant = {
        candidate.astimezone(timezone.utc): candidate for candidate in valid_candidates
    }
    if not by_instant:
        raise ValueError(f"{coordinate} is a nonexistent local time in {target_timezone}")
    if len(by_instant) > 1:
        if fold is None:
            raise ValueError(f"{coordinate} is ambiguous in {target_timezone}; specify fold=0 or fold=1")
        return candidates[fold]
    if fold is not None:
        matching = next(iter(by_instant.values()))
        return matching
    return next(iter(by_instant.values()))


class BaseInterval(abstract_interval.AbstractInterval):
    __name__ = 'BaseInterval'
    start: float
    stop: float

    """
    Class for a base interval, with a single lower and upper bound, and an optional value input for how much the 
    interval is worth.
    
    Objects can be instantiated in multiple ways:
    BaseInterval(loc=(0, 2)) -> Interval from 0 to 2 provided as first input
    BaseInterval(loc=0, stop=2) -> Interval from 0 to 2 provided as separate inputs
    BaseInterval(loc=(0, 2, 2)) -> Interval from 0 to 2 with value=2, all using the first input
    BaseInterval(loc=0, stop=2, value=2) -> Interval from 0 to 2 with value=2, provided as separate inputs
    
    When adding two BaseIntervals (say, x and y) together, one of multiple things might happen automatically:
    - If x and y both have the same start and stop, the values are added together and a single BaseInterval is returned
    - If x and y have the same value and the endpoints fit together (one's start is the others' stop), a single
        BaseInterval is returned with the same value and the encompassing start and stop.
    - Otherwise, an IntervalMeter is returned, initialized with x and y in its input. See IntervalMeter for details.
    """

    def __init__(self, loc: Sequence[float] | float,
                 stop: Optional[float] = None,
                 value: Optional[float] = None) -> None:
        """Create an interval from bounds or a sequence of bounds and an optional value.

        A scalar ``loc`` defaults to the unit interval ``[loc, loc + 1]`` when ``stop``
        is omitted. A sequence may contain ``(start, stop, value)``. Bounds must
        be finite and ordered; equal bounds are allowed. Datetime starts require
        an explicit stop, and aware bounds are ordered by their absolute instants.
        """
        if isinstance(loc, collections.abc.Sequence):
            self.start, self.stop = loc[:2]
            self.value: float = value if value is not None else (loc[2] if len(loc) >= 3 else 1)
        else:
            if isinstance(loc, datetime) and stop is None:
                raise TypeError("datetime intervals require an explicit stop")
            self.start, self.stop = loc, (stop if stop is not None else loc + 1)
            self.value = value if value is not None else 1

        start_domain = _coordinate_domain(self.start)
        stop_domain = _coordinate_domain(self.stop)
        if start_domain is None or stop_domain is None:
            raise TypeError("interval bounds must both be finite numbers or datetimes")
        if start_domain != stop_domain:
            raise TypeError("interval bounds must use the same coordinate domain and timezone awareness")
        if start_domain == "numeric":
            if not math.isfinite(self.start) or not math.isfinite(self.stop):
                raise ValueError("interval bounds must be finite")
        if _compare_coordinates(self.start, self.stop) > 0:
            raise ValueError("interval start must be less than or equal to stop")
        self._length: float = _interval_length(self.start, self.stop)  # type: ignore[assignment]

    def to_args(self: T, ign_value: bool = False) -> tuple[float, ...]:
        # Convert interval to its arguments for initialization, with an optional input to ignore the value
        return (self.start, self.stop, self.value) if self.value != 1 and not ign_value else (self.start, self.stop)

    def to_args_and_replace(self: T, replace: Optional[Mapping[str, float]] = None) -> tuple[float, ...]:
        # Convert interval to its arguments for initialization, with the option to use a dict to replace start,
        # stop or value with a new value.
        if replace is None:
            return self.to_args()
        start = replace['start'] if 'start' in replace else self.start
        stop = replace['stop'] if 'stop' in replace else self.stop
        value = replace['value'] if 'value' in replace else self.value
        return (start, stop, value) if value != 1 else (start, stop)

    def as_index(self: T) -> T:
        return self.copy_with_replace({'value': 1})

    def copy_with_replace(self: T, replace: Optional[Mapping[str, float]] = None) -> T:
        if replace is None:
            return self.copy()
        return self.__class__(self.to_args_and_replace(replace=replace))

    def copy(self: T) -> T:
        return self.__copy__()

    def __copy__(self: T) -> T:
        return self.__class__(self.to_args())

    def as_meter(self: T) -> 'interval_meter.IntervalMeter':
        return interval_meter.IntervalMeter(self)

    def as_counter(self: T) -> 'interval_meter.IntervalCounter':
        return interval_meter.IntervalCounter(self)

    def as_set(self: T) -> 'interval_set.IntervalSet':
        return interval_set.IntervalSet(self)

    def as_list(self: T) -> 'interval_list.IntervalList':
        return interval_list.IntervalList(self)

    def as_pdf(self: T) -> 'intervalues.IntervalPdf':
        if isinstance(self.start, datetime):
            raise TypeError("IntervalPdf does not support datetime coordinates")
        from .interval_pdf import IntervalPdf

        return IntervalPdf(self)

    def to_timezone(
        self: T,
        target_timezone: Optional[tzinfo],
        *,
        remove_timezone: bool = False,
        fold: Optional[int] = None,
    ) -> T:
        """Return a copy converted to a timezone, preserving instants or wall time.

        Pass ``target_timezone=None, remove_timezone=True`` to strip timezone
        information while preserving displayed local times. Naive local times
        require ``fold`` when ambiguous and reject nonexistent times.
        """
        if not isinstance(self.start, datetime) or not isinstance(self.stop, datetime):
            raise TypeError("timezone conversion requires datetime coordinates")

        start = _convert_datetime_timezone(
            self.start,
            target_timezone,
            remove_timezone=remove_timezone,
            fold=fold,
        )
        stop = _convert_datetime_timezone(
            self.stop,
            target_timezone,
            remove_timezone=remove_timezone,
            fold=fold,
        )
        from .base_interval_discrete import BaseDiscreteInterval

        if isinstance(self, BaseDiscreteInterval):
            converted = self.__class__(
                start,
                stop,
                step=self.step,
                count=self.count,
                value=self.value,
            )
            if not _coordinates_equal(converted.stop, stop):
                raise ValueError("timezone conversion cannot preserve this discrete interval's point sequence")
            return converted
        return self.__class__(start, stop, value=self.value)

    def convert_timezone_inplace(
        self: T,
        target_timezone: Optional[tzinfo],
        *,
        remove_timezone: bool = False,
        fold: Optional[int] = None,
    ) -> T:
        """Convert this interval in place; failed conversions leave it unchanged."""
        converted = self.to_timezone(
            target_timezone,
            remove_timezone=remove_timezone,
            fold=fold,
        )
        self.__dict__.clear()
        self.__dict__.update(converted.__dict__)
        return self

    def _update_length(self: T) -> None:
        self._length = _interval_length(self.start, self.stop)  # type: ignore[assignment]

    def get_length(self: T) -> float:
        return self._length * self.value  # type: ignore[return-value]

    def __contains__(self: T, val: object) -> bool:
        if isinstance(val, BaseInterval):
            return (
                _compare_coordinates(self.start, val.start) <= 0
                and _compare_coordinates(self.stop, val.stop) >= 0
            )
        if isinstance(val, datetime):
            return (
                _compare_coordinates(self.start, val) <= 0
                and _compare_coordinates(val, self.stop) <= 0
            )
        if isinstance(val, (int, float)):
            return (
                _compare_coordinates(self.start, val) <= 0
                and _compare_coordinates(val, self.stop) <= 0
            )
        return False

    def __eq__(self: T, other: object) -> bool:
        if isinstance(other, BaseInterval) and type(other) is type(self):
            return (
                _coordinates_equal(self.start, other.start)
                and _coordinates_equal(self.stop, other.stop)
                and self.value == other.value
            )
        if type(other) in [interval_meter.IntervalMeter, interval_set.IntervalSet, interval_list.IntervalList,
                           interval_meter.IntervalCounter, intervalues.IntervalPdf]:
            return other == self
        return False

    def __hash__(self: T) -> int:
        if isinstance(self.start, datetime) and self.start.utcoffset() is not None:
            start, stop = _ordering_coordinate(self.start), _ordering_coordinate(self.stop)
            args = (start, stop, self.value) if self.value != 1 else (start, stop)
            return hash(args)
        return hash(self.to_args())

    def __iter__(self: T) -> Iterator[tuple[float, float]]:
        yield self.start, self.value
        yield self.stop, -self.value

    def __repr__(self: T) -> str:
        return f"{self.__name__}[{self.start};{self.stop}" + (f";{self.value}]" if self.value != 1 else "]")

    def __str__(self: T) -> str:
        return f"[{self.start};{self.stop}" + (f";{self.value}]" if self.value != 1 else "]")

    def __call__(self: T) -> tuple[tuple[float, float], ...] | tuple[float, ...]:
        return tuple(self)

    def __getitem__(self: T, index: object) -> float:
        if isinstance(index, self.__class__):
            return self.value / index.value if index in self else 0
        if isinstance(index, (int, float, datetime)):
            return self.value if index in self else 0
        return 0

    def overlaps(self: T, other: T) -> bool:
        """Return whether the inclusive coordinate ranges share any point."""
        return _compare_coordinates(self.start, other.stop) <= 0 and _compare_coordinates(other.start, self.stop) <= 0

    def left_overlaps(self: T, other: T) -> bool:
        """Return whether ``other`` starts strictly inside this interval."""
        return _compare_coordinates(self.start, other.start) < 0 and _compare_coordinates(other.start, self.stop) < 0

    def right_overlaps(self: T, other: T) -> bool:
        """Return whether ``other`` stops strictly inside this interval."""
        return _compare_coordinates(self.start, other.stop) < 0 and _compare_coordinates(other.stop, self.stop) < 0

    def contains(self: T, other: T) -> bool:
        return _compare_coordinates(self.start, other.start) <= 0 and _compare_coordinates(self.stop, other.stop) >= 0

    def left_borders(self: T, other: T) -> bool:
        return _coordinates_equal(self.stop, other.start)

    def right_borders(self: T, other: T) -> bool:
        return _coordinates_equal(self.start, other.stop)

    def borders(self: T, other: T) -> bool:
        return self.left_borders(other) or self.right_borders(other)

    def intersection_support(self: T, other: 'BaseInterval') -> 'intervalues.IntervalSet':
        """Return the geometric support shared with another interval.

        Continuous intervals include endpoint-only contact as a degenerate
        interval. Discrete intervals return the common represented points.
        Mixing continuous and discrete intervals is not supported.
        """
        if not isinstance(other, BaseInterval):
            raise TypeError("other must be a BaseInterval")

        from .base_interval_discrete import BaseDiscreteInterval
        if isinstance(self, BaseDiscreteInterval) != isinstance(other, BaseDiscreteInterval):
            raise TypeError("Cannot intersect discrete and continuous intervals")

        if isinstance(self, BaseDiscreteInterval):
            return self.as_set().intersection(other.as_set())

        start = _coordinate_max(self.start, other.start)
        stop = _coordinate_min(self.stop, other.stop)
        if _compare_coordinates(start, stop) > 0:
            return intervalues.IntervalSet()

        support = intervalues.IntervalSet()
        # Internal datetime support precedes the public annotation update.
        support.data.add(BaseInterval(start, stop))  # type: ignore[arg-type]
        return support

    def intersection(self: T, other: 'BaseInterval') -> 'intervalues.IntervalMeter':
        """Return the pointwise product of values over shared support.

        Continuous endpoint-only intersections have no positive-length support
        and therefore produce an empty meter. Discrete intersections preserve
        every common represented point. Mixed continuous/discrete inputs raise
        ``TypeError``.
        """
        support = self.intersection_support(other)
        if not support:
            return intervalues.IntervalMeter()

        from .base_interval_discrete import BaseDiscreteInterval
        product = self.value * other.value
        weighted_segments: list[BaseInterval] = []
        for interval in support:
            if isinstance(interval, BaseDiscreteInterval):
                weighted_segments.append(interval.with_value(product))
            elif _compare_coordinates(interval.start, interval.stop) < 0:
                weighted_segments.append(interval.with_value(product))
        return intervalues.IntervalMeter(weighted_segments)

    def distance_to(self: T, other: 'BaseInterval') -> float:
        """Return the coordinate distance between this interval and another.

        The distance is zero for overlapping or touching intervals and does
        not depend on either interval's value. Datetime intervals return an
        elapsed ``timedelta``.
        """
        _compare_coordinates(self.start, other.start)
        if isinstance(self.start, datetime):
            if _compare_coordinates(self.stop, other.start) < 0:
                return _interval_length(self.stop, other.start)  # type: ignore[return-value]
            if _compare_coordinates(other.stop, self.start) < 0:
                return _interval_length(other.stop, self.start)  # type: ignore[return-value]
            return timedelta(0)  # type: ignore[return-value]
        return max(other.start - self.stop, self.start - other.stop, 0)

    def clamp(self: T, value: float) -> float:
        """Clamp a coordinate to this interval's inclusive bounds."""
        if isinstance(self.start, datetime):
            _compare_coordinates(self.start, value)
            if _compare_coordinates(value, self.start) < 0:
                return self.start  # type: ignore[return-value]
            if _compare_coordinates(value, self.stop) > 0:
                return self.stop  # type: ignore[return-value]
            return value  # type: ignore[return-value]
        if isinstance(value, datetime):
            _compare_coordinates(self.start, value)
        if math.isnan(value):
            raise ValueError("value must not be NaN")
        return min(max(value, self.start), self.stop)

    def split_at(self: T, points: Iterable[float]) -> tuple['BaseInterval', ...]:
        """Split into ordered pieces at the supplied interior coordinates.

        Continuous pieces share their split boundary. Discrete pieces assign
        each point at or before a split coordinate to the left-hand piece.
        Split coordinates outside the interval are ignored.
        """
        from .base_interval_discrete import BaseDiscreteInterval

        split_points = tuple(points)
        temporal = isinstance(self.start, datetime)
        for point in split_points:
            if temporal:
                _compare_coordinates(self.start, point)
            elif isinstance(point, datetime):
                _compare_coordinates(self.start, point)
            elif not isinstance(point, (int, float)) or isinstance(point, bool):
                raise ValueError("split points must be finite numbers")
            elif not math.isfinite(point):
                raise ValueError("split points must be finite numbers")

        if isinstance(self, BaseDiscreteInterval):
            discrete_boundaries = sorted({
                int(min(max(math.floor((point - self.start) / self.step) + 1, 1), self.count - 1))
                for point in split_points
                if self.start <= point < self.stop
            })
            bounds = [0, *discrete_boundaries, self.count]
            return tuple(
                BaseDiscreteInterval(
                    self.start + bounds[index] * self.step,
                    count=bounds[index + 1] - bounds[index],
                    step=self.step,
                    value=self.value,
                )
                for index in range(len(bounds) - 1)
                if bounds[index] < bounds[index + 1]
            )

        boundaries = [
            point for point in split_points
            if _compare_coordinates(self.start, point) < 0 and _compare_coordinates(point, self.stop) < 0
        ]
        boundaries.sort(key=_ordering_coordinate)
        unique_boundaries: list[object] = []
        for point in boundaries:
            if not unique_boundaries or _compare_coordinates(unique_boundaries[-1], point) != 0:
                unique_boundaries.append(point)
        coordinates = [self.start, *unique_boundaries, self.stop]
        return tuple(
            self.__class__((start, stop, self.value))  # type: ignore[arg-type]
            for start, stop in zip(coordinates, coordinates[1:])
            if _compare_coordinates(start, stop) < 0
        ) or (self.copy(),)

    def is_disjoint_with(self: T, other: T) -> bool:
        """Return whether the inclusive coordinate ranges share no points."""
        return _compare_coordinates(self.stop, other.start) < 0 or _compare_coordinates(other.stop, self.start) < 0

    # Used for ordering, for which it is useful to order by start-point first, and stop-point second.
    def __lt__(self: T, other: 'abstract_interval.AbstractInterval') -> bool:
        if not isinstance(other, BaseInterval):
            return other > self
        _compare_coordinates(self.start, other.start)
        _compare_coordinates(self.stop, other.stop)
        return self._ordering_key() < other._ordering_key()

    def __le__(self: T, other: 'abstract_interval.AbstractInterval') -> bool:
        if not isinstance(other, BaseInterval):
            return other >= self
        _compare_coordinates(self.start, other.start)
        _compare_coordinates(self.stop, other.stop)
        return self._ordering_key() <= other._ordering_key()

    def __gt__(self: T, other: 'abstract_interval.AbstractInterval') -> bool:
        if not isinstance(other, BaseInterval):
            return other < self
        _compare_coordinates(self.start, other.start)
        _compare_coordinates(self.stop, other.stop)
        return self._ordering_key() > other._ordering_key()

    def __ge__(self: T, other: 'abstract_interval.AbstractInterval') -> bool:
        if not isinstance(other, BaseInterval):
            return other <= self
        _compare_coordinates(self.start, other.start)
        _compare_coordinates(self.stop, other.stop)
        return self._ordering_key() >= other._ordering_key()

    def _ordering_key(self: T) -> tuple[object, object, int, object, int, float]:
        """Return a total-order key shared with discrete interval subclasses."""
        start, stop = _ordering_coordinate(self.start), _ordering_coordinate(self.stop)
        return start, stop, 0, 0, 0, self.value

    def __add__(self: T, other: 'BaseInterval | abstract_interval.AbstractIntervalCollection') -> (
            abstract_interval.AbstractInterval):
        if isinstance(other, BaseInterval):
            if other.start == self.stop and other.value == self.value:
                return BaseInterval((self.start, other.stop, self.value))
            if self.start == other.stop and other.value == self.value:
                return BaseInterval((other.start, self.stop, self.value))
            if self.start == other.start and self.stop == other.stop:
                return BaseInterval((self.start, self.stop, self.value + other.value))
            return interval_meter.IntervalMeter([self, other])
        return other + self

    def __iadd__(self: T, other: 'BaseInterval | abstract_interval.AbstractIntervalCollection') -> (
            abstract_interval.AbstractInterval):
        return self + other

    def __radd__(self: T, other: 'BaseInterval | abstract_interval.AbstractIntervalCollection') -> (
            abstract_interval.AbstractInterval):
        if isinstance(other, BaseInterval):
            return other.__add__(self)
        return other.__add__(self)

    def __sub__(self: T, other: 'BaseInterval | abstract_interval.AbstractIntervalCollection') -> (
            abstract_interval.AbstractInterval):
        if isinstance(other, abstract_interval.AbstractIntervalCollection):
            return -other + self
        if self.value == other.value:
            if self.start == other.start and other.stop < self.stop:
                return BaseInterval((other.stop, self.stop, self.value))
            if self.start == other.start and other.stop > self.stop:
                return BaseInterval((self.stop, other.stop, -self.value))
            if self.start < other.start and self.stop == other.stop:
                return BaseInterval((self.start, other.start, self.value))
            if self.start > other.start and self.stop == other.stop:
                return BaseInterval((other.start, self.start, -self.value))
        if self.start == other.start and self.stop == other.stop:
            return BaseInterval((self.start, self.stop), value=self.value - other.value)
        if self == other:
            return EmptyInterval()
        return interval_meter.IntervalMeter([self, -other])

    def __isub__(self: T, other: 'BaseInterval | abstract_interval.AbstractIntervalCollection') -> (
            abstract_interval.AbstractInterval):
        return self - other

    def __neg__(self: T) -> T:
        return self.__mul__(-1)

    def __mul__(self: T, num: float) -> T:
        if isinstance(num, int) or isinstance(num, float):
            return self.__class__((self.start, self.stop), value=num * self.value)
        raise ValueError("Multiplication should be with an int or a float.")

    def __rmul__(self: T, num: float) -> T:
        return self * num

    def __imul__(self: T, num: float) -> T:
        if isinstance(num, int) or isinstance(num, float):
            return self.__class__((self.start, self.stop), value=num * self.value)
        raise ValueError("Multiplication should be with an int or a float.")

    def __truediv__(self: T, num: float) -> T:
        return self * (1 / num)

    def __idiv__(self: T, num: float) -> T:
        return self * (1 / num)

    def get_value(self) -> float:
        return self.value

    def set_value(self, val: float) -> None:
        """Set the interval's value in place.

        Since intervals are hashable, do not change the value while an
        interval is being used as a dictionary or set key.
        """
        self.value = val

    def mult_value(self, val: float) -> None:
        """Multiply the interval's value in place.

        Since intervals are hashable, do not change the value while an
        interval is being used as a dictionary or set key.
        """
        self.value *= val

    def with_value(self: T, value: float) -> T:
        """Return a copy of this interval with a different value."""
        return self.copy_with_replace({'value': value})

    def __lshift__(self: T, shift: float) -> T:
        return self.__class__(self.to_args_and_replace({
            'start': _shift_coordinate(self.start, -shift),  # type: ignore[dict-item]
            'stop': _shift_coordinate(self.stop, -shift),  # type: ignore[dict-item]
        }))

    def __rshift__(self: T, shift: float) -> T:
        return self.__class__(self.to_args_and_replace({
            'start': _shift_coordinate(self.start, shift),  # type: ignore[dict-item]
            'stop': _shift_coordinate(self.stop, shift),  # type: ignore[dict-item]
        }))

    def min(self) -> float:
        return self.start

    def max(self) -> float:
        return self.stop


def UnitInterval() -> BaseInterval:
    """
    Utility function to return a default BaseInterval from 0 to 1.
    :return: a BaseInterval(0, 1)
    """
    return BaseInterval(0, 1)


def EmptyInterval() -> BaseInterval:
    """
    Utility function to generate an empty interval, which is otherwise not supported.
    This can be compared with other intervals, if needed (for example, to use as the smallest interval in an algorithm).
    :return:
    """
    interval = UnitInterval()
    interval.start, interval.stop, interval._length = 0, 0, 0
    interval.__name__ = 'EmptyInterval'
    return interval
