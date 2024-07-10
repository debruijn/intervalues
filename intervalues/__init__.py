from .abstract_interval import AbstractInterval, AbstractIntervalCollector
from .interval_counter import IntervalCounterFloat
from .interval_set import IntervalSetFloat
from .base_interval import BaseInterval, UnitInterval, EmptyInterval
from .base_interval import ValueInterval as _ValueInterval
from .combine_intervals import combine_intervals


with open('VERSION') as version_file:
    __version__ = version_file.read().strip()
