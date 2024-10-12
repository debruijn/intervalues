from intervalues import BaseInterval, combine_intervals, combine_via_rust
from random import Random
import time


INTERVAL_MANY = [10, 1000, 10000, 100000, 1000000, ]


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
    intervals = [x if x[0] < x[1] else (x[1], x[0]) for x in split_to_pairs(nums)]
    intervals = [BaseInterval(interval) for interval in intervals if interval[0] != interval[1]]
    before = time.time_ns()
    combine_via_rust(intervals)
    after = time.time_ns()
    return (after-before)/1000000


def combine_many_rustfl(nums):
    intervals = [x if x[0] < x[1] else (x[1], x[0]) for x in split_to_pairs(nums)]
    intervals = [BaseInterval(interval) for interval in intervals if interval[0] != interval[1]]
    before = time.time_ns()
    combine_via_rust(intervals, 8)
    after = time.time_ns()
    return (after-before)/1000000


if __name__ == "__main__":
    rand_this = Random()
    for nr in INTERVAL_MANY:
        print(f"\nRun for {nr} intervals to combine")

        nums = [rand_this.randint(0, 10) for _ in range(nr * 2)]
        print(f'Python, ints: {combine_many(nums)} ms')
        print(f'Rust, ints: {combine_many_rust(nums)} ms')

        nums = [rand_this.randint(0, 10) + 0.5 for _ in range(nr * 2)]
        print(f'Python, floats: {combine_many(nums)} ms')
        print(f'Rust, floats: {combine_many_rustfl(nums)} ms')
