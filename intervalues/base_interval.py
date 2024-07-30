from intervalues import interval_meter, interval_list
from intervalues import interval_set
from intervalues import abstract_interval


class BaseInterval(abstract_interval.AbstractInterval):
    __name__ = 'BaseInterval'

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

    def __init__(self, loc, stop=None, value=None):
        if type(loc) in (list, tuple):
            self.start, self.stop = loc[:2]  # Assume it is tuple for now
            self.value = value if value is not None else (loc[2] if len(loc) >= 3 else 1)
        else:
            self.start, self.stop = loc, stop
            self.value = value if value is not None else 1

        self._length = self.stop - self.start

    def to_args(self, ign_value=False):
        # Convert interval to its arguments for initialization, with an optional input to ignore the value
        return (self.start, self.stop, self.value) if self.value != 1 and not ign_value else (self.start, self.stop)

    def to_args_and_replace(self, replace=None):
        # Convert interval to its arguments for initialization, with the option to use a dict to replace start,
        # stop or value with a new value.
        if replace is None:
            return self.to_args()
        start = replace['start'] if 'start' in replace else self.start
        stop = replace['stop'] if 'stop' in replace else self.stop
        value = replace['value'] if 'value' in replace else self.value
        return (start, stop, value) if value != 1 else (start, stop)

    def as_index(self):
        return self.copy_with_replace({'value': 1})

    def copy_with_replace(self, replace=None):
        if replace is None:
            return self.copy()
        return BaseInterval(self.to_args_and_replace(replace=replace))

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        return BaseInterval(self.to_args())

    def as_meter(self):
        return interval_meter.IntervalMeter([self])

    def as_counter(self):
        return interval_meter.IntervalCounter([self])

    def as_set(self):
        return interval_set.IntervalSet([self])

    def as_list(self):
        return interval_list.IntervalList(self)

    def _update_length(self):
        self._length = self.stop - self.start

    def get_length(self):
        return self._length * self.value

    def __contains__(self, val):
        if type(val) is BaseInterval:
            return self.start <= val.start and self.stop >= val.stop
        return self.start <= val <= self.stop

    def __eq__(self, other):
        if type(other) is BaseInterval:
            return self.start == other.start and self.stop == other.stop and self.value == other.value
        if type(other) in [interval_meter.IntervalMeter, interval_set.IntervalSet, interval_list.IntervalList,
                           interval_meter.IntervalCounter]:
            return other == self
        return False

    def __hash__(self):
        return hash(self.to_args())

    def __iter__(self):
        yield self.start, self.value
        yield self.stop, -self.value

    def __len__(self):
        return self.get_length()

    def __repr__(self):
        return f"{self.__name__}[{self.start};{self.stop}" + (f";{self.value}]" if self.value != 1 else "]")

    def __str__(self):
        return f"[{self.start};{self.stop}" + (f";{self.value}]" if self.value != 1 else "]")

    def __call__(self):
        return tuple(self)

    def __getitem__(self, index):
        if type(index) in (int, float):
            return self.value if index in self else 0
        else:
            return self.value / index.value if index in self else 0

    def overlaps(self, other):
        return self.left_overlaps(other) or self.right_overlaps(other)

    def left_overlaps(self, other):
        return self.start < other.start < self.stop

    def right_overlaps(self, other):
        return self.start < other.stop < self.stop

    def contains(self, other):
        return self.start <= other.start and self.stop >= other.stop

    def left_borders(self, other):
        return self.stop == other.start

    def right_borders(self, other):
        return self.start == other.stop

    def borders(self, other):
        return self.left_borders(other) or self.right_borders(other)

    def is_disjoint_with(self, other):
        return ((not self.overlaps(other)) and (not self.borders(other)) and (not self.contains(other)) and
                (not other.contains(self))) and (not self == other)

    # Used for ordering, for which it is useful to order by start-point first, and stop-point second.
    def __lt__(self, other):
        if not isinstance(other, BaseInterval):
            return other > self
        return self.start < other.start or (self.start == other.start and self.stop < other.stop)

    def __le__(self, other):
        if not isinstance(other, BaseInterval):
            return other >= self
        return self.start <= other.start

    def __gt__(self, other):
        if not isinstance(other, BaseInterval):
            return other < self
        return self.start > other.start

    def __ge__(self, other):
        if not isinstance(other, BaseInterval):
            return other <= self
        return self.start >= other.start or (self.start == other.start and self.stop > other.stop)

    def __add__(self, other):
        if isinstance(other, BaseInterval):
            if other.start == self.stop and other.value == self.value:
                return BaseInterval((self.start, other.stop, self.value))
            if self.start == other.stop and other.value == self.value:
                return BaseInterval((other.start, self.stop, self.value))
            if self.start == other.start and self.stop == other.stop:
                return BaseInterval((self.start, self.stop, self.value + other.value))
            return interval_meter.IntervalMeter([self, other])
        return other + self

    def __iadd__(self, other):
        return self + other

    def __radd__(self, other):
        return other + self

    def __sub__(self, other):
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

    def __isub__(self, other):
        return self - other

    def __neg__(self):
        return self.__mul__(-1)

    def __mul__(self, num):
        if isinstance(num, int) or isinstance(num, float):
            return BaseInterval((self.start, self.stop), value=num * self.value)
        raise ValueError("Multiplication should be with an int or a float.")

    def __rmul__(self, num):
        return self * num

    def __imul__(self, num):
        if isinstance(num, int) or isinstance(num, float):
            return BaseInterval((self.start, self.stop), value=num * self.value)
        raise ValueError("Multiplication should be with an int or a float.")

    def __truediv__(self, num):
        return self * (1 / num)

    def __idiv__(self, num):
        return self * (1 / num)

    def get_value(self):
        return self.value

    def set_value(self, val):
        self.value = val

    def mult_value(self, val):
        self.value *= val

    def __lshift__(self, shift):
        return BaseInterval((self.start - shift, self.stop - shift), value=self.value)

    def __rshift__(self, shift):
        return BaseInterval((self.start + shift, self.stop + shift), value=self.value)

    def min(self):
        return self.start

    def max(self):
        return self.stop


def ValueInterval(item, value=1):  # Used for compatibility reasons - will be removed
    return BaseInterval(item, value=value)


def UnitInterval():
    """
    Utility function to return a default BaseInterval from 0 to 1.
    :return: a BaseInterval(0, 1)
    """
    return BaseInterval(0, 1)


def EmptyInterval():
    """
    Utility function to generate an empty interval, which is otherwise not supported.
    This can be compared with other intervals, if needed (for example, to use as the smallest interval in an algorithm).
    :return:
    """
    interval = UnitInterval()
    interval.start, interval.stop, interval._length = 0, 0, 0
    interval.__name__ = 'EmptyInterval'
    return interval
