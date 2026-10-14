import math

import pytest

from intervalues.base_interval import BaseInterval
from intervalues.interval_map import IntervalMap, combine_maps


def segment_bounds(interval_map):
    return [(interval.start, interval.stop, payload) for interval, payload in interval_map.items()]


def test_assign_creates_sorted_segments_and_items_returns_snapshot():
    interval_map = IntervalMap(default=None)
    interval_map.assign(5, 8, "late")
    interval_map.assign(0, 2, "early")

    snapshot = interval_map.items()

    assert segment_bounds(interval_map) == [(0, 2, "early"), (5, 8, "late")]
    assert tuple(interval for interval in interval_map) == tuple(pair[0] for pair in snapshot)
    assert isinstance(snapshot, tuple)
    assert len(interval_map) == 2
    interval_map.clear()
    assert len(snapshot) == 2
    assert len(interval_map) == 0


def test_items_and_iteration_do_not_expose_mutable_internal_intervals():
    interval_map = IntervalMap()
    interval_map.assign(0, 2, "value")

    item_interval = interval_map.items()[0][0]
    iterated_interval = next(iter(interval_map))
    item_interval.start = -10
    iterated_interval.stop = 20

    assert segment_bounds(interval_map) == [(0, 2, "value")]


@pytest.mark.parametrize(
    ("start", "stop", "expected"),
    [
        (2, 4, [(0, 2, "old"), (2, 4, "new"), (4, 10, "old")]),
        (0, 4, [(0, 4, "new"), (4, 10, "old")]),
        (6, 10, [(0, 6, "old"), (6, 10, "new")]),
        (-2, 12, [(-2, 12, "new")]),
        (0, 10, [(0, 10, "new")]),
    ],
)
def test_assign_replaces_all_overlap_shapes(start, stop, expected):
    interval_map = IntervalMap()
    interval_map.assign(0, 10, "old")

    interval_map.assign(start, stop, "new")

    assert segment_bounds(interval_map) == expected


def test_assign_overwrites_multiple_segments_and_preserves_outer_fragments():
    interval_map = IntervalMap()
    interval_map.assign(0, 2, "left")
    interval_map.assign(2, 4, "middle")
    interval_map.assign(4, 6, "right")

    interval_map.assign(1, 5, "replacement")

    assert segment_bounds(interval_map) == [
        (0, 1, "left"),
        (1, 5, "replacement"),
        (5, 6, "right"),
    ]


def test_assignment_uses_base_interval_value_unless_overridden():
    interval_map = IntervalMap()
    interval_map.assign(BaseInterval(1, 3, value=7))
    interval_map.assign(BaseInterval(4, 6, value=8), value=["opaque", 1])
    interval_map.assign(BaseInterval(7, 9), value=["keyword"])

    assert segment_bounds(interval_map) == [
        (1, 3, 7),
        (4, 6, ["opaque", 1]),
        (7, 9, ["keyword"]),
    ]


def test_equal_adjacent_payloads_merge_but_default_payloads_remain_covered():
    interval_map = IntervalMap(default="default")
    interval_map.assign(0, 2, ["same"])
    interval_map.assign(2, 4, ["same"])
    interval_map.assign(4, 5, "default")

    assert segment_bounds(interval_map) == [
        (0, 4, ["same"]),
        (4, 5, "default"),
    ]
    assert interval_map.items()[1][1] == interval_map.default


@pytest.mark.parametrize(
    ("start", "stop", "error", "message"),
    [
        (1, 1, ValueError, "positive length"),
        (2, 1, ValueError, "less than or equal"),
        (True, 2, TypeError, "start must be an int, float, or datetime"),
        (0, False, TypeError, "stop must be an int, float, or datetime"),
        (float("nan"), 2, ValueError, "start must be finite"),
        (0, float("inf"), ValueError, "stop must be finite"),
    ],
)
def test_invalid_assignment_does_not_change_existing_map(start, stop, error, message):
    interval_map = IntervalMap()
    interval_map.assign(0, 3, "stable")
    before = interval_map.items()

    with pytest.raises(error, match=message):
        interval_map.assign(start, stop, "invalid")

    assert interval_map.items() == before


def test_assign_rejects_unsupported_conflict_and_malformed_arguments():
    interval_map = IntervalMap()

    with pytest.raises(ValueError, match="conflict must be 'replace'"):
        interval_map.assign(0, 1, "value", conflict="ignore")
    with pytest.raises(TypeError, match="requires all three"):
        interval_map.assign(0, 1)
    with pytest.raises(TypeError, match="value keyword"):
        interval_map.assign(BaseInterval(0, 1), "one", "two")


def test_reset_removes_coverage_and_preserves_unaffected_fragments():
    interval_map = IntervalMap(default=None)
    interval_map.assign(0, 10, "outer")
    interval_map.reset(BaseInterval(3, 7))

    assert segment_bounds(interval_map) == [(0, 3, "outer"), (7, 10, "outer")]


@pytest.mark.parametrize(
    ("reset_interval", "expected"),
    [
    (BaseInterval(2, 4), [(0, 2, "left"), (4, 6, "middle"), (6, 8, "right")]),
    (BaseInterval(-1, 3), [(3, 6, "middle"), (6, 8, "right")]),
    (BaseInterval(3, 7), [(0, 3, "left"), (7, 8, "right")]),
    (BaseInterval(-1, 7), [(7, 8, "right")]),
    ],
)
def test_reset_handles_partial_full_and_multiple_overlaps(reset_interval, expected):
    interval_map = IntervalMap()
    interval_map.assign(0, 3, "left")
    interval_map.assign(3, 6, "middle")
    interval_map.assign(6, 8, "right")

    interval_map.reset(reset_interval)

    assert segment_bounds(interval_map) == expected


@pytest.mark.parametrize(
    ("interval", "error", "message"),
    [
        (BaseInterval(2, 2), ValueError, "positive length"),
        ("not an interval", TypeError, "must be a BaseInterval"),
    ],
)
def test_invalid_reset_does_not_change_existing_map(interval, error, message):
    interval_map = IntervalMap()
    interval_map.assign(0, 3, "stable")
    before = interval_map.items()

    with pytest.raises(error, match=message):
        interval_map.reset(interval)

    assert interval_map.items() == before


def test_reset_rejects_reversed_interval_without_changing_map():
    interval_map = IntervalMap()
    interval_map.assign(0, 3, "stable")
    before = interval_map.items()
    invalid_interval = BaseInterval(1, 3)
    invalid_interval.start = 3
    invalid_interval.stop = 1

    with pytest.raises(ValueError, match="less than or equal"):
        interval_map.reset(invalid_interval)

    assert interval_map.items() == before


def test_reset_does_not_retain_payload_equal_to_default_as_coverage():
    interval_map = IntervalMap(default=None)
    interval_map.assign(0, 5, "mapped")
    interval_map.reset(BaseInterval(0, 5))

    assert interval_map.items() == ()


def test_merge_comparison_error_keeps_assignment_atomic():
    class ExplodingEquality:
        def __eq__(self, other):
            raise RuntimeError("equality failed")

    interval_map = IntervalMap()
    interval_map.assign(0, 1, ExplodingEquality())
    before = interval_map.items()

    with pytest.raises(RuntimeError, match="equality failed"):
        interval_map.assign(1, 2, ExplodingEquality())

    assert interval_map.items() == before


def test_copy_is_shallow_and_segment_instances_are_not_replaced():
    payload = []
    interval_map = IntervalMap(default=payload)
    interval_map.assign(0, 2, payload)

    copied = interval_map.copy()

    assert copied is not interval_map
    assert copied.default is payload
    assert copied.items() == interval_map.items()
    assert copied.items()[0][1] is payload
    assert math.isfinite(copied.items()[0][0].start)


def test_lookup_and_membership_follow_half_open_boundaries():
    interval_map = IntervalMap(default="gap")
    interval_map.assign(0, 2, "left")
    interval_map.assign(2, 4, "right")

    assert interval_map[0] == "left"
    assert interval_map[1.999] == "left"
    assert interval_map[2] == "right"
    assert interval_map[4] == "gap"
    assert 0 in interval_map
    assert 2 in interval_map
    assert 4 not in interval_map
    assert -1 not in interval_map


def test_lookup_distinguishes_covered_none_and_default_equal_payloads():
    interval_map = IntervalMap(default=None)
    interval_map.assign(0, 1, None)
    interval_map.assign(2, 3, "default")
    interval_map.default = "default"

    assert interval_map[0.5] is None
    assert 0.5 in interval_map
    assert interval_map[2.5] == "default"
    assert 2.5 in interval_map
    assert interval_map[1.5] == "default"
    assert 1.5 not in interval_map


@pytest.mark.parametrize(
    ("coordinate", "error", "message"),
    [
        (True, TypeError, "coordinate must be an int, float, or datetime"),
        ("1", TypeError, "coordinate must be an int, float, or datetime"),
        (float("nan"), ValueError, "coordinate must be finite"),
        (float("inf"), ValueError, "coordinate must be finite"),
    ],
)
def test_lookup_rejects_invalid_coordinates(coordinate, error, message):
    interval_map = IntervalMap()

    with pytest.raises(error, match=message):
        interval_map[coordinate]


def test_contains_returns_false_for_non_coordinate_values():
    interval_map = IntervalMap()
    interval_map.assign(0, 1, "value")

    assert True not in interval_map
    assert "0.5" not in interval_map
    assert float("nan") not in interval_map


def test_combine_maps_partitions_resolved_maps_and_substitutes_absent():
    first = IntervalMap(default=99)
    first.assign(0, 60, 1)
    first.assign(20, 40, 2)
    second = IntervalMap(default=88)
    second.assign(0, 30, 3)
    first_before = first.items()
    second_before = second.items()

    combined = combine_maps([first, second], combine=sum, absent=0)

    assert segment_bounds(combined) == [
        (0, 20, 4),
        (20, 30, 5),
        (30, 40, 2),
        (40, 60, 1),
    ]
    assert combined.default == 0
    assert first.items() == first_before
    assert second.items() == second_before


def test_combine_maps_preserves_input_order_for_non_commutative_combiner():
    first = IntervalMap()
    first.assign(0, 2, "A")
    second = IntervalMap()
    second.assign(0, 2, "B")
    seen = []

    def combine(values):
        seen.append(values)
        return "".join(values)

    combined = combine_maps([first, second], combine=combine, absent="-")

    assert combined[1] == "AB"
    assert seen == [("A", "B")]


def test_combine_maps_omits_all_absent_spans_and_uses_absent_as_default():
    first = IntervalMap()
    first.assign(0, 1, 1)
    second = IntervalMap()
    second.assign(2, 3, 2)
    calls = []

    def combine(values):
        calls.append(values)
        return sum(values)

    combined = combine_maps([first, second], combine=combine, absent=0)

    assert segment_bounds(combined) == [(0, 1, 1), (2, 3, 2)]
    assert calls == [(1, 0), (0, 2)]
    assert combined[1.5] == 0


def test_combine_maps_empty_inputs_return_empty_map_with_absent_default():
    assert combine_maps([], combine=sum, absent=0).items() == ()
    assert combine_maps([IntervalMap(default=9)], combine=sum, absent=0).items() == ()


def test_combine_maps_keeps_none_and_unhashable_payloads_opaque():
    first = IntervalMap()
    first.assign(0, 1, None)
    second = IntervalMap()
    second.assign(0, 1, ["payload"])

    combined = combine_maps(
        [first, second],
        combine=lambda values: list(values),
        absent="absent",
    )

    assert combined[0.5] == [None, ["payload"]]


def test_combine_maps_propagates_combiner_errors_and_validates_inputs():
    source = IntervalMap()
    source.assign(0, 1, 1)

    def fail_combine(values):
        raise RuntimeError("combine failed")

    with pytest.raises(RuntimeError, match="combine failed"):
        combine_maps([source], combine=fail_combine, absent=0)
    with pytest.raises(TypeError, match="only IntervalMap"):
        combine_maps([object()], combine=sum, absent=0)
    with pytest.raises(TypeError, match="combine must be callable"):
        combine_maps([source], combine=None, absent=0)
