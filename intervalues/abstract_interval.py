import abc
import intervalues
from typing import Iterator, Optional, Counter, TypeVar

T = TypeVar('T', bound='intervalues.BaseInterval')


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


class AbstractIntervalCollection(AbstractInterval):
    """
    Abstract class for interval collections of intervals in some way.
    In general, the relevant data for each collection wil be contained in a `data` attribute.

    Contains methods for:
    - accessing/defining/changing the contents of `data`
    - comparing with other objects
    - converting to a base interval
    """

    @abc.abstractmethod
    def __init__(self, data: Optional[Counter | list | set] = None):
        self.data: Counter | list | set = list() if data is None else data

    def get_data(self) -> Counter | list | set:
        return self.data

    def set_data(self, data: Counter | list | set):
        self.data = data

    @abc.abstractmethod
    def get_length(self) -> float:
        pass

    def __contains__(self, x: 'intervalues.BaseInterval | float') -> bool:
        return x in self.data

    def __repr__(self) -> str:
        return f"{self.__class__}:{self.data}"

    def __str__(self) -> str:
        return self.__repr__()

    @abc.abstractmethod
    def __getitem__(self, x) -> float:
        pass

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and (self.data == other.data)

    def __hash__(self) -> int:
        return hash(tuple(self))

    def __iter__(self) -> Iterator:
        return iter(self.data)

    @abc.abstractmethod
    def __add__(self, other: 'T | AbstractIntervalCollection') -> \
            'T | AbstractIntervalCollection':
        pass

    @abc.abstractmethod
    def __mul__(self, other: float) -> 'AbstractIntervalCollection':
        pass

    def __neg__(self) -> 'AbstractIntervalCollection':
        return self.__mul__(-1)

    @abc.abstractmethod
    def update(self, data):
        pass

    def min(self) -> float:
        return min(min(x) for x in self.data)

    def max(self) -> float:
        return max(max(x) for x in self.data)

    def as_single_interval(self) -> 'intervalues.BaseInterval':
        return intervalues.BaseInterval(self.min(), self.max())
