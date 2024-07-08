from intervalues import interval_counter, base_interval
from itertools import chain, pairwise


def combine_intervals(intervals, object_exists=None):

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
