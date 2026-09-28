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


def test_subtraction_base():
    a = IntervalPdf([BaseInterval((0, 1))])
    b = BaseInterval((2, 3, 0.5))
    c = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert c - b == a
    c -= b
    assert a == c


def test_subtraction_pdf():
    a = IntervalPdf([BaseInterval((0, 1))])
    b = BaseInterval((2, 3), value=0.5)
    c = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert c - b == a
    c -= b
    assert a == c


@pytest.mark.parametrize("mult", (2, -2, 0))
def test_multiplication(mult):
    a = IntervalPdf([BaseInterval((0, 2))]) * mult
    b = IntervalPdf([BaseInterval((0, 2))])
    assert a == b
    a *= mult
    assert a == b*mult


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
