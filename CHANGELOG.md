# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added interval utilities for coordinate distance, clamping, and splitting, plus copy-with-value support.
- Added collection helpers for empty-state and bounds queries, finding containing intervals, and meter regions above a value threshold.
- Added `BaseInterval.intersection_support()` for geometric overlap and `intersection()` for value-aware pointwise products, returning `IntervalSet` and `IntervalMeter` respectively.
- Added detailed documentation for interval, collection, endpoint, and continuous/discrete semantics.
- Kept large compatible discrete set runs compact during union, intersection, and difference instead of expanding all represented points.
- Added compact intersection and bounded periodic-difference paths for aligned integer-coordinate sequences with integer-multiple steps.
- Defined `IntervalSet` subset/superset by geometric coverage, exact normalized `remove()` separately from geometric `discard()`, and exact-coordinate discrete set algebra.

### Changed
- Tightened public type annotations across interval classes and collection APIs.
- Defined continuous bounds as finite and ordered, permitting zero-length intervals.
- Made continuous ordering lexicographic and clarified ordering and equality across discrete intervals and collections; aligned equal-object hashes.
- Adopted closed-set endpoint behavior: touching intervals overlap and are not disjoint, and continuous set intersection retains the shared endpoint.
- Clarified collection semantics and corrected discrete interval set operations to preserve represented steps.

### Fixed
- Corrected continuous and discrete `IntervalSet` intersection behavior, including intersections across discrete step sizes.
- Preserved non-unit discrete steps during set normalization and combination.
- Kept nearby discrete coordinates distinct during normalization; tolerance remains limited to membership and indexing.
- Preserved closed-interval boundary points in continuous difference where excluding them would require open endpoints.

## [0.3.1] - 2026-09-26

### Added
- Added optional Rust-extension fallback to the Python implementation
- Added Ruff and Mypy quality checks to CI
- Added repeatable Python/Rust interval-combination benchmarks
- Advertised package type annotations with the PEP 561 `py.typed` marker

### Changed
- Consolidated package metadata in `pyproject.toml`
- Reworked internal imports to reduce reliance on package-level re-exports
- Improved README documentation and examples
- Added a stub for the optional Rust extension so Mypy can check the Python package without building Rust

### Fixed
- Corrected discrete interval dispatch for list and tuple inputs
- Fixed discrete fallback typing so only narrowed discrete intervals reach the discrete combiner
- Removed unexpected debug output from PDF cumulative sampling

## [0.3.0] - 2024-10-13

### Added
- Optional Rust-powered calculations for `combine_intervals`, using `combine_via_rust` for now
- Construct IntervalMeter using rust, with the `use_rust` input boolean for now
- Extra example and tests for these calculations

### Changed
- Version is now primarily stored in VERSION due to Py+Rust build conflict with it being in .py file

### Fixed
- Some cleanup

## [0.2.1] - 2024-08-17

### Changed
- Updated the version to 0.2.x as well, oops :)

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
