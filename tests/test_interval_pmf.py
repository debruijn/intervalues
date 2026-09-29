import random

import pytest

from intervalues import BaseDiscreteInterval, BaseInterval, IntervalPdf, IntervalPmf


def test_pmf_normalizes_discrete_interval_points():
    pmf = IntervalPmf(BaseDiscreteInterval(0, 4, step=2))

    assert [point for point, _ in pmf.items()] == [0, 2, 4]
    assert [mass for _, mass in pmf.items()] == pytest.approx([1 / 3] * 3)
    assert pmf.total_mass() == pytest.approx(1)


def test_pmf_data_is_read_only():
    pmf = IntervalPmf(BaseDiscreteInterval(0, 1))

    with pytest.raises(TypeError):
        pmf.data[0] = 0.5


def test_pmf_applies_interval_value_as_mass_at_each_point():
    pmf = IntervalPmf([
        BaseDiscreteInterval(0, 2, value=1),
        BaseDiscreteInterval(2, 4, value=3),
    ])

    assert [pmf.mass_at(point) for point in (0, 1, 2, 3, 4)] == pytest.approx(
        [1 / 12, 1 / 12, 4 / 12, 3 / 12, 3 / 12]
    )


def test_pmf_lookup_cdf_and_quantile():
    pmf = IntervalPmf([
        BaseDiscreteInterval(0, 0, value=1),
        BaseDiscreteInterval(2, 2, value=2),
        BaseDiscreteInterval(5, 5, value=1),
    ])

    assert pmf[0] == pytest.approx(0.25)
    assert pmf.mass_at(1) == 0
    assert pmf.cumulative(-1) == 0
    assert pmf.cumulative(1) == pytest.approx(0.25)
    assert pmf.cumulative(2) == pytest.approx(0.75)
    assert pmf.cumulative(10) == pytest.approx(1)
    assert pmf.inverse_cumulative(0) == 0
    assert pmf.inverse_cumulative(0.25) == 0
    assert pmf.inverse_cumulative(0.26) == 2
    assert pmf.inverse_cumulative(1) == 5


def test_pmf_sampling_is_reproducible_and_returns_only_support_values():
    pmf = IntervalPmf(BaseDiscreteInterval(0, 10, step=2))

    samples = pmf.sample(20, rng=random.Random(123))

    assert samples == pmf.sample(20, rng=random.Random(123))
    assert all(point in {0, 2, 4, 6, 8, 10} for point in samples)
    assert pmf.sample(0) == []


@pytest.mark.parametrize(
    "data, error",
    [
        ([], ValueError),
        ([BaseInterval(0, 1)], TypeError),
        ([BaseDiscreteInterval(0, 1, value=-1)], ValueError),
        ([BaseDiscreteInterval(0, 1, value=float("nan"))], ValueError),
        ([BaseDiscreteInterval(0, 1, value=0)], ValueError),
        ([BaseDiscreteInterval(0, 1), BaseInterval(2, 3)], TypeError),
    ],
)
def test_pmf_rejects_invalid_inputs(data, error):
    with pytest.raises(error):
        IntervalPmf(data)


@pytest.mark.parametrize(
    "probability, error",
    [
        (-0.1, ValueError),
        (1.1, ValueError),
        (float("inf"), ValueError),
        (float("nan"), ValueError),
        (True, TypeError),
    ],
)
def test_pmf_quantile_rejects_invalid_probability(probability, error):
    pmf = IntervalPmf(BaseDiscreteInterval(0, 1))

    with pytest.raises(error):
        pmf.inverse_cumulative(probability)


def test_continuous_pdf_rejects_discrete_interval():
    with pytest.raises(TypeError, match="probability-mass"):
        IntervalPdf(BaseDiscreteInterval(0, 2))


def test_discrete_interval_conversion_to_pmf():
    pmf = BaseDiscreteInterval(0, 2, step=0.5).as_pmf()

    assert isinstance(pmf, IntervalPmf)
    assert len(pmf) == 5
    assert pmf.total_mass() == pytest.approx(1)
