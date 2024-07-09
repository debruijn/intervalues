from collections import Counter
from intervalues import base_interval
from intervalues.abstract_interval import AbstractIntervalCollector
from intervalues.combine_intervals import combine_intervals
import intervalues


class IntervalCounter(AbstractIntervalCollector):
    def __init__(self):
        pass


class IntervalCounterFloat(IntervalCounter):

    def __init__(self, data=None):
        super().__init__()
        self.data = Counter()
        if data is not None:
            if type(data) in (list, tuple, set):
                combine_intervals(data, object_exists=self)
            elif type(data) is base_interval.BaseInterval:
                self.data[data.as_index()] = data.value
            else:
                combine_intervals(tuple(data), object_exists=self)

    def items(self):
        return self.data.items()

    def clear(self):
        self.data.clear()

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        new_counter = __class__()
        new_counter.data = self.data.copy()
        return new_counter

    def elements(self):
        return self.data.elements()

    def get(self, __key):
        return self.data.get(__key)

    def keys(self):
        return self.data.keys()

    def most_common(self, n=None):  # This is different; normal counter by default n=len(counter.keys())
        return self.data.most_common(n)

    def pop(self,
            __key):  # Potentially overwrite to subtract 1 and return it. You "get one of the counts of the interval".
        return self.data.pop(__key)

    def popitem(self):
        return self.data.popitem()

    def setdefault(self, key, default=None):
        return self.data.setdefault(key, default)

    def subtract(self, other):
        self.__isub__(other)

    def total(self):  # total length or total count of intervals?
        return self.data.total()

    def total_length(self):
        return sum([k.get_length() * v for k, v in self.data.items()])

    def get_length(self, index=None):
        if index is None:
            return self.total_length()
        return self[index] * index.get_length()

    def __len__(self):
        return len(self.keys())

    def update(self, other, times=1):
        if self == other:
            self.__imul__(times + 1)
        elif isinstance(other, IntervalCounterFloat):
            self.update_counter(other, times=times)
        elif isinstance(other, base_interval.BaseInterval):
            self.update_interval(other, times=times)
        else:
            raise ValueError(f'Input {other} is not of type {IntervalCounterFloat} or {base_interval.BaseInterval}')
        self.check_intervals()

    def update_counter(self, other, times=1, one_by_one=False):
        # TODO: if both self and other are big, rerunning combine_intervals might be faster. If other is small, not.
        # TODO: So decide on what to choose: combine_intervals, update_interval, or a mixture depending on size.
        if self == other:
            self.__imul__(times + 1)
        else:
            if not one_by_one:  # Join counters in one go - better for large counters with much overlap
                self_as_base = [k * v for k, v in self.items()]  # TODO: use new as_valueint method
                other_as_base = [k * v * times for k, v in other.items()]
                combined = combine_intervals(self_as_base + other_as_base)
                self.data = combined.data
            else:  # Place other one by one - better in case of small other or small prob of overlap
                for k, v in other.items():
                    self.update_interval(k, times=v * times)

    def update_interval(self, other, times=1):
        if all([x.is_disjoint_with(other) for x in self.data.keys()]):
            self.data[other] = times
        elif other in self.data.keys():
            self.data[other] = self.data[other] + times
        else:
            self.data[other] = times
            self.check_intervals()

    def check_intervals(self):
        keys = sorted(self.data.keys(), key=lambda x: x.start)
        for i in range(len(keys) - 1):  # Here is where I would use pairwise.. IF I HAD ONE :)
            key1, key2 = keys[i], keys[i + 1]
            if key1.stop > key2.start:
                self.align_intervals()
                return
        for key in keys:
            if self[key] == 0:
                del self.data[key]

    def align_intervals(self):
        self_as_base = [k * v for k, v in self.items()]
        aligned = combine_intervals(self_as_base)
        self.data = aligned.data

    def find_which_contains(self, other):
        for key in self.data.keys():
            if other in key:
                return key
        return False

    def values(self):
        return self.data.values()

    def __add__(self, other):
        new = self.copy()
        new.update(other)
        return new

    def __iadd__(self, other):
        self.update(other)
        return self

    def __sub__(self, other):
        new = self.copy()
        new.update(other, times=-1)
        return new

    def __isub__(self, other):
        self.update(other, times=-1)
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

    def __contains__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            for key, val in self.data.items():
                if other in key:
                    return val
            return 0

        elif isinstance(other, base_interval.BaseInterval):
            if other.value == 1:
                return other in self.data.keys() or any([other in x for x in self.data.keys()])
            else:
                index_version = base_interval.BaseInterval(other.to_args_and_replace(replace={'value': 1}))
                return index_version in self.data.keys() or any([index_version in x for x in self.data.keys()])

        else:
            raise ValueError(f'Not correct use of "in" for {other}')

    def __getitem__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            for key, val in self.data.items():
                if other in key:
                    return val
            return 0

        elif isinstance(other, base_interval.BaseInterval):
            if other.value == 1:
                if other in self.data:
                    return self.data[other]
                return sum([self.data[x] for x in self.data.keys() if other in x])
            else:
                index_version = base_interval.BaseInterval(other.to_args_and_replace(replace={'value': 1}))
                if index_version in self.data:
                    return self.data[index_version] / other.value
                return sum([self.data[x] for x in self.data.keys() if index_version in x]) / other.value
        else:
            raise ValueError(f'Not correct use of indexing with {other}')

    def key_compare(self, other):
        keys1, keys2 = sorted(self.keys()), sorted(other.keys())
        while len(keys1) * len(keys2) > 0:
            key1, key2 = keys1.pop(0), keys2.pop(0)
            if key1 < key2:
                return True
            if key2 < key1:
                return False

        return len(keys2) > 0  # shorter before longer - like in BaseInterval

    # Implemented to align with BaseInterval ordering, since BaseInterval(0,1) == IntervalCounter((BaseInterval(0,1): 1)
    def __lt__(self, other):
        other = other.as_counter() if not isinstance(other, self.__class__) else other
        return self.key_compare(other)

    def __le__(self, other):
        other = other.as_counter() if not isinstance(other, self.__class__) else other
        return set(self.keys()) == set(other.keys()) or self.key_compare(other)

    def __gt__(self, other):
        other = other.as_counter() if not isinstance(other, self.__class__) else other
        return other.key_compare(self)

    def __ge__(self, other):
        other = other.as_counter() if not isinstance(other, self.__class__) else other
        return set(self.keys()) == set(other.keys()) or other.key_compare(self)

    def __eq__(self, other):  # Equal if also IntervalCounter, with same keys, and same counts for all keys.
        if isinstance(other, type(self)):
            return ((set(self.keys()) == set(other.keys())) and
                    all(self[x] == other[x] for x in self.keys()))
        if isinstance(other, base_interval.BaseInterval) and len(self.keys()) == 1:
            return (other in self.keys()) and other.get_length() == self.get_length()
        return False

    def __hash__(self):
        return hash(tuple(self))

    def __iter__(self):
        for iter_key in iter(self.data):
            yield iter_key * self[iter_key]

    def min(self):
        return min(self.data.keys()).min()

    def max(self):
        return max(self.data.keys()).max()

    def as_set(self):
        return intervalues.IntervalSetFloat(tuple(self))


class IntervalCounterFloatTodo(IntervalCounterFloat):

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
