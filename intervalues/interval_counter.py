from collections import Counter
from intervalues.base_interval import BaseInterval, ValueInterval
from intervalues.abstract_interval import AbstractInterval
from intervalues.combine_intervals import combine_intervals


# TODO: compare this Counter implementation with a "ValueInterval"  based one -> what is faster?


class IntervalCounter(AbstractInterval):
    def __init__(self):
        pass


class IntervalCounterFloat(IntervalCounter):

    def __init__(self, data=None):
        super().__init__()
        self.data = Counter()
        if data is not None:
            combine_intervals(data, object=self)

    def items(self):
        return self.data.items()

    def clear(self):
        self.data.clear()

    def copy(self):
        new_counter = __class__()
        new_counter.data = self.data.copy()
        return new_counter

    def elements(self):
        return self.data.elements()

    def get(self, __key):
        return self.data.get(__key)

    def keys(self):
        return self.data.keys()

    def most_common(self, n=1):  # This is different; normal counter by default n=len(counter.keys())
        return self.data.most_common(n)

    def pop(self, __key):  # Potentially overwrite to subtract 1 and return it. You "get one of the counts of the interval".
        return self.data.pop(__key)

    def popitem(self):
        return self.data.popitem()

    def setdefault(self, key, default=None):
        return self.data.setdefault(key, default)

    def subtract(self, other):
        pass

    def total(self):  # total length or total count of intervals?
        return self.data.total()

    def total_length(self):
        return sum([k.get_length() * v for k, v in self.data.items()])

    def get_length(self):
        return self.total_length()

    def __len__(self):
        return len(self.keys())

    def update(self, other, times=1):
        if self == other:
            self.__imul__(times + 1)
        elif isinstance(other, IntervalCounterFloat):
            self.update_counter(other, times=times)
        elif isinstance(other, BaseInterval):
            self.update_interval(other, times=times*other.value)
        else:
            raise ValueError(f'Input {other} is not of type {IntervalCounterFloat} or {BaseInterval}')

    def update_counter(self, other, times=1, one_by_one=False):
        # TODO: if both self and other are big, rerunning combine_intervals might be faster. If other is small, not.
        # TODO: So decide on what to choose: combine_intervals, update_interval, or a mixture depending on size.
        if self == other:
            self.__imul__(times + 1)
        else:
            if not one_by_one:  # Join counters in one go - better for large counters with much overlap
                self_as_valueint = [k*v for k,v in self.items()]  # TODO: use new as_valueint method
                other_as_valueint = [k*v*times for k,v in other.items()]
                combined = combine_intervals(self_as_valueint + other_as_valueint)
                self.data = combined.data
            else:  # Place other one by one - better in case of small other or small prob of overlap
                for k, v in other.items():
                    self.update_interval(k, times=v*times)

    def update_interval(self, other, depth=0, times=1):
        if all([x.is_disjoint_with(other) for x in self.data.keys()]):
            self.data[other] = times
        elif other in self.data.keys():
            self.data[other] = self.data[other] + times
        else:
            self.data[other] = times
            self.check_intervals()

    def check_intervals(self):
        keys = sorted(self.data.keys(), key= lambda x: x.start)
        for i in range(len(keys) - 1):  # Here is where I would use pairwise.. IF I HAD ONE :)
            key1, key2 = keys[i], keys[i+1]
            if not key1.stop <= key2.start:
                self.align_intervals()
                return

    def align_intervals(self):
        self_as_valueint = [k * v for k, v in self.items()]  # TODO: use new as_valueint method
        aligned = combine_intervals(self_as_valueint)
        self.data = aligned.data

    def find_which_contains(self, other):
        for key in self.data.keys():
            if key.contains(other):
                return key
        return False

    def find_first_contained_by(self, other):
        for key in self.data.keys():
            if other.contains(key):
                return key
        return False

    def find_left_overlap(self, other):
        for key in self.data.keys():
            if key.left_overlaps(other):
                return key
        return False

    def find_right_overlap(self, other):
        for key in self.data.keys():
            if other.left_overlaps(key):
                return key
        return False

    def values(self):
        return self.data.values()

    def __add__(self, other):
        new = self.__class__()
        new.update(self)
        new.update(other)
        return new

    def __iadd__(self, other):
        self.update(other)
        return self

    def __mul__(self, other):
        new = self.__class__()
        new.update(self, times=other)
        return new

    def __imul__(self, other):
        for k, v in self.items():
            self.data[k] = v * other
        return self

    def __repr__(self):
        return f"IntervalCounterFloat:{dict(self.data)}"

    def __str__(self):
        return self.__repr__()

    def __contains__(self, value):
        if isinstance(value, int) or isinstance(value, float):
            for key, val in self.data.items():
                if value in key:
                    return val
            return 0

        elif isinstance(value, BaseInterval):
            return value in self.data.keys()

        else:
            raise ValueError(f'Not correct use of "in" for {value}')

    def __getitem__(self, value):
        if isinstance(value, int) or isinstance(value, float):
            for key, val in self.data.items():
                if value in key:
                    return val
            return 0

        elif isinstance(value, BaseInterval):
            return self.data[value]

        else:
            raise ValueError(f'Not correct use of indexing with {value}')

    def __lt__(self, other):
        raise NotImplementedError('__lt__ not yet implemented')
        # True if: (1) other[key] <= self[key] for all keys in other and at least 1 is < or self has 1 key not in other;
        # or (2) this is True after taking merging into account (e.g. [1,3]: 2 < [1,2]: 2; [2,3]: 3)

    def __le__(self, other):
        raise NotImplementedError('__le__ not yet implemented')

    def __gt__(self, other):
        raise NotImplementedError('__gt__ not yet implemented')

    def __ge__(self, other):
        raise NotImplementedError('__ge__ not yet implemented')

    def __eq__(self, other):  # Equal if also IntervalCounter, with same keys, and same counts for all keys.
        if isinstance(other, type(self)):
            return ((set(self.keys()) == set(other.keys())) and
                all(self[x] == other[x] for x in self.keys()))
        if isinstance(other, BaseInterval) and len(self.keys()) == 1:
            return (other in self.keys()) and other.get_length() == self.get_length()
        return False

    def __hash__(self):
        return hash(tuple(self))

    def __iter__(self):
        return self.data.__iter__()

    def __call__(self):
        raise NotImplementedError('__call__ not yet implemented')  # What should it be?

    def draw(self):
        raise NotImplementedError('To do')  # Draw a value from all intervals - only works if no infinite interval

    def plot(self):
        raise NotImplementedError('To do')  # Barplot of counts

    def cdf(self, val):
        raise NotImplementedError('To do')  # Use as cdf: P(X<=val)

    def pdf(self, val):
        raise NotImplementedError('To do')  # use as pdf: P(X=val) (Integer interval) or Probability of the interval.
        # Alternative a "Scaled" version that automatically updates the counts to sum/integrate to 1 (not real counts).

    def to_integer_interval(self):
        raise NotImplementedError('To do')
