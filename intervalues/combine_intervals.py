from intervalues import interval_meter, base_interval, interval_set
from itertools import chain, pairwise


def combine_intervals(intervals, object_exists=None, combined_type='meter'):
    """
    Function to efficiently combine BaseIntervals. This is done by doing the following:
    - Sort the endpoints of all intervals, with effect. E.g. BaseInterval(0,1,2) -> (0,2), (1,-2). In words: an interval
        from 0 to 1 with value 2 is converted to a value increase of 2 at 0, and a value decrease of -2 at 1.
    - Then go over all sorted endpoints, and keep track of the aggregate value
    - When the aggregate value changes (or when it changes sign, for a set), create an interval for the recent interval

    :param intervals: the iterable containing the BaseIntervals
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

    if combined_type == 'meter':
        return combine_intervals_meter(intervals, object_exists)
    if combined_type == 'set':
        return combine_intervals_set(intervals, object_exists)
    if combined_type == 'counter':
        return combine_intervals_counter(intervals, object_exists)


def combine_intervals_meter(intervals, object_exists=None):

    # Sort all values and their effect (+/-)
    endpoints = sorted(chain.from_iterable(intervals))  # Alt: sorted(sum([list(x) for x in intervals], []))
    meter = interval_meter.IntervalMeter() if object_exists is None else object_exists
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
                    meter.data[base_interval.BaseInterval(curr_streak)] = last_val
                last_val = curr_val
                curr_streak = [pt1[0], pt2[0]]
        elif pt2[0] > pt1[0]:
            if curr_streak is not None:
                meter.data[base_interval.BaseInterval(curr_streak)] = last_val
                curr_streak = None
            last_val = 0

    if curr_streak is not None:
        meter.data[base_interval.BaseInterval(curr_streak)] = curr_val if endpoints[-2][0] > endpoints[-1][0] else last_val

    return meter


def combine_intervals_set(intervals, object_exists=None):

    # Sort all values and their effect (+/-)
    endpoints = sorted(chain.from_iterable(intervals))  # Alt: sorted(sum([list(x) for x in intervals], []))
    this_set = interval_set.IntervalSet() if object_exists is None else object_exists
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


def combine_intervals_counter(intervals, object_exists=None):

    # Sort all values and their effect (+/-)
    endpoints = sorted(chain.from_iterable(intervals))  # Alt: sorted(sum([list(x) for x in intervals], []))
    counter = interval_meter.IntervalCounter() if object_exists is None else object_exists
    curr_val = 0
    last_val = 0
    curr_streak = None
    for pt1, pt2 in pairwise(endpoints):

        curr_val += pt1[1]
        if curr_val > 0 and pt2[0] > pt1[0]:  # Avoid empty intervals
            if curr_val == last_val:
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
