from intervalues import interval_counter


class BaseInterval(object):

    def __init__(self, item):
        self.start, self.stop = item  # Assume it is tuple for now
        self.length = self.stop - self.start
        self.value = 1
        if self.length == 0:
            raise ValueError('Is a single point. Might support later should not happen right now.')

    def get_length(self):
        return self.length * self.value

    def __contains__(self, val):  # check numeric
        return self.start <= val <= self.stop

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.start == other.start and self.stop == other.stop  # Potentially use math.isclose

    def __hash__(self):
        return hash(tuple(self))  # TODO: or self.start, self.stop, self.value? Or without self.value?

    def __iter__(self):
        yield self.start, self.value
        yield self.stop, -self.value

    def __len__(self):
        return self.get_length()

    def __repr__(self):
        return f"UnitInterval[{self.start:.4f};{self.stop:.4f}]"

    def __str__(self):
        return f"[{self.start};{self.stop}]"

    def __call__(self):
        return tuple(self)

    def __getitem__(self, index):
        return self.start if index == 0 else self.stop

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

    def compare(self, other):  # TODO: not happy with this. Let's see what makes sense when applying it.
        if self == other:
            return 0
        if self < other:
            return -2
        if self <= other:
            return -1
        if self > other:
            return 2
        if self >= other:
            return 1
        else:
            return 1j

    def __add__(self, other):  # This is "optimal" for combining intervals when possible, but will be inconsistent
        if other.start == self.stop:
            return BaseInterval((self.start, other.stop))
        if self.start == other.stop:
            return BaseInterval((other.start, self.stop))
        return interval_counter.IntervalCounterFloat([self, other])

    def get_value(self):
        return self.value


class ValueInterval(BaseInterval):

    def __init__(self, item, value=1):
        super().__init__(item)
        self.value = value

    def set_value(self, val):
        self.value = val
