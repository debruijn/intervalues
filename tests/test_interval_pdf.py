import math
import random

from intervalues import (
    BaseDiscreteInterval,
    BaseInterval,
    IntervalCounter,
    IntervalList,
    IntervalMeter,
    IntervalPdf,
    IntervalSet,
)
import pytest


@pytest.mark.parametrize(
    "data, error",
    [
        (None, ValueError),
        ([], ValueError),
        ([BaseInterval(0, 1, value=-1)], ValueError),
        ([BaseInterval(0, 1, value=float("nan"))], ValueError),
        ([BaseInterval(0, 1, value=float("inf"))], ValueError),
        ([BaseInterval(0, 0)], ValueError),
        ([BaseInterval(0, 1e308, value=2)], ValueError),
        ([BaseInterval(0, 1), BaseInterval(2, 3, value=-1)], ValueError),
        ([BaseDiscreteInterval(0, 2)], TypeError),
    ],
)
def test_invalid_pdf_inputs(data, error):
    with pytest.raises(error):
        IntervalPdf(data)


def test_normalize_rejects_invalid_density_without_mutating_it():
    pdf = IntervalPdf(BaseInterval(0, 1))
    interval = next(iter(pdf.keys()))
    pdf.data[interval] = -1

    with pytest.raises(ValueError, match="finite and non-negative"):
        pdf.normalize()

    assert pdf.data[interval] == -1


def test_normalize_rejects_zero_mass():
    pdf = IntervalPdf(BaseInterval(0, 1))
    pdf.data.clear()

    with pytest.raises(ValueError, match="empty"):
        pdf.normalize()


def test_total_length():
    a = IntervalPdf([BaseInterval(0, 1), BaseInterval(2, 3)])
    assert a.total_length() == 1
    assert a.total_length(force=True) == 1

    a.data[BaseInterval(0, 1)] = 3
    assert a.total_length() == 1
    assert a.total_length(force=True) > 1


def test_normalize():
    a = IntervalPdf(BaseInterval(0, 1))
    a.data[BaseInterval(0, 1)] = 3
    a.normalize()
    assert a.total_length(force=True) == 1


def test_normalize_init():
    a = IntervalPdf([BaseInterval(0, 1)])
    b = IntervalPdf([BaseInterval(0, 1, 2)])
    assert a == b


def test_normalize_pop():
    a = IntervalPdf([BaseInterval(0, 1), BaseInterval(2, 3)])
    assert a.total_length(force=True) == 1
    a.popitem()
    assert a.total_length(force=True) == 1

    a = IntervalPdf([BaseInterval(0, 1), BaseInterval(2, 3)])
    a.pop(BaseInterval(2, 3))
    assert a.total_length(force=True) == 1


def test_addition_base():
    a = IntervalPdf([BaseInterval((0, 1))])
    b = BaseInterval((2, 3))
    c = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_base_value():
    a = IntervalPdf([BaseInterval((0, 1))])
    b = BaseInterval((2, 3, 2))
    c = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_pdf():
    a = IntervalPdf([BaseInterval((0, 1))])
    b = IntervalPdf([BaseInterval((2, 3))])
    c = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_overlap():
    a = IntervalPdf([BaseInterval((0, 2))])
    b = IntervalPdf([BaseInterval((1, 3))])
    c = IntervalPdf([BaseInterval((0, 1)), BaseInterval((1, 2)) * 2, BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_subtraction_and_negation_are_not_supported():
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(NotImplementedError, match="Subtraction"):
        pdf - BaseInterval(0, 1)
    with pytest.raises(NotImplementedError, match="Subtraction"):
        pdf -= BaseInterval(0, 1)
    with pytest.raises(NotImplementedError, match="Negation"):
        -pdf


@pytest.mark.parametrize("mult", (2, 0.5))
def test_multiplication(mult):
    a = IntervalPdf([BaseInterval((0, 2))]) * mult
    b = IntervalPdf([BaseInterval((0, 2))])
    assert a == b
    a *= mult
    assert a == b*mult


@pytest.mark.parametrize("mult", (0, -2, float("inf"), float("nan")))
def test_multiplication_rejects_invalid_scale(mult):
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(ValueError, match="finite and positive"):
        pdf * mult
    with pytest.raises(ValueError, match="finite and positive"):
        pdf *= mult


def test_update_is_a_normalized_nonnegative_mixture():
    pdf = IntervalPdf(BaseInterval(0, 1))

    pdf.update(BaseInterval(2, 3))

    assert pdf.total_length(force=True) == pytest.approx(1)
    assert pdf.probability_between(0, 1) == pytest.approx(0.5)
    assert pdf.probability_between(2, 3) == pytest.approx(0.5)


def test_weighted_mixture_with_disjoint_pdfs():
    left = IntervalPdf(BaseInterval(0, 1))
    right = IntervalPdf(BaseInterval(2, 4))

    pdf = IntervalPdf.mixture([left, right], weights=[3, 1])

    assert pdf.probability_between(0, 1) == pytest.approx(0.75)
    assert pdf.probability_between(2, 4) == pytest.approx(0.25)
    assert pdf.total_length(force=True) == pytest.approx(1)


def test_weighted_mixture_with_overlapping_pdfs():
    left = IntervalPdf(BaseInterval(0, 2))
    right = IntervalPdf(BaseInterval(1, 3))

    pdf = IntervalPdf.mixture([left, right], weights=[3, 1])

    assert pdf.probability_between(0, 1) == pytest.approx(0.375)
    assert pdf.probability_between(1, 2) == pytest.approx(0.5)
    assert pdf.probability_between(2, 3) == pytest.approx(0.125)


def test_default_pdf_mixture_is_equal_weight_and_supports_zero_weights():
    left = IntervalPdf(BaseInterval(0, 1))
    right = IntervalPdf(BaseInterval(2, 3))

    equal_mix = IntervalPdf.mixture([left, right])
    zero_weight_mix = IntervalPdf.mixture([left, right], weights=[1, 0])

    assert equal_mix.probability_between(0, 1) == pytest.approx(0.5)
    assert equal_mix.probability_between(2, 3) == pytest.approx(0.5)
    assert zero_weight_mix == left


@pytest.mark.parametrize(
    "distributions, weights, error",
    [
        ([], None, ValueError),
        ([IntervalPdf(BaseInterval(0, 1))], [], ValueError),
        ([IntervalPdf(BaseInterval(0, 1))], [0], ValueError),
        ([IntervalPdf(BaseInterval(0, 1))], [-1], ValueError),
        ([IntervalPdf(BaseInterval(0, 1))], [float("inf")], ValueError),
        ([IntervalPdf(BaseInterval(0, 1))], [float("nan")], ValueError),
        ([IntervalPdf(BaseInterval(0, 1))], [True], TypeError),
        ([IntervalPdf(BaseInterval(0, 1)), IntervalPdf(BaseInterval(1, 2))], [1], ValueError),
        ([BaseInterval(0, 1)], None, TypeError),
    ],
)
def test_mixture_rejects_invalid_components_or_weights(distributions, weights, error):
    with pytest.raises(error):
        IntervalPdf.mixture(distributions, weights)


def test_condition_clips_and_renormalizes_across_segments_and_gaps():
    pdf = IntervalPdf([BaseInterval(0, 2), BaseInterval(4, 6, value=2)])

    conditioned = pdf.condition(1, 5)

    assert conditioned.probability_between(1, 2) == pytest.approx(1 / 3)
    assert conditioned.probability_between(2, 4) == pytest.approx(0)
    assert conditioned.probability_between(4, 5) == pytest.approx(2 / 3)
    assert conditioned.total_length(force=True) == pytest.approx(1)


def test_condition_allows_infinite_bounds():
    pdf = IntervalPdf([BaseInterval(0, 1), BaseInterval(2, 3)])

    assert pdf.condition(float("-inf"), 1) == IntervalPdf(BaseInterval(0, 1))
    assert pdf.condition(2, float("inf")) == IntervalPdf(BaseInterval(2, 3))


@pytest.mark.parametrize(
    "start, stop",
    [
        (2, 1),
        (1, 1),
        (float("nan"), 2),
        (0, float("nan")),
        (3, 4),
    ],
)
def test_condition_rejects_invalid_or_zero_probability_ranges(start, stop):
    pdf = IntervalPdf([BaseInterval(0, 1), BaseInterval(2, 3)])

    with pytest.raises(ValueError, match="stop|range|zero-probability"):
        pdf.condition(start, stop)


def test_condition_rejects_non_real_bounds():
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(TypeError, match="real numbers"):
        pdf.condition(True, 1)


def test_distribution_distances_identical_and_disjoint_uniform_pdfs():
    uniform = IntervalPdf(BaseInterval(0, 1))
    identical = IntervalPdf(BaseInterval(0, 1, value=4))
    disjoint = IntervalPdf(BaseInterval(1, 2))

    assert uniform.kolmogorov_distance(identical) == pytest.approx(0)
    assert uniform.wasserstein_distance(identical) == pytest.approx(0)
    assert uniform.total_variation_distance(identical) == pytest.approx(0)
    assert uniform.overlap_coefficient(identical) == pytest.approx(1)
    assert uniform.hellinger_distance(identical) == pytest.approx(0)
    assert uniform.jensen_shannon_divergence(identical) == pytest.approx(0)
    assert uniform.kl_divergence(identical) == pytest.approx(0)

    assert uniform.kolmogorov_distance(disjoint) == pytest.approx(1)
    assert uniform.wasserstein_distance(disjoint) == pytest.approx(1)
    assert uniform.total_variation_distance(disjoint) == pytest.approx(1)
    assert uniform.overlap_coefficient(disjoint) == pytest.approx(0)
    assert uniform.hellinger_distance(disjoint) == pytest.approx(1)
    assert uniform.jensen_shannon_divergence(disjoint) == pytest.approx(math.log(2))
    assert uniform.kl_divergence(disjoint) == math.inf
    assert disjoint.kl_divergence(uniform) == math.inf


def test_distribution_distances_for_partially_overlapping_uniform_pdfs():
    left = IntervalPdf(BaseInterval(0, 2))
    right = IntervalPdf(BaseInterval(1, 3))

    assert left.kolmogorov_distance(right) == pytest.approx(0.5)
    assert left.wasserstein_distance(right) == pytest.approx(1)
    assert left.total_variation_distance(right) == pytest.approx(0.5)
    assert left.overlap_coefficient(right) == pytest.approx(0.5)
    assert left.hellinger_distance(right) == pytest.approx(math.sqrt(0.5))
    assert left.jensen_shannon_divergence(right) == pytest.approx(math.log(2) / 2)
    assert left.kl_divergence(right) == math.inf


def test_kl_divergence_is_finite_when_density_supports_match():
    first = IntervalPdf(BaseInterval(0, 2))
    second = IntervalPdf([BaseInterval(0, 1, value=2), BaseInterval(1, 2)])

    assert first.kl_divergence(second) == pytest.approx(0.5 * math.log(1.125))
    assert second.kl_divergence(first) == pytest.approx(
        (2 / 3) * math.log(4 / 3) + (1 / 3) * math.log(2 / 3)
    )


def test_distribution_comparison_requires_another_pdf():
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(TypeError, match="another IntervalPdf"):
        pdf.total_variation_distance(BaseInterval(0, 1))


@pytest.mark.parametrize("times", [-1, float("inf"), float("nan")])
def test_update_rejects_invalid_mixture_weight(times):
    pdf = IntervalPdf(BaseInterval(0, 1))
    original = pdf.copy()

    with pytest.raises(ValueError, match="finite and non-negative"):
        pdf.update(BaseInterval(2, 3), times=times)

    assert pdf == original


def test_clear_and_setdefault_are_not_supported():
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(NotImplementedError, match="cannot be cleared"):
        pdf.clear()
    with pytest.raises(NotImplementedError, match="setdefault"):
        pdf.setdefault(BaseInterval(2, 3), 1)
    assert pdf.total_length(force=True) == pytest.approx(1)


def test_pop_cannot_remove_last_positive_mass():
    pdf = IntervalPdf(BaseInterval(0, 1))
    interval = next(iter(pdf.keys()))

    with pytest.raises(ValueError, match="zero-mass"):
        pdf.pop(interval)

    assert pdf.total_length(force=True) == pytest.approx(1)
    assert interval in pdf.data


def test_set_data_normalizes_and_rolls_back_invalid_data():
    pdf = IntervalPdf(BaseInterval(0, 1))
    interval = next(iter(pdf.keys()))
    pdf.set_data({interval: 2.0})
    assert pdf.data[interval] == pytest.approx(1)

    with pytest.raises(ValueError, match="non-negative"):
        pdf.set_data({interval: -1.0})
    assert pdf.data[interval] == pytest.approx(1)


def test_equality_different_order():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = IntervalPdf([BaseInterval((2, 3)), BaseInterval((0, 1))])
    assert a == b


def test_find_which_contains():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((1, 3)) * 2])
    assert [a.find_which_contains(x) for x in [1, 2]] == list(a.keys())


def test_contains():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert BaseInterval((0, 1)) in a
    assert BaseInterval((1, 3, 2)) in a
    assert 1 in a
    assert 2 in a
    assert 5.0 not in a


def test_contains_as_superset():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert BaseInterval((1, 2, 2)) in a
    assert BaseInterval((1.5, 2.5)) in a


def test_get_item():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert a[BaseInterval((0, 1))] == 0.2
    assert a[BaseInterval((1, 3))] == 0.4
    assert a[BaseInterval((1, 3, 2))] == 0.2
    assert a[1] == 0.2
    assert a[2] == 0.4
    assert a[5.0] == 0


def test_get_item_as_superset():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert a[BaseInterval((1.5, 2.5))] == 0.4
    assert a[BaseInterval((0, 0.5, 2))] == 0.1


def split_to_pairs(iterable):
    a = iter(iterable)
    return zip(a, a)


def test_min_max():
    a = IntervalPdf([BaseInterval((0, 4))])
    b = IntervalPdf([BaseInterval((0, 4)), BaseInterval((2, 3))])

    assert a.min() == 0
    assert b.min() == 0
    assert a.max() == 4
    assert b.max() == 4


def test_single_interval():
    a = IntervalPdf([BaseInterval((0, 1))])
    b = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])

    assert a.as_single_interval() == BaseInterval(0, 1)
    assert b.as_single_interval() == BaseInterval(0, 3)


def test_as_set():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_set()
    c = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert b == c


def test_as_set_value():
    a = IntervalPdf([BaseInterval((0, 1, 2)), BaseInterval((2, 3, 3))])
    b = a.as_set()
    c = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert b == c


def test_as_list():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_list()
    c = IntervalList([BaseInterval((0, 1, 0.5)), BaseInterval((2, 3, 0.5))])
    assert b == c


def test_as_list_value():
    a = IntervalPdf([BaseInterval((0, 1, 2)), BaseInterval((2, 3, 3))])
    b = a.as_list()
    c = IntervalList([BaseInterval((0, 1, 0.4)), BaseInterval((2, 3, 0.6))])
    assert b == c


def test_as_counter():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_counter()
    c = IntervalCounter()
    assert b == c


def test_as_meter():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_meter()
    c = IntervalMeter([BaseInterval((0, 1, 0.5)), BaseInterval((2, 3, 0.5))])
    assert b == c


def test_cumulative():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3, 2)), BaseInterval((3, 4))])
    assert a.cumulative(0) == 0
    assert a.cumulative(1) == 0.25
    assert a.cumulative(2) == 0.25
    assert a.cumulative(2.5) == 0.5
    assert a.cumulative(3) == 0.75
    assert a.cumulative(4) == 1


def test_cumulative_outside_support_and_inside_gaps():
    pdf = IntervalPdf([BaseInterval(1, 2), BaseInterval(4, 6, value=2)])

    assert pdf.cumulative(float("-inf")) == 0
    assert pdf.cumulative(0) == 0
    assert pdf.cumulative(2) == pytest.approx(0.2)
    assert pdf.cumulative(3) == pytest.approx(0.2)
    assert pdf.cumulative(4) == pytest.approx(0.2)
    assert pdf.cumulative(6) == 1
    assert pdf.cumulative(7) == 1
    assert pdf.cumulative(float("inf")) == 1


def test_cumulative_rejects_nan():
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(ValueError, match="NaN"):
        pdf.cumulative(float("nan"))


def test_probability_between_support_gaps_and_ranges():
    pdf = IntervalPdf([BaseInterval(1, 2), BaseInterval(4, 6, value=2)])

    assert pdf.probability_between(1, 2) == pytest.approx(0.2)
    assert pdf.probability_between(2, 4) == pytest.approx(0)
    assert pdf.probability_between(1.5, 5) == pytest.approx(0.5)
    assert pdf.probability_between(-1, 10) == pytest.approx(1)
    assert pdf.probability_between(float("-inf"), float("inf")) == pytest.approx(1)
    assert pdf.probability_between(3, 3) == 0


def test_probability_between_rejects_reversed_bounds_and_nan():
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(ValueError, match="stop must be greater"):
        pdf.probability_between(1, 0)
    with pytest.raises(ValueError, match="NaN"):
        pdf.probability_between(float("nan"), 1)
    with pytest.raises(ValueError, match="NaN"):
        pdf.probability_between(0, float("nan"))


def test_density_at_support_gaps_and_boundaries():
    pdf = IntervalPdf([
        BaseInterval(0, 1, value=1),
        BaseInterval(1, 2, value=2),
        BaseInterval(3, 4, value=1),
    ])

    assert pdf.density_at(-1) == 0
    assert pdf.density_at(0) == pytest.approx(0.25)
    assert pdf.density_at(1) == pytest.approx(0.5)
    assert pdf.density_at(2) == 0
    assert pdf.density_at(2.5) == 0
    assert pdf.density_at(3) == pytest.approx(0.25)
    assert pdf.density_at(4) == pytest.approx(0.25)
    assert pdf.density_at(5) == 0


def test_density_and_survival_reject_nan():
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(ValueError, match="NaN"):
        pdf.density_at(float("nan"))
    with pytest.raises(ValueError, match="NaN"):
        pdf.survival(float("nan"))


def test_survival_is_complement_of_cdf():
    pdf = IntervalPdf([BaseInterval(0, 1), BaseInterval(2, 3, value=2)])

    assert pdf.survival(-1) == 1
    assert pdf.survival(0.5) == pytest.approx(5 / 6)
    assert pdf.survival(1.5) == pytest.approx(2 / 3)
    assert pdf.survival(3) == 0


def test_distribution_summaries_for_uniform_pdf():
    pdf = IntervalPdf(BaseInterval(2, 6))

    assert pdf.mean() == 4
    assert pdf.variance() == pytest.approx(4 / 3)
    assert pdf.standard_deviation() == pytest.approx((4 / 3) ** 0.5)
    assert pdf.quantile(0.25) == 3
    assert pdf.median() == 4
    assert pdf.credible_interval(0.5) == (3, 5)


def test_distribution_summaries_for_weighted_gapped_pdf():
    pdf = IntervalPdf([BaseInterval(0, 1), BaseInterval(2, 4, value=2)])

    assert pdf.mean() == pytest.approx(2.5)
    assert pdf.variance() == pytest.approx(77 / 60)
    assert pdf.standard_deviation() == pytest.approx((77 / 60) ** 0.5)
    assert pdf.quantile(0.6) == pytest.approx(3)
    assert pdf.median() == pytest.approx(2.75)
    assert pdf.credible_interval(0.8) == pytest.approx((0.5, 3.75))


def test_highest_density_region_for_uniform_pdf_is_one_centered_piece():
    pdf = IntervalPdf(BaseInterval(0, 10))

    region = pdf.highest_density_region(0.8)

    assert [(interval.start, interval.stop) for interval in sorted(region)] == [(1, 9)]
    assert pdf.probability_between(1, 9) == pytest.approx(0.8)


def test_highest_density_region_can_be_disjoint():
    pdf = IntervalPdf([BaseInterval(0, 1, value=2), BaseInterval(2, 4)])

    region = pdf.highest_density_region(0.75)

    assert [(interval.start, interval.stop) for interval in sorted(region)] == [
        (0, 1),
        (2.5, 3.5),
    ]
    assert sum(pdf.probability_between(interval.start, interval.stop) for interval in region) == pytest.approx(0.75)


def test_highest_density_region_trims_ties_deterministically():
    pdf = IntervalPdf([BaseInterval(0, 1), BaseInterval(2, 3)])

    region = pdf.highest_density_region(0.25)

    assert [(interval.start, interval.stop) for interval in sorted(region)] == [(0.25, 0.75)]
    assert pdf.probability_between(0.25, 0.75) == pytest.approx(0.25)


def test_highest_density_region_accepts_full_probability_mass():
    pdf = IntervalPdf([BaseInterval(0, 1), BaseInterval(2, 3)])

    region = pdf.highest_density_region(1)

    assert [(interval.start, interval.stop) for interval in sorted(region)] == [(0, 1), (2, 3)]


@pytest.mark.parametrize("mass", [0, -0.1, 1.1, float("inf"), float("nan")])
def test_highest_density_region_rejects_invalid_mass(mass):
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(ValueError, match=r"\(0, 1\]"):
        pdf.highest_density_region(mass)


def test_highest_density_region_rejects_non_real_mass():
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(TypeError, match="real number"):
        pdf.highest_density_region(True)


@pytest.mark.parametrize("level", [0, 1, -0.1, 1.1, float("inf"), float("nan")])
def test_credible_interval_rejects_invalid_level(level):
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(ValueError, match=r"\(0, 1\)"):
        pdf.credible_interval(level)


def test_credible_interval_rejects_non_real_level():
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(TypeError, match="real number"):
        pdf.credible_interval(True)


def test_inverse_cumulative():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3, 2)), BaseInterval((3, 4))])
    assert a.inverse_cumulative(0) == 0
    assert a.inverse_cumulative(0.25) == 1
    assert a.inverse_cumulative(0.5) == 2.5
    assert a.inverse_cumulative(0.75) == 3
    assert a.inverse_cumulative(1) == 4


def test_inverse_cumulative_endpoints_boundaries_and_gaps():
    pdf = IntervalPdf([BaseInterval(1, 2), BaseInterval(4, 6, value=2)])

    assert pdf.inverse_cumulative(0) == 1
    assert pdf.inverse_cumulative(0.2) == 2
    assert pdf.inverse_cumulative(0.6) == 5
    assert pdf.inverse_cumulative(1) == 6


@pytest.mark.parametrize("probability", [-0.1, 1.1, float("-inf"), float("inf"), float("nan")])
def test_inverse_cumulative_rejects_invalid_probability(probability):
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        pdf.inverse_cumulative(probability)


def test_inverse_cumulative_rejects_non_real_probability():
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(TypeError, match="real number"):
        pdf.inverse_cumulative(True)


def test_sample_count_and_seeded_reproducibility():
    pdf = IntervalPdf([BaseInterval(0, 1), BaseInterval(2, 4)])

    assert pdf.sample(0) == []
    assert pdf.sample(5, rng=random.Random(1234)) == pdf.sample(5, rng=random.Random(1234))


@pytest.mark.parametrize("count", [-1, 1.5])
def test_sample_rejects_invalid_count_value(count):
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises((TypeError, ValueError), match="non-negative integer"):
        pdf.sample(count)


def test_sample_rejects_boolean_count():
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(TypeError, match="non-negative integer"):
        pdf.sample(True)


def test_sample_rejects_invalid_rng():
    pdf = IntervalPdf(BaseInterval(0, 1))

    with pytest.raises(TypeError, match="random.Random"):
        pdf.sample(rng=object())


def test_sample_values_are_within_support():
    pdf = IntervalPdf([BaseInterval(1, 2), BaseInterval(4, 6)])

    samples = pdf.sample(100, rng=random.Random(456))

    assert len(samples) == 100
    assert all(1 <= value <= 2 or 4 <= value <= 6 for value in samples)
