import math
import random
from random import Random
from types import MappingProxyType
from typing import Mapping, Optional, Sequence

from .base_interval_discrete import BaseDiscreteInterval


class IntervalPmf:
    """A normalized probability mass function over finite discrete points.

    Each point in an input ``BaseDiscreteInterval`` contributes its interval
    value as unnormalized mass. Overlapping inputs add mass at matching
    coordinates. This is distinct from ``IntervalPdf``, whose values are
    continuous densities over positive-length ranges.
    """

    def __init__(self, data: Sequence[BaseDiscreteInterval] | BaseDiscreteInterval):
        intervals: Sequence[BaseDiscreteInterval]
        if isinstance(data, BaseDiscreteInterval):
            intervals = (data,)
        elif isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
            intervals = tuple(data)
        else:
            raise TypeError("IntervalPmf requires discrete intervals")
        if not intervals:
            raise ValueError("IntervalPmf requires at least one discrete interval")

        masses: dict[float, float] = {}
        for interval in intervals:
            if not isinstance(interval, BaseDiscreteInterval):
                raise TypeError("IntervalPmf inputs must be BaseDiscreteInterval instances")
            if not math.isfinite(interval.start) or not math.isfinite(interval.stop):
                raise ValueError("Discrete PMF coordinates must be finite")
            if not math.isfinite(interval.value) or interval.value < 0:
                raise ValueError("Discrete PMF weights must be finite and non-negative")
            for coordinate, _ in interval:
                masses[coordinate] = masses.get(coordinate, 0.0) + interval.value
                if not math.isfinite(masses[coordinate]):
                    raise ValueError("Discrete PMF total mass must be finite")

        try:
            total = math.fsum(masses.values())
        except OverflowError as error:
            raise ValueError("IntervalPmf must have finite, positive total mass") from error
        if not math.isfinite(total) or total <= 0:
            raise ValueError("IntervalPmf must have finite, positive total mass")
        self._data = {coordinate: mass / total for coordinate, mass in masses.items() if mass > 0}

    @property
    def data(self) -> Mapping[float, float]:
        """Read-only mapping of discrete coordinates to normalized masses."""
        return MappingProxyType(self._data)

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self):
        return iter(sorted(self.data))

    def __getitem__(self, coordinate: float) -> float:
        return self.mass_at(coordinate)

    def __repr__(self) -> str:
        return f"IntervalPmf:{dict(sorted(self.data.items()))}"

    def items(self) -> list[tuple[float, float]]:
        return sorted(self.data.items())

    def mass_at(self, coordinate: float) -> float:
        """Return the probability mass at an exact discrete coordinate."""
        if isinstance(coordinate, bool) or not isinstance(coordinate, (int, float)):
            raise TypeError("coordinate must be a real number")
        if math.isnan(coordinate):
            raise ValueError("coordinate must not be NaN")
        return self.data.get(coordinate, 0.0)

    def total_mass(self) -> float:
        """Return the sum of point masses."""
        return math.fsum(self.data.values())

    def cumulative(self, coordinate: float) -> float:
        """Return the probability of a value less than or equal to coordinate."""
        if isinstance(coordinate, bool) or not isinstance(coordinate, (int, float)):
            raise TypeError("coordinate must be a real number")
        if math.isnan(coordinate):
            raise ValueError("coordinate must not be NaN")
        return math.fsum(mass for point, mass in self.data.items() if point <= coordinate)

    def inverse_cumulative(self, probability: float) -> float:
        """Return the smallest support point whose cumulative mass reaches p."""
        if isinstance(probability, bool) or not isinstance(probability, (int, float)):
            raise TypeError("probability must be a real number")
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("probability must be finite and in [0, 1]")
        points = self.items()
        if probability == 0:
            return points[0][0]
        cumulative = 0.0
        for point, mass in points:
            cumulative += mass
            if probability <= cumulative:
                return point
        return points[-1][0]

    def sample(self, k: int = 1, rng: Optional[Random] = None) -> list[float]:
        """Draw k points, optionally using a caller-provided seeded RNG."""
        if isinstance(k, bool) or not isinstance(k, int):
            raise TypeError("k must be a non-negative integer")
        if k < 0:
            raise ValueError("k must be a non-negative integer")
        if rng is not None and not isinstance(rng, Random):
            raise TypeError("rng must be an instance of random.Random")
        if rng is None:
            return [self.inverse_cumulative(random.random()) for _ in range(k)]
        return [self.inverse_cumulative(rng.random()) for _ in range(k)]
