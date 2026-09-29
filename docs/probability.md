# Probability distributions

`intervalues` provides two probability distribution types:

- `IntervalPdf` represents a continuous, piecewise-constant density over
  positive-length intervals.
- `IntervalPmf` represents point probabilities on discrete coordinates.

They are separate types because continuous density and discrete point mass
have different meanings and operations. Continuous interval endpoints are
treated as boundaries; open-versus-closed endpoint semantics are not
distinguished.

## Continuous distributions with `IntervalPdf`

Construct an `IntervalPdf` from a `BaseInterval` or a sequence of intervals.
Input interval values act as relative density weights; the resulting
distribution is normalized to total probability 1. Inputs must have finite
bounds, positive lengths, finite non-negative weights, and positive total
mass.

```python
import intervalues as iv

pdf = iv.IntervalPdf([
    iv.BaseInterval(0, 1, value=1),
    iv.BaseInterval(2, 4, value=2),
])
```

### Probability, density, and sampling

`cumulative(x)` returns the probability at or below `x`. It is zero below
support, one above support, and constant in gaps. `probability_between(a, b)`
returns mass in a range, clipped to the support; reversed bounds are invalid.
`density_at(x)` returns a density, not a point probability, and `survival(x)`
returns the probability of a value greater than `x`.

```python
pdf.cumulative(1.5)
pdf.probability_between(0.5, 3)
pdf.density_at(0.5)
pdf.survival(1.5)

import random

draws = pdf.sample(100, rng=random.Random(42))
```

Sampling accepts a non-negative integer count. Supplying a seeded
`random.Random` makes the result reproducible.

### Summaries and credible regions

The distribution provides exact piecewise-constant calculations for
`mean()`, `variance()`, and `standard_deviation()`. Use `quantile(p)` or
`median()` for quantiles, `credible_interval(level)` for an equal-tailed
interval, and `highest_density_region(mass)` for a potentially disjoint
highest-density region.

```python
pdf.mean()
pdf.standard_deviation()
pdf.median()
pdf.credible_interval(0.95)
pdf.highest_density_region(0.95)
```

### Mixtures and conditioning

`IntervalPdf.mixture(distributions, weights=...)` builds a weighted mixture.
Weights must be finite and non-negative, with at least one positive weight.
`condition(start, stop)` clips the PDF to a range and renormalizes it; an
empty or zero-probability range is invalid. Infinite conditioning bounds may
be used to clip only one side.

```python
other = iv.IntervalPdf(iv.BaseInterval(3, 5))
combined = iv.IntervalPdf.mixture([pdf, other], weights=[3, 1])
restricted = pdf.condition(0.5, 3)
```

### Comparing distributions

The following methods compare one `IntervalPdf` with another:

- `kolmogorov_distance(other)` and `wasserstein_distance(other)`
- `total_variation_distance(other)` and `overlap_coefficient(other)`
- `hellinger_distance(other)` and `jensen_shannon_divergence(other)`
- `kl_divergence(other)` for directed Kullback-Leibler divergence
- `quantile_difference(other, probabilities)`
- `first_order_stochastically_dominates(other, strict=False)`
- `comparison_segments(other)` for aligned density and CDF data suitable for
  plotting

The distances and divergences are calculated exactly over the aligned
piecewise-constant segments. `kl_divergence` returns infinity when `other` has
zero density on a positive-mass region of `self`.

```python
reference = iv.IntervalPdf(iv.BaseInterval(1, 3))
pdf.wasserstein_distance(reference)
pdf.quantile_difference(reference, [0.1, 0.5, 0.9])
```

## Discrete distributions with `IntervalPmf`

Convert a `BaseDiscreteInterval` to a PMF with `as_pmf()`, or construct an
`IntervalPmf` from one or more discrete intervals. Each point receives its
interval's value as relative mass; overlapping inputs add mass at matching
coordinates before normalization.

```python
points = iv.BaseDiscreteInterval(0, 4, step=2)
pmf = points.as_pmf()

pmf.mass_at(2)
pmf.cumulative(2)
pmf.inverse_cumulative(0.5)
pmf.sample(3, rng=random.Random(42))
```

PMF coordinates and weights must be finite, weights non-negative, and total
mass positive. `IntervalPdf` does not accept discrete intervals.

## Sample-based diagnostics

`empirical_cdf_distance(samples)` returns the one-sample Kolmogorov-Smirnov
(KS) distance as a descriptive statistic. `goodness_of_fit_test` returns that
statistic and a Monte Carlo p-value against this PDF. Its null model must be
fully specified independently of the observations. If parameters were
estimated from the tested samples, this method does not automatically refit
them in each simulation, so its p-value is not calibrated for that procedure.

`IntervalPdf.two_sample_ks_test(samples_a, samples_b)` returns the two-sample
KS statistic and a permutation p-value. The test assumes the pooled
observations are exchangeable under the null. Both tests default to 999
simulations/permutations, accept a seeded `random.Random` via `rng`, and use a
plus-one correction for the Monte Carlo p-value.

```python
pdf.empirical_cdf_distance([0.2, 0.5, 0.8])
pdf.goodness_of_fit_test([0.2, 0.5, 0.8], simulations=999, rng=random.Random(42))
iv.IntervalPdf.two_sample_ks_test(
    [0.2, 0.5, 0.8],
    [0.1, 0.6, 0.9],
    permutations=999,
    rng=random.Random(42),
)
```
