import abc
import random
import intervalues


class AbstractInterval(abc.ABC):
    pass


# TODO: implement Set -> move same implementations for Set and Counter to below -> make sure shared between B/S/C is in
# AI above.

class AbstractIntervalCollector(AbstractInterval):

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

    # @abc.abstractmethod
    def as_single_interval(self):
        return intervalues.BaseInterval(self.min(), self.max())
