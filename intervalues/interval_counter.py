import abc
from collections import Counter
from intervalues.unit_interval import UnitInterval


class AbstractInterval(abc.ABC):

    @abc.abstractmethod
    def __init__(self, input):
        pass


class ContinuousInterval(AbstractInterval):
    def __init__(self, input):
        pass


class IntervalCounterFloat(ContinuousInterval):

    def __init__(self, input=None):
        super().__init__(input)
        self.counter = Counter([input] if not (isinstance(input, list) or input is None) else input)  # For now, assume input is of type single_interval
        self.check_intervals()

    def items(self):
        return self.counter.items()

    def clear(self):
        self.counter.clear()

    def copy(self):
        new_counter = __class__()
        new_counter.counter = self.counter.copy()
        return new_counter

    def elements(self):
        return self.counter.elements()

    def get(self, __key):
        return self.counter.get(__key)

    def keys(self):
        return self.counter.keys()

    def most_common(self, n=1):  # This is different; normal counter by default n=len(counter.keys())
        return self.counter.most_common(n)

    def pop(self, __key):  # Potentially overwrite to subtract 1 and return it. You "get one of the counts of the interval".
        return self.counter.pop(__key)

    def popitem(self):
        return self.counter.popitem()

    def setdefault(self, key, default=None):
        return self.counter.setdefault(key, default)

    def subtract(self, other):
        pass

    def total(self):  # total length or total count of intervals?
        return self.counter.total()

    def total_length(self):
        return self.__len__()

    def __len__(self):
        return sum([k.length * v for k, v in self.counter.items()])

    def update(self, other, times=1):  # TODO: times > 1
        if isinstance(other, IntervalCounterFloat):
            self.update_counter(other)
        elif isinstance(other, UnitInterval):
            self.update_interval(other)
        else:
            raise ValueError(f'Input {other} is not of type {IntervalCounterFloat} or {UnitInterval}')

    def update_counter(self, other):
        if self == other:
            other = other.copy()
        for k, v in other.items():
            self.update_interval(k, times=v)

    def update_interval(self, other, depth=0, times=1):
        if all([x.is_disjoint_with(other) for x in self.counter.keys()]):
            self.counter[other] = times
        else:  # The above is the only case after which no check has to be done
            if other in self.counter.keys():
                self.counter[other] = self.counter[other] + times
            elif self.find_which_contains(other) is not False:
                k = self.find_which_contains(other)
                v = self.counter[k]
                if k.start < other.start:
                    lower = UnitInterval((k.start, other.start))
                    self.counter[lower] = v
                if other.stop < k.stop:
                    higher = UnitInterval((other.stop, k.stop))
                    self.counter[higher] = v
                del self.counter[k]
                self.counter[other] = v + times
            elif self.find_first_contained_by(other) is not False:
                k = self.find_first_contained_by(other)
                self.counter[k] += times
                if other.start < k.start:
                    lower = UnitInterval((other.start, k.start))
                    self.update_interval(lower, depth + 1, times=times)
                if k.stop < other.stop:
                    higher = UnitInterval((k.stop, other.stop))
                    self.update_interval(higher, depth + 1, times=times)
            elif self.find_left_overlap(other) is not False:
                k = self.find_left_overlap(other)
                v = self.counter[k]
                lower = UnitInterval((k.start, other.start))
                middle = UnitInterval((other.start, k.stop))
                higher = UnitInterval((k.stop, other.stop))
                self.counter[lower] = v
                self.counter[middle] = v + times
                del self.counter[k]
                self.update_interval(higher, depth + 1, times=times)
            elif self.find_right_overlap(other) is not False:
                k = self.find_right_overlap(other)
                v = self.counter[k]
                lower = UnitInterval((other.start, k.start))
                middle = UnitInterval((k.start, other.stop))
                higher = UnitInterval((other.stop, k.stop))
                self.counter[higher] = v
                self.counter[middle] = v + times
                del self.counter[k]
                self.update_interval(lower, depth + 1, times=times)
            else:
                self.counter[other] = times

            if depth == 0:
                self.check_intervals()

    def check_intervals(self, n=1):
        # TODO: improve by going less deep in the function
        keys = sorted(self.counter.keys(), key=lambda x: x.start)
        for i in range(len(keys) - 1):
            key1, key2 = keys[i], keys[i+1]
            if key2.start > key1.start:  # If we are not in a tie
                if key1.stop == key2.start and self.counter[key1] == self.counter[key2]:
                    joined = UnitInterval((key1.start, key2.stop))
                    self.counter[joined] = self.counter[key1]
                    del self.counter[key1]
                    del self.counter[key2]
                    self.check_intervals(n)
                    return
                elif key1.stop > key2.start:
                    lower = UnitInterval((key1.start, key2.start))
                    self.counter[lower] = self.counter[key1]
                    if key1.stop < key2.stop:
                        middle = UnitInterval((key2.start, key1.stop))
                        higher = UnitInterval((key1.stop, key2.stop))
                        self.counter[higher] = self.counter[key2]
                        self.counter[middle] = self.counter[key1] + self.counter[key2]
                        del self.counter[key2]
                        del self.counter[key1]
                        self.check_intervals(n)
                    elif key1.stop > key2.stop:
                        middle = UnitInterval((key2.start, key2.stop))
                        higher = UnitInterval((key2.stop, key1.stop))
                        self.counter[higher] = self.counter[key1]
                        self.counter[middle] = self.counter[key1] + self.counter[key2]
                        del self.counter[key1]

                    else:  # key1.stop == key2.stop
                        higher = UnitInterval((key2.start, key1.stop))
                        self.counter[higher] = self.counter[key1] + self.counter[key2]
                        del self.counter[key1]

                    # del self.counter[key1]
                    return
            else:  # We are in a tie for start
                lower = UnitInterval((key1.start, min(key2.stop, key1.stop)))
                self.counter[lower] = self.counter[key1] + self.counter[key2]
                higher = UnitInterval((min(key2.stop, key1.stop), max(key2.stop, key1.stop)))
                self.counter[higher] = self.counter[key1] if key1.stop > key2.stop else self.counter[key2]
                if key1 != lower:
                    del self.counter[key1]
                else:
                    del self.counter[key2]
                    self.check_intervals(n)
                # del self.counter[key1 if key1 != lower else key2]
                return
        if n > 1:
            self.check_intervals(n-1)

    def find_which_contains(self, other):
        for key in self.counter.keys():
            if key.contains(other):
                return key
        return False

    def find_first_contained_by(self, other):
        for key in self.counter.keys():
            if other.contains(key):
                return key
        return False

    def find_left_overlap(self, other):
        for key in self.counter.keys():
            if key.left_overlaps(other):
                return key
        return False

    def find_right_overlap(self, other):
        for key in self.counter.keys():
            if other.left_overlaps(key):
                return key
        return False

    def values(self):
        return self.counter.values()

    def __add__(self, other):
        new = self.__class__()
        new.update(self)
        new.update(other)
        return new

    def __repr__(self):
        return f"ContinuousIntervalCounter:{dict(self.counter)}"

    def __str__(self):
        return self.__repr__()

    def __contains__(self, value):
        if isinstance(value, int) or isinstance(value, float):
            for key, val in self.counter.items():
                if value in key:
                    return val
            return 0

        elif isinstance(value, UnitInterval):
            return value in self.counter.keys()

        else:
            raise ValueError(f'Not correct use of "in" for {value}')

    def __getitem__(self, value):
        if isinstance(value, int) or isinstance(value, float):
            for key, val in self.counter.items():
                if value in key:
                    return val
            return 0

        elif isinstance(value, UnitInterval):
            return self.counter[value]

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
        return ((isinstance(other, type(self)) and set(self.keys()) == set(other.keys())) and
                all(self[x] == other[x] for x in self.keys()))

    def __hash__(self):
        return hash(tuple(self))

    def __iter__(self):
        return self.counter.__iter__()

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