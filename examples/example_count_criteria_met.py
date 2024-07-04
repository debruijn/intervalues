# This example shows an example of how to use this, in this case for finding a value in a range 0 to 100 that meets the
# most requirements. The requirements could be for example functions that need to exceed 0 to be met, and as a starting
# point here I assume it has already been detected for which values these functions are positive.

from random import random
from intervalues import IntervalCounterFloat, UnitInterval

n_reqs = 250
reqs = [(random()*100, random()*100) for _ in range(n_reqs)]

# Convert reqs to intervals
intervals = [UnitInterval((min(x), max(x))) for x in reqs]

# Combine intervals to one Counter
interval_counter = IntervalCounterFloat(intervals.copy())
interval_counter_one_by_one = IntervalCounterFloat()
for interval in intervals:
    interval_counter_one_by_one.update(interval)

# Check that total length of the counter and the individual intervals is the same
print(f"Counter total: {interval_counter.total_length():.4f}; "
      f"Counter one by one: {interval_counter_one_by_one.total_length():.4f}; "
      f"Sum of indiviual intervals: {sum(x.length for x in intervals):.4f}")
print(f"Number of final subintervals: {len(interval_counter.counter)}")
print(f"Number of final subintervals: {len(interval_counter_one_by_one.counter)}")

print(f"The most common (or one of): {interval_counter.most_common(1)}")
print(f"The most common (or one of): {interval_counter_one_by_one.most_common(1)}")
