from intervalues import BaseInterval, combine_intervals
from random import Random
from intervalues_pyrust import combine_intervals_int, combine_intervals_float
import time


INTERVAL_MANY = [5, 1000, 10000, 100000, 1000000, ]


def split_to_pairs(iterable):
    a = iter(iterable)
    return zip(a, a)


def combine_many(nums):
    intervals = [x if x[0] < x[1] else (x[1], x[0]) for x in split_to_pairs(nums)]
    intervals = [BaseInterval(interval) for interval in intervals if interval[0] != interval[1]]
    before = time.time_ns()
    combine_intervals(intervals)
    after = time.time_ns()
    return (after-before)/1000000


def combine_many_rust(nums):
    intervals = [x + (1, ) if x[0] < x[1] else (x[1], x[0], 1) for x in split_to_pairs(nums) if x[0] != x[1]]
    before = time.time_ns()
    combine_intervals_int(intervals)
    after = time.time_ns()
    return (after-before)/1000000


def combine_many_rustfl(nums):
    intervals = [x + (1, ) if x[0] < x[1] else (x[1], x[0], 1) for x in split_to_pairs(nums) if x[0] != x[1]]
    before = time.time_ns()
    combine_intervals_float(intervals, 8)
    after = time.time_ns()
    return (after-before)/1000000


if __name__ == "__main__":
    rand_this = Random()
    for nr in INTERVAL_MANY:
        print(f"\nRun for {nr} intervals to combine")
        nums = [rand_this.randint(0, 10) for _ in range(nr * 2)]

        print('Python, ints', combine_many(nums))
        print('Rust, ints', combine_many_rust(nums))

        nums = [rand_this.randint(0, 10) + 0.5 for _ in range(nr * 2)]

        print('Python, floats', combine_many(nums))
        print('Rust, floats', combine_many_rustfl(nums))
