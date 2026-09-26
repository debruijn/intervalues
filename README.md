# intervalues

`intervalues` combines numeric intervals and tracks coverage or values across them. It supports continuous intervals, discrete intervals with a configurable step, and collection types for different use cases.

## Installation

```shell
pip install intervalues
```

The optional Rust extension accelerates interval combination for larger inputs. Without it, the package and its Rust-named helper continue to work using the Python implementation.

## Quick start

```python
import intervalues as iv

interval_a = iv.BaseInterval(0, 2)
interval_b = iv.BaseInterval(1, 3)
meter = iv.IntervalMeter([interval_a, interval_b])

print(meter)
# IntervalMeter:{BaseInterval[0;1]: 1, BaseInterval[1;2]: 2, BaseInterval[2;3]: 1}
print(meter[1.5])  # 2: the overlapping region has a combined value of 2
```

`BaseInterval(start, stop, value=1)` represents a continuous interval. `BaseDiscreteInterval(start, stop, step=1, value=1)` represents the points from `start` through `stop` at the given step; the stop is included when it aligns with the step. For example:

```python
points = iv.BaseDiscreteInterval(0, 4, step=2)
print(list(points))  # [(0, 1), (2, 1), (4, 1)]
```

Continuous interval endpoints are treated as boundaries; open-versus-closed endpoint semantics are not distinguished.

## Choose a collection

- `IntervalMeter` combines values over overlapping regions. Values may be non-integer or negative.
- `IntervalCounter` tracks non-negative integer coverage counts.
- `IntervalSet` tracks the union of covered regions, without retaining multiplicity.
- `IntervalList` retains the original intervals and their order, including duplicates.
- `IntervalPdf` normalizes an interval meter to total weighted length 1 and supports cumulative probabilities and sampling.

For example, the same two overlapping intervals form one covered region in a set, while the meter and counter retain the overlap count:

```python
covered = iv.IntervalSet([interval_a, interval_b])
counter = iv.IntervalCounter([interval_a, interval_b])
print(covered)  # IntervalSet:{BaseInterval[0;3]}
print(counter[1.5])  # 2
```

An `IntervalPdf` can be built from intervals and used to calculate cumulative probability or draw samples:

```python
pdf = iv.IntervalPdf([interval_a, interval_b])
print(pdf.cumulative(1.5))  # 0.5
samples = pdf.sample(3)  # Three random values drawn from the distribution
```

## Rust acceleration

Use the Rust implementation explicitly with `combine_via_rust(intervals)` or `IntervalMeter(intervals, use_rust=True)`. Rust combination converts coordinates to integers by default; set `nr_digits` to retain a chosen number of decimal places. This quantization can affect results. If the extension is unavailable, the Python implementation is used and retains the original coordinate precision, so `nr_digits` has no effect.

## Examples

Runnable scenarios are in [`examples/`](examples/):

- [`example_count_criteria_met.py`](examples/example_count_criteria_met.py) counts how many criteria cover each value in a range.
- [`example_airfield_coverage.py`](examples/example_airfield_coverage.py) estimates runway capacity from aircraft schedules.
- [`example_student_regulations_impact.py`](examples/example_student_regulations_impact.py) combines discrete student-number ranges affected by regulations.
- [`example_maturin.py`](examples/example_maturin.py) compares Python and Rust combination timings.

Run an example from the repository root with `python examples/example_count_criteria_met.py` (replace the filename to run another). The timing example uses repeatable inputs, excludes setup and warm-up time, and reports median timings; adjust its workload with `python examples/example_maturin.py --sizes 100 1000 10000 --repeats 5`. Rust timings are shown only when the extension is installed.

## Development

The test suite uses pytest. Run it from the repository root with:

```shell
python -m pytest
```

Building the package with its declared build dependencies builds the Rust extension; importing and using the package does not require that extension.

Type annotations are included in the package for static type checkers.
