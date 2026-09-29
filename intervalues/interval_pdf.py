import math
import random
from collections import Counter
from random import Random
from typing import Mapping, Optional, Sequence

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
    value from any subinterval in the IntervalPdf using the normalized value as density. Supported updates combine
    non-negative mass and renormalize. Adding two PDFs retains the existing equal-weight mixture behavior;
    ``mixture`` accepts explicit weights. Direct edits to the exposed ``data`` Counter bypass these guarantees.
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

    def clear(self) -> None:
        raise NotImplementedError("An IntervalPdf cannot be cleared; construct a new PDF instead")

    def set_data(self, data: Mapping['intervalues.BaseInterval', float]) -> None:
        old_data = self.data
        self.data = Counter(data)
        try:
            self.normalize()
        except (TypeError, ValueError):
            self.data = old_data
            raise

    def pop(self, __key: 'intervalues.BaseInterval') -> float:
        if __key not in self.data:
            raise KeyError(__key)
        self._ensure_removal_preserves_mass(__key)
        item = self.data.pop(__key)
        self.normalize()
        return float(item)

    def popitem(self) -> tuple['intervalues.BaseInterval', float]:
        if not self.data:
            raise KeyError("popitem(): dictionary is empty")
        key = next(reversed(self.data))
        self._ensure_removal_preserves_mass(key)
        item = self.data.popitem()
        self.normalize()
        return item[0], float(item[1])

    def _ensure_removal_preserves_mass(self, removed: 'intervalues.BaseInterval') -> None:
        remaining_mass = math.fsum(
            interval.get_length() * weight
            for interval, weight in self.items()
            if interval != removed
        )
        if not math.isfinite(remaining_mass) or remaining_mass <= 0:
            raise ValueError("Removing this interval would leave an empty or zero-mass IntervalPdf")

    def setdefault(self, key, default=None):
        raise NotImplementedError("setdefault is not supported for IntervalPdf; use update instead")

    def update(self, other: object, times: float = 1) -> None:
        self._validate_update_times(times)
        meter = self._as_valid_meter(other)
        IntervalMeter.update_meter(self, meter, times=times)
        self.normalize()

    def update_meter(self, other: IntervalMeter, times: float = 1, one_by_one: bool = False) -> None:
        self._validate_update_times(times)
        meter = self._as_valid_meter(other)
        IntervalMeter.update_meter(self, meter, times=times, one_by_one=False)
        self.normalize()

    def update_interval(self, other: 'intervalues.BaseInterval', times: float = 1) -> None:
        self._validate_update_times(times)
        meter = self._as_valid_meter(other)
        IntervalMeter.update_meter(self, meter, times=times)
        self.normalize()

    def _validate_update_times(self, times: float) -> None:
        if isinstance(times, bool) or not isinstance(times, (int, float)):
            raise TypeError("PDF update weight must be a real number")
        if not math.isfinite(times) or times < 0:
            raise ValueError("PDF update weight must be finite and non-negative")

    def _as_valid_meter(self, other: object) -> IntervalMeter:
        if isinstance(other, intervalues.BaseInterval):
            meter = IntervalMeter(other)
        elif isinstance(other, IntervalMeter):
            meter = other.as_meter()
        elif isinstance(other, intervalues.AbstractInterval):
            meter = other.as_meter()
        else:
            raise TypeError("PDF updates require an interval or interval collection")

        from .base_interval_discrete import BaseDiscreteInterval

        for interval, weight in meter.items():
            if (
                isinstance(interval, BaseDiscreteInterval)
                or not math.isfinite(interval.start)
                or not math.isfinite(interval.stop)
                or interval.get_length() <= 0
                or not math.isfinite(weight)
                or weight < 0
            ):
                raise ValueError("PDF updates require finite, non-negative continuous weights")
        return meter

    def subtract(self, other: object) -> None:
        raise NotImplementedError("Subtraction is not defined for probability distributions")

    def __sub__(self, other: object) -> 'IntervalPdf':
        raise NotImplementedError("Subtraction is not defined for probability distributions")

    def __isub__(self, other: object) -> 'IntervalPdf':
        raise NotImplementedError("Subtraction is not defined for probability distributions")

    def __neg__(self) -> 'IntervalPdf':
        raise NotImplementedError("Negation is not defined for probability distributions")

    def total_length(self, force: bool = False) -> float:
        if not force:
            return 1
        return super().total_length()

    def __mul__(self, other: float) -> 'IntervalPdf':
        self._validate_pdf_scale(other)
        return self.copy()

    def __imul__(self, other: float) -> 'IntervalPdf':
        self._validate_pdf_scale(other)
        return self

    def _validate_pdf_scale(self, other: float) -> None:
        if isinstance(other, bool) or not isinstance(other, (int, float)):
            raise TypeError("PDF scale must be a real number")
        if not math.isfinite(other) or other <= 0:
            raise ValueError("PDF scale must be finite and positive")

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
        probability does not accumulate while ``x`` is in a gap. This is the
        cumulative distribution function; point lookup returns density instead.
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

    def probability_between(self, start: float, stop: float) -> float:
        """Return the probability mass in the coordinate range [start, stop].

        The range is clipped to the distribution's support. Reversed bounds
        raise ``ValueError``; equal bounds have zero probability.
        """
        if math.isnan(start) or math.isnan(stop):
            raise ValueError("range bounds must not be NaN")
        if stop < start:
            raise ValueError("stop must be greater than or equal to start")
        if stop == start:
            return 0.0
        return self.cumulative(stop) - self.cumulative(start)

    def density_at(self, x: float) -> float:
        """Return the probability density at coordinate ``x``, not point mass.

        At a shared segment boundary, use the density of the segment to the
        right. The rightmost support endpoint uses the final segment's density.
        """
        if math.isnan(x):
            raise ValueError("x must not be NaN")

        intervals = sorted(self.items(), key=lambda item: item[0].start)
        for interval, density in intervals:
            if interval.start <= x < interval.stop:
                return density
        if intervals and x == intervals[-1][0].stop:
            return intervals[-1][1]
        return 0.0

    def survival(self, x: float) -> float:
        """Return the probability of a value greater than ``x``."""
        return 1.0 - self.cumulative(x)

    def mean(self) -> float:
        """Return the expected coordinate under this distribution."""
        return math.fsum(
            density * interval.get_length() * (interval.start + interval.stop) / 2
            for interval, density in self.items()
        )

    def variance(self) -> float:
        """Return the variance under this distribution."""
        mean = self.mean()
        return math.fsum(
            density * interval.get_length() * (
                ((interval.start + interval.stop) / 2 - mean) ** 2
                + interval.get_length() ** 2 / 12
            )
            for interval, density in self.items()
        )

    def standard_deviation(self) -> float:
        """Return the standard deviation under this distribution."""
        return math.sqrt(self.variance())

    def cumsum(self, x: float) -> float:
        return self.cumulative(x)

    def quantile(self, p: float) -> float:
        """Return the coordinate at cumulative probability ``p``."""
        return self.inverse_cumulative(p)

    def median(self) -> float:
        """Return the median coordinate."""
        return self.quantile(0.5)

    def credible_interval(self, level: float = 0.95) -> tuple[float, float]:
        """Return the equal-tailed interval containing ``level`` probability.

        ``level`` must be finite and strictly between zero and one.
        """
        if isinstance(level, bool) or not isinstance(level, (int, float)):
            raise TypeError("level must be a real number")
        if not math.isfinite(level) or not 0 < level < 1:
            raise ValueError("level must be finite and in (0, 1)")
        tail_probability = (1 - level) / 2
        return self.quantile(tail_probability), self.quantile(1 - tail_probability)

    def highest_density_region(self, mass: float = 0.95) -> 'intervalues.IntervalSet':
        """Return a highest-density region containing exactly ``mass`` probability.

        Higher-density segments are included first. If the target cuts through
        a density tie, a centered portion of the leftmost tied segment is
        selected, making the result deterministic. The returned set may have
        multiple disjoint regions.
        """
        if isinstance(mass, bool) or not isinstance(mass, (int, float)):
            raise TypeError("mass must be a real number")
        if not math.isfinite(mass) or not 0 < mass <= 1:
            raise ValueError("mass must be finite and in (0, 1]")

        segments = sorted(
            ((interval, density) for interval, density in self.items() if density > 0),
            key=lambda item: (-item[1], item[0].start),
        )
        remaining_mass = mass
        selected: list[intervalues.BaseInterval] = []
        for interval, density in segments:
            segment_mass = density * interval.get_length()
            if remaining_mass >= segment_mass or math.isclose(
                remaining_mass, segment_mass, rel_tol=1e-12, abs_tol=1e-15
            ):
                selected.append(interval)
                remaining_mass = max(0.0, remaining_mass - segment_mass)
                if remaining_mass == 0:
                    break
                continue

            selected_length = remaining_mass / density
            margin = (interval.get_length() - selected_length) / 2
            selected.append(
                intervalues.BaseInterval(
                    interval.start + margin,
                    interval.stop - margin,
                )
            )
            break

        return intervalues.IntervalSet(selected)

    @classmethod
    def mixture(
        cls,
        distributions: Sequence['IntervalPdf'],
        weights: Optional[Sequence[float]] = None,
    ) -> 'IntervalPdf':
        """Return a mixture of PDFs with optional non-negative mixture weights.

        Each input PDF is normalized before its density is scaled by the
        corresponding weight. Weights are normalized by the resulting PDF
        construction, so their absolute scale does not matter.
        """
        distributions = tuple(distributions)
        if not distributions:
            raise ValueError("At least one PDF is required for a mixture")
        if any(not isinstance(pdf, IntervalPdf) for pdf in distributions):
            raise TypeError("All mixture components must be IntervalPdf instances")

        if weights is None:
            mixture_weights = (1.0,) * len(distributions)
        else:
            mixture_weights = tuple(weights)
            if len(mixture_weights) != len(distributions):
                raise ValueError("The number of weights must match the number of PDFs")
            for weight in mixture_weights:
                if isinstance(weight, bool) or not isinstance(weight, (int, float)):
                    raise TypeError("Mixture weights must be real numbers")
                if not math.isfinite(weight) or weight < 0:
                    raise ValueError("Mixture weights must be finite and non-negative")

        if not any(weight > 0 for weight in mixture_weights):
            raise ValueError("At least one mixture weight must be positive")

        weighted_intervals = [
            interval * weight
            for pdf, weight in zip(distributions, mixture_weights)
            if weight > 0
            for interval in pdf
        ]
        return cls(weighted_intervals)

    def condition(self, start: float, stop: float) -> 'IntervalPdf':
        """Return the distribution conditioned to lie within [start, stop].

        Bounds may be infinite to clip only one side. NaN or reversed bounds
        are invalid, and conditioning on a zero-probability range raises
        ``ValueError``.
        """
        if isinstance(start, bool) or not isinstance(start, (int, float)):
            raise TypeError("range bounds must be real numbers")
        if isinstance(stop, bool) or not isinstance(stop, (int, float)):
            raise TypeError("range bounds must be real numbers")
        if math.isnan(start) or math.isnan(stop):
            raise ValueError("range bounds must not be NaN")
        if stop < start:
            raise ValueError("stop must be greater than or equal to start")
        if stop == start:
            raise ValueError("Cannot condition an IntervalPdf on a zero-probability range")

        clipped = []
        for interval, density in self.items():
            clipped_start = max(interval.start, start)
            clipped_stop = min(interval.stop, stop)
            if clipped_start < clipped_stop and density > 0:
                clipped.append(intervalues.BaseInterval(clipped_start, clipped_stop, density))
        if not clipped:
            raise ValueError("Cannot condition an IntervalPdf on a zero-probability range")
        return self.__class__(clipped)

    def _comparison_segments(
        self,
        other: 'IntervalPdf',
    ) -> list[tuple[float, float, float, float]]:
        if not isinstance(other, IntervalPdf):
            raise TypeError("Distribution comparisons require another IntervalPdf")
        breakpoints = sorted({
            point
            for pdf in (self, other)
            for interval in pdf.keys()
            for point in (interval.start, interval.stop)
        })
        segments = []
        for start, stop in zip(breakpoints, breakpoints[1:]):
            if start == stop:
                continue
            midpoint = start + (stop - start) / 2
            density_a = math.fsum(
                density for interval, density in self.items()
                if interval.start <= midpoint < interval.stop
            )
            density_b = math.fsum(
                density for interval, density in other.items()
                if interval.start <= midpoint < interval.stop
            )
            segments.append((start, stop, density_a, density_b))
        return segments

    @staticmethod
    def _validate_probabilities(probabilities: Sequence[float]) -> tuple[float, ...]:
        values = tuple(probabilities)
        for probability in values:
            if isinstance(probability, bool) or not isinstance(probability, (int, float)):
                raise TypeError("Probabilities must be real numbers")
            if not math.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError("Probabilities must be finite and in [0, 1]")
        return values

    def quantile_difference(
        self,
        other: 'IntervalPdf',
        probabilities: Sequence[float],
    ) -> list[tuple[float, float]]:
        """Return pairs of quantile differences ``(p, self_Q(p) - other_Q(p))``."""
        self._comparison_segments(other)
        return [
            (probability, self.quantile(probability) - other.quantile(probability))
            for probability in self._validate_probabilities(probabilities)
        ]

    def first_order_stochastically_dominates(
        self,
        other: 'IntervalPdf',
        *,
        strict: bool = False,
    ) -> bool:
        """Return whether this distribution is no larger than ``other``.

        For this method, X <=st Y means F_X(x) >= F_Y(x) at every coordinate.
        If ``strict`` is true, at least one coordinate must have strict
        dominance. Consequently, true indicates values from ``self`` tend to
        be no larger than values from ``other``.
        """
        self._comparison_segments(other)
        points = sorted({
            point
            for pdf in (self, other)
            for interval in pdf.keys()
            for point in (interval.start, interval.stop)
        })
        differences = [self.cumulative(point) - other.cumulative(point) for point in points]
        dominates = all(difference >= -1e-12 for difference in differences)
        return dominates and (not strict or any(difference > 1e-12 for difference in differences))

    def comparison_segments(
        self,
        other: 'IntervalPdf',
    ) -> list[tuple[float, float, float, float, float, float]]:
        """Return aligned support segments for plotting or inspection.

        Each tuple contains ``(start, stop, density_self, density_other,
        cdf_self_at_start, cdf_other_at_start)``. Coordinates outside both
        supports are omitted; gaps inside the combined support are included.
        """
        return [
            (
                start,
                stop,
                density_a,
                density_b,
                self.cumulative(start),
                other.cumulative(start),
            )
            for start, stop, density_a, density_b in self._comparison_segments(other)
        ]

    def kolmogorov_distance(self, other: 'IntervalPdf') -> float:
        """Return the maximum absolute difference between the two CDFs."""
        self._comparison_segments(other)
        breakpoints = {
            point
            for pdf in (self, other)
            for interval in pdf.keys()
            for point in (interval.start, interval.stop)
        }
        return max(
            (abs(self.cumulative(point) - other.cumulative(point)) for point in breakpoints),
            default=0.0,
        )

    def wasserstein_distance(self, other: 'IntervalPdf') -> float:
        """Return the exact one-dimensional Wasserstein-1 distance."""
        segments = self._comparison_segments(other)
        areas = []
        for start, stop, _, _ in segments:
            left_difference = self.cumulative(start) - other.cumulative(start)
            right_difference = self.cumulative(stop) - other.cumulative(stop)
            width = stop - start
            left_abs = abs(left_difference)
            right_abs = abs(right_difference)
            if left_difference * right_difference < 0:
                areas.append(width * (left_abs**2 + right_abs**2) / (2 * (left_abs + right_abs)))
            else:
                areas.append(width * (left_abs + right_abs) / 2)
        return math.fsum(areas)

    def total_variation_distance(self, other: 'IntervalPdf') -> float:
        """Return one half of the integrated absolute density difference."""
        return 0.5 * math.fsum(
            (stop - start) * abs(density_a - density_b)
            for start, stop, density_a, density_b in self._comparison_segments(other)
        )

    def overlap_coefficient(self, other: 'IntervalPdf') -> float:
        """Return the integral of the pointwise minimum of the two densities."""
        return math.fsum(
            (stop - start) * min(density_a, density_b)
            for start, stop, density_a, density_b in self._comparison_segments(other)
        )

    def hellinger_distance(self, other: 'IntervalPdf') -> float:
        """Return the Hellinger distance using the conventional [0, 1] scale."""
        squared_distance = 0.5 * math.fsum(
            (stop - start) * (math.sqrt(density_a) - math.sqrt(density_b)) ** 2
            for start, stop, density_a, density_b in self._comparison_segments(other)
        )
        return math.sqrt(max(0.0, squared_distance))

    def jensen_shannon_divergence(self, other: 'IntervalPdf') -> float:
        """Return the symmetric Jensen-Shannon divergence in natural-log units."""
        terms = []
        for start, stop, density_a, density_b in self._comparison_segments(other):
            midpoint = (density_a + density_b) / 2
            if density_a > 0:
                terms.append(0.5 * (stop - start) * density_a * math.log(density_a / midpoint))
            if density_b > 0:
                terms.append(0.5 * (stop - start) * density_b * math.log(density_b / midpoint))
        return max(0.0, math.fsum(terms))

    def kl_divergence(self, other: 'IntervalPdf') -> float:
        """Return D_KL(self || other), or infinity if other has zero density.

        The divergence uses natural logarithms and is infinite when the
        reference PDF is zero on any positive-mass part of this PDF.
        """
        terms = []
        for start, stop, density_a, density_b in self._comparison_segments(other):
            if density_a == 0:
                continue
            if density_b == 0:
                return math.inf
            terms.append((stop - start) * density_a * math.log(density_a / density_b))
        return max(0.0, math.fsum(terms))

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
