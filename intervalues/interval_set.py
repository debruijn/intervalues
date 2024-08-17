import collections
from typing import Optional, Sequence, Iterator

from intervalues import base_interval
from intervalues.abstract_interval import AbstractIntervalCollection
from intervalues.combine_intervals import combine_intervals_set, combine_intervals_meter, combine_intervals_set_discrete
import intervalues


class IntervalSet(AbstractIntervalCollection):
    __name__ = 'IntervalSet'

    """
    Class for a set of intervals, that tracks the occurence of individual subintervals across its inputs.

    Objects can be instantiated in multiple ways (with `a = BaseInterval((1, 3))` and `b = BaseInterval((0, 2))`):
    - IntervalSet(a) -> using a single interval
    - IntervalSet([a, b]) -> using a list, tuple or set of intervals

    The data is collected in a standard set. For this, the BaseIntervals are converted to value=1, since the IntervalSet
    doesn't track how often subintervals are featured.

    All methods available for sets (intersection, symmetric_difference, etc) are available, as well as all 
    IntervalCollection methods (get_length, max, etc). IntervalSets can be combined together (union/intersection) or 
    differenced. They can also be converted to IntervalCounters, IntervalMeters or IntervalLists. 
    """

    def __init__(self, data: Optional[Sequence['intervalues.BaseInterval'] | 'intervalues.BaseInterval'] = None):
        super().__init__()
        self.data: set = set()
        if data is not None:
            self.discrete: bool = True if type(data) == Sequence[
                intervalues.BaseDiscreteInterval] | intervalues.BaseDiscreteInterval else False
            if self.discrete:
                if isinstance(data, collections.abc.Sequence):
                    combine_intervals_set_discrete(data, object_exists=self)  # type: ignore[arg-type]
                elif type(data) is intervalues.BaseDiscreteInterval:
                    self.data = {data.as_index()}
            else:
                if isinstance(data, collections.abc.Sequence):
                    combine_intervals_set(data, object_exists=self)
                elif type(data) is base_interval.BaseInterval:
                    self.data = {data.as_index()}

    def add(self, other: 'IntervalSet'):
        self.update_set(other)

    def difference(self, other: 'IntervalSet') -> 'IntervalSet':
        return self - other

    def difference_update(self, other: 'IntervalSet'):
        self.__isub__(other)

    def discard(self, item: 'IntervalSet'):
        self.data -= item.data

    def intersection(self, other: 'IntervalSet') -> 'IntervalSet':
        new = self.copy()
        new += other
        return new

    def intersection_update(self, other: 'IntervalSet'):
        self.__iadd__(other)

    def isdisjoint(self, other: 'IntervalSet') -> bool:
        return all([x.is_disjoint_with(y) for x in self.data for y in other.data])

    def issubset(self, other: 'IntervalSet') -> bool:
        return all([any([x in y for y in other.data]) for x in self.data])

    def issuperset(self, other: 'IntervalSet') -> bool:
        return other.issubset(self)

    def pop(self) -> 'intervalues.BaseInterval':
        return self.data.pop()

    def remove(self, item: 'intervalues.BaseInterval'):
        if item not in self.data:
            raise KeyError(f"{item} not in {self}")
        self.data.remove(item)

    def symmetric_difference(self, other: 'IntervalSet') -> 'IntervalSet':
        return self ^ other

    def symmetric_difference_update(self, other: 'IntervalSet'):
        new = self.symmetric_difference(other)
        self.data = new.data

    def union(self, other: 'IntervalSet') -> 'IntervalSet':
        return self + other

    def __and__(self, other: 'IntervalSet') -> 'IntervalSet':
        new = self.__class__()
        new.data = self.data & other.data if isinstance(other, self.__class__) else \
            (other.data if other in self.data or any([other in x for x in self.data]) else set())
        return new

    def __iand__(self, other: 'IntervalSet') -> 'IntervalSet':
        if isinstance(other, self.__class__):
            self.data &= other.data
        else:
            self.data = other.data if other in self.data else set()
        return self

    def __ior__(self, other: 'IntervalSet') -> 'IntervalSet':
        self.__iadd__(other)
        return self

    def __ixor__(self, other: 'IntervalSet') -> 'IntervalSet':
        new = self ^ other
        self.data = new.data
        return self

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __or__(self, other: 'IntervalSet') -> 'IntervalSet':
        return self + other

    def __xor__(self, other: 'IntervalSet') -> 'IntervalSet':
        return (self - other) + (other - self)

    def clear(self):
        self.data.clear()

    def copy(self) -> 'IntervalSet':
        return self.__copy__()

    def __copy__(self) -> 'IntervalSet':
        new_counter = self.__class__()
        new_counter.data = self.data.copy()
        return new_counter

    def subtract(self, other: 'IntervalSet'):
        self.__isub__(other)

    def total_length(self) -> float:
        return sum([k.get_length() for k in self.data])

    def get_length(self, index: Optional['intervalues.BaseInterval'] = None) -> float:
        if index is None:
            return self.total_length()
        return (index in self) * index.get_length()

    def __len__(self) -> int:
        return len(self.data)

    def update(self, other: 'IntervalSet | intervalues.BaseInterval', reverse: bool = False):
        if self == other:
            if reverse:
                self.clear()
            return
        elif isinstance(other, IntervalSet):
            self.update_set(other, reverse=reverse)
        elif isinstance(other, base_interval.BaseInterval):
            self.update_interval(other, reverse=reverse)
        else:
            raise ValueError(f'Input {other} is not of type {IntervalSet} or {base_interval.BaseInterval}')
        self.check_intervals()

    def update_set(self, other: 'IntervalSet', one_by_one: bool = False, reverse: bool = False):
        if self == other:
            return
        else:
            if not one_by_one:  # Join sets in one go - better for large sets with much overlap
                if not reverse:
                    combined = combine_intervals_set(list(self.data) + list(other.data))
                    self.data = combined.data
                else:
                    combined = combine_intervals_meter(list(self.data) + [-x for x in other.data]).as_set()
                    self.data = combined.data
            else:  # Place other one by one - better in case of small other or small prob of overlap
                for k in other.data:
                    self.update_interval(k, reverse=reverse)

    def update_interval(self, other: 'intervalues.BaseInterval', reverse: bool = False):
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
                combined = combine_intervals_set(list(self.data) + [-1 * other])
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

    def find_which_contains(self, other: 'intervalues.BaseInterval | float') -> 'bool | intervalues.BaseInterval':
        for key in self.data:
            if other in key:
                return key
        return False

    def __add__(self, other: 'intervalues.BaseInterval | AbstractIntervalCollection') -> 'IntervalSet':
        new = self.copy()
        new.update(other.as_set() if not isinstance(other, IntervalSet) else other)
        return new

    def __iadd__(self, other: 'intervalues.BaseInterval | AbstractIntervalCollection') -> 'IntervalSet':
        self.update(other.as_set() if not isinstance(other, IntervalSet) else other)
        return self

    def __sub__(self, other: 'IntervalSet | intervalues.BaseInterval') -> 'IntervalSet':
        new = self.copy()
        new.update(other, reverse=True)
        return new

    def __isub__(self, other: 'IntervalSet | intervalues.BaseInterval') -> 'IntervalSet':
        self.update(other, reverse=True)
        return self

    def __mul__(self, other: int | float) -> 'IntervalSet':
        return self.copy()

    def __repr__(self) -> str:
        return f"{self.__name__}:{self.data}"

    def __str__(self) -> str:
        return self.__repr__()

    def __contains__(self,  other: 'intervalues.BaseInterval | float') -> bool:
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

    def __getitem__(self, other: 'intervalues.BaseInterval | float') -> float:
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

    def key_compare(self, other: 'IntervalSet') -> bool:
        keys1, keys2 = sorted(self.data), sorted(other.data)
        while len(keys1) * len(keys2) > 0:
            key1, key2 = keys1.pop(0), keys2.pop(0)
            if key1 < key2:
                return True
            if key2 < key1:
                return False

        return len(keys2) > 0  # shorter before longer - like in BaseInterval

    # Implemented to align with BaseInterval ordering, since BaseInterval(0,1) == IntervalCounter((BaseInterval(0,1): 1)
    def __lt__(self, other: 'IntervalSet') -> bool:
        other = other.as_set() if not isinstance(other, self.__class__) else other
        return self.key_compare(other)

    def __le__(self, other: 'IntervalSet') -> bool:
        other = other.as_set() if not isinstance(other, self.__class__) else other
        return self == other or self.key_compare(other)

    def __gt__(self, other: 'IntervalSet') -> bool:
        other = other.as_set() if not isinstance(other, self.__class__) else other
        return other.key_compare(self)

    def __ge__(self, other: 'IntervalSet') -> bool:
        other = other.as_set() if not isinstance(other, self.__class__) else other
        return self == other or other.key_compare(self)

    def __eq__(self, other: object) -> bool:  # Equal if also IntervalSet, with same intervals in it.
        if isinstance(other, type(self)):
            return self.data == other.data
        if isinstance(other, base_interval.BaseInterval) and len(self.data) == 1:
            return other in self.data  # and other.get_length() == self.get_length()
        return False

    def __hash__(self) -> int:
        return hash(tuple(self))

    def __iter__(self) -> Iterator:
        return iter(self.data)

    def min(self) -> float:
        return min(self.data).min()

    def max(self) -> float:
        return max(self.data).max()

    def as_meter(self) -> 'intervalues.IntervalMeter':
        return intervalues.IntervalMeter(list(iter(self.data)))

    def as_list(self) -> 'intervalues.IntervalList':
        return intervalues.IntervalList(list(iter(self)))

    def as_counter(self) -> 'intervalues.IntervalCounter':
        return intervalues.IntervalCounter(tuple(self))

    def as_set(self) -> 'intervalues.IntervalSet':
        return self.copy()

    def as_pdf(self) -> 'intervalues.IntervalPdf':
        return intervalues.IntervalPdf(tuple(self))
