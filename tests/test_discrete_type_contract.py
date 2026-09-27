import pytest

from intervalues import BaseDiscreteInterval, BaseInterval, IntervalSet


@pytest.mark.parametrize("count", [1.5, True])
def test_discrete_interval_rejects_non_integer_count(count):
    with pytest.raises(TypeError, match="count must be an integer"):
        BaseDiscreteInterval(0, count=count)


@pytest.mark.parametrize("count", [0, -1])
def test_discrete_interval_rejects_non_positive_count(count):
    with pytest.raises(ValueError, match="count must be at least 1"):
        BaseDiscreteInterval(0, count=count)


@pytest.mark.parametrize("step", [0, -1, float("inf"), float("nan")])
def test_discrete_interval_rejects_invalid_step(step):
    with pytest.raises(ValueError, match="step must be greater than zero"):
        BaseDiscreteInterval(0, count=3, step=step)


def test_discrete_interval_rejects_stop_before_start():
    with pytest.raises(ValueError, match="stop must be greater than or equal to start"):
        BaseDiscreteInterval(2, stop=1)


def test_discrete_interval_accepts_positive_integer_count():
    interval = BaseDiscreteInterval(1, count=3, step=0.5)

    assert interval.count == 3
    assert interval.stop == 2
    assert list(interval) == [(1, 1), (1.5, 1), (2, 1)]


def test_interval_set_discrete_reflects_current_contents():
    interval_set = IntervalSet()
    assert interval_set.discrete is False
    assert IntervalSet([]).discrete is False

    interval_set.update(BaseDiscreteInterval(0, count=2))
    assert interval_set.discrete is True

    with pytest.raises(TypeError, match="Cannot mix discrete and continuous"):
        interval_set.update(BaseInterval(3, 4))
    with pytest.raises(TypeError, match="Cannot mix discrete and continuous"):
        interval_set.update(IntervalSet([BaseInterval(3, 4)]))

    interval_set.clear()
    assert interval_set.discrete is False

    interval_set.update(BaseInterval(3, 4))
    assert interval_set.discrete is False
