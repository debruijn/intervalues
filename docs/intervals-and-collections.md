# Intervals and collections

This guide covers the general interval and collection APIs. For continuous
probability densities and discrete probability masses, see the
[probability distributions guide](probability.md).

## Choosing an interval representation

### Continuous ranges: `BaseInterval`

`BaseInterval(start, stop, value=1)` represents a continuous range with an
optional numeric value. A sequence may also be used:

```python
import intervalues as iv

interval = iv.BaseInterval(2, 5, value=3)
same_interval = iv.BaseInterval((2, 5, 3))

assert interval == same_interval
assert interval.get_length() == 9
```

`get_length()` is the range length multiplied by the interval value. It is
therefore a weighted length, not necessarily a geometric length when the value
is not 1.

Bounds must be finite and ordered (`start <= stop`); reversed or non-finite
bounds raise `ValueError`. Equal bounds are allowed and represent a
zero-length interval. `EmptyInterval()` is the conventional empty value at
`[0, 0]`, but it compares equal to `BaseInterval(0, 0)`.

Continuous intervals compare in lexicographic `(start, stop, value)` order.
Discrete intervals also compare their step and point count when bounds match.
Discrete tolerance applies to coordinate membership, not interval equality or
hashing. Consequently, two nearby discrete intervals may both contain
approximately matching coordinates while remaining distinct dictionary/set
keys.

Coordinates at either endpoint are considered contained. The API does not
distinguish open from closed endpoints; endpoints act as range boundaries for
continuous operations. `overlaps()` is true when two inclusive ranges share
any coordinate, including containment, identical ranges, and endpoint-only
contact. `is_disjoint_with()` is true only when there is a strict gap.
Therefore, `BaseInterval(0, 1)` and `BaseInterval(1, 2)` overlap at `1` and are
not disjoint; their intersection is the zero-length interval `[1, 1]`.
Zero-length intervals contain their coordinate, including `EmptyInterval()`
at `0`; an actually empty `IntervalSet()` contains no coordinates.

Use `UnitInterval()` for `[0, 1]` or `EmptyInterval()` for the special empty
interval `[0, 0]`. Empty intervals have zero length. Other zero-length
intervals are valid degenerate intervals and contain their single coordinate.

`intersection_support(other)` returns an `IntervalSet` containing only the
shared coordinates, independent of either interval's value. The
value-aware `intersection(other)` returns an `IntervalMeter` whose value over
the overlap is the product of the input values:

```python
left = iv.BaseInterval(0, 2, value=3)
right = iv.BaseInterval(1, 3, value=4)

assert left.intersection_support(right) == iv.IntervalSet(iv.BaseInterval(1, 2))
assert left.intersection(right) == iv.IntervalMeter(iv.BaseInterval(1, 2, value=12))
```

Discrete interval intersections keep only common represented points, including
when the intervals use different steps. A continuous interval cannot be
intersected with a discrete interval; these methods raise `TypeError` for mixed
coordinate domains. A continuous point-only intersection appears in
`intersection_support()` as a zero-length interval; the value-aware meter is
empty because a single point has no positive-length support.

### Discrete points: `BaseDiscreteInterval`

`BaseDiscreteInterval(start, stop, step=1, value=1)` represents a finite
sequence of points. The stop is included when it aligns with the step;
otherwise it is reduced to the last aligned point. Alternatively, construct
from a point count:

```python
points = iv.BaseDiscreteInterval(0, 5, step=2)
counted_points = iv.BaseDiscreteInterval(0, count=3, step=2)

assert list(points) == [(0, 1), (2, 1), (4, 1)]
assert points == counted_points
assert points.point_count == 3
```

Discrete intervals report zero continuous length. Use `point_count` for their
cardinality, `coordinate_at(index)` for a zero-based point position, and
`index_of(coordinate)` to find a contained point's position. Indices must be
integers in range, and `index_of` raises `ValueError` for coordinates that are
not represented.

`clamp(value)` clamps continuous intervals to their bounds. For a discrete
interval it returns the nearest represented point, choosing the lower point
when exactly between two points.

## Interval utilities

Both interval classes support `distance_to(other)`, `clamp(value)`, and
`split_at(points)`. Distance is zero for overlapping or touching ranges and
does not depend on interval values.

```python
continuous = iv.BaseInterval(0, 10, value=2)
assert continuous.distance_to(iv.BaseInterval(12, 15)) == 2
assert continuous.clamp(12) == 10

pieces = continuous.split_at([3, 7])
assert pieces == (
    iv.BaseInterval(0, 3, value=2),
    iv.BaseInterval(3, 7, value=2),
    iv.BaseInterval(7, 10, value=2),
)
```

Continuous pieces share each split boundary. For discrete intervals, each
point at or before a cut goes into the left piece, so the pieces partition the
original points without overlap. Cuts outside the interval are ignored;
non-finite or non-numeric cuts raise `ValueError`.

`with_value(value)` returns a copy with a changed value. `set_value()` and
`mult_value()` instead mutate in place. Since interval values participate in
hashing, do not mutate an interval while it is stored in a set or used as a
dictionary key.

## Choosing a collection

| Type | Use it when | How contents behave |
| --- | --- | --- |
| `IntervalList` | Individual intervals are records and order or duplicates matter. | Preserves insertion order and duplicate entries; overlapping intervals remain separate records. |
| `IntervalSet` | Only covered regions matter. | Represents geometric coverage; interval values and overlap multiplicity are discarded. |
| `IntervalMeter` | You need arbitrary real-valued weights over regions. | Adds values over overlaps; values may be fractional or negative. |
| `IntervalCounter` | You need non-negative integer coverage counts. | Counts overlapping coverage; zero-count regions are dropped. |

Construct a collection from a single interval or a list/tuple of intervals.
Collections also provide `is_empty`, `bounds`, and `find_all_containing(value)`.
`bounds` is the outer `(minimum, maximum)` coordinate pair, or `None` when the
collection is empty. `find_all_containing` returns every stored interval that
contains a coordinate or interval. Empty collection `min()` and `max()` raise
`ValueError`.

### `IntervalList`: retain separate records

Use a list when insertion order and repeated entries are meaningful:

```python
bookings = iv.IntervalList([
    iv.BaseInterval(9, 10),
    iv.BaseInterval(9.5, 11),
    iv.BaseInterval(9, 10),
])

assert len(bookings) == 3
assert bookings[9.75] == 3
assert list(bookings)[0] == iv.BaseInterval(9, 10)
```

`IntervalList`'s `[]` and `count()` perform interval-value lookups; they are not
positional indexing or `list.count()`. Use `at(index)` for positional access;
it follows Python list indexing, including negative indices and `IndexError`
for positions outside the list. `filter_by_coordinate(coordinate)` returns the
stored records containing a coordinate, while `filter_by_range(interval)`
returns records that share coordinates with the query. Both filters preserve
insertion order and duplicate records. Range filtering treats continuous
endpoint contact as overlap and, for discrete intervals, requires a shared
represented point; mixing continuous and discrete intervals raises `TypeError`.
List operations such as `append`, `insert`, `pop`, `reverse`, and `sort` act on
the stored records.

`total_length()` sums each record's weighted length separately, so overlapping
records contribute more than once.

### `IntervalSet`: geometric coverage

Sets discard interval values and overlap multiplicity. Use set operations to
combine coverage:

```python
morning = iv.IntervalSet(iv.BaseInterval(8, 11))
afternoon = iv.IntervalSet(iv.BaseInterval(13, 17))
workday = morning | afternoon

assert iv.BaseInterval(9, 10) in workday
assert iv.BaseInterval(11, 13) not in workday
assert workday.intersection(iv.IntervalSet(iv.BaseInterval(10, 14))) == iv.IntervalSet(
    [iv.BaseInterval(10, 11), iv.BaseInterval(13, 14)]
)
```

For continuous ranges, intersection includes every shared coordinate, so
touching only at an endpoint produces a zero-length interval. `isdisjoint()`
is false whenever intersection is non-empty. For discrete sets, intersection
and disjointness use shared represented coordinates. Discrete and continuous
sets cannot be mixed in an operation. `add()` and `discard()` accept either
one interval or another `IntervalSet`; they update geometric membership rather
than interval values.

Discrete set normalization keeps stored coordinates exact; tolerance is used
only for direct point membership and indexing, not set algebra or normalization.
Runs with the same step and aligned coordinates are compacted, and a run fully
covered by another run is redundant and removed. Partially overlapping
step sequences remain separate compact runs. Union and aligned,
equal-step intersection/difference operate on runs without expanding their
points. Additional compact intersection/difference paths cover aligned
integer-coordinate sequences whose steps are exact integer multiples, within
the exactly representable integer range of floating-point coordinates.
Periodic difference produces one compact run per retained residue class and
uses that path only when at most 64 such runs are needed. Other incompatible
step sequences retain exact results through point-based fallback and may
require enumerating points.

`issubset()` and `issuperset()` compare geometric coverage, independent of
continuous interval segmentation. For non-empty continuous and discrete sets,
mixed-domain comparisons and operations raise `TypeError`; empty sets retain
the usual empty-set subset/superset rules. `remove(interval)` removes an exact
stored normalized interval and raises `KeyError` when it is absent.
`discard(interval)` instead removes geometric coverage. Because this API only
represents closed intervals, continuous difference retains boundary points
where excluding them would require an open endpoint.

`total_length()` is the total geometric coverage for continuous intervals.
For discrete intervals, use `point_count` on individual intervals: their
continuous length is zero.

### `IntervalMeter` and `IntervalCounter`: aggregate values

Meters combine values across overlaps. Counters provide integer coverage:

```python
a = iv.BaseInterval(0, 2)
b = iv.BaseInterval(1, 3)

meter = iv.IntervalMeter([a, b])
counter = iv.IntervalCounter([a, b])

assert meter[1.5] == 2
assert counter[1.5] == 2
assert meter.regions_at_least(2) == iv.IntervalSet(iv.BaseInterval(1, 2))
```

`support` returns an `IntervalSet` of represented coordinates, regardless of
their values. `coverage_length()` measures continuous support without weighting,
while `support_point_count()` counts distinct represented points for discrete
support; each raises `TypeError` when used with the other coordinate type.
Both return zero for an empty meter or counter.

`total_length()` remains weighted: it sums each partition's geometric length
multiplied by its value. For a counter this is the integral of the coverage
count, not just the length of covered support. `average_value(within)` computes
the length-weighted average over a continuous `BaseInterval`, or the arithmetic
mean over a discrete interval's represented points. Uncovered parts contribute
zero; domain and collection coordinate types must match. Omitting `within`
computes over represented support only. A zero-length continuous domain raises
`ValueError`.

`minimum_value()`, `maximum_value()`, `median_value()`, and `mode_value()`
summarize represented numeric values, not coordinate bounds (the existing
collection `min()` and `max()` still report coordinate bounds). These
statistics use the same coordinate-measure weighting as the mean: continuous
segment lengths or discrete represented-point counts. Supplying `within`
includes uncovered portions as value zero; without it, only represented
support contributes. A median split exactly between two central values is
their arithmetic midpoint. `mode_value()` returns a sorted tuple containing
every value tied for greatest measure. Empty support without a domain and
domains with zero measure raise `ValueError`.

Discrete statistics visit represented points so overlaps between differently
stepped runs are counted once; large discrete supports can therefore take time
proportional to their point count.

`regions_at_least(minimum)` returns represented regions whose value meets the
threshold; it does not add uncovered regions for zero or negative thresholds.
`regions_below(maximum)` returns represented regions strictly below the
threshold. Pass `within=BaseInterval(...)` to include uncovered parts of a
finite domain when zero is below the threshold. With no domain, only represented
regions are considered. These queries return closed intervals, so boundary
points follow the package's closed-set behavior.

Meters and counters expose Counter-like views including `items()`, `keys()`,
`values()`, and `most_common()`. A missing meter key lookup through `get()`
returns `None`; coordinate/value lookup with `[]` returns zero outside
coverage.

## Mutation, data, and conversions

Collection objects and their `data` containers are mutable. Prefer class
operations (`IntervalSet.add`, `IntervalList.append`, `IntervalMeter.update`,
and similar methods) so each type can preserve its intended representation.
Direct edits to `data` are possible but can bypass normalization or
type-specific validation.

All interval collections can be converted using `as_list()`, `as_set()`,
`as_meter()`, or `as_counter()`. Conversions may change meaning: a set discards
values, a list preserves the collection's current intervals but does not
reconstruct original inputs, and a counter converts values to integer counts.
`BaseDiscreteInterval.as_pmf()` creates a discrete probability distribution;
continuous PDFs and discrete PMFs are covered in the
[probability distributions guide](probability.md).
