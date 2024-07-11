from intervalues import base_interval
from intervalues.abstract_interval import AbstractIntervalCollector
import intervalues


class IntervalList(AbstractIntervalCollector):
    def __init__(self):
        pass


class IntervalListFloat(IntervalList):

    def __init__(self, data=None):
        super().__init__()
        self.data = list()
        if data is not None:
            if type(data) in (list, tuple, set):
                self.data = list(data)
                # combine_intervals_counter(data, object_exists=self)
            elif type(data) is base_interval.BaseInterval:
                self.data.append(data)
            else:
                self.data = list(data)

    def clear(self):
        self.data.clear()

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        new_list = __class__()
        new_list.data = self.data.copy()
        return new_list

    def pop(self, __index):
        return self.data.pop(__index)

    def total_length(self):
        return sum([k.get_length() for k in self.data])

    def get_length(self, index=None):
        if index is None:
            return self.total_length()
        return self[index] * index.get_length()

    def __len__(self):
        return len(self.data)

    def update(self, other, times=1):
        if isinstance(other, self.__class__):
            self.data.extend(other.data*times)
        elif isinstance(other, base_interval.BaseInterval):
            if other.get_length() > 0:
                self.data.extend([other] * times)
        else:
            raise ValueError(f'Input {other} is not of type {IntervalListFloat} or {base_interval.BaseInterval}')

    def find_which_contains(self, other):
        if other in self:
            return [interval for interval in self.data if other in interval]
        return False

    def __add__(self, other):
        new = self.copy()
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
        self.data *= other
        return self

    def __repr__(self):
        return f"IntervalListFloat:{self.data}"

    def __str__(self):
        return self.__repr__()

    def __contains__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return any([other in x for x in self.data])

        elif isinstance(other, base_interval.BaseInterval):
            if other.value == 1:
                return other in self.data or any([other in x for x in self.data])
            else:
                index_version = base_interval.BaseInterval(other.to_args_and_replace(replace={'value': 1}))
                return index_version in self.data or any([index_version in x for x in self.data])

        else:
            raise ValueError(f'Not correct use of "in" for {other}')

    def __getitem__(self, other):
        return sum([x[other] for x in self.data])

    def key_compare(self, other):
        keys1, keys2 = sorted(self.data), sorted(other.data)
        while len(keys1) * len(keys2) > 0:
            key1, key2 = keys1.pop(0), keys2.pop(0)
            if key1 < key2:
                return True
            if key2 < key1:
                return False

        return len(keys2) > 0  # shorter before longer - like in BaseInterval

    # Implemented to align with BaseInterval ordering, since BaseInterval(0,1) == IntervalCounter((BaseInterval(0,1): 1)
    def __lt__(self, other):
        other = other.as_list() if not isinstance(other, self.__class__) else other
        return self.data < other.data

    def __le__(self, other):
        other = other.as_list() if not isinstance(other, self.__class__) else other
        return self.data <= other.data

    def __gt__(self, other):
        other = other.as_list() if not isinstance(other, self.__class__) else other
        return self.data > other.data

    def __ge__(self, other):
        other = other.as_list() if not isinstance(other, self.__class__) else other
        return self.data >= other.data

    def __eq__(self, other):  # Equal if also IntervalList, with same keys, and same counts for all keys.
        if isinstance(other, type(self)):
            return self.data == other.data
        if isinstance(other, base_interval.BaseInterval) and len(self.data) == 1:
            return (other in self.data) and other.get_length() == self.get_length()
        return False

    def __hash__(self):
        return hash(tuple(self))

    def __iter__(self):
        return iter(self.data)

    def min(self):
        return min(self.data).min()

    def max(self):
        return max([x.max() for x in self.data])

    def as_set(self):
        return intervalues.IntervalSetFloat(tuple(self))

    def as_counter(self):
        return intervalues.IntervalCounterFloat(tuple(self))

    def append(self, other):
        self.update(other)

    def extend(self, other):
        self.update(other)

    def count(self, item):
        return self[item]

    def reverse(self):
        self.data.reverse()

    def insert(self, __index, __object):
        self.data.insert(__index, __object)

    def sort(self, key=None, reverse=False):
        self.data.sort(key=key, reverse=reverse)


class IntervalListFloatTodo(IntervalListFloat):

    def __call__(self):
        raise NotImplementedError('__call__ not yet implemented')  # What should it be?

    def draw(self, **kwargs):
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
