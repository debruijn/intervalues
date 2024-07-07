from intervalues import interval_counter


# TODO: EmptyInterval (not exactly a point..) and UnitInterval (so BaseInterval((0,1))
# TODO: consider removal of ValueInterval and just using BaseInterval with a value -- should be easier to maintain?
# TODO: or alternatively, return an IntervalCounter when value is not 1

class BaseInterval(object):

    __name__ = 'BaseInterval'

    def __init__(self, item, stop=None, value=None):  #, type=None):
        if type(item) in (list, tuple):
            self.start, self.stop = item[:2]  # Assume it is tuple for now
            self.value = value if value is not None else (item[2] if len(item) >= 3 else 1)
            # self.type = type if type is not None else (item[3] if len(item) >= 4 else None)
        else:
            self.start, self.stop = item, stop
            self.value = value if value is not None else 1

        self._length = self.stop - self.start
        if self._length == 0:
            raise ValueError('Is a single point. Might support later should not happen right now.')

    def to_args(self):
        return self.start, self.stop, self.value

    def _update_length(self):
        self._length = self.stop - self.start

    def get_length(self):
        return self._length * self.value

    def __contains__(self, val):  # check numeric
        return self.start <= val <= self.stop

    def __eq__(self, other):
        if type(other) in (BaseInterval, ValueInterval):
            return self.start == other.start and self.stop == other.stop and self.value == other.value
        if type(other) == interval_counter.IntervalCounterFloat:
            return other == self
        return False

    def __hash__(self):
        return hash(tuple(self))  # TODO: or self.start, self.stop, self.value? Or without self.value?

    def __iter__(self):
        yield self.start, self.value
        yield self.stop, -self.value

    def __len__(self):
        return self.get_length()

    def __repr__(self):
        return f"{self.__name__}[{self.start};{self.stop}" + f";{self.value}]" if self.value != 1 else "]"

    def __str__(self):
        return f"[{self.start};{self.stop}" + f";{self.value}]" if self.value != 1 else "]"

    def __call__(self):
        return tuple(self)

    def __getitem__(self, index):
        return self.value if index in self else 0  # 1 if index == 0 else self.stop

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

    def __lt__(self, other):
        return self.stop < other.start

    def __le__(self, other):
        return self.start < other.start and self.stop < other.stop

    def __gt__(self, other):
        return self.start > other.stop

    def __ge__(self, other):
        return self.start > other.start and self.stop > other.stop

    # TODO: rework after ValueInterval removal
    def __add__(self, other):  # This is "optimal" for combining intervals when possible, but will be inconsistent
        if isinstance(other, BaseInterval):
            if other.start == self.stop and other.value == self.value:
                return BaseInterval((self.start, other.stop)) if self.value == 1 else (
                    ValueInterval((self.start, other.stop), value=self.value))
            if self.start == other.stop and other.value == self.value:
                return BaseInterval((other.start, self.stop)) if self.value == 1 else (
                    ValueInterval((other.start, self.stop), value=self.value))
            if self.start == other.start and self.stop == other.stop:
                return ValueInterval((self.start, self.stop), value=self.value + other.value)
            return interval_counter.IntervalCounterFloat([self, other])
        return other + self

    def __iadd__(self, other):
        return self + other

    def __radd__(self, other):
        return other + self

    # TODO: rework after ValueInterval removal
    def __sub__(self, other):
        if self.value == other.value:
            if self.start == other.start and other.stop < self.stop:
                return BaseInterval((other.stop, self.stop)) if self.value == 1 else (
                    ValueInterval((other.stop, self.stop), value=self.value))
            if self.start == other.start and other.stop > self.stop:
                return -BaseInterval((self.stop, other.stop)) if self.value == 1 else (
                    ValueInterval((self.stop, other.stop), value=-self.value))
            if self.start < other.start and self.stop == other.stop:
                return BaseInterval((self.start, other.start)) if self.value == 1 else (
                    ValueInterval((self.start, other.start), value=self.value))
            if self.start > other.start and self.stop == other.stop:
                return -BaseInterval((other.start, self.start)) if self.value == 1 else (
                    ValueInterval((other.start, self.start), value=-self.value))
        if self.start == other.start and self.stop == other.stop:
            return ValueInterval((self.start, self.stop), value=self.value - other.value)
        if self == other:
            return None
            # Future:  return EmptyInterval
        return interval_counter.IntervalCounterFloat([self, -other])

    def __isub__(self, other):
        return self - other

    def __neg__(self):
        return self.__mul__(-1)

    # TODO: rework after ValueInterval removal
    def __mul__(self, num):
        if isinstance(num, int) or isinstance(num, float):
            if num * self.value == 1:
                return BaseInterval((self.start, self.stop))
            else:
                return ValueInterval(item=(self.start, self.stop), value=num*self.value)
        else:
            raise ValueError("Multiplication should be with an int or a float.")

    def __rmul__(self, num):
        return self * num

    # TODO: rework after ValueInterval removal
    def __imul__(self, num):
        if isinstance(num, int) or isinstance(num, float):
            return ValueInterval(item=(self.start, self.stop), value=num)
        else:
            raise ValueError("Multiplication should be with an int or a float.")

    def __truediv__(self, num):
        return self * (1 / num)

    def __idiv__(self, num):
        return self * (1 / num)

    # TODO: rework after ValueInterval removal
    def __floordiv__(self, num):
        if self.value // num == 1:
            return BaseInterval((self.start, self.stop))
        else:
            return ValueInterval((self.start, self.stop), value=self.value // num)

    # TODO: rework after ValueInterval removal
    def __ifloordiv__(self, num):
        if self.value // num == 1:
            return BaseInterval((self.start, self.stop))
        else:
            return ValueInterval((self.start, self.stop), value=self.value // num)

    def get_value(self):
        return self.value

    # TODO: rework after ValueInterval removal
    def __lshift__(self, shift):
        return BaseInterval((self.start-shift, self.stop-shift))

    def __rshift__(self, shift):
        return BaseInterval((self.start+shift, self.stop+shift))

    # TODO: rework after ValueInterval removal
    def __copy__(self):
        return BaseInterval((self.start, self.stop))


class ValueInterval(BaseInterval):
    __name__ = 'ValueInterval'

    def __init__(self, item, value=1.0):
        super().__init__(item)
        self.value = value

    # TODO: rework after ValueInterval removal
    def set_value(self, val):
        self.value = val

    def mult_value(self, val):
        self.value *= val

    def __mul__(self, num):
        if isinstance(num, int) or isinstance(num, float):
            if num * self.value == 1:
                return BaseInterval((self.start, self.stop))
            else:
                return ValueInterval(item=(self.start, self.stop), value=num * self.value)
        else:
            raise ValueError("Multiplication should be with an int or a float.")

    def __rmul__(self, num):
        return self * num

    def __imul__(self, num):
        if isinstance(num, int) or isinstance(num, float):
            self.mult_value(num)
            return self
        else:
            raise ValueError("Multiplication should be with an int or a float.")

    def __repr__(self):
        return f"{self.__name__}[{self.start};{self.stop};{self.value}]"

    def __str__(self):
        return f"[{self.start};{self.stop};{self.value}]"

    def __lshift__(self, shift):
        return ValueInterval((self.start-shift, self.stop-shift), value=self.value)

    def __rshift__(self, shift):
        return ValueInterval((self.start+shift, self.stop+shift), value=self.value)

    def __copy__(self):
        return ValueInterval((self.start, self.stop), value=self.value)
