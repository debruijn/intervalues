from itertools import chain
from intervalues import UnitInterval, combine_intervals
import pytest
from random import Random


INTERVAL_MANY = [5, 10, 25, 100, 250, 500, 1000, 10000]


def test_combine_disjoint():

    interval1 = UnitInterval((0, 1))
    interval2 = UnitInterval((2, 3))

    counter = combine_intervals([interval1, interval2])
    assert counter.total_length() == interval1.get_length() + interval2.get_length()

    new1, new2 = counter.keys()

    assert interval1 == new1
    assert interval2 == new2

    assert (1, 1) == tuple(counter.values())


def test_combine_overlap():
    interval1 = UnitInterval((0, 2))
    interval2 = UnitInterval((1, 3))

    counter = combine_intervals([interval1, interval2])

    assert counter.total_length() == interval1.get_length() + interval2.get_length()

    new1, new2, new3 = counter.keys()

    interval3 = UnitInterval((0, 1))
    interval4 = UnitInterval((1, 2))
    interval5 = UnitInterval((2, 3))

    assert interval3 == new1
    assert interval4 == new2
    assert interval5 == new3

    assert (1, 2, 1) == tuple(counter.values())


@pytest.mark.parametrize("int1,int2", [((0, 1), (1, 2)), ((1, 2), (0, 1))])
def test_combine_borders(int1, int2):  # touch

    interval1 = UnitInterval(int1)
    interval2 = UnitInterval(int2)

    counter = combine_intervals([interval1, interval2])
    assert counter.total_length() == interval1.get_length() + interval2.get_length()

    interval3 = UnitInterval((0, 2))

    assert interval3 == tuple(counter.keys())[0]
    assert (1,) == tuple(counter.values())


@pytest.mark.parametrize("int1,int2", [((0, 2), (0, 1)), ((0, 2), (1, 2)), ((0, 2), (0.5, 1.5))])
def test_contains(int1, int2):

    interval1 = UnitInterval(int1)
    interval2 = UnitInterval(int2)

    counter = combine_intervals([interval1, interval2])
    assert counter.total_length() == interval1.get_length() + interval2.get_length()
    assert counter.most_common(1)[0][1] == 2
    assert counter.most_common(2)[1][1] == 1


@pytest.mark.parametrize("nr_intervals", INTERVAL_MANY)
def test_combine_many(nr_intervals):
    K = 5
    intervals = [UnitInterval((i, i + K)) for i in range(nr_intervals)]
    Random(42).shuffle(intervals)
    counter = combine_intervals(intervals)
    assert counter.total_length() == K * nr_intervals

    middle_interval = UnitInterval((K-1, nr_intervals))
    assert counter.most_common(1)[0][0] == middle_interval
    sorted_keys = sorted(counter.keys(), key=lambda x: x.start)  # TODO: Evaluate whether this should work without key
    assert tuple(counter[x] for x in sorted_keys) == (1, 2, 3, 4, 5, 4, 3, 2, 1)


def split_to_pairs(iterable):
    a = iter(iterable)
    return zip(a, a)


@pytest.mark.parametrize("nr_intervals", INTERVAL_MANY)
def test_combine_many_varying(nr_intervals):
    nums = list(chain.from_iterable([[2*x, 2*x+1] for x in range(nr_intervals)]))
    Random(42).shuffle(nums)
    intervals = [x if x[0] < x[1] else (x[1], x[0]) for x in split_to_pairs(nums)]
    intervals = [UnitInterval(interval) for interval in intervals]
    counter = combine_intervals(intervals)
    assert counter.total_length() == sum(interval.get_length() for interval in intervals)

    # Only thing we know for sure: count for lowest and highest should be 1
    # (but "lowest" is not necessarily [0;1], can be [0;2])
    assert counter[0] == 1
    assert counter[2*nr_intervals-1] == 1


@pytest.mark.parametrize("nr_intervals", INTERVAL_MANY)
def test_combine_many_random(nr_intervals):
    nums = [Random().random() for _ in range(nr_intervals*2)]
    intervals = [x if x[0] < x[1] else (x[1], x[0]) for x in split_to_pairs(nums)]
    intervals = [UnitInterval(interval) for interval in intervals]
    counter = combine_intervals(intervals)
    assert counter.total_length() == pytest.approx(sum(interval.get_length() for interval in intervals))

    # Only thing we know for sure: count for lowest and highest should be 1
    assert counter[min(counter)] == 1
    assert counter[max(counter)] == 1
    assert len(counter.keys()) == 2 * nr_intervals - 1


@pytest.mark.parametrize("nr_intervals", INTERVAL_MANY)
def test_combine_many_randint(nr_intervals):
    nums = [Random().randint(0, 10) for _ in range(nr_intervals * 2)]
    intervals = [x if x[0] < x[1] else (x[1], x[0]) for x in split_to_pairs(nums)]
    intervals = [UnitInterval(interval) for interval in intervals if interval[0] != interval[1]]
    counter = combine_intervals(intervals)
    assert counter.total_length() == sum(interval.get_length() for interval in intervals)
    assert len(counter.keys()) <= 2 * nr_intervals - 1