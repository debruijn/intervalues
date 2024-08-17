# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2024-08-17 

### Added
- Type-hinting for all methods and functions in `intervalues`.
- `BaseDiscreteInterval`, a new class to keep track of discrete intervals (integer intervals but also decimal)
- Three new `combine_interval` sub-functions for discrete sets, meters and counters
- An example that shows how to use integer intervals

### Fixed
- Various small bug fixes due to using type-hinting.

## [0.1.1] - 2024-08-01

### Changed
- Updated this changelog to reflect the changes in 0.1.0

## [0.1.0] - 2024-07-30

### Added
- New example added, showing Intervalues in the context of airfield landing strip capacity
- Added Gitlab CI/CD via a .gitlab-ci.yml, running tests and examples
- Added more in-code documentation and comments

### Changed
- Small update to 'criteria-met' example to show an additional usage of the Intervalues syntax.
- Moved various abstract methods around to properly define `AbstractInterval` and `AbstractIntervalCollection`
- Various renaming of internal variables

## [0.0.3] - 2024-07-20

### Added

- This `CHANGELOG.md`, with older entries written retroactively
- `IntervalPdf`, to use an interval (or a collection thereof) for sampling purposes
- Various small fixes
- Added a `Getting started` section to `README.md`

### Changed
- Update the `Features` in `README.md` to be more in line with the status after the renaming in 0.0.2.

## [0.0.2] - 2024-07-11

### Added

- `IntervalList` for unstructured aggregation and procedures that involve FIFO/LIFO setups
- A revamped `IntervalCounter` to only allow integer and positive counts
- Utility functions to create an empty interval, or an interval from 0 to 1
- Unit tests of the `IntervalList` and revampled `IntervalCounter`

### Changed

- Renamed old `IntervalCounter` to `IntervalMeter` to reflect it measuring values
- Renamed `UnitInterval` to `BaseInterval` to reflect that _unit_ tends to be reserved for items of length 1

### Removed

- `ValueInterval`, the features of which are now included in BaseInterval in order to simplify logic


## [0.0.1] - 2024-07-10

### Added

- `UnitInterval` and `ValueInterval` as classes for individual section intervals, including unit tests
- `IntervalCounter` and `IntervalSet` as interval collections, including unit tests
- `combine_intervals`, a utility function that splits intervals into smaller ones if there is overlap
- An example of how to use intervalues
- An initial packaging setup including `README.md`, `pyproject.toml` and `setup.py`
