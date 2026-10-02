import collections
from typing import Optional, Sequence, Iterator

from . import base_interval
from .abstract_interval import AbstractIntervalCollection
from .combine_intervals import combine_intervals_meter, combine_intervals_set
import intervalues


def _discrete_intervals_from_points(points: Sequence[float]) -> tuple['intervalues.BaseDiscreteInterval', ...]:
    from .base_interval_discrete import BaseDiscreteInterval

    sorted_points = sorted(set(points))
    intervals: list[BaseDiscreteInterval] = []
    index = 0
    while index < len(sorted_points):
        if index + 1 == len(sorted_points):
            intervals.append(BaseDiscreteInterval(sorted_points[index], count=1))
            index += 1
            continue

        step = sorted_points[index + 1] - sorted_points[index]
        end = index + 2
        while end < len(sorted_points) and sorted_points[end] == sorted_points[index] + (end - index) * step:
            end += 1
        intervals.append(BaseDiscreteInterval(sorted_points[index], count=end - index, step=step))
        index = end
    return tuple(intervals)


def _intersect_discrete_aligned_runs(
    left: 'intervalues.BaseDiscreteInterval',
    right: 'intervalues.BaseDiscreteInterval',
) -> Optional[tuple['intervalues.BaseDiscreteInterval', ...]]:
    """Intersect exact aligned runs without expanding their coordinates.

    ``None`` means the inputs require the general point-based path.
    """
    from .base_interval_discrete import BaseDiscreteInterval

    integer_result = _intersect_discrete_integer_step_runs(left, right)
    if integer_result is not None:
        return integer_result
    if left.stop < right.start or right.stop < left.start:
        return ()
    if left.step != right.step:
        return None

    offset = (right.start - left.start) / left.step
    right_start_index = round(offset)
    if left.start + right_start_index * left.step != right.start:
        return None

    first_index = max(0, right_start_index)
    last_index = min(left.count - 1, right_start_index + right.count - 1)
    if first_index > last_index:
        return ()
    return (
        BaseDiscreteInterval(
            left.start + first_index * left.step,
            count=last_index - first_index + 1,
            step=left.step,
        ),
    )


def _is_exact_integer_coordinate_run(interval: 'intervalues.BaseDiscreteInterval') -> bool:
    """Restrict arithmetic shortcuts to integers exactly representable by float."""
    maximum_exact_integer = 2**53
    return (
        float(interval.start).is_integer()
        and float(interval.stop).is_integer()
        and float(interval.step).is_integer()
        and abs(interval.start) <= maximum_exact_integer
        and abs(interval.stop) <= maximum_exact_integer
        and interval.step <= maximum_exact_integer
    )


def _intersect_discrete_integer_step_runs(
    left: 'intervalues.BaseDiscreteInterval',
    right: 'intervalues.BaseDiscreteInterval',
) -> Optional[tuple['intervalues.BaseDiscreteInterval', ...]]:
    """Intersect aligned integer-coordinate runs when one step divides the other."""
    from .base_interval_discrete import BaseDiscreteInterval

    if not _is_exact_integer_coordinate_run(left) or not _is_exact_integer_coordinate_run(right):
        return None

    fine, coarse = (left, right) if left.step <= right.step else (right, left)
    fine_step, coarse_step = int(fine.step), int(coarse.step)
    if coarse_step % fine_step:
        return None
    if (int(coarse.start) - int(fine.start)) % fine_step:
        return ()

    first_index = max(0, (int(fine.start) - int(coarse.start) + coarse_step - 1) // coarse_step)
    last_index = min(
        coarse.count - 1,
        (int(fine.stop) - int(coarse.start)) // coarse_step,
    )
    if first_index > last_index:
        return ()
    return (
        BaseDiscreteInterval(
            int(coarse.start) + first_index * coarse_step,
            count=last_index - first_index + 1,
            step=coarse_step,
        ),
    )


def _contains_discrete_exact(interval: 'intervalues.BaseDiscreteInterval', coordinate: float) -> bool:
    """Check exact coordinate representation without the membership tolerance."""
    if coordinate < interval.start or coordinate > interval.stop:
        return False
    index = round((coordinate - interval.start) / interval.step)
    return 0 <= index < interval.count and interval.start + index * interval.step == coordinate


def _covers_discrete_interval(
    cover: 'intervalues.BaseDiscreteInterval',
    candidate: 'intervalues.BaseDiscreteInterval',
) -> bool:
    """Return whether one exact step sequence covers another."""
    if candidate.start < cover.start or candidate.stop > cover.stop:
        return False
    start_offset = (candidate.start - cover.start) / cover.step
    offset = round(start_offset)
    if cover.start + offset * cover.step != candidate.start or offset < 0:
        return False
    if candidate.count == 1:
        return offset < cover.count

    step_ratio = candidate.step / cover.step
    ratio = round(step_ratio)
    if ratio < 1 or cover.step * ratio != candidate.step:
        return False
    return offset >= 0 and offset + (candidate.count - 1) * ratio < cover.count


def _subtract_discrete_run(
    interval: 'intervalues.BaseDiscreteInterval',
    removal: 'intervalues.BaseDiscreteInterval',
    max_residues: int = 64,
) -> Optional[tuple['intervalues.BaseDiscreteInterval', ...]]:
    """Subtract one overlapping run, compacting bounded periodic holes."""
    from .base_interval_discrete import BaseDiscreteInterval

    common = _intersect_discrete_aligned_runs(interval, removal)
    if common is None:
        return None
    if not common:
        return (interval,)

    overlap = common[0]
    if interval.step == overlap.step or overlap.count == 1:
        offset = (overlap.start - interval.start) / interval.step
        first_removed = round(offset)
        if interval.start + first_removed * interval.step != overlap.start:
            return None
        last_removed = first_removed + overlap.count - 1
        result: list[BaseDiscreteInterval] = []
        if first_removed > 0:
            result.append(BaseDiscreteInterval(interval.start, count=first_removed, step=interval.step))
        after = last_removed + 1
        if after < interval.count:
            result.append(
                BaseDiscreteInterval(interval.start + after * interval.step, count=interval.count - after,
                                     step=interval.step)
            )
        return tuple(result)

    if not _is_exact_integer_coordinate_run(interval) or not _is_exact_integer_coordinate_run(overlap):
        return None
    if int(overlap.step) % int(interval.step):
        return None
    ratio = int(overlap.step) // int(interval.step)
    if ratio > max_residues:
        return None

    first_removed = int(overlap.start - interval.start) // int(interval.step)
    last_removed = first_removed + (overlap.count - 1) * ratio
    result = []
    if first_removed > 0:
        result.append(BaseDiscreteInterval(interval.start, count=first_removed, step=interval.step))

    interior_start, interior_stop = first_removed + 1, last_removed - 1
    removed_residue = first_removed % ratio
    for residue in range(ratio):
        if residue == removed_residue:
            continue
        first = interior_start + (residue - interior_start) % ratio
        if first <= interior_stop:
            count = (interior_stop - first) // ratio + 1
            result.append(
                BaseDiscreteInterval(
                    int(interval.start) + first * int(interval.step),
                    count=count,
                    step=ratio * int(interval.step),
                )
            )

    after = last_removed + 1
    if after < interval.count:
        result.append(
            BaseDiscreteInterval(interval.start + after * interval.step, count=interval.count - after,
                                 step=interval.step)
        )
    return tuple(result)


def _normalize_discrete_data(
    intervals: Sequence['intervalues.BaseDiscreteInterval'],
) -> set['intervalues.BaseInterval']:
    """Compact compatible runs and discard runs wholly covered by another."""
    from .combine_intervals import combine_intervals_set_discrete
    from .base_interval_discrete import BaseDiscreteInterval

    combined = combine_intervals_set_discrete(intervals)
    ordered = sorted(
        (interval for interval in combined.data if isinstance(interval, BaseDiscreteInterval)),
        key=lambda interval: (interval.start, interval.stop, interval.step),
    )
    normalized: set[intervalues.BaseInterval] = set()
    for candidate in ordered:
        if not any(
            cover is not candidate
            and _covers_discrete_interval(cover, candidate)
            and (
                not _covers_discrete_interval(candidate, cover)
                or (cover.start, cover.stop, cover.step) < (candidate.start, candidate.stop, candidate.step)
            )
            for cover in ordered
        ):
            normalized.add(candidate)
    return normalized


def _subtract_discrete_aligned_runs(
    minuends: set['intervalues.BaseInterval'],
    subtrahends: set['intervalues.BaseInterval'],
) -> Optional[tuple['intervalues.BaseDiscreteInterval', ...]]:
    """Subtract aligned runs compactly; return ``None`` if unsupported."""
    from .base_interval_discrete import BaseDiscreteInterval

    left = tuple(interval for interval in minuends if isinstance(interval, BaseDiscreteInterval))
    right = tuple(interval for interval in subtrahends if isinstance(interval, BaseDiscreteInterval))
    if len(left) != len(minuends) or len(right) != len(subtrahends):
        return None

    result: list[BaseDiscreteInterval] = []
    for interval in left:
        remaining_runs = [interval]
        for removal in right:
            next_runs: list[BaseDiscreteInterval] = []
            for run in remaining_runs:
                if removal.stop < run.start or run.stop < removal.start:
                    next_runs.append(run)
                    continue
                difference = _subtract_discrete_run(run, removal)
                if difference is None:
                    return None
                next_runs.extend(difference)
            if len(next_runs) > 256:
                return None
            remaining_runs = next_runs
            if not remaining_runs:
                break
        result.extend(remaining_runs)
    return tuple(result)


def _continuous_covers(
    covering: Sequence['intervalues.BaseInterval'],
    candidates: Sequence['intervalues.BaseInterval'],
) -> bool:
    """Check geometric coverage independent of interval segmentation."""
    ordered_cover = sorted(covering, key=lambda interval: (interval.start, interval.stop))
    for candidate in candidates:
        cursor = candidate.start
        for interval in ordered_cover:
            if interval.stop < cursor:
                continue
            if interval.start > cursor:
                break
            cursor = max(cursor, interval.stop)
            if cursor >= candidate.stop:
                break
        if cursor < candidate.stop:
            return False
    return True


class IntervalSet(AbstractIntervalCollection[set['intervalues.BaseInterval']]):
    __name__ = 'IntervalSet'

    """
    Class for a set of intervals, that tracks the occurence of individual subintervals across its inputs.

    Objects can be instantiated in multiple ways (with `a = BaseInterval((1, 3))` and `b = BaseInterval((0, 2))`):
    - IntervalSet(a) -> using a single interval
    - IntervalSet([a, b]) -> using a list or tuple of intervals

    The data is collected in a standard set. For this, the BaseIntervals are converted to value=1, since the IntervalSet
    doesn't track how often subintervals are featured.

    All methods available for sets (intersection, symmetric_difference, etc) are available, as well as all 
    IntervalCollection methods (get_length, max, etc). IntervalSets can be combined together (union/intersection) or 
    differenced. They can also be converted to IntervalCounters, IntervalMeters or IntervalLists. 
    """

    def __init__(
        self,
        data: Optional[Sequence['intervalues.BaseInterval'] | 'intervalues.BaseInterval'] = None,
    ) -> None:
        """Create a normalized union from one interval or a sequence of intervals."""
        super().__init__()
        self.data: set[intervalues.BaseInterval] = set()
        if data is not None:
            from .base_interval_discrete import BaseDiscreteInterval

            is_discrete_input = (
                isinstance(data, BaseDiscreteInterval)
                or (isinstance(data, collections.abc.Sequence)
                    and bool(data)
                    and all(isinstance(interval, BaseDiscreteInterval) for interval in data))
            )
            if isinstance(data, collections.abc.Sequence):
                has_discrete = any(isinstance(interval, BaseDiscreteInterval) for interval in data)
                has_continuous = any(
                    isinstance(interval, base_interval.BaseInterval)
                    and not isinstance(interval, BaseDiscreteInterval)
                    for interval in data
                )
                if has_discrete and has_continuous:
                    raise TypeError("Cannot mix discrete and continuous intervals in an IntervalSet")
            if is_discrete_input:
                if isinstance(data, collections.abc.Sequence):
                    discrete_intervals = tuple(
                        interval for interval in data if isinstance(interval, BaseDiscreteInterval)
                    )
                    self.data = set(_normalize_discrete_data(discrete_intervals))
                elif isinstance(data, BaseDiscreteInterval):
                    self.data = {data.as_index()}
            else:
                if isinstance(data, collections.abc.Sequence):
                    combine_intervals_set(data, object_exists=self)
                elif isinstance(data, base_interval.BaseInterval):
                    self.data = {data.as_index()}

    @property
    def discrete(self) -> bool:
        """Whether the set currently contains only discrete intervals."""
        from .base_interval_discrete import BaseDiscreteInterval

        return bool(self.data) and all(isinstance(interval, BaseDiscreteInterval) for interval in self.data)

    def add(self, other: 'IntervalSet | intervalues.BaseInterval') -> None:
        self.update(other)

    def difference(self, other: 'IntervalSet | intervalues.BaseInterval') -> 'IntervalSet':
        return self - other

    def difference_update(self, other: 'IntervalSet | intervalues.BaseInterval') -> None:
        self.__isub__(other)

    def discard(self, item: 'IntervalSet | intervalues.BaseInterval') -> None:
        self.update(item, reverse=True)

    def intersection(self, other: 'IntervalSet') -> 'IntervalSet':
        """Return regions represented by both sets.

        Continuous intersections include shared endpoints as zero-length
        intervals. Discrete intersections contain points present in both sets,
        including sets whose intervals use different steps.
        """
        if not self.data or not other.data:
            return self.__class__()

        from .base_interval_discrete import BaseDiscreteInterval

        left_discrete = tuple(interval for interval in self.data if isinstance(interval, BaseDiscreteInterval))
        right_discrete = tuple(interval for interval in other.data if isinstance(interval, BaseDiscreteInterval))
        left_continuous = tuple(
            interval for interval in self.data
            if isinstance(interval, base_interval.BaseInterval) and not isinstance(interval, BaseDiscreteInterval)
        )
        right_continuous = tuple(
            interval for interval in other.data
            if isinstance(interval, base_interval.BaseInterval) and not isinstance(interval, BaseDiscreteInterval)
        )
        if len(left_discrete) + len(left_continuous) != len(self.data) or \
                len(right_discrete) + len(right_continuous) != len(other.data) or \
                (left_discrete and left_continuous) or (right_discrete and right_continuous):
            raise TypeError("Cannot intersect discrete and continuous intervals in an IntervalSet")
        if bool(left_discrete) != bool(right_discrete):
            raise TypeError("Cannot intersect discrete and continuous intervals in an IntervalSet")

        if left_discrete:
            common_intervals: list[BaseDiscreteInterval] = []
            for left in left_discrete:
                for right in right_discrete:
                    compact_intersection = _intersect_discrete_aligned_runs(left, right)
                    if compact_intersection is not None:
                        common_intervals.extend(compact_intersection)
                        continue
                    smaller, larger = (left, right) if left.count <= right.count else (right, left)
                    common_intervals.extend(
                        _discrete_intervals_from_points(
                            tuple(point for point, _ in smaller if _contains_discrete_exact(larger, point))
                        )
                    )

            result = self.__class__()
            result.data = _normalize_discrete_data(common_intervals)
            return result

        from .combine_intervals import combine_intervals_set

        intersections = []
        point_intersections: set[float] = set()
        for left_interval in left_continuous:
            for right_interval in right_continuous:
                start = max(left_interval.start, right_interval.start)
                stop = min(left_interval.stop, right_interval.stop)
                if start < stop:
                    intersections.append(base_interval.BaseInterval(start, stop))
                elif start == stop:
                    point_intersections.add(start)

        result = combine_intervals_set(intersections)
        for point in point_intersections:
            if not any(point in interval for interval in result.data):
                result.data.add(base_interval.BaseInterval(point, point))
        return result

    def intersection_update(self, other: 'IntervalSet') -> None:
        intersection = self.intersection(other)
        self.data = intersection.data

    def isdisjoint(self, other: 'IntervalSet') -> bool:
        """Return whether the sets share no coordinates."""
        if not self.data or not other.data:
            return True
        if self.discrete != other.discrete:
            raise TypeError("Cannot compare discrete and continuous intervals in an IntervalSet")
        if self.discrete:
            return not self.intersection(other).data
        return all([x.is_disjoint_with(y) for x in self.data for y in other.data])

    def issubset(self, other: 'IntervalSet') -> bool:
        """Return whether every coordinate in this set is covered by ``other``."""
        if not self.data:
            return True
        if not other.data:
            return False
        if self.discrete != other.discrete:
            raise TypeError("Cannot compare discrete and continuous intervals in an IntervalSet")
        if self.discrete:
            return not (self - other).data
        return _continuous_covers(tuple(other.data), tuple(self.data))

    def issuperset(self, other: 'IntervalSet') -> bool:
        """Return whether ``other`` is geometrically covered by this set."""
        return other.issubset(self)

    def pop(self) -> 'intervalues.BaseInterval':
        return self.data.pop()

    def remove(self, item: 'intervalues.BaseInterval') -> None:
        """Remove an exactly stored normalized interval, raising ``KeyError`` if absent.

        Unlike :meth:`discard`, this does not remove a geometric portion.
        """
        from .base_interval_discrete import BaseDiscreteInterval

        if self.data and self.discrete != isinstance(item, BaseDiscreteInterval):
            raise TypeError("Cannot mix discrete and continuous intervals in an IntervalSet")
        normalized_item = item.as_index()
        if normalized_item not in self.data:
            raise KeyError(f"{item} not in {self}")
        self.data.remove(normalized_item)

    def symmetric_difference(self, other: 'IntervalSet') -> 'IntervalSet':
        return self ^ other

    def symmetric_difference_update(self, other: 'IntervalSet') -> None:
        new = self.symmetric_difference(other)
        self.data = new.data

    def union(self, other: 'IntervalSet | intervalues.BaseInterval') -> 'IntervalSet':
        return self + other

    def __and__(self, other: 'IntervalSet') -> 'IntervalSet':
        return self.intersection(other)

    def __iand__(self, other: 'IntervalSet') -> 'IntervalSet':
        self.intersection_update(other)
        return self

    def __ior__(self, other: 'IntervalSet') -> 'IntervalSet':
        self.__iadd__(other)
        return self

    def __ixor__(self, other: 'IntervalSet') -> 'IntervalSet':
        new = self ^ other
        self.data = new.data
        return self

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __or__(self, other: 'IntervalSet') -> 'IntervalSet':
        return self + other

    def __xor__(self, other: 'IntervalSet') -> 'IntervalSet':
        return (self - other) + (other - self)

    def clear(self) -> None:
        self.data.clear()

    def copy(self) -> 'IntervalSet':
        return self.__copy__()

    def __copy__(self) -> 'IntervalSet':
        new_counter = self.__class__()
        new_counter.data = self.data.copy()
        return new_counter

    def subtract(self, other: 'IntervalSet') -> None:
        self.__isub__(other)

    def total_length(self) -> float:
        return sum([k.get_length() for k in self.data])

    def get_length(self, index: Optional['intervalues.BaseInterval'] = None) -> float:
        if index is None:
            return self.total_length()
        return (index in self) * index.get_length()

    def __len__(self) -> int:
        return len(self.data)

    def update(self, other: object, reverse: bool = False) -> None:
        if self == other:
            if reverse:
                self.clear()
            return
        elif isinstance(other, IntervalSet):
            self.update_set(other, reverse=reverse)
        elif isinstance(other, base_interval.BaseInterval):
            self.update_interval(other, reverse=reverse)
        else:
            raise ValueError(f'Input {other} is not of type {IntervalSet} or {base_interval.BaseInterval}')
        self.check_intervals()

    def update_set(self, other: 'IntervalSet', one_by_one: bool = False, reverse: bool = False) -> None:
        from .base_interval_discrete import BaseDiscreteInterval

        if self == other:
            return
        else:
            if self.data and other.data and self.discrete != other.discrete:
                raise TypeError("Cannot mix discrete and continuous intervals in an IntervalSet")
            if self.discrete or other.discrete:
                if reverse:
                    difference = _subtract_discrete_aligned_runs(self.data, other.data)
                    if difference is not None:
                        self.data = _normalize_discrete_data(difference)
                        return
                    other_intervals = tuple(
                        interval for interval in other.data if isinstance(interval, BaseDiscreteInterval)
                    )
                    remaining_points = [
                        point
                        for interval in self.data
                        for point, _ in interval
                        if not any(
                            _contains_discrete_exact(other_interval, point)
                            for other_interval in other_intervals
                        )
                    ]
                    self.data = set(_discrete_intervals_from_points(remaining_points))
                elif other.data:
                    discrete_intervals = tuple(
                        interval
                        for interval in (*self.data, *other.data)
                        if isinstance(interval, BaseDiscreteInterval)
                    )
                    self.data = _normalize_discrete_data(discrete_intervals)
                return
            if not one_by_one:  # Join sets in one go - better for large sets with much overlap
                if not reverse:
                    combined = combine_intervals_set(list(self.data) + list(other.data))
                    self.data = combined.data
                else:
                    combined = combine_intervals_meter(list(self.data) + [-x for x in other.data]).as_set()
                    self.data = combined.data
            else:  # Place other one by one - better in case of small other or small prob of overlap
                for k in other.data:
                    self.update_interval(k, reverse=reverse)

    def update_interval(self, other: 'intervalues.BaseInterval', reverse: bool = False) -> None:
        from .base_interval_discrete import BaseDiscreteInterval

        if self.data and self.discrete != isinstance(other, BaseDiscreteInterval):
            raise TypeError("Cannot mix discrete and continuous intervals in an IntervalSet")
        other = other.as_index()
        if isinstance(other, BaseDiscreteInterval):
            self.update(self.__class__(other), reverse=reverse)
            return
        if all([x.is_disjoint_with(other) for x in self.data]):
            if not reverse:
                self.data.add(other)
        elif other in self.data:
            if reverse:
                self.data.remove(other)
            return
        else:
            if not reverse:
                self.data.add(other)
            else:
                combined = combine_intervals_set(list(self.data) + [-1 * other])
                self.data = combined.data
            self.check_intervals()

    def check_intervals(self) -> None:
        if self.discrete:
            return
        keys = sorted(self.data, key=lambda x: x.start)
        for i in range(len(keys) - 1):
            key1, key2 = keys[i], keys[i + 1]
            if key1.stop >= key2.start:
                self.align_intervals()
                return

    def align_intervals(self) -> None:
        self_as_base = [k for k in self.data]
        aligned = combine_intervals_set(self_as_base)
        self.data = aligned.data

    def find_which_contains(self, other: 'intervalues.BaseInterval | float') -> 'bool | intervalues.BaseInterval':
        for key in self.data:
            if other in key:
                return key
        return False

    def __add__(self, other: 'intervalues.BaseInterval | AbstractIntervalCollection') -> 'IntervalSet':
        new = self.copy()
        new.update(other.as_set() if not isinstance(other, IntervalSet) else other)
        return new

    def __iadd__(self, other: 'intervalues.BaseInterval | AbstractIntervalCollection') -> 'IntervalSet':
        self.update(other.as_set() if not isinstance(other, IntervalSet) else other)
        return self

    def __sub__(self, other: 'IntervalSet | intervalues.BaseInterval') -> 'IntervalSet':
        new = self.copy()
        new.update(other, reverse=True)
        return new

    def __isub__(self, other: 'IntervalSet | intervalues.BaseInterval') -> 'IntervalSet':
        self.update(other, reverse=True)
        return self

    def __mul__(self, other: int | float) -> 'IntervalSet':
        return self.copy()

    def __repr__(self) -> str:
        return f"{self.__name__}:{self.data}"

    def __str__(self) -> str:
        return self.__repr__()

    def __contains__(self, other: object) -> bool:
        if isinstance(other, int) or isinstance(other, float):
            for key in self.data:
                if other in key:
                    return True
            return False

        elif isinstance(other, base_interval.BaseInterval):
            from .base_interval_discrete import BaseDiscreteInterval

            if self.data and self.discrete != isinstance(other, BaseDiscreteInterval):
                raise TypeError("Cannot compare discrete and continuous intervals in an IntervalSet")
            index_version = other.as_index()
            return index_version in self.data or any(index_version in interval for interval in self.data)

        else:
            raise ValueError(f'Not correct use of "in" for {other}')

    def __getitem__(self, other: object) -> float:
        if isinstance(other, int) or isinstance(other, float):
            for key in self.data:
                if other in key:
                    return 1
            return 0

        elif isinstance(other, base_interval.BaseInterval):
            from .base_interval_discrete import BaseDiscreteInterval

            if self.data and self.discrete != isinstance(other, BaseDiscreteInterval):
                raise TypeError("Cannot compare discrete and continuous intervals in an IntervalSet")
            index_version = other.as_index()
            return 1 if index_version in self.data or any(index_version in interval for interval in self.data) else 0

        else:
            raise ValueError(f'Not correct use of indexing with {other}')

    def key_compare(self, other: 'IntervalSet') -> bool:
        keys1, keys2 = sorted(self.data), sorted(other.data)
        while len(keys1) * len(keys2) > 0:
            key1, key2 = keys1.pop(0), keys2.pop(0)
            if key1 < key2:
                return True
            if key2 < key1:
                return False

        return len(keys2) > 0  # shorter before longer - like in BaseInterval

    # Implemented to align with BaseInterval ordering, since BaseInterval(0,1) == IntervalCounter((BaseInterval(0,1): 1)
    def __lt__(self, other: 'IntervalSet') -> bool:
        other = other.as_set() if not isinstance(other, self.__class__) else other
        return self.key_compare(other)

    def __le__(self, other: 'IntervalSet') -> bool:
        other = other.as_set() if not isinstance(other, self.__class__) else other
        return self == other or self.key_compare(other)

    def __gt__(self, other: 'IntervalSet') -> bool:
        other = other.as_set() if not isinstance(other, self.__class__) else other
        return other.key_compare(self)

    def __ge__(self, other: 'IntervalSet') -> bool:
        other = other.as_set() if not isinstance(other, self.__class__) else other
        return self == other or other.key_compare(self)

    def __eq__(self, other: object) -> bool:  # Equal if also IntervalSet, with same intervals in it.
        if isinstance(other, type(self)):
            return self.data == other.data
        if isinstance(other, base_interval.BaseInterval) and len(self.data) == 1:
            return other in self.data  # and other.get_length() == self.get_length()
        return False

    def __hash__(self) -> int:
        if len(self.data) == 1:
            return hash(next(iter(self.data)))
        return hash(frozenset(self.data))

    def __iter__(self) -> Iterator['intervalues.BaseInterval']:
        return iter(self.data)

    def min(self) -> float:
        return min(self.data).min()

    def max(self) -> float:
        return max(self.data).max()

    def as_meter(self) -> 'intervalues.IntervalMeter':
        return intervalues.IntervalMeter(list(iter(self.data)))

    def as_list(self) -> 'intervalues.IntervalList':
        return intervalues.IntervalList(list(iter(self)))

    def as_counter(self) -> 'intervalues.IntervalCounter':
        return intervalues.IntervalCounter(tuple(self))

    def as_set(self) -> 'intervalues.IntervalSet':
        return self.copy()

    def as_pdf(self) -> 'intervalues.IntervalPdf':
        return intervalues.IntervalPdf(tuple(self))
