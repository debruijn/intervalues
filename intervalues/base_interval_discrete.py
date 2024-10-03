from typing import Sequence, Iterator, Optional, TypeVar
import collections

from intervalues import interval_meter
from intervalues import BaseInterval, EmptyInterval
from intervalues import abstract_interval


T = TypeVar('T', bound='BaseInterval')
U = TypeVar('U', bound='BaseDiscreteInterval')


class BaseDiscreteInterval(BaseInterval):
    __name__ = 'BaseDiscreteInterval'
    tol = 0.000001

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

    def __init__(self, loc: Sequence[float] | float, stop: Optional[float] = None, step: Optional[float] = None,
                 count: Optional[int] = None, value: Optional[float] = None):
        super().__init__(0)
        if isinstance(loc, collections.abc.Sequence):
            self.start, self.stop = loc[:2]
            self.step: float = step if step is not None else (loc[2] if len(loc) >= 3 else 1)
            self.value: float = value if value is not None else (loc[4] if len(loc) >= 5 else 1)
            self.count: int = (loc[3] if len(loc) >= 4 else 1) if self.stop is None else (
                self.find_count(self.start, self.stop, self.step))
        elif count is not None:
            self.start = loc
            self.count = count
            self.step = step if step is not None else 1
            self.stop = loc + self.step * (self.count - 1)
            self.value = value if value is not None else 1
        else:
            self.start, self.stop = loc, (stop if stop is not None else loc + 1)
            self.step = step if step is not None else 1
            self.value = value if value is not None else 1
            self.count = self.find_count(self.start, self.stop, self.step)

        self.stop = self.start + (self.count - 1) * self.step

    def find_count(self: U, start: float, stop: float, step: float) -> int:
        return int(self.tol + (stop - start) / step) + 1

    def to_args(self: U, ign_value: bool = False) -> tuple[float, ...]:
        # Convert interval to its arguments for initialization, with an optional input to ignore the value
        if self.value != 1 and not ign_value:
            return self.start, self.stop, self.step, self.count, self.value
        elif self.step != 1:
            return self.start, self.stop, self.step, self.count
        else:
            return self.start, self.stop

    def to_args_full(self: U) -> tuple[float, ...]:
        return self.start, self.stop, self.step, self.count, self.value

    def to_args_and_replace(self: U, replace: Optional[dict] = None) -> tuple[float, ...]:
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
        return hash(self.to_args_full())

    def get_length(self) -> float:
        return 0

    def equal_with_tol(self: U, num1: float, num2: float) -> bool:
        return num1 - self.tol < num2 < num1 + self.tol

    def is_integer_tol(self: U, num: float) -> bool:
        return self.equal_with_tol(num, int(num + self.tol))

    def __contains__(self: U, val: 'T | float') -> bool:
        if type(val) is BaseInterval:
            return False
        if isinstance(val, self.__class__):
            if val.count == 1:
                return val.min() in self
            if not self.is_integer_tol(val.step / self.step):
                return False
            if val.stop > self.stop or val.start < self.start:
                return False
            return val.min() in self  # If range(val) in range(self), and val.step = k*self.step, then we check 1 value
        elif isinstance(val, int) or isinstance(val, float):  # in this case, val should be float
            times_step = ((val - self.start) / self.step)
            return self.start - self.tol <= val <= self.stop + self.tol and self.is_integer_tol(times_step)
        return False

    def __eq__(self: U, other: object) -> bool:
        if isinstance(other, BaseDiscreteInterval):
            return self.to_args() == other.to_args()
        return False

    def __iter__(self: U) -> Iterator:
        for i in range(self.count):
            yield self.start + i * self.step, self.value

    def __repr__(self: U) -> str:
        return (f"{self.__name__}[{self.start};{self.stop};{self.step}" +
                (f";{self.value}]" if self.value != 1 else "]"))

    def __str__(self: U) -> str:
        return f"[{self.start};{self.stop};{self.step}" + (f";{self.value}]" if self.value != 1 else "]")

    def __call__(self: U) -> tuple[float, ...]:  # type: ignore[override]
        return self.to_args_full()

    def left_borders(self: U, other: U) -> bool:
        return self.step == other.step and self.stop + self.step == other.start

    def right_borders(self: U, other: U) -> bool:
        return self.step == other.step and self.start == other.stop + self.step

    def __add__(self: U, other: 'T | abstract_interval.AbstractIntervalCollection') -> (
            'T | U | abstract_interval.AbstractIntervalCollection'):
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
                if other.count == 1 and other.start == self.stop + self.step:
                    return self.__class__(self.to_args_and_replace({'stop': other.start}))
                if other.count == 1 and other.start == self.start - self.step:
                    return self.__class__(self.to_args_and_replace({'start': other.start}))
                if self.count == 1 and self.start == other.stop + other.step:
                    return self.__class__(other.to_args_and_replace({'stop': self.start}))
                if self.count == 1 and self.start == other.start - self.step:
                    return self.__class__(other.to_args_and_replace({'start': self.start}))

            # If different values or stepsizes, can't directly combine (unless otherwise the same)
            if self.value != other.value or self.step != other.step:
                return self._apply_combine(other)

            # If the difference is bigger than the stepsize, can't directly combine
            if self.stop + self.step < other.start or other.stop + self.step < self.start:
                return self._apply_combine(other)

            # If they can be appended together, do that
            if self.stop + self.step == other.start:
                return self.__class__(self.to_args_and_replace({'stop': other.stop}))
            if other.stop + self.step == self.start:
                return self.__class__(other.to_args_and_replace({'stop': self.stop}))

            # If one fits exactly in between the other, we can use half the stepsize
            if abs(self.start - other.start) == self.step/2 and abs(self.stop - other.stop) == self.step/2:
                return self.__class__(min(self.start, other.start), max(self.stop, other.stop),
                                      step=self.step/2, value=self.value)

            return self._apply_combine(other)  # Catch-all for other situations but should not trigger

        return other + self  # type: ignore[return-value]

    def _apply_combine(self: 'BaseDiscreteInterval', other: 'BaseDiscreteInterval') -> 'interval_meter.IntervalMeter':
        from intervalues import combine_intervals_meter_discrete
        return combine_intervals_meter_discrete([self, other])

    def __sub__(self: U, other: 'T | abstract_interval.AbstractIntervalCollection') -> (
            abstract_interval.AbstractInterval):
        if isinstance(other, abstract_interval.AbstractIntervalCollection):
            return -other + self
        if isinstance(other, BaseDiscreteInterval):
            if self == other:
                return EmptyInterval()
            return self + (-other)
        return interval_meter.IntervalMeter([self, -other])
