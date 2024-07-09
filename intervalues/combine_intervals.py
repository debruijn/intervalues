from intervalues import interval_counter, base_interval, interval_set
from itertools import chain, pairwise


def combine_intervals(intervals, object_exists=None, type='counter'):
    if type == 'counter':
        return combine_intervals_counter(intervals, object_exists)
    if type == 'set':
        return combine_intervals_set(intervals, object_exists)


def combine_intervals_counter(intervals, object_exists=None):

    # Sort all values and their effect (+/-)
    endpoints = sorted(chain.from_iterable(intervals))  # Alt: sorted(sum([list(x) for x in intervals], []))
    counter = interval_counter.IntervalCounterFloat() if object_exists is None else object_exists
    curr_val = 0
    last_val = 0
    curr_streak = None
    for pt1, pt2 in pairwise(endpoints):

        curr_val += pt1[1]
        if curr_val > 0 and pt2[0] > pt1[0]:  # Avoid empty intervals
            if curr_val == last_val:
                curr_streak[1] = pt2[0]
            else:
                if curr_streak is not None:
                    counter.data[base_interval.BaseInterval(curr_streak)] = last_val
                last_val = curr_val
                curr_streak = [pt1[0], pt2[0]]
        elif pt2[0] > pt1[0]:
            if curr_streak is not None:
                counter.data[base_interval.BaseInterval(curr_streak)] = last_val
                curr_streak = None
            last_val = 0

    if curr_streak is not None:
        counter.data[base_interval.BaseInterval(curr_streak)] = curr_val if endpoints[-2][0] > endpoints[-1][0] else last_val

    return counter


def combine_intervals_set(intervals, object_exists=None):

    # Sort all values and their effect (+/-)
    endpoints = sorted(chain.from_iterable(intervals))  # Alt: sorted(sum([list(x) for x in intervals], []))
    this_set = interval_set.IntervalSetFloat() if object_exists is None else object_exists
    curr_val = 0
    last_val = 0
    curr_streak = None
    for pt1, pt2 in pairwise(endpoints):

        curr_val += pt1[1]
        if curr_val > 0 and pt2[0] > pt1[0]:  # Avoid empty intervals
            if curr_val > 0 and last_val > 0:
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
