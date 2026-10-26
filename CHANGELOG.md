# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Raise the minimum supported Python version to 3.12 and align the Rust stable-ABI floor and CI targets; Python 3.10 and 3.11 are no longer supported.

## [0.4.0] - 2026-10-14

### Added
- Added runtime datetime-coordinate support to intervals and collections, including discrete `timedelta` steps and explicit timezone conversion.
- Added `IntervalMap` replacement mappings, range reset, and `combine_maps()`, plus `PriorityIntervalMap` with priority updates, provenance, explanations, active regions, batch lookup, nested resolution, and snapshots.
- Added `FunctionInterval` and `IntervalFunction` for piecewise numeric functions with explicit overlap combiners and defaults.
- Added `IntervalPmf` for discrete probability-mass distributions and expanded `IntervalPdf` with distribution summaries and regions, mixtures and conditioning, comparisons and distances, and sample-based diagnostics.
- Added interval utilities for coordinate distance, clamping, splitting, copying with a new value, and geometric or value-aware intersection.
- Added collection queries and analytics, including positional and range access, bounds and coverage, summary statistics, threshold regions, clipping, and contained intervals.
- Added compact discrete-set union, intersection, and difference paths for compatible runs and integer-multiple step sequences, avoiding point enumeration where the exact result stays compact.
- Added recursive `deep_copy()` while preserving the existing shallow `copy()` behavior.
- Added a deterministic solar-market dispatch example and expanded interval, collection, probability, temporal-coordinate, and discrete-semantics documentation.
- Added the `py.typed` marker, repeatable Python/Rust benchmarks, and Ruff/Mypy quality checks.
- Added a non-publishing Linux release-artifact workflow for the source distribution, CPython stable-ABI and PyPy wheels, and Python fallback wheel.

### Changed
- Exported `Coordinate` and `Length` typing aliases and tightened public annotations; numeric lengths are unchanged, while datetime geometric lengths return `timedelta`.
- Defined continuous bounds as finite and ordered, allowing zero-length intervals; adopted closed-set endpoint behavior and consistent ordering, equality, and hashing.
- Clarified discrete-set semantics: subset and superset use geometric coverage, `remove()` is exact while `discard()` is geometric, and set operations preserve represented coordinates and steps.
- Clarified that collection `.data` remains mutable and that `copy()` is shallow; use `deep_copy()` for recursive copies.
- Tightened the `IntervalPdf` contract to finite, non-negative, positive-length continuous distributions; unsupported inherited mutation and arithmetic operations now fail explicitly.
- Made the Python implementation the safe fallback when the optional Rust extension is unavailable; retained Rust acceleration for supported numeric inputs.
- Consolidated package metadata, modernized development dependency management and CI around uv, and clarified internal imports, extension stubs, and project documentation.

### Fixed
- Preserved signed datetime values in `IntervalMeter` combinations and corrected continuous and discrete set intersections.
- Preserved non-unit discrete steps and nearby coordinates through normalization and combination, while keeping tolerance limited to membership and indexing.
- Preserved closed-interval boundary points in continuous difference and corrected discrete dispatch and fallback typing.
- Removed unexpected debug output from PDF cumulative sampling.

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
