from __future__ import annotations

import abc
from typing import Any, Collection, Generic, Iterator, TypeVar

import intervalues


CollectionData = TypeVar('CollectionData', bound=Collection[Any])


class AbstractInterval(abc.ABC):
    """
    Abstract class for intervals of any type: a single base interval, or a collection of intervals in some way.

    Contains self-explaining methods for:
    - converting the object to a IntervalCounter/IntervalList/IntervalMeter
    - calculating some general interval properties, the max/min and the length/weight of it
    """

    @abc.abstractmethod
    def as_counter(self) -> 'intervalues.IntervalCounter': pass

    @abc.abstractmethod
    def as_list(self) -> 'intervalues.IntervalList': pass

    @abc.abstractmethod
    def as_meter(self) -> 'intervalues.IntervalMeter': pass

    @abc.abstractmethod
    def as_set(self) -> 'intervalues.IntervalSet': pass

    @abc.abstractmethod
    def as_pdf(self) -> 'intervalues.IntervalPdf': pass

    @abc.abstractmethod
    def get_length(self) -> float: pass

    @abc.abstractmethod
    def max(self) -> float: pass

    @abc.abstractmethod
    def min(self) -> float: pass


class AbstractIntervalCollection(AbstractInterval, Generic[CollectionData]):
    """
    Abstract class for interval collections of intervals in some way.
    In general, the relevant data for each collection wil be contained in a `data` attribute.

    Contains methods for:
    - accessing/defining/changing the contents of `data`
    - comparing with other objects
    - converting to a base interval
    """

    data: CollectionData

    def get_data(self) -> CollectionData:
        return self.data

    def set_data(self, data: CollectionData) -> None:
        self.data = data

    @abc.abstractmethod
    def get_length(self) -> float:
        pass

    def __contains__(self, x: object) -> bool:
        return x in self.data

    def __repr__(self) -> str:
        return f"{self.__class__}:{self.data}"

    def __str__(self) -> str:
        return self.__repr__()

    @abc.abstractmethod
    def __getitem__(self, x: object) -> float:
        pass

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and (self.data == other.data)

    def __hash__(self) -> int:
        return hash(tuple(self))

    def __iter__(self) -> Iterator['intervalues.BaseInterval']:
        return iter(self.data)

    @abc.abstractmethod
    def __add__(self, other: 'intervalues.BaseInterval | AbstractIntervalCollection') -> 'AbstractInterval':
        pass

    @abc.abstractmethod
    def __mul__(self, other: float) -> 'AbstractIntervalCollection':
        pass

    def __neg__(self) -> 'AbstractIntervalCollection':
        return self.__mul__(-1)

    def min(self) -> float:
        return min(x.min() for x in self.data)

    def max(self) -> float:
        return max(x.max() for x in self.data)

    def as_single_interval(self) -> 'intervalues.BaseInterval':
        from .base_interval import BaseInterval

        return BaseInterval(self.min(), self.max())
