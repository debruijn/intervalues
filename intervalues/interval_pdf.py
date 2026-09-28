import math
import random
from random import Random
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
        """Return the probability at or below ``x``.

        Values below the support return 0, values above it return 1, and
        probability does not accumulate while ``x`` is in a gap.
        """
        if math.isnan(x):
            raise ValueError("x must not be NaN")

        probability = 0.0
        for interval, density in sorted(self.items(), key=lambda item: item[0].start):
            if x <= interval.start:
                break
            probability += density * min(x - interval.start, interval.get_length())
            if x < interval.stop:
                break
        return min(max(probability, 0.0), 1.0)

    def cumsum(self, x: float) -> float:
        return self.cumulative(x)

    def inverse_cumulative(self, p: float) -> float:
        """Return the quantile at probability ``p``, which must be in [0, 1].

        At the endpoints, return the minimum or maximum coordinate of the
        support. At an exact cumulative boundary, return the end of the
        preceding positive-density interval.
        """
        if isinstance(p, bool) or not isinstance(p, (int, float)):
            raise TypeError("p must be a real number")
        if not math.isfinite(p) or not 0 <= p <= 1:
            raise ValueError("p must be finite and in [0, 1]")

        intervals = [
            (interval, density)
            for interval, density in sorted(self.items(), key=lambda item: item[0].start)
            if density > 0
        ]
        if p == 0:
            return intervals[0][0].start
        if p == 1:
            return intervals[-1][0].stop

        cumulative = 0.0
        for interval, density in intervals:
            interval_mass = density * interval.get_length()
            next_cumulative = cumulative + interval_mass
            if p <= next_cumulative:
                return interval.start + (p - cumulative) / density
            cumulative = next_cumulative

        return intervals[-1][0].stop

    def sample(self, k: int = 1, rng: Optional[Random] = None) -> list[float]:
        """Draw ``k`` samples, optionally using a caller-provided RNG.

        Passing a seeded ``random.Random`` instance makes the result
        reproducible. A count of zero returns an empty list.
        """
        if isinstance(k, bool) or not isinstance(k, int):
            raise TypeError("k must be a non-negative integer")
        if k < 0:
            raise ValueError("k must be a non-negative integer")
        if rng is not None and not isinstance(rng, Random):
            raise TypeError("rng must be an instance of random.Random")
        if rng is None:
            return [self.inverse_cumulative(random.random()) for _ in range(k)]
        return [self.inverse_cumulative(rng.random()) for _ in range(k)]

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
