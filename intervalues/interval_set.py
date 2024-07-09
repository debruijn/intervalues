import intervalues
from intervalues import base_interval
from intervalues.abstract_interval import AbstractIntervalCollector
from intervalues.combine_intervals import combine_intervals_set, combine_intervals_counter


class IntervalSet(AbstractIntervalCollector):
    def __init__(self):
        pass


class IntervalSetFloat(IntervalSet):

    def __init__(self, data=None):
        super().__init__()
        self.data = set()
        if data is not None:
            if type(data) in (list, tuple, set):
                combine_intervals_set(data, object_exists=self)
            elif type(data) is base_interval.BaseInterval:
                self.data = {data.as_index()}
            else:
                combine_intervals_set(tuple(data), object_exists=self)

    def add(self, other):  # reliably restored by inspect
        self.update_interval(other)

    def difference(self, other):  # reliably restored by inspect
        return self - other

    def difference_update(self, other):  # reliably restored by inspect
        self.__isub__(other)

    def discard(self, item):  # reliably restored by inspect
        self.data -= item

    def intersection(self, other):  # reliably restored by inspect
        new = self.copy()
        new += other
        return new

    def intersection_update(self, other):  # reliably restored by inspect
        self.__iadd__(other)

    def isdisjoint(self, other):  # reliably restored by inspect
        return all([x.is_disjoint_with(y) for x in self.data for y in other.data])

    def issubset(self, other):  # reliably restored by inspect
        return all([any([x in y for y in other.data]) for x in self.data])

    def issuperset(self, other):  # reliably restored by inspect
        return other.issubset(self)

    def pop(self):  # reliably restored by inspect
        return self.data.pop()

    def remove(self, item):  # reliably restored by inspect
        if item not in self.data:
            raise KeyError(f"{item} not in {self}")
        self.data.remove(item)

    def symmetric_difference(self, other):  # reliably restored by inspect
        return self | other

    def symmetric_difference_update(self, other):  # reliably restored by inspect
        new = self.symmetric_difference(other)
        self.data = new.data

    def union(self, other):  # reliably restored by inspect
        return self + other

    def __and__(self, other):  # reliably restored by inspect
        new = __class__()
        new.data = self.data & other.data if isinstance(other, self.__class__) else \
            (other.data if other in self.data or any([other in x for x in self.data]) else set())
        return new

    def __iand__(self, other):  # reliably restored by inspect
        if isinstance(other, self.__class__):
            self.data &= other.data
        else:
            self.data = other.data if other in self.data else set()
        return self

    def __ior__(self, other):  # reliably restored by inspect
        self.__add__(other)
        return self

    def __ixor__(self, other):  # reliably restored by inspect
        new = self | other
        self.data = new.data

    def __ne__(self, other):  # reliably restored by inspect
        return not self.__eq__(other)

    def __or__(self, other):  # reliably restored by inspect
        return self + other

    def __xor__(self, other):  # reliably restored by inspect
        return (self - other) + (other - self)

    def clear(self):
        self.data.clear()

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        new_counter = __class__()
        new_counter.data = self.data.copy()
        return new_counter

    def subtract(self, other):
        self.__isub__(other)

    def total_length(self):
        return sum([k.get_length() for k in self.data])

    def get_length(self, index=None):
        if index is None:
            return self.total_length()
        return (index in self) * index.get_length()

    def __len__(self):
        return len(self.data)

    def update(self, other, reverse=False):
        if self == other:
            if reverse:
                self.clear()
            return
        elif isinstance(other, IntervalSetFloat):
            self.update_set(other, reverse=reverse)
        elif isinstance(other, base_interval.BaseInterval):
            self.update_interval(other, reverse=reverse)
        else:
            raise ValueError(f'Input {other} is not of type {IntervalSetFloat} or {base_interval.BaseInterval}')
        self.check_intervals()

    def update_set(self, other, one_by_one=False, reverse=False):
        if self == other:
            return
        else:
            if not one_by_one:  # Join counters in one go - better for large counters with much overlap
                if not reverse:
                    combined = combine_intervals_set(list(self.data) + list(other.data))
                    self.data = combined.data
                else:
                    combined = combine_intervals_counter(list(self.data) + [-x for x in other.data]).as_set()
                    self.data = combined.data
            else:  # Place other one by one - better in case of small other or small prob of overlap
                for k in other.data:
                    self.update_interval(k, reverse=reverse)

    def update_interval(self, other, reverse=False):
        if all([x.is_disjoint_with(other) for x in self.data]):
            if not reverse:
                self.data.add(other)
        elif other in self.data:
            if reverse:
                self.data.remove(other)
            return
        else:
            if not reverse:
                self.data.add(other)
            else:
                combined = combine_intervals_counter(list(self.data) + [-1*other])
                self.data = combined.data
            self.check_intervals()

    def check_intervals(self):
        keys = sorted(self.data, key=lambda x: x.start)
        for i in range(len(keys) - 1):
            key1, key2 = keys[i], keys[i + 1]
            if key1.stop > key2.start:
                self.align_intervals()
                return

    def align_intervals(self):
        self_as_base = [k for k in self.data]
        aligned = combine_intervals_set(self_as_base)
        self.data = aligned.data

    def find_which_contains(self, other):
        for key in self.data:
            if other in key:
                return key
        return False

    def __add__(self, other):
        new = self.copy()
        new.update(other)
        return new

    def __iadd__(self, other):
        self.update(other)
        return self

    def __sub__(self, other):
        new = self.copy()
        new.update(other, reverse=True)
        # new.data -= other.data
        return new

    def __isub__(self, other):
        self.update(other, reverse=True)
        # self.data -= other.data
        return self

    def __repr__(self):
        return f"IntervalSetFloat:{self.data}"

    def __str__(self):
        return self.__repr__()

    def __contains__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            for key in self.data:
                if other in key:
                    return True
            return False

        elif isinstance(other, base_interval.BaseInterval):
            if other.value == 1:
                return other in self.data or any([other in x for x in self.data])
            else:
                index_version = base_interval.BaseInterval(other.to_args_and_replace(replace={'value': 1}))
                return index_version in self.data or any([index_version in x for x in self.data])

        else:
            raise ValueError(f'Not correct use of "in" for {other}')

    def __getitem__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            for key in self.data:
                if other in key:
                    return 1
            return 0

        elif isinstance(other, base_interval.BaseInterval):
            if other.value == 1:
                return 1 if other in self.data or any([other in x for x in self.data]) else 0
            else:
                index_version = base_interval.BaseInterval(other.to_args_and_replace(replace={'value': 1}))
                return 1 if index_version in self.data or any([index_version in x for x in self.data]) else 0

        else:
            raise ValueError(f'Not correct use of indexing with {other}')

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
        other = other.as_set() if not isinstance(other, self.__class__) else other
        return self.key_compare(other)

    def __le__(self, other):
        other = other.as_set() if not isinstance(other, self.__class__) else other
        return self == other or self.key_compare(other)

    def __gt__(self, other):
        other = other.as_set() if not isinstance(other, self.__class__) else other
        return other.key_compare(self)

    def __ge__(self, other):
        other = other.as_set() if not isinstance(other, self.__class__) else other
        return self == other or other.key_compare(self)

    def __eq__(self, other):  # Equal if also IntervalCounter, with same keys, and same counts for all keys.
        if isinstance(other, type(self)):
            return self.data == other.data
        if isinstance(other, base_interval.BaseInterval) and len(self.data) == 1:
            return other in self.data  # and other.get_length() == self.get_length()
        return False

    def __hash__(self):
        return hash(tuple(self))

    def __iter__(self):
        return iter(self.data)

    def min(self):
        return min(self.data).min()

    def max(self):
        return max(self.data).max()

    def as_counter(self):
        return intervalues.IntervalCounterFloat(list(iter(self.data)))


class IntervalSetFloatTodo(IntervalSetFloat):

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
