# This example shows an example of how to use this, in this case for finding a value in a range 0 to 100 that meets the
# most requirements out of a total of 250. The requirements could be for example functions that need to exceed 0 to be
# met, and as a starting point here I assume it has already been detected for which values these functions are positive.

from random import random
import intervalues as iv

n_reqs = 250
reqs = [(random()*100, random()*100) for _ in range(n_reqs)]  # For which interval each requirement is positive

# Convert requirements to intervals
intervals = [iv.BaseInterval((min(x), max(x))) for x in reqs]

# Combine intervals to one Counter
interval_counter = iv.IntervalCounter(intervals.copy())
interval_counter_one_by_one = iv.IntervalCounter()
for interval in intervals:
    interval_counter_one_by_one.update(interval)

# Check that total length of the counter and the individual intervals is the same
print(f"Counter total: {interval_counter.total_length():.4f}; "
      f"Counter one by one: {interval_counter_one_by_one.total_length():.4f}; "
      f"Sum of individual intervals: {sum(x.get_length() for x in intervals):.4f}")
print(f"Number of final subintervals: {len(interval_counter.data)}")
print(f"The most common subinterval: {interval_counter.most_common(1)}")
