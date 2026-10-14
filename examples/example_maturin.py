"""Compare interval-combination runtimes for the Python and optional Rust implementations."""

import argparse
from importlib.util import find_spec
from random import Random
from statistics import median
from time import perf_counter

from intervalues import BaseInterval, combine_intervals, combine_via_rust


def make_intervals(count: int, seed: int, offset: float = 0) -> list[BaseInterval]:
    rng = Random(seed)
    intervals = []
    for _ in range(count):
        start = rng.randint(0, count * 2) + offset
        stop = rng.randint(0, count * 2) + offset
        if start == stop:
            stop += 1
        intervals.append(BaseInterval((min(start, stop), max(start, stop))))
    return intervals


def benchmark(combine, intervals: list[BaseInterval], repeats: int) -> float:
    combine(intervals)
    timings = []
    for _ in range(repeats):
        start = perf_counter()
        combine(intervals)
        timings.append(perf_counter() - start)
    return median(timings) * 1000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sizes",
        nargs="+",
        type=int,
        default=[100, 1_000, 10_000],
        help="interval counts to benchmark (default: 100 1000 10000)",
    )
    parser.add_argument("--repeats", type=int, default=3, help="timed runs per implementation")
    parser.add_argument("--seed", type=int, default=42, help="seed used to generate repeatable inputs")
    args = parser.parse_args()
    if args.repeats < 1 or any(size < 1 for size in args.sizes):
        parser.error("--repeats and each --sizes value must be positive")

    has_rust = find_spec("intervalues_pyrust") is not None
    if not has_rust:
        print("Rust extension not installed; reporting Python timings only.")

    print(f"Median of {args.repeats} timed runs; input generation and warm-up excluded.")
    print("intervals | numeric inputs | Python (ms) | Rust (ms) | Rust speedup")
    for count in args.sizes:
        integer_intervals = make_intervals(count, args.seed)
        float_intervals = make_intervals(count, args.seed, offset=0.5)
        workloads = [
            ("integers", integer_intervals, lambda intervals: combine_intervals(intervals),
             lambda intervals: combine_via_rust(intervals)),
            ("floats (1 d.p.)", float_intervals, lambda intervals: combine_intervals(intervals),
             lambda intervals: combine_via_rust(intervals, nr_digits=1)),
        ]
        for label, intervals, python_combine, rust_combine in workloads:
            python_ms = benchmark(python_combine, intervals, args.repeats)
            if has_rust:
                python_result = python_combine(intervals)
                rust_result = rust_combine(intervals)
                if python_result != rust_result:
                    raise AssertionError(f"Python and Rust results differ for {count} {label} intervals")
                rust_ms = benchmark(rust_combine, intervals, args.repeats)
                print(f"{count:9} | {label:15} | {python_ms:11.3f} | {rust_ms:9.3f} | "
                      f"{python_ms / rust_ms:12.2f}x")
            else:
                print(f"{count:9} | {label:15} | {python_ms:11.3f} | {'n/a':>9} | {'n/a':>12}")


if __name__ == "__main__":
    main()
