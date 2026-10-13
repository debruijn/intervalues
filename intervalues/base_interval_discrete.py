from typing import TYPE_CHECKING, Iterable, Sequence, Iterator, Mapping, Optional, TypeVar, cast
import collections
import math
from datetime import datetime, timedelta, timezone

from . import abstract_interval, interval_meter
from .base_interval import (
    BaseInterval,
    Coordinate,
    EmptyInterval,
    _coordinate_max,
    _coordinate_min,
    _compare_coordinates,
    _coordinates_equal,
    _ordering_coordinate,
    _shift_coordinate,
)

if TYPE_CHECKING:
    from .interval_pmf import IntervalPmf


U = TypeVar('U', bound='BaseDiscreteInterval')
IntervalArgument = Coordinate | timedelta


def _elapsed_between(start: datetime, stop: datetime) -> timedelta:
    _compare_coordinates(start, stop)
    if start.utcoffset() is not None:
        return stop.astimezone(timezone.utc) - start.astimezone(timezone.utc)
    return stop - start


def _coordinate_distance(left: Coordinate, right: Coordinate) -> float | timedelta:
    if isinstance(left, datetime) and isinstance(right, datetime):
        return abs(_elapsed_between(left, right))
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return abs(left - right)
    raise TypeError("coordinates must use the same numeric/datetime domain")


class BaseDiscreteInterval(BaseInterval):
    __name__ = 'BaseDiscreteInterval'
    tol = 0.000001
    count: int
    step: float | timedelta

    """
    Class for a base interval of discrete numbers, with a single lower and upper bound, and an optional value input for
    how much the interval is worth. There is also an optional step input determining the size of the gaps between
    numbers, with default being 1. Alternatively to providing a stop value, one can also provide a count input, with
    stop then becoming start + (count - 1) * step.
    
    Objects can be instantiated in multiple ways:
    BaseDiscreteInterval(loc=(0, 2)) -> Interval containing 0, 1 and 2
    BaseDiscreteInterval(loc=0, stop=2) -> Interval containing 0, 1 and 2, with a different syntax
    BaseDiscreteInterval(loc=(0, 2, 0.5)) -> Interval containing 0, 0.5, 1, 1.5 and 2
    BaseDiscreteInterval(loc=0, stop=2, step=0.5) -> Same interval again
    BaseDiscreteInterval(loc=0, count=5, step=0.5) -> Same interval yet again
    
    When the stop does not align with start + k*step (with k integer valued), stop is automatically reduced:
    BaseDiscreteInterval(loc=0, stop=2.4, step=0.5) -> Returns a BaseDiscreteInterval(loc=0, stop=2, step=0.5)
    
    For testing equality of numbers, there is a default tolerance attribute called `.tol` set at 0.000001. This can be
    overwritten in an instantiated object. For example: `x = iv.BaseDiscreteInterval(0, 1)` and then `x.tol /= 100` for
    a more accurate tolerance in case of working with smaller numbers.
    
    When adding two BaseDiscreteInterval (say, x and y) together, one of multiple things might happen automatically:
    - If x and y both have the same start, step and stop, the values are added together and a single 
        BaseDiscreteInterval is returned
    - If x and y have the same step and value and the endpoints fit together (one's start is the others' stop + step), a
        single BaseDiscreteInterval is returned with the same value and the encompassing start and stop.
    - This also happens if the two intervals have the same value but a different step, but one of them consists of only
        one point 
    - Otherwise, an IntervalMeter is returned, initialized via combine_intervals_discrete_meter().
    """

    def __init__(self, loc: Sequence[Coordinate | timedelta] | Coordinate, stop: Optional[Coordinate] = None,
                 step: Optional[float | timedelta] = None,
                 count: Optional[int] = None, value: Optional[float] = None) -> None:
        """Create a discrete interval using a stop bound or a point count.

        Points advance by ``step`` (default 1). The stop is inclusive when aligned
        to the step; otherwise it is reduced to the last aligned point.
        """
        super().__init__(0)
        if isinstance(loc, collections.abc.Sequence):
            self.start = loc[0]  # type: ignore[assignment]
            self.stop = loc[1]  # type: ignore[assignment]
            self.step = step if step is not None else (loc[2] if len(loc) >= 3 else 1)  # type: ignore[assignment]
            self.value: float = value if value is not None else (
                cast(float, loc[4]) if len(loc) >= 5 else 1
            )
            if isinstance(self.start, datetime) and not isinstance(self.step, timedelta):
                raise TypeError("datetime discrete intervals require an explicit timedelta step")
            if self.stop is None:
                self.count = self._validate_count(loc[3] if len(loc) >= 4 else 1)
            else:
                self.count = self.find_count(self.start, self.stop, self.step)
        elif count is not None:
            self.start = loc  # type: ignore[assignment]
            self.count = self._validate_count(count)
            self.step = step if step is not None else 1  # type: ignore[assignment]
            self.value = value if value is not None else 1
            if isinstance(self.start, datetime) and step is None:
                raise TypeError("datetime discrete intervals require an explicit timedelta step")
        else:
            if isinstance(loc, datetime) and stop is None:
                raise TypeError("datetime discrete intervals require an explicit stop or count")
            if stop is None:
                if not isinstance(loc, (int, float)):
                    raise TypeError("numeric discrete intervals require numeric coordinates")
                stop = loc + 1
            self.start, self.stop = loc, stop  # type: ignore[assignment]
            self.step = step if step is not None else 1  # type: ignore[assignment]
            self.value = value if value is not None else 1
            if isinstance(self.start, datetime) and not isinstance(self.step, timedelta):
                raise TypeError("datetime discrete intervals require an explicit timedelta step")
            self.count = self.find_count(self.start, self.stop, self.step)

        if isinstance(self.start, datetime):
            if not isinstance(self.step, timedelta):
                raise TypeError("datetime discrete intervals require an explicit timedelta step")
            if self.step <= timedelta(0):
                raise ValueError("step must be greater than zero")
            self.stop = self.coordinate_at(self.count - 1)  # type: ignore[assignment]
        else:
            if isinstance(self.step, timedelta):
                raise TypeError("timedelta steps require datetime coordinates")
            if not math.isfinite(self.step) or self.step <= 0:
                raise ValueError("step must be greater than zero")
            self.stop = self.start + (self.count - 1) * self.step

    @staticmethod
    def _validate_count(count: object) -> int:
        if isinstance(count, bool) or not isinstance(count, int):
            raise TypeError("count must be an integer")
        if count < 1:
            raise ValueError("count must be at least 1")
        return count

    def find_count(self: U, start: Coordinate, stop: Coordinate, step: float | timedelta) -> int:
        if isinstance(start, datetime) or isinstance(stop, datetime):
            if not isinstance(start, datetime) or not isinstance(stop, datetime):
                raise TypeError("discrete bounds must both be datetimes")
            if not isinstance(step, timedelta):
                raise TypeError("datetime discrete intervals require an explicit timedelta step")
            if step <= timedelta(0):
                raise ValueError("step must be greater than zero")
            if _compare_coordinates(start, stop) > 0:
                raise ValueError("stop must be greater than or equal to start")
            return self._validate_count(_elapsed_between(start, stop) // step + 1)
        if isinstance(step, timedelta):
            raise TypeError("coordinates and steps must use the same numeric/datetime domain")
        if not math.isfinite(step) or step <= 0:
            raise ValueError("step must be greater than zero")
        if stop < start:
            raise ValueError("stop must be greater than or equal to start")
        count = int(self.tol + (stop - start) / step) + 1
        self._validate_count(count)
        return count

    @property
    def point_count(self) -> int:
        """Number of discrete coordinates represented by this interval."""
        return self.count

    def coordinate_at(self, index: int) -> Coordinate:
        """Return the coordinate at a zero-based point index."""
        if isinstance(index, bool) or not isinstance(index, int):
            raise TypeError("index must be an integer")
        if index < 0 or index >= self.count:
            raise IndexError("discrete interval index out of range")
        if isinstance(self.start, datetime):
            if not isinstance(self.step, timedelta):
                raise TypeError("datetime discrete intervals require timedelta steps")
            return _shift_coordinate(self.start, index * self.step)  # type: ignore[return-value]
        if isinstance(self.step, timedelta):
            raise TypeError("numeric discrete intervals require numeric steps")
        return self.start + index * self.step

    def index_of(self, coordinate: Coordinate) -> int:
        """Return the zero-based index of a coordinate contained in the interval."""
        if isinstance(self.start, datetime):
            if not isinstance(coordinate, datetime):
                raise TypeError("datetime intervals require datetime coordinates")
            _compare_coordinates(self.start, coordinate)
            if coordinate not in self:
                raise ValueError(f"{coordinate} is not a point in this interval")
            if not isinstance(self.step, timedelta):
                raise TypeError("datetime discrete intervals require timedelta steps")
            return _elapsed_between(self.start, coordinate) // self.step
        if isinstance(coordinate, datetime):
            raise TypeError("datetime coordinates require a datetime interval")
        if not isinstance(coordinate, (int, float)) or isinstance(coordinate, bool):
            raise TypeError("coordinate must be a number")
        if not math.isfinite(coordinate) or coordinate not in self:
            raise ValueError(f"{coordinate} is not a point in this interval")
        return round((coordinate - cast(float, self.start)) / cast(float, self.step))

    def clamp(self: U, value: Coordinate) -> Coordinate:
        """Clamp to the nearest represented coordinate, preferring the lower on ties."""
        if isinstance(self.start, datetime):
            if not isinstance(value, datetime):
                raise TypeError("datetime intervals require datetime coordinates")
            _compare_coordinates(self.start, value)
            if _compare_coordinates(value, self.start) <= 0:
                return self.start
            if _compare_coordinates(value, self.stop) >= 0:
                return self.stop
            elapsed = _elapsed_between(self.start, value)
            if not isinstance(self.step, timedelta):
                raise TypeError("datetime discrete intervals require timedelta steps")
            lower_index, remainder = divmod(elapsed, self.step)
            index = lower_index if remainder * 2 <= self.step else lower_index + 1
            return self.coordinate_at(index)
        if isinstance(value, datetime):
            raise TypeError("datetime coordinates require a datetime interval")
        start = cast(float, self.start)
        stop = cast(float, self.stop)
        step = cast(float, self.step)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError("value must be a number")
        if math.isnan(value):
            raise ValueError("value must not be NaN")
        if value <= start:
            return start
        if value >= stop:
            return stop
        position = (value - start) / step
        lower_index = math.floor(position)
        index = lower_index if position - lower_index <= 0.5 else lower_index + 1
        return self.coordinate_at(index)

    def to_args(self: U, ign_value: bool = False) -> tuple[IntervalArgument, ...]:
        # Convert interval to its arguments for initialization, with an optional input to ignore the value
        if self.value != 1 and not ign_value:
            return self.start, self.stop, self.step, self.count, self.value
        elif self.step != 1:
            return self.start, self.stop, self.step, self.count
        else:
            return self.start, self.stop

    def to_args_full(self: U) -> tuple[IntervalArgument, ...]:
        return self.start, self.stop, self.step, self.count, self.value

    def to_args_and_replace(
        self: U,
        replace: Optional[Mapping[str, IntervalArgument]] = None,
    ) -> tuple[IntervalArgument, ...]:
        # Convert interval to its arguments for initialization, with the option to use a dict to replace start,
        # stop or value with a new value.
        if replace is None:
            return self.to_args()
        start = replace['start'] if 'start' in replace else self.start
        stop = replace['stop'] if 'stop' in replace else self.stop
        step = replace['step'] if 'step' in replace else self.step
        count = replace['count'] if 'count' in replace else self.count
        value = replace['value'] if 'value' in replace else self.value
        return (start, stop, step, count, value) if value != 1 else \
            (start, stop, step, count) if step != 1 else (start, stop)

    def __hash__(self: U) -> int:
        if isinstance(self.start, datetime) and self.start.utcoffset() is not None:
            return hash((
                _ordering_coordinate(self.start),
                _ordering_coordinate(self.stop),
                self.step,
                self.count,
                self.value,
            ))
        return hash(self.to_args_full())

    def _ordering_key(self: U) -> tuple[object, object, int, object, int, float]:
        return _ordering_coordinate(self.start), _ordering_coordinate(self.stop), 1, self.step, self.count, self.value

    def get_length(self) -> float:
        return 0

    def equal_with_tol(self: U, num1: float, num2: float) -> bool:
        return num1 - self.tol < num2 < num1 + self.tol

    def is_integer_tol(self: U, num: float) -> bool:
        return self.equal_with_tol(num, int(num + self.tol))

    def __contains__(self: U, val: object) -> bool:
        if type(val) is BaseInterval:
            return False
        if isinstance(self.start, datetime):
            if isinstance(val, BaseDiscreteInterval):
                if not isinstance(val.start, datetime):
                    raise TypeError("discrete intervals must use the same numeric/datetime domain")
                _compare_coordinates(self.start, val.start)
                if val.count == 1:
                    return val.start in self
                if val.start not in self or val.stop not in self:
                    return False
                start_index = self.index_of(val.start)
                if val.step % self.step != timedelta(0):  # type: ignore[operator]
                    return False
                end_index = self.index_of(val.stop)
                return end_index - start_index == (val.count - 1) * (val.step // self.step)  # type: ignore[operator]
            if isinstance(val, datetime):
                if _compare_coordinates(self.start, val) > 0 or _compare_coordinates(val, self.stop) > 0:
                    return False
                return _elapsed_between(self.start, val) % self.step == timedelta(0)  # type: ignore[operator]
            if isinstance(val, (int, float)):
                _compare_coordinates(self.start, val)
            return False
        start = cast(float, self.start)
        stop = cast(float, self.stop)
        step = cast(float, self.step)
        if isinstance(val, datetime):
            _compare_coordinates(self.start, val)
            return False
        if isinstance(val, self.__class__):
            if val.count == 1:
                return val.min() in self
            if not self.is_integer_tol(cast(float, val.step) / step):
                return False
            val_start = cast(float, val.start)
            val_stop = cast(float, val.stop)
            if val_stop > stop or val_start < start:
                return False
            return val.min() in self  # If range(val) in range(self), and val.step = k*self.step, then we check 1 value
        elif isinstance(val, int) or isinstance(val, float):  # in this case, val should be float
            times_step = ((val - start) / step)
            return start - self.tol <= val <= stop + self.tol and self.is_integer_tol(times_step)
        return False

    def __eq__(self: U, other: object) -> bool:
        if isinstance(other, BaseDiscreteInterval):
            if isinstance(self.start, datetime) and isinstance(other.start, datetime):
                return (
                    _compare_coordinates(self.start, other.start) == 0
                    and _compare_coordinates(self.stop, other.stop) == 0
                    and self.step == other.step
                    and self.count == other.count
                    and self.value == other.value
                )
            return self.to_args() == other.to_args()
        return False

    def __iter__(self: U) -> Iterator[tuple[Coordinate, float]]:
        for i in range(self.count):
            yield self.coordinate_at(i), self.value  # type: ignore[misc]

    def split_at(self: U, points: Iterable[Coordinate]) -> tuple['BaseDiscreteInterval', ...]:
        """Split represented points so each point at or before a boundary is on its left."""
        if not isinstance(self.start, datetime):
            return super().split_at(points)  # type: ignore[return-value]

        boundaries: set[int] = set()
        for point in points:
            if not isinstance(point, datetime):
                raise TypeError("datetime intervals require datetime split points")
            _compare_coordinates(self.start, point)
            if _compare_coordinates(point, self.start) < 0 or _compare_coordinates(point, self.stop) >= 0:
                continue
            left_count = _elapsed_between(self.start, point) // self.step + 1  # type: ignore[operator]
            if 0 < left_count < self.count:
                boundaries.add(left_count)

        positions = [0, *sorted(boundaries), self.count]
        return tuple(
            BaseDiscreteInterval(
                self.coordinate_at(positions[index]),
                count=positions[index + 1] - positions[index],
                step=self.step,
                value=self.value,
            )
            for index in range(len(positions) - 1)
        )

    def __repr__(self: U) -> str:
        return (f"{self.__name__}[{self.start};{self.stop};{self.step}" +
                (f";{self.value}]" if self.value != 1 else "]"))

    def __str__(self: U) -> str:
        return f"[{self.start};{self.stop};{self.step}" + (f";{self.value}]" if self.value != 1 else "]")

    def __call__(self: U) -> tuple[IntervalArgument, ...]:
        return self.to_args_full()

    def as_pmf(self) -> 'IntervalPmf':
        """Convert this finite discrete interval into a normalized PMF."""
        if isinstance(self.start, datetime):
            raise TypeError("IntervalPmf does not support datetime coordinates")
        from .interval_pmf import IntervalPmf

        return IntervalPmf(self)

    def left_borders(self: U, other: U) -> bool:
        if isinstance(self.stop, datetime):
            return (
                self.step == other.step
                and isinstance(other.start, datetime)
                and _compare_coordinates(_shift_coordinate(self.stop, self.step), other.start) == 0
            )
        return self.step == other.step and cast(float, self.stop) + cast(float, self.step) == cast(
            float, other.start
        )

    def right_borders(self: U, other: U) -> bool:
        if isinstance(self.start, datetime):
            return (
                self.step == other.step
                and isinstance(other.stop, datetime)
                and _compare_coordinates(self.start, _shift_coordinate(other.stop, other.step)) == 0
            )
        return self.step == other.step and cast(float, self.start) == cast(float, other.stop) + cast(
            float, other.step
        )

    def __add__(self: U, other: 'BaseInterval | abstract_interval.AbstractIntervalCollection') -> (
            abstract_interval.AbstractInterval):
        if isinstance(other, BaseDiscreteInterval):
            # Options:
            # - one loc, same val, can be appended -> do it
            # - different step size -> meter
            # - not adjacent -> meter
            # - same step size, adjacent: combine if same value else meter
            # - same step size, exactly in the middle: combine if same value else meter
            # - same except for value -> combine value

            # If same as index, add up values
            if self.as_index() == other.as_index():
                return self.__class__(self.to_args_and_replace({'value': self.value + other.value}))

            # If one of the two consists of just 1 count and can be prepended/appended to the other, do that
            if self.value == other.value:
                if other.count == 1 and _coordinates_equal(
                    other.start,
                    cast(Coordinate, _shift_coordinate(self.stop, self.step)),
                ):
                    return self.__class__(self.to_args_and_replace({'stop': other.start}))
                if other.count == 1 and _coordinates_equal(
                    other.start,
                    cast(Coordinate, _shift_coordinate(self.start, -self.step)),
                ):
                    return self.__class__(self.to_args_and_replace({'start': other.start}))
                if self.count == 1 and _coordinates_equal(
                    self.start,
                    cast(Coordinate, _shift_coordinate(other.stop, other.step)),
                ):
                    return self.__class__(other.to_args_and_replace({'stop': self.start}))
                if self.count == 1 and _coordinates_equal(
                    self.start,
                    cast(Coordinate, _shift_coordinate(other.start, -self.step)),
                ):
                    return self.__class__(other.to_args_and_replace({'start': self.start}))

            # If different values or stepsizes, can't directly combine (unless otherwise the same)
            if self.value != other.value or self.step != other.step:
                return self._apply_combine(other)

            # If the difference is bigger than the stepsize, can't directly combine
            if (
                _compare_coordinates(
                    cast(Coordinate, _shift_coordinate(self.stop, self.step)),
                    other.start,
                ) < 0
                or _compare_coordinates(
                    cast(Coordinate, _shift_coordinate(other.stop, other.step)),
                    self.start,
                ) < 0
            ):
                return self._apply_combine(other)

            # If they can be appended together, do that
            if _coordinates_equal(
                cast(Coordinate, _shift_coordinate(self.stop, self.step)),
                other.start,
            ):
                return self.__class__(self.to_args_and_replace({'stop': other.stop}))
            if _coordinates_equal(
                cast(Coordinate, _shift_coordinate(other.stop, self.step)),
                self.start,
            ):
                return self.__class__(other.to_args_and_replace({'stop': self.stop}))

            # If one fits exactly in between the other, we can use half the stepsize
            half_step = self.step / 2
            if (
                _coordinate_distance(self.start, other.start) == half_step
                and _coordinate_distance(self.stop, other.stop) == half_step
            ):
                return self.__class__(
                    _coordinate_min(self.start, other.start),
                    _coordinate_max(self.stop, other.stop),
                    step=half_step,
                    value=self.value,
                )

            return self._apply_combine(other)  # Catch-all for other situations but should not trigger

        if isinstance(other, BaseInterval):
            return other.__add__(self)
        return other.__add__(self)

    def _apply_combine(self: 'BaseDiscreteInterval', other: 'BaseDiscreteInterval') -> 'interval_meter.IntervalMeter':
        from .combine_intervals import combine_intervals_meter_discrete

        return combine_intervals_meter_discrete([self, other])

    def __sub__(self: U, other: 'BaseInterval | abstract_interval.AbstractIntervalCollection') -> (
            abstract_interval.AbstractInterval):
        if isinstance(other, abstract_interval.AbstractIntervalCollection):
            return -other + self
        if isinstance(other, BaseDiscreteInterval):
            if self == other:
                return EmptyInterval()
            return self + (-other)
        return interval_meter.IntervalMeter([self, -other])
