from typing import Optional, Sequence

import intervalues
from random import random


class IntervalPdf(intervalues.IntervalMeter):
    __name__ = 'IntervalPdf'

    """
    Class for a probability density function across intervals, that can be used for sampling and other statistical 
    purposes.

    Objects can be instantiated in multiple ways (with `a = BaseInterval((1, 3))` and `b = BaseInterval((0, 2))`):
    - IntervalPdf(a) -> using a single interval
    - IntervalPdf([a, b]) -> using a list, tuple or set of intervals

    The data is collected in a standard Counter. For the keys, the BaseIntervals are converted to value=1, and the value
    is tracked using the value of the Counter. In contrast to IntervalMeters, the values of IntervalPdfs will 
    automatically be scaled such that the total length equals 1, like a probability density should.

    All methods available for Counters (most_common, items, etc) are available, as well as all IntervalCollection
    methods (get_length, max, etc). Use .cumulative to convert a IntervalPdf into a Cdf, or use sample to draw a random
    value from any subinterval in the IntervalPdf using the normalized value as density.
    """
    def __init__(self, data: Optional[Sequence['intervalues.BaseInterval'] | 'intervalues.BaseInterval'] = None):
        super().__init__(data)
        self.normalize()

    def normalize(self):
        total = self.total_length(force=True)
        for k, v in self.items():
            self.data[k] = v / total

    def pop(self, __key: 'intervalues.BaseInterval') -> float:
        item = self.data.pop(__key)
        self.normalize()
        return item

    def popitem(self) -> tuple['intervalues.BaseInterval', float]:
        item = self.data.popitem()
        self.normalize()
        return item

    def total_length(self, force: bool = False) -> float:
        if not force:
            return 1
        return super().total_length()

    def __mul__(self, other: float) -> 'IntervalPdf':
        return self.copy()

    def __imul__(self, other: float) -> 'IntervalPdf':
        return self

    def __repr__(self) -> str:
        return f"{self.__name__}:{dict(self.data)}"

    def check_intervals(self):
        super().check_intervals()
        if self.total_length(force=True) != 1:
            self.normalize()

    def align_intervals(self):
        super().align_intervals()
        self.normalize()

    def cumulative(self, x: float) -> float:
        pre = sum([self.get_length(i) for i in self.keys() if i.max() < x])
        this: 'bool | intervalues.BaseInterval' = self.find_which_contains(x)
        if isinstance(this, intervalues.BaseInterval):
            this_val = self.get_length(this) * (x - this.min()) / (this.max() - this.min())
        else:
            this_val = 0
        return pre + this_val

    def cumsum(self, x: float) -> float:
        return self.cumulative(x)

    def inverse_cumulative(self, p: float) -> float:
        # Note: here the inverse-CDF sampling method is used. Alternatively, we could a combination of random.choice to
        # select a subinterval and then random() to sample within that subinterval in an uniform way.

        keys = sorted(self.keys())
        i: int = -1
        sum_p: float = 0
        last: float = 0
        while sum_p < p:
            i += 1
            last = sum_p
            sum_p += self.get_length(keys[i])
        if i == -1:
            return 0

        where_in_curr = (p - last) / self.get_length(keys[i])
        min_curr, max_curr = keys[i].min(), keys[i].max()
        x = where_in_curr * (max_curr - min_curr) + min_curr
        print(where_in_curr, keys[i], min_curr, max_curr)

        return x

    def sample(self, k: int = 1) -> list[float]:
        return [self.inverse_cumulative(random()) for _ in range(k)]

    def as_meter(self) -> 'intervalues.IntervalMeter':
        return intervalues.IntervalMeter(tuple(self))

    @staticmethod
    def as_my_type(other: 'intervalues.AbstractInterval') -> 'IntervalPdf':
        return other.as_pdf()

    def copy(self) -> 'IntervalPdf':
        return self.__copy__()

    def __copy__(self) -> 'IntervalPdf':
        new_counter = self.__class__()
        new_counter.data = self.data.copy()
        return new_counter
