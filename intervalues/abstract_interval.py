import abc
import random
import intervalues


class AbstractInterval(abc.ABC):
    """
    Abstract class for intervals of any type: a single base interval, or a collection of intervals in some way.

    Contains self-explaining methods for:
    - converting the object to a IntervalCounter/IntervalList/IntervalMeter
    - calculating some general interval properties, the max/min and the length/weight of it
    """

    @abc.abstractmethod
    def as_counter(self): pass

    @abc.abstractmethod
    def as_list(self): pass

    @abc.abstractmethod
    def as_meter(self): pass

    @abc.abstractmethod
    def get_length(self): pass

    @abc.abstractmethod
    def max(self): pass

    @abc.abstractmethod
    def min(self): pass


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
    def __init__(self, data=None):
        self.data = (None,) if data is None else data

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data

    def get_length(self):
        return len(self.data)

    def __len__(self):
        return len(self.data)

    def sample(self, k=1):
        return random.sample(self.data, k=k)

    def draw(self, k=1):
        return self.sample(k=k)

    def __contains__(self, x):
        return x in self.data

    def __repr__(self):
        return f"{self.__class__}:{self.data}"

    def __str__(self):
        return self.__repr__()

    def __getitem__(self, x):
        return self.data[x]

    def __eq__(self, other):
        return isinstance(other, type(self)) and (self.data == other.data)

    def __hash__(self):
        return hash(tuple(self))

    def __iter__(self):
        return iter(self.data)

    def __add__(self, other):
        return __class__(self.data + other.data)

    def __iadd__(self, other):
        self.data += other.data

    def update(self, data):
        self.data += data

    def min(self):
        return min(self.data)

    def max(self):
        return max(self.data)

    def as_single_interval(self):
        return intervalues.BaseInterval(self.min(), self.max())
