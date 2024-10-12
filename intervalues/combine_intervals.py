from collections import defaultdict
from typing import Optional, Sequence

import intervalues
from intervalues import interval_meter, base_interval, interval_set
from itertools import chain, pairwise
from intervalues_pyrust import combine_intervals_int, combine_intervals_float


def combine_via_rust(intervals: Sequence['intervalues.BaseInterval | intervalues.BaseDiscreteInterval'],
                     nr_digits: int = 0) -> 'intervalues.IntervalMeter':
    out = combine_intervals_int([x.to_args() + (1,) if x.value == 1 else x.to_args()
                                 for x in intervals]) if nr_digits == 0 \
        else combine_intervals_float([x.to_args() + (1.0,) if x.value == 1 else x.to_args()
                                      for x in intervals], nr_digits)
    base_intervals = [intervalues.BaseInterval(x) for x in out]
    return interval_meter.IntervalMeter(base_intervals, skip_combine=True)


def combine_intervals(intervals: Sequence['intervalues.BaseInterval | intervalues.BaseDiscreteInterval'],
                      object_exists: Optional[object] = None,
                      combined_type: str = 'meter') -> (
        'intervalues.IntervalCounter | intervalues.IntervalMeter | intervalues.IntervalSet'):
    """
    Function to efficiently combine BaseIntervals. This is done by doing the following:
    - Sort the endpoints of all intervals, with effect. E.g. BaseInterval(0,1,2) -> (0,2), (1,-2). In words: an interval
        from 0 to 1 with value 2 is converted to a value increase of 2 at 0, and a value decrease of -2 at 1.
    - Then go over all sorted endpoints, and keep track of the aggregate value
    - When the aggregate value changes (or when it changes sign, for a set), create an interval for the recent interval

    :param intervals: the sequence containing the BaseIntervals
    :param object_exists: if an existing object already exists for which the data needs to updated, use this input
    :param combined_type: one of 'meter', 'set', or 'counter', depending on which collection type should be created
    :return: an object from one of the IntervalMeter/IntervalSet/IntervalCounter classes, with the combined intervals
        as data attribute

    Examples:
    a = BaseInterval((1, 3))
    b = BaseInterval((0, 2))
    combine_intervals([a, b])
    -> IntervalMeter:{BaseInterval[0;1]: 1, BaseInterval[1;2]: 2, BaseInterval[2;3]: 1}

    combine_intervals([a, b], combined_type='set')
    -> IntervalSet:{BaseInterval[0;3]}
    """
    discrete = True if type(intervals) == Sequence[intervalues.BaseDiscreteInterval] else False
    if object_exists is None:
        if discrete:
            if combined_type == 'meter':
                return combine_intervals_meter_discrete(intervals, None)  # type: ignore[arg-type]
            if combined_type == 'set':
                return combine_intervals_set_discrete(intervals, None)  # type: ignore[arg-type]
            if combined_type == 'counter':
                return combine_intervals_counter_discrete(intervals, None)  # type: ignore[arg-type]
        else:
            if combined_type == 'meter':
                return combine_intervals_meter(intervals, None)
            if combined_type == 'set':
                return combine_intervals_set(intervals, None)
            if combined_type == 'counter':
                return combine_intervals_counter(intervals, None)
    else:
        if discrete:
            if isinstance(object_exists, intervalues.IntervalCounter):
                return combine_intervals_counter_discrete(intervals, object_exists)  # type: ignore[arg-type]
            if isinstance(object_exists, intervalues.IntervalMeter):
                return combine_intervals_meter_discrete(intervals, object_exists)  # type: ignore[arg-type]
            if isinstance(object_exists, intervalues.IntervalSet):
                return combine_intervals_set_discrete(intervals, object_exists)  # type: ignore[arg-type]
        else:
            if isinstance(object_exists, intervalues.IntervalCounter):
                return combine_intervals_counter(intervals, object_exists)
            if isinstance(object_exists, intervalues.IntervalMeter):
                return combine_intervals_meter(intervals, object_exists)
            if isinstance(object_exists, intervalues.IntervalSet):
                return combine_intervals_set(intervals, object_exists)
    raise TypeError(f'intervalues.combine_intervals not available to make a class of type {combined_type}')


def combine_intervals_meter(intervals: Sequence['intervalues.BaseInterval'],
                            object_exists: Optional['intervalues.IntervalMeter'] = None) -> 'intervalues.IntervalMeter':
    # Sort all values and their effect (+/-)
    endpoints = sorted(chain.from_iterable(intervals))  # Alt: sorted(sum([list(x) for x in intervals], []))
    meter = interval_meter.IntervalMeter() if object_exists is None else object_exists
    curr_val = 0
    last_val = 0
    curr_streak: Optional[list[float]] = None
    for pt1, pt2 in pairwise(endpoints):

        curr_val += pt1[1]
        if curr_val != 0 and pt2[0] > pt1[0]:  # Avoid empty intervals
            if curr_val == last_val and curr_streak is not None:
                curr_streak[1] = pt2[0]
            else:
                if curr_streak is not None:
                    meter.data[base_interval.BaseInterval(curr_streak)] = last_val
                last_val = curr_val
                curr_streak = [pt1[0], pt2[0]]
        elif pt2[0] > pt1[0]:
            if curr_streak is not None:
                meter.data[base_interval.BaseInterval(curr_streak)] = last_val
                curr_streak = None
            last_val = 0

    if curr_streak is not None:
        meter.data[base_interval.BaseInterval(curr_streak)] = curr_val if endpoints[-2][0] > endpoints[-1][
            0] else last_val

    return meter


def combine_intervals_set(intervals: Sequence['intervalues.BaseInterval'],
                          object_exists: Optional['intervalues.IntervalSet'] = None) -> 'intervalues.IntervalSet':
    # Sort all values and their effect (+/-)
    endpoints = sorted(chain.from_iterable(intervals))  # Alt: sorted(sum([list(x) for x in intervals], []))
    this_set = interval_set.IntervalSet() if object_exists is None else object_exists
    curr_val = 0
    last_val = 0
    curr_streak: Optional[list[float]] = None
    for pt1, pt2 in pairwise(endpoints):

        curr_val += pt1[1]
        if curr_val > 0 and pt2[0] > pt1[0]:  # Avoid empty intervals
            if curr_val > 0 and last_val > 0 and curr_streak is not None:
                curr_streak[1] = pt2[0]
            else:
                if curr_streak is not None:  # TO add check pos
                    this_set.data.add(base_interval.BaseInterval(curr_streak))
                last_val = curr_val
                curr_streak = [pt1[0], pt2[0]]
        elif pt2[0] > pt1[0]:
            if curr_streak is not None:
                this_set.data.add(base_interval.BaseInterval(curr_streak))
                curr_streak = None
            last_val = 0

    if curr_streak is not None:
        this_set.data.add(base_interval.BaseInterval(curr_streak))

    return this_set


def combine_intervals_counter(intervals: Sequence['intervalues.BaseInterval'],
                              object_exists: Optional['intervalues.IntervalCounter'] = None) -> \
        'intervalues.IntervalCounter':
    # Sort all values and their effect (+/-)
    endpoints = sorted(chain.from_iterable(intervals))  # Alt: sorted(sum([list(x) for x in intervals], []))
    counter = interval_meter.IntervalCounter() if object_exists is None else object_exists
    curr_val = 0
    last_val = 0
    curr_streak: Optional[list[float]] = None
    for pt1, pt2 in pairwise(endpoints):

        curr_val += pt1[1]
        if curr_val > 0 and pt2[0] > pt1[0]:  # Avoid empty intervals
            if curr_val == last_val and curr_streak is not None:
                curr_streak[1] = pt2[0]
            else:
                if curr_streak is not None and last_val >= 1:
                    counter.data[base_interval.BaseInterval(curr_streak)] = int(last_val)
                last_val = curr_val
                curr_streak = [pt1[0], pt2[0]]
        elif pt2[0] > pt1[0]:
            if curr_streak is not None:
                if last_val >= 1:
                    counter.data[base_interval.BaseInterval(curr_streak)] = int(last_val)
                curr_streak = None
            last_val = 0

    if curr_streak is not None:
        new_val = curr_val if endpoints[-2][0] > endpoints[-1][0] else last_val
        if new_val >= 1:
            counter.data[base_interval.BaseInterval(curr_streak)] = int(new_val)

    return counter


def combine_intervals_meter_discrete(intervals: Sequence['intervalues.BaseDiscreteInterval'],
                                     object_exists: Optional[
                                         'intervalues.IntervalMeter'] = None) -> 'intervalues.IntervalMeter':
    # Initial implementation will be to only combine those with the same `step` and on compatible multiples of `step`.
    # This will be fine in most cases, since in most use cases the step will be the same (e.g. all 1) and start at 0.
    # Later on, there might be an improvement in which these will be combined, potentially with "repeating patterns" or
    # something like that.

    intervals_by_step = defaultdict(list)
    for interval in intervals:
        intervals_by_step[(interval.step, interval.start % interval.step)].append(interval)
    meter = interval_meter.IntervalMeter() if object_exists is None else object_exists  # TODO: might be different IntervalMeter

    for i_step, intervals_step in intervals_by_step.items():

        # Sort all values and their effect (+/-)
        this_step, _ = i_step
        endpoints = sorted(chain.from_iterable(((interval.start, interval.value), (interval.stop + this_step, -interval.value))
                                               for interval in intervals_step))
        curr_val = 0  # type: ignore[assignment]
        last_val = 0
        curr_streak: Optional[list[float]] = None
        for pt1, pt2 in pairwise(endpoints):

            curr_val += pt1[1]  # type: ignore[assignment]
            if curr_val != 0 and pt2[0] > pt1[0]:  # Avoid empty intervals
                if curr_val == last_val and curr_streak is not None:
                    curr_streak[1] = pt2[0]
                else:
                    if curr_streak is not None:
                        curr_streak[1] -= this_step
                        meter.data[intervalues.BaseDiscreteInterval(curr_streak)] = last_val
                    last_val = curr_val
                    curr_streak = [pt1[0], pt2[0]]
            elif pt2[0] > pt1[0]:
                if curr_streak is not None:
                    curr_streak[1] -= this_step
                    meter.data[intervalues.BaseDiscreteInterval(curr_streak)] = last_val
                    curr_streak = None
                last_val = 0

        if curr_streak is not None:
            curr_streak[1] -= this_step
            meter.data[intervalues.BaseDiscreteInterval(curr_streak)] = curr_val if endpoints[-2][0] > endpoints[-1][
                0] else last_val

    return meter


def combine_intervals_counter_discrete(intervals: Sequence['intervalues.BaseDiscreteInterval'],
                                     object_exists: Optional[
                                         'intervalues.IntervalCounter'] = None) -> 'intervalues.IntervalCounter':
    # See caveats at `combine_intervals_meter_discrete`

    intervals_by_step = defaultdict(list)
    for interval in intervals:
        intervals_by_step[(interval.step, interval.start % interval.step)].append(interval)
    counter = interval_meter.IntervalCounter() if object_exists is None else object_exists  # TODO: might be different IntervalCounter

    for i_step, intervals_step in intervals_by_step.items():

        # Sort all values and their effect (+/-)
        this_step, _ = i_step
        endpoints = sorted(chain.from_iterable(((interval.start, interval.value), (interval.stop + this_step, -interval.value))
                                               for interval in intervals_step))
        curr_val = 0  # type: ignore[assignment]
        last_val = 0
        curr_streak: Optional[list[float]] = None
        for pt1, pt2 in pairwise(endpoints):

            curr_val += pt1[1]  # type: ignore[assignment]
            if curr_val > 0 and pt2[0] > pt1[0]:  # Avoid empty intervals
                if curr_val == last_val and curr_streak is not None:
                    curr_streak[1] = pt2[0]
                else:
                    if curr_streak is not None:
                        curr_streak[1] -= this_step
                        counter.data[intervalues.BaseDiscreteInterval(curr_streak)] = int(last_val)
                    last_val = curr_val
                    curr_streak = [pt1[0], pt2[0]]
            elif pt2[0] > pt1[0]:
                if curr_streak is not None:
                    curr_streak[1] -= this_step
                    if last_val >= 1:
                        counter.data[intervalues.BaseDiscreteInterval(curr_streak)] = int(last_val)
                    curr_streak = None
                last_val = 0

        if curr_streak is not None:
            new_val = curr_val if endpoints[-2][0] > endpoints[-1][0] else last_val
            if new_val >= 1:
                curr_streak[1] -= this_step
                counter.data[intervalues.BaseDiscreteInterval(curr_streak)] = int(new_val)

    return counter


def combine_intervals_set_discrete(intervals: Sequence['intervalues.BaseDiscreteInterval'],
                                     object_exists: Optional[
                                         'intervalues.IntervalSet'] = None) -> 'intervalues.IntervalSet':
    # See caveats at `combine_intervals_meter_discrete`

    intervals_by_step = defaultdict(list)
    for interval in intervals:
        intervals_by_step[(interval.step, interval.start % interval.step)].append(interval)
    this_set = interval_set.IntervalSet() if object_exists is None else object_exists  # TODO: might be different IntervalSet

    for i_step, intervals_step in intervals_by_step.items():

        # Sort all values and their effect (+/-)
        this_step, _ = i_step
        endpoints = sorted(chain.from_iterable(((interval.start, interval.value), (interval.stop + this_step, -interval.value))
                                               for interval in intervals_step))
        curr_val = 0  # type: ignore[assignment]
        last_val = 0
        curr_streak: Optional[list[float]] = None
        for pt1, pt2 in pairwise(endpoints):

            curr_val += pt1[1]  # type: ignore[assignment]
            if curr_val > 0 and pt2[0] > pt1[0]:  # Avoid empty intervals
                if curr_val > 0 and last_val > 0 and curr_streak is not None:
                    curr_streak[1] = pt2[0]
                else:
                    if curr_streak is not None:
                        curr_streak[1] -= this_step
                        this_set.data.add(intervalues.BaseDiscreteInterval(curr_streak))
                    last_val = curr_val
                    curr_streak = [pt1[0], pt2[0]]
            elif pt2[0] > pt1[0]:
                if curr_streak is not None:
                    curr_streak[1] -= this_step
                    this_set.data.add(intervalues.BaseDiscreteInterval(curr_streak))
                    curr_streak = None
                last_val = 0

        if curr_streak is not None:
            curr_streak[1] -= this_step
            this_set.data.add(intervalues.BaseDiscreteInterval(curr_streak))

    return this_set
