import collections
from collections import Counter
from typing import Optional, Sequence, Iterator, ItemsView, KeysView, ValuesView

from intervalues import base_interval
from intervalues.abstract_interval import AbstractIntervalCollection
from intervalues.combine_intervals import combine_intervals_meter, combine_intervals_counter
import intervalues


class IntervalMeter(AbstractIntervalCollection):
    __name__ = 'IntervalMeter'

    """
    Class for a meter of intervals, that measures the value of individual subintervals across its inputs.
    
    Objects can be instantiated in multiple ways (with `a = BaseInterval((1, 3))` and `b = BaseInterval((0, 2))`):
    - IntervalMeter(a) -> using a single interval
    - IntervalMeter([a, b]) -> using a list, tuple or set of intervals
    
    The data is collected in a standard Counter. For the keys, the BaseIntervals are converted to value=1, and the value
    is tracked using the value of the Counter. In contrast to IntervalCounters, the values of IntervalMeters can take
    any real number, so including negative and/or non-integer.
    
    All methods available for Counters (most_common, items, etc) are available, as well as all IntervalCollection
    methods (get_length, max, etc). IntervalMeters can be added together, or multiplied with a numeric value. They can
    also be converted to IntervalCounters, IntervalSets or IntervalLists. Finally, they can be converted to an
    IntervalPdf for sampling purposes.
    """

    def __init__(self, data: Optional[Sequence['intervalues.BaseInterval'] | 'intervalues.BaseInterval'] = None,
                 skip_combine=False, use_rust=False, nr_digits=0):
        super().__init__()
        self.data: Counter = Counter()
        if data is not None:
            if skip_combine:
                if all(type(x) == intervalues.BaseInterval for x in data):
                    temp_dict = {x.as_index(): x.value for x in data}
                    self.data.update(temp_dict)
                else:
                    raise TypeError('Can\'t ignore combine due to input not being sequence of BaseIntervals.')
            else:
                if isinstance(data, collections.abc.Sequence):
                    if use_rust:
                        self.data = intervalues.combine_via_rust(data, nr_digits).data
                    else:
                        combine_intervals_meter(data, object_exists=self)
                elif isinstance(data, base_interval.BaseInterval):
                    self.data[data.as_index()] = data.value  # type: ignore[assignment]

    def items(self) -> 'ItemsView':
        return self.data.items()

    def clear(self):
        self.data.clear()

    def copy(self) -> 'IntervalMeter':
        return self.__copy__()

    def __copy__(self) -> 'IntervalMeter':
        new_meter = self.__class__()
        new_meter.data = self.data.copy()
        return new_meter

    def elements(self) -> 'Iterator':
        return self.data.elements()

    def get(self, __key: 'intervalues.BaseInterval') -> float:
        return self.data.get(__key)  # type: ignore[return-value]

    def keys(self) -> 'KeysView':
        return self.data.keys()

    def most_common(self, n: Optional[int] = None) -> 'list[tuple[intervalues.BaseInterval, float]]':
        return self.data.most_common(n)   # type: ignore[return-value]

    def pop(self, __key: 'intervalues.BaseInterval') -> float:
        return self.data.pop(__key)  # type: ignore[return-value]

    def popitem(self) -> tuple['intervalues.BaseInterval', float]:
        return self.data.popitem()  # type: ignore[return-value]

    def setdefault(self, key, default=None):
        return self.data.setdefault(key, default)

    def subtract(self, other: 'intervalues.BaseInterval | IntervalMeter'):
        self.__isub__(other)

    def total(self) -> float:
        return self.data.total()  # type: ignore[return-value]

    def total_length(self) -> float:
        return sum([k.get_length() * v for k, v in self.data.items()])

    def get_length(self, index: 'Optional[intervalues.BaseInterval]' = None) -> float:
        if index is None:
            return self.total_length()
        return self[index] * index.get_length()

    def __len__(self) -> int:
        return len(self.keys())

    def update(self, other: 'intervalues.BaseInterval | IntervalMeter', times: float = 1):
        if self == other:
            self.__imul__(times + 1)
        elif isinstance(other, self.__class__):
            self.update_meter(other, times=times)
        elif isinstance(other, base_interval.BaseInterval):
            if other.value != 1:
                index_version = base_interval.BaseInterval(other.to_args_and_replace(replace={'value': 1}))
                self.update_interval(index_version, times=times * other.get_value())
            else:
                self.update_interval(other, times=times)
        else:
            raise ValueError(f'Input {other} is not of type {self.__class__} or {base_interval.BaseInterval}')
        self.check_intervals()

    def update_meter(self, other: 'IntervalMeter', times: float = 1, one_by_one: bool = False):
        if self == other:
            self.__imul__(times + 1)
        else:
            if not one_by_one:  # Join meters in one go - better for large meters with much overlap
                self_as_base = [k * v for k, v in self.items()]
                other_as_base = [k * v * times for k, v in other.items()]
                combined = combine_intervals_meter(self_as_base + other_as_base)
                self.data = combined.data
            else:  # Place other one by one - better in case of small other or small prob of overlap
                for k, v in other.items():
                    self.update_interval(k, times=v * times)

    def update_interval(self, other: 'intervalues.BaseInterval', times: float = 1):
        if all([x.is_disjoint_with(other) for x in self.data.keys()]):
            self.data[other] = times  # type: ignore[assignment]
        elif other in self.data.keys():
            self.data[other] = self.data[other] + times  # type: ignore[assignment]
        else:
            self.data[other] = times  # type: ignore[assignment]
            self.check_intervals()

    def check_intervals(self):
        keys = sorted(self.data.keys(), key=lambda x: x.start)
        for i in range(len(keys) - 1):  # Here is where I would use pairwise... IF I HAD ONE :)
            key1, key2 = keys[i], keys[i + 1]
            if key1.stop > key2.start:
                self.align_intervals()
                return
        for key in keys:
            if self[key] == 0:
                del self.data[key]

    def align_intervals(self):
        self_as_base = [k * v for k, v in self.items()]
        aligned = combine_intervals_meter(self_as_base)
        self.data = aligned.data

    def find_which_contains(self, other: 'intervalues.BaseInterval | float') -> 'bool | intervalues.BaseInterval':
        for key in self.data.keys():
            if other in key:
                return key
        return False

    def values(self) -> ValuesView:
        return self.data.values()

    def __add__(self, other: 'intervalues.BaseInterval | intervalues.AbstractIntervalCollection') -> 'IntervalMeter':
        new = self.copy()
        new.update(self.as_my_type(other) if not type(other) is self.__class__ else other)
        # new.update(self.as_my_type(other) if isinstance(other, IntervalMeter) else other)
        return new

    def __iadd__(self, other: 'intervalues.BaseInterval | intervalues.AbstractIntervalCollection') -> 'IntervalMeter':
        self.update(self.as_my_type(other) if not type(other) is self.__class__ else other)
        return self

    def __sub__(self, other: 'intervalues.BaseInterval | IntervalMeter') -> 'IntervalMeter':
        new = self.copy()
        new.update(other, times=-1)
        return new

    def __isub__(self, other: 'intervalues.BaseInterval | IntervalMeter') -> 'IntervalMeter':
        self.update(other, times=-1)
        return self

    def __mul__(self, other: float) -> 'IntervalMeter':
        new = self.__class__()
        new.update(self, times=other)
        return new

    def __imul__(self, other: float) -> 'IntervalMeter':
        for k, v in self.items():
            self.data[k] = v * other
        return self

    def __repr__(self) -> str:
        return f"{self.__name__}:{dict(self.data)}"

    def __str__(self) -> str:
        return self.__repr__()

    def __contains__(self, other: 'intervalues.BaseInterval | float') -> bool:
        if isinstance(other, int) or isinstance(other, float):
            for key, val in self.data.items():
                if other in key:
                    return True
            return False

        elif isinstance(other, base_interval.BaseInterval):
            if other.value == 1:
                return other in self.data.keys() or any([other in x for x in self.data.keys()])
            else:
                index_version = base_interval.BaseInterval(other.to_args_and_replace(replace={'value': 1}))
                return index_version in self.data.keys() or any([index_version in x for x in self.data.keys()])

        else:
            raise ValueError(f'Not correct use of "in" for {other}')

    def __getitem__(self, other: 'intervalues.BaseInterval | float') -> float:
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

    def key_compare(self, other: 'IntervalMeter') -> bool:
        keys1, keys2 = sorted(self.keys()), sorted(other.keys())
        while len(keys1) * len(keys2) > 0:
            key1, key2 = keys1.pop(0), keys2.pop(0)
            if key1 < key2:
                return True
            if key2 < key1:
                return False

        return len(keys2) > 0  # shorter before longer - like in BaseInterval

    # Implemented to align with BaseInterval ordering, since BaseInterval(0,1) == IntervalMeter((BaseInterval(0,1): 1)
    def __lt__(self, other: 'intervalues.AbstractInterval') -> bool:
        other = other.as_meter() if not isinstance(other, self.__class__) else other
        return self.key_compare(other)

    def __le__(self, other: 'intervalues.AbstractInterval') -> bool:
        other = other.as_meter() if not isinstance(other, self.__class__) else other
        return set(self.keys()) == set(other.keys()) or self.key_compare(other)

    def __gt__(self, other: 'intervalues.AbstractInterval') -> bool:
        other = other.as_meter() if not isinstance(other, self.__class__) else other
        return other.key_compare(self)

    def __ge__(self, other: 'intervalues.AbstractInterval') -> bool:
        other = other.as_meter() if not isinstance(other, self.__class__) else other
        return set(self.keys()) == set(other.keys()) or other.key_compare(self)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, type(self)):
            return ((set(self.keys()) == set(other.keys())) and
                    all(self[x] == other[x] for x in self.keys()))
        if isinstance(other, base_interval.BaseInterval) and len(self.keys()) == 1:
            return (other in self.keys()) and other.get_length() == self.get_length()
        return False

    def __hash__(self) -> int:
        return hash(tuple(self))

    def __iter__(self) -> Iterator:
        for iter_key in iter(self.data):
            yield iter_key * self[iter_key]

    def min(self) -> float:
        return min(self.data.keys()).min()

    def max(self) -> float:
        return max(self.data.keys()).max()

    def as_set(self) -> 'intervalues.IntervalSet':
        return intervalues.IntervalSet(tuple(self))

    def as_list(self) -> 'intervalues.IntervalList':
        return intervalues.IntervalList(tuple(self))

    def as_counter(self) -> 'IntervalCounter':
        return IntervalCounter(tuple(self))

    def as_meter(self) -> 'IntervalMeter':
        return self.copy()

    def as_pdf(self) -> 'intervalues.IntervalPdf':
        return intervalues.IntervalPdf(tuple(self))

    @staticmethod
    def as_my_type(other: 'intervalues.AbstractInterval') -> 'IntervalMeter':
        return other.as_meter()


class IntervalCounter(IntervalMeter):
    __name__ = 'IntervalCounter'

    """
    Class for a counter of intervals, that measures how often individual subintervals are featured across its inputs.

    Objects can be instantiated in multiple ways (with `a = BaseInterval((1, 3))` and `b = BaseInterval((0, 2))`):
    - IntervalCounter(a) -> using a single interval
    - IntervalCounter([a, b]) -> using a list, tuple or set of intervals

    The data is collected in a standard Counter. For the keys, the BaseIntervals are converted to value=1, and the value
    is tracked using the value of the Counter. Contrasted with a IntervalMeter, the values in an IntervalCounter can
    only be non-negative integers, e.g. counts. (Note that counts of 0 will often lead to that key being dropped)

    All methods available for Counters (most_common, items, etc) are available, as well as all IntervalCollection
    methods (get_length, max, etc). IntervalCounters can be added together, or multiplied with a numeric value. They can
    also be converted to IntervalMeters, IntervalSets or IntervalLists. Finally, they can be converted to an
    IntervalPdf for sampling purposes.
    """

    def __init__(self, data: Optional[Sequence['intervalues.BaseInterval'] | 'intervalues.BaseInterval'] = None):
        super().__init__()
        self.data: Counter = Counter()
        if data is not None:
            if isinstance(data, collections.abc.Sequence):
                combine_intervals_counter(data, object_exists=self)
            elif type(data) is base_interval.BaseInterval:
                if data.value > 0:
                    self.data[data.as_index()] = int(data.value)

    def update_meter(self, other: 'IntervalMeter', times: float = 1, one_by_one: bool = False):
        if self == other:
            if times >= 0:
                self.__imul__(times + 1)
            else:
                self.clear()
        else:
            if not one_by_one:  # Join counters in one go - better for large counters with much overlap
                self_as_base = [k * v for k, v in self.items()]
                other_as_base = [k * int(v * times) for k, v in other.items()]
                combined = combine_intervals_counter(self_as_base + other_as_base)
                self.data = combined.data
            else:  # Place other one by one - better in case of small other or small prob of overlap
                for k, v in other.items():
                    self.update_interval(k, times=int(v * times))

    def update_interval(self, other: 'intervalues.BaseInterval', times: float = 1):
        if all([x.is_disjoint_with(other) for x in self.data.keys()]):
            if times >= 1:
                self.data[other] = int(times)
        elif other in self.data.keys():
            self.data[other] = self.data[other] + int(times) if self.data[other] + times >= 1 else 0
        else:
            self.data[other] = int(times) if times >= 1 else 0
            self.check_intervals()

    def check_intervals(self):
        keys = sorted(self.data.keys(), key=lambda x: x.start)
        for i in range(len(keys) - 1):  # Here is where I would use pairwise... IF I HAD ONE :)
            key1, key2 = keys[i], keys[i + 1]
            if key1.stop > key2.start:
                self.align_intervals()
                return
        for key in keys:
            if self[key] <= 0:
                del self.data[key]
            elif type(self[key]) is float:
                self.data[key] = int(self.data[key])

    def align_intervals(self):
        self_as_base = [k * v for k, v in self.items()]
        aligned = combine_intervals_counter(self_as_base)
        self.data = aligned.data

    def __mul__(self, other: float):
        new = self.__class__()
        if other > 0:
            new.update(self, times=other)
        return new

    def __imul__(self, other: float):
        if other > 0:
            for k, v in self.items():
                self.data[k] = int(v * other)
        else:
            self.clear()
        return self

    # Implemented to align with BaseInterval ordering, since BaseInterval(0,1) == IntervalCounter((BaseInterval(0,1): 1)
    def __lt__(self, other: 'intervalues.AbstractInterval') -> bool:
        other = other.as_counter() if not isinstance(other, self.__class__) else other
        return self.key_compare(other)

    def __le__(self, other: 'intervalues.AbstractInterval') -> bool:
        other = other.as_counter() if not isinstance(other, self.__class__) else other
        return set(self.keys()) == set(other.keys()) or self.key_compare(other)

    def __gt__(self, other: 'intervalues.AbstractInterval') -> bool:
        other = other.as_counter() if not isinstance(other, self.__class__) else other
        return other.key_compare(self)

    def __ge__(self, other: 'intervalues.AbstractInterval') -> bool:
        other = other.as_counter() if not isinstance(other, self.__class__) else other
        return set(self.keys()) == set(other.keys()) or other.key_compare(self)

    def as_counter(self) -> 'IntervalCounter':
        return self.copy()

    def as_meter(self) -> 'IntervalMeter':
        return IntervalMeter(tuple(self))

    @staticmethod
    def as_my_type(other: 'intervalues.AbstractInterval') -> 'IntervalCounter':
        return other.as_counter()

    def copy(self) -> 'IntervalCounter':
        return self.__copy__()

    def __copy__(self) -> 'IntervalCounter':
        new_counter = self.__class__()
        new_counter.data = self.data.copy()
        return new_counter
