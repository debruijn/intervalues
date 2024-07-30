# This example shows an example of how to use this, in this case in the context of managing an airfield with planes
# landing throughout the day. In this example, it is assumed that every day has the same schedule. The question is for
# a given schedule what the capacity would need to be on its landing strips. Capacity of gates are ignored, just as
# delays and other uncertainties.

# Setup:
# There are N planes.
# Each plane has two different relevant time periods: when it arrives and when it departs.
# Some planes need more time for either task, so I will use different plane classes for this.
# Some planes need more time inbetween before they can leave again (more passengers, or more guidelines to check).
# The planes need to request access for a whole 15 minutes at a time, even if they only need 1 minute out of it.

from intervalues import BaseInterval, IntervalCounter, EmptyInterval
import random

# Settings of simulation
N = 120
probs = [0.5, 0.3, 0.2]  # Sizes of planes with longer times for larger planes
label = ['Small', 'Medium', 'Big']
landing_time_taken = [5/60, 10/60, 15/60]
departure_time_taken = [10/60, 20/60, 30/60]
intermediate_time = [4, 6, 8]  # Time between landing and departure for each type.

# Initialize variables
counters_per_type = [IntervalCounter() for _ in range(3)]
printable_schedule = []


def add_to_schedule(period, schedule, granularity=0.25):  # 0.25 -> every 15 mins
    # Add a period to the schedule, keeping in mind that times past 24 should converted to the time in the next day.
    # A granularity can be applied to remove a distinction between when in a period you see a plane.
    period = tuple(int(x / granularity)*granularity for x in period)
    if period[1] > 24:
        schedule += BaseInterval(period[0], 24)
        schedule += BaseInterval(0, period[1] - 24)
    else:
        schedule += BaseInterval(period)


def format_hour(hour):
    minutes = int((hour - int(hour)) * 60)
    minutes = str(minutes) if minutes >= 10 else '0' + str(minutes)
    hour = str(int(hour)) if hour >= 10 else '0' + str(int(hour))
    return f"{hour}:{minutes}"


for i in range(N):
    # For each plane, generate the type and when it starts to land.
    type_plane = random.choices((0, 1, 2), probs)[0]
    init_time = random.random()*24

    # Landing is from that initial time up to how long it takes to land.
    landing = (init_time, init_time + landing_time_taken[type_plane])
    add_to_schedule(landing, counters_per_type[type_plane])  # Add to counter of the current plane type

    # Departure starts after the intermediate time has been added to the final landing time.
    departure = (landing[1] + intermediate_time[type_plane]) % 24
    departure = (departure, departure + departure_time_taken[type_plane])
    add_to_schedule(departure, counters_per_type[type_plane])  # Add to counter of the current plane type

    printable_schedule.append([landing, departure, type_plane])

# A combined counter can be made by summing the counters together.
counter_total = sum(counters_per_type, start=EmptyInterval())
most_busy = counter_total.most_common(10)

# Print results: the schedule, how many landing strips are needed, the busiest time periods, and also busiest time per
# plane type.
print('The schedule being considered:')
printable_schedule.sort(key=lambda x: x[0][0])
for i, val in enumerate(printable_schedule):
    print(f'Plane {i+1} ({label[val[2]]}): lands from {format_hour(val[0][0])} to {format_hour(val[0][1])}; '
          f'departs from {format_hour(val[1][0])} to {format_hour(val[1][1])}.')

print(f'\nWith this schedule, this airfield needs {most_busy[0][1]} landing strips to meet capacity.\n')

print('Top 10 most busy quarters at landing strip: ')
for i, val in enumerate(most_busy):
    print(f'\t{i+1}: from {format_hour(val[0].start)} to {format_hour(val[0].stop)} with {val[1]} planes.')

print('\nBest time to spot a plane of each type:')
for i in range(3):
    most_busy = counters_per_type[i].most_common(1)
    print(f'\t{label[i]}: from {format_hour(most_busy[0][0].start)} to {format_hour(most_busy[0][0].stop)} with '
          f'{most_busy[0][1]} planes.')
