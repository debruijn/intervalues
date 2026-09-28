import math
from random import random
from typing import Optional, Sequence

import intervalues
from .interval_meter import IntervalMeter


class IntervalPdf(IntervalMeter):
    __name__ = 'IntervalPdf'

    """
    Class for a probability density function across intervals, that can be used for sampling and other statistical 
    purposes.

    Objects can be instantiated in multiple ways (with `a = BaseInterval((1, 3))` and `b = BaseInterval((0, 2))`):
    - IntervalPdf(a) -> using a single interval
    - IntervalPdf([a, b]) -> using a list or tuple of intervals

    The data is collected in a standard Counter. For the keys, the BaseIntervals are converted to value=1, and the value
    is tracked using the value of the Counter. In contrast to IntervalMeters, the values of IntervalPdfs will 
    automatically be scaled such that the total length equals 1, like a probability density should.

    All methods available for Counters (most_common, items, etc) are available, as well as all IntervalCollection
    methods (get_length, max, etc). Use .cumulative to convert a IntervalPdf into a Cdf, or use sample to draw a random
    value from any subinterval in the IntervalPdf using the normalized value as density.
    """
    def __init__(self, data: Optional[Sequence['intervalues.BaseInterval'] | 'intervalues.BaseInterval'] = None):
        """Create a continuous probability density with finite, non-negative weights.

        Empty inputs, discrete intervals, and inputs with zero or non-finite
        weighted length are not valid probability densities.
        """
        from .base_interval_discrete import BaseDiscreteInterval

        intervals: Sequence[intervalues.BaseInterval]
        if isinstance(data, intervalues.BaseInterval):
            intervals = (data,)
        elif isinstance(data, Sequence):
            intervals = tuple(data)
        else:
            raise ValueError("IntervalPdf requires at least one continuous interval")

        if not intervals:
            raise ValueError("IntervalPdf requires at least one continuous interval")
        for interval in intervals:
            if not isinstance(interval, intervalues.BaseInterval):
                raise TypeError("IntervalPdf inputs must be BaseInterval instances")
            if isinstance(interval, BaseDiscreteInterval):
                raise TypeError("Discrete intervals require a probability-mass distribution")
            if not math.isfinite(interval.start) or not math.isfinite(interval.stop):
                raise ValueError("IntervalPdf bounds must be finite")
            if interval.get_length() <= 0:
                raise ValueError("IntervalPdf intervals must have positive length")
            if not math.isfinite(interval.value) or interval.value < 0:
                raise ValueError("IntervalPdf weights must be finite and non-negative")

        super().__init__(data)
        self.normalize()

    def normalize(self) -> None:
        from .base_interval_discrete import BaseDiscreteInterval

        if not self.data:
            raise ValueError("Cannot normalize an empty IntervalPdf")
        for interval, weight in self.items():
            if isinstance(interval, BaseDiscreteInterval):
                raise TypeError("Discrete intervals require a probability-mass distribution")
            if not math.isfinite(interval.start) or not math.isfinite(interval.stop):
                raise ValueError("IntervalPdf bounds must be finite")
            if interval.get_length() <= 0:
                raise ValueError("IntervalPdf intervals must have positive length")
            if not math.isfinite(weight) or weight < 0:
                raise ValueError("IntervalPdf weights must be finite and non-negative")

        total = self.total_length(force=True)
        if not math.isfinite(total) or total <= 0:
            raise ValueError("IntervalPdf must have finite, positive weighted length")
        normalized = {interval: weight / total for interval, weight in self.items()}
        for interval, weight in normalized.items():
            self._weights()[interval] = weight

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

    def check_intervals(self) -> None:
        super().check_intervals()
        if self.total_length(force=True) != 1:
            self.normalize()

    def align_intervals(self) -> None:
        super().align_intervals()
        self.normalize()

    def cumulative(self, x: float) -> float:
        """Return the cumulative probability through coordinate ``x``."""
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
        """Return the coordinate at cumulative probability ``p``."""
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
        new_counter = self.__class__.__new__(self.__class__)
        IntervalMeter.__init__(new_counter)
        new_counter.data = self.data.copy()
        return new_counter
