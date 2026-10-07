from enum import IntEnum
from fractions import Fraction

import pytest

from intervalues.base_interval import BaseInterval
from intervalues.interval_map import (
    IntervalMap,
    PriorityIntervalMap,
    PriorityLookupResult,
    PriorityResolutionExplanation,
    PrioritySourceHandle,
)


def make_map(start, stop, value, *, default=None):
    interval_map = IntervalMap(default=default)
    interval_map.assign(start, stop, value)
    return interval_map


def bounds(intervals):
    return [(interval.start, interval.stop) for interval in intervals]


def test_lookup_uses_highest_explicit_priority_then_resolver_default():
    resolver = PriorityIntervalMap(default="gap")
    low = make_map(0, 5, "low", default="low default")
    high = make_map(2, 4, "high", default="high default")
    resolver.add(low, 1)
    resolver.add(high, 2)

    assert [resolver[x] for x in (-1, 0, 1, 2, 3, 4, 5)] == [
        "gap", "low", "low", "high", "high", "low", "gap",
    ]
    assert 3 in resolver
    assert 5 not in resolver


def test_lookup_preserves_explicit_none_and_default_equal_coverage():
    resolver = PriorityIntervalMap(default=None)
    source = make_map(0, 1, None, default="source default")
    resolver.add(source, 1)
    source.assign(2, 3, "resolver default")
    resolver.default = "resolver default"

    assert resolver[0.5] is None
    assert 0.5 in resolver
    assert resolver[2.5] == "resolver default"
    assert 2.5 in resolver
    assert resolver[1.5] == "resolver default"
    assert 1.5 not in resolver


def test_lookup_can_return_winning_source_and_priority_or_resolver_default():
    resolver = PriorityIntervalMap(default="gap")
    lower_handle, _ = resolver.add(make_map(0, 4, "lower"), 1)
    upper_handle, _ = resolver.add(make_map(1, 3, None), 2)

    covered = resolver.lookup(2, with_priority=True)
    uncovered = resolver.lookup(5, with_priority=True)

    assert covered == PriorityLookupResult(value=None, source=upper_handle, priority=2)
    assert covered.used_default is False
    assert uncovered == PriorityLookupResult(value="gap", source=None, priority=None)
    assert uncovered.used_default is True
    assert resolver.lookup(0.5, with_priority=True).source is lower_handle
    assert resolver[2] is None


def test_explain_reports_uncovered_higher_precedence_sources_and_winner():
    resolver = PriorityIntervalMap(default="gap")
    low_handle, _ = resolver.add(make_map(0, 5, "low"), 1)
    middle_handle, _ = resolver.add(make_map(2, 4, "middle"), 3)
    high_handle, _ = resolver.add(make_map(3, 5, "high"), 5)
    unrelated_handle, _ = resolver.add(make_map(20, 30, "unrelated"), 7)

    explanation = resolver.explain(2.5)
    assert explanation == PriorityResolutionExplanation(
        coordinate=2.5,
        value="middle",
        source=middle_handle,
        priority=3,
        uncovered_sources=(unrelated_handle, high_handle),
    )
    assert explanation.used_default is False
    assert low_handle not in explanation.uncovered_sources


def test_explain_default_lists_all_sources_as_uncovered_in_precedence_order():
    resolver = PriorityIntervalMap(default=None, tie_policy="last")
    first_handle, _ = resolver.add(make_map(0, 1, None), 2)
    second_handle, _ = resolver.add(make_map(0, 1, "same priority"), 2)
    higher_handle, _ = resolver.add(make_map(3, 4, "higher"), 5)

    explanation = resolver.explain(2)
    assert explanation == PriorityResolutionExplanation(
        coordinate=2,
        value=None,
        source=None,
        priority=None,
        uncovered_sources=(higher_handle, second_handle, first_handle),
    )
    assert explanation.used_default is True


@pytest.mark.parametrize(
    ("coordinate", "error", "message"),
    [
        (True, TypeError, "coordinate must be an int or float"),
        ("1", TypeError, "coordinate must be an int or float"),
        (float("nan"), ValueError, "coordinate must be finite"),
        (float("inf"), ValueError, "coordinate must be finite"),
    ],
)
def test_lookup_and_explain_reject_invalid_coordinates(coordinate, error, message):
    resolver = PriorityIntervalMap()

    with pytest.raises(error, match=message):
        resolver.lookup(coordinate, with_priority=True)
    with pytest.raises(error, match=message):
        resolver.explain(coordinate)


def test_add_returns_handle_and_whether_registration_wins_any_region():
    resolver = PriorityIntervalMap()
    higher = make_map(0, 5, "higher")
    lower_partially_masked = make_map(2, 7, "lower")
    lower_fully_masked = make_map(1, 3, "masked")
    empty = IntervalMap()

    _, higher_active = resolver.add(higher, 3)
    lower_handle, lower_active = resolver.add(lower_partially_masked, 1)
    _, masked_active = resolver.add(lower_fully_masked, 0)
    _, empty_active = resolver.add(empty, -1)

    assert higher_active is True
    assert lower_active is True
    assert masked_active is False
    assert empty_active is False
    assert resolver[6] == "lower"
    assert isinstance(lower_handle, PrioritySourceHandle)


def test_active_regions_returns_half_open_snapshot_of_only_winning_coverage():
    resolver = PriorityIntervalMap()
    high = make_map(2, 4, "high")
    low = IntervalMap()
    low.assign(0, 2, "low")
    low.assign(2, 6, "low")
    low.assign(8, 9, "low")
    low_handle, _ = resolver.add(low, 1)
    resolver.add(high, 2)

    regions = resolver.active_regions(low_handle)
    assert bounds(regions) == [(0, 2), (4, 6), (8, 9)]

    regions[0].start = -100
    low.assign(6, 7, "new live region")
    assert bounds(resolver.active_regions(low_handle)) == [(0, 2), (4, 7), (8, 9)]


def test_active_regions_and_priority_update_reflect_live_sources_and_priority():
    resolver = PriorityIntervalMap()
    low_handle, _ = resolver.add(make_map(0, 10, "low"), 1)
    high_handle, initially_active = resolver.add(make_map(3, 7, "high"), 2)

    assert initially_active is True
    assert bounds(resolver.active_regions(low_handle)) == [(0, 3), (7, 10)]
    assert bounds(resolver.active_regions(high_handle)) == [(3, 7)]

    assert resolver.update_priority(high_handle, 0) is False
    assert bounds(resolver.active_regions(low_handle)) == [(0, 10)]
    assert bounds(resolver.active_regions(high_handle)) == []

    assert resolver.update_priority(high_handle, 3) is True
    assert bounds(resolver.active_regions(low_handle)) == [(0, 3), (7, 10)]

    resolver.replace(high_handle, IntervalMap())
    assert resolver.update_priority(high_handle, 3) is False
    assert bounds(resolver.active_regions(high_handle)) == []


def test_active_regions_rejects_stale_or_foreign_handles():
    resolver = PriorityIntervalMap()
    other = PriorityIntervalMap()
    handle, _ = resolver.add(make_map(0, 1, "value"), 1)

    with pytest.raises(KeyError, match="not registered"):
        other.active_regions(handle)
    resolver.remove(handle)
    with pytest.raises(KeyError, match="not registered"):
        resolver.active_regions(handle)


@pytest.mark.parametrize(
    ("tie_policy", "expected"),
    [("first", "first"), ("last", "last")],
)
def test_equal_priority_first_or_last_registration_wins(tie_policy, expected):
    resolver = PriorityIntervalMap(tie_policy=tie_policy)
    resolver.add(make_map(0, 2, "first"), 1)
    resolver.add(make_map(0, 2, "last"), 1)

    assert resolver[1] == expected


def test_equal_priority_can_be_rejected_during_add_and_reprioritization():
    resolver = PriorityIntervalMap(tie_policy="error")
    first, _ = resolver.add(make_map(0, 2, "first"), 1)
    second, _ = resolver.add(make_map(0, 2, "second"), 2)

    with pytest.raises(ValueError, match="priority values must be unique"):
        resolver.add(make_map(0, 2, "duplicate"), 1)
    with pytest.raises(ValueError, match="priority values must be unique"):
        resolver.update_priority(second, 1)

    assert resolver[1] == "second"
    assert resolver.update_priority(second, 3) is True
    assert resolver[1] == "second"
    assert resolver[1] != resolver.default
    assert resolver.update_priority(first, 0) is False
    assert resolver[1] == "second"


def test_equal_priority_tie_break_keys_and_registration_order():
    resolver = PriorityIntervalMap(tie_policy="key")
    resolver.add(make_map(0, 2, "first"), 1, tie_break_key=7)
    resolver.add(make_map(0, 2, "lower key"), 1, tie_break_key=2)
    resolver.add(make_map(0, 2, "equal key later"), 1, tie_break_key=7)

    assert resolver[1] == "first"


def test_numeric_priorities_accept_int_enum_and_reject_invalid_values():
    class Priority(IntEnum):
        LOW = 1
        HIGH = 2

    resolver = PriorityIntervalMap()
    resolver.add(make_map(0, 1, "enum"), Priority.HIGH)
    assert resolver[0.5] == "enum"
    resolver.add(make_map(1, 2, "fraction"), Fraction(10**1000, 3))
    assert resolver[1.5] == "fraction"

    for invalid in (True, "1"):
        with pytest.raises(TypeError, match="finite real number"):
            resolver.add(IntervalMap(), invalid)
    for invalid in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError, match="priority must be finite"):
            resolver.add(IntervalMap(), invalid)


def test_live_edits_replacement_and_removal_reveal_lower_priority_source():
    resolver = PriorityIntervalMap(default="gap")
    lower = make_map(0, 5, "lower")
    upper = make_map(1, 4, "upper")
    lower_handle, _ = resolver.add(lower, 1)
    upper_handle, _ = resolver.add(upper, 2)

    upper.reset(BaseInterval(2, 3))
    assert resolver[2.5] == "lower"

    replacement = make_map(2, 3, "replacement")
    resolver.replace(upper_handle, replacement)
    assert resolver[2.5] == "replacement"
    assert resolver[1.5] == "lower"

    resolver.remove(upper_handle)
    assert resolver[2.5] == "lower"
    assert resolver[5] == "gap"
    assert resolver[1] == "lower"

    with pytest.raises(KeyError, match="not registered"):
        resolver.remove(upper_handle)
    with pytest.raises(KeyError, match="not registered"):
        resolver.replace(upper_handle, upper)
    with pytest.raises(KeyError, match="not registered"):
        resolver.update_priority(upper_handle, 3)

    next_handle, _ = resolver.add(upper, 2)
    assert next_handle is not upper_handle
    assert resolver[1.5] == "upper"
    assert lower_handle is not next_handle


def test_handles_are_registration_specific_even_for_same_map_object():
    resolver = PriorityIntervalMap(tie_policy="last")
    source = make_map(0, 1, "value")
    first, _ = resolver.add(source, 1)
    second, _ = resolver.add(source, 1)

    assert first is not second
    resolver.remove(second)
    assert resolver[0.5] == "value"


@pytest.mark.parametrize(
    ("operation", "expected_error", "message"),
    [
        ("bad_map", TypeError, "source must be an IntervalMap"),
        ("missing_key", TypeError, "tie_break_key is required"),
        ("unexpected_key", TypeError, "only supported"),
        ("unknown_tie_policy", ValueError, "tie_policy must be"),
    ],
)
def test_source_and_tie_configuration_validation(operation, expected_error, message):
    if operation == "unknown_tie_policy":
        with pytest.raises(expected_error, match=message):
            PriorityIntervalMap(tie_policy="unknown")
    elif operation == "bad_map":
        with pytest.raises(expected_error, match=message):
            PriorityIntervalMap().add(object(), 1)
    elif operation == "missing_key":
        with pytest.raises(expected_error, match=message):
            PriorityIntervalMap(tie_policy="key").add(IntervalMap(), 1)
    else:
        with pytest.raises(expected_error, match=message):
            PriorityIntervalMap().add(IntervalMap(), 1, tie_break_key=0)
