from intervalues import BaseInterval, EmptyInterval, IntervalSet, IntervalMeter, IntervalList, IntervalCounter
import pytest


def test_addition_base():
    a = IntervalSet([BaseInterval((0, 1))])
    b = BaseInterval((2, 3))
    c = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_set():
    a = IntervalSet([BaseInterval((0, 1))])
    b = IntervalSet([BaseInterval((2, 3))])
    c = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_overlap():
    a = IntervalSet([BaseInterval((0, 2))])
    b = IntervalSet([BaseInterval((1, 3))])
    c = IntervalSet([BaseInterval((0, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_empty():
    a = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.copy()
    e = EmptyInterval()
    assert a + e == a
    assert e + a == a
    a += e
    assert a == b


def test_subtraction_base():
    a = IntervalSet([BaseInterval((0, 1))])
    b = BaseInterval((2, 3))
    c = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert c - b == a
    assert -b + c == c
    c -= b
    assert a == c


def test_subtraction_set():
    a = IntervalSet([BaseInterval((0, 1))])
    b = IntervalSet([BaseInterval((2, 3))])
    c = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert c - b == a
    c -= b
    assert a == c


def test_subtraction_overlap():
    a = IntervalSet([BaseInterval((0, 1))])
    b = IntervalSet([BaseInterval((1, 3))])
    c = IntervalSet([BaseInterval((0, 3))])
    assert c - b == a
    c -= b
    assert a == c


def test_equality_different_order():
    a = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = IntervalSet([BaseInterval((2, 3)), BaseInterval((0, 1))])
    assert a == b


def test_equality_base():
    a = IntervalSet([BaseInterval((0, 1))])
    b = BaseInterval((0, 1))
    assert a == b
    assert b == a


def test_equality_base_reduced():
    a = IntervalSet([BaseInterval((0, 1)), BaseInterval((1, 2))])
    b = BaseInterval((0, 2))
    assert a == b
    assert b == a


def test_comparison():
    interval1 = IntervalSet([BaseInterval((0, 1))])
    interval2 = IntervalSet([BaseInterval((0, 2))])
    interval3 = IntervalSet([BaseInterval((1, 2))])
    interval4 = IntervalSet([BaseInterval((0, 1, 2))])
    interval5 = IntervalSet([BaseInterval((0, 1)), BaseInterval((1, 2, 2))])
    assert interval1 < interval3
    assert interval1 < interval2
    assert interval3 > interval2
    assert interval3 > interval1
    assert not interval1 < interval4
    assert not interval1 > interval4
    assert interval1 <= interval4
    assert interval1 >= interval4
    assert interval1 < interval5


def test_comparison_base():
    interval1 = IntervalSet([BaseInterval((0, 1))])
    interval2 = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    base1 = BaseInterval(0, 1)
    base2 = BaseInterval(1, 2)
    base3 = BaseInterval(0, 2)

    # Test in one direction
    assert interval1 <= base1
    assert interval1 >= base1
    assert not interval1 > base1
    assert not interval1 < base1
    assert interval1 < base2
    assert interval1 < base3
    assert interval2 > base1
    assert interval2 < base2
    assert interval2 < base3

    # Test in the other direction
    assert base1 >= interval1
    assert base1 <= interval1
    assert not base1 < interval1
    assert not base1 > interval1
    assert base2 > interval1
    assert base3 > interval1
    assert base1 < interval2
    assert base2 > interval2
    assert base3 > interval2


def test_length():
    a = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 4))*2])
    assert a.get_length() == 3
    assert a.get_length(BaseInterval((0, 1))) == 1
    assert a.get_length(BaseInterval((2, 4))) == 2


def test_find_which_contains():
    a = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3)) * 2])
    assert [a.find_which_contains(x) for x in [1, 2]] == list(a)


def test_contains():
    a = IntervalSet([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert BaseInterval((0, 1)) in a
    assert BaseInterval((1, 3, 2)) in a
    assert 1 in a
    assert 2 in a
    assert 5.0 not in a


def test_contains_as_superset():
    a = IntervalSet([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert BaseInterval((1, 2, 2)) in a
    assert BaseInterval((1.5, 2.5)) in a


def test_get_item():
    a = IntervalSet([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert a[BaseInterval((0, 1))] == 1
    assert a[BaseInterval((1, 3))] == 1
    assert a[BaseInterval((1, 3, 2))] == 1
    assert a[1] == 1
    assert a[2] == 1
    assert a[5.0] == 0


def test_get_item_as_superset():
    a = IntervalSet([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert a[BaseInterval((1.5, 2.5))] == 1
    assert a[BaseInterval((0, 0.5, 2))] == 1


def split_to_pairs(iterable):
    a = iter(iterable)
    return zip(a, a)


def test_min_max():
    a = IntervalSet([BaseInterval((0, 4))])
    b = IntervalSet([BaseInterval((0, 4)), BaseInterval((2, 3))])

    assert a.min() == 0
    assert b.min() == 0
    assert a.max() == 4
    assert b.max() == 4


def test_single_interval():
    a = IntervalSet([BaseInterval((0, 1))])
    b = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])

    assert a.as_single_interval() == BaseInterval(0, 1)
    assert b.as_single_interval() == BaseInterval(0, 3)


def test_as_meter():
    a = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_meter()
    c = IntervalMeter([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert b == c


def test_as_counter():
    a = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_counter()
    c = IntervalCounter([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert b == c


def test_as_list():
    a = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_list()
    c = IntervalList([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert b == c


def test_or():
    a = BaseInterval((0, 1)).as_set()
    b = BaseInterval((2, 3)).as_set()
    c = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a | b == c
    a |= b
    assert a == c


def test_xor():
    a = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = IntervalSet([BaseInterval((0, 1))])
    c = IntervalSet([BaseInterval((2, 3))])
    assert a ^ b == c
    a ^= b
    assert a == c


def test_intersection_overlapping_continuous_intervals():
    left = IntervalSet([BaseInterval(0, 3), BaseInterval(5, 8)])
    right = IntervalSet([BaseInterval(2, 6)])

    assert left.intersection(right) == IntervalSet([BaseInterval(2, 3), BaseInterval(5, 6)])
    assert left & right == IntervalSet([BaseInterval(2, 3), BaseInterval(5, 6)])
    assert left.intersection(right) != left + right


def test_intersection_includes_touching_continuous_boundaries():
    left = IntervalSet(BaseInterval(0, 1))
    right = IntervalSet(BaseInterval(1, 2))

    assert left.intersection(right) == IntervalSet(BaseInterval(1, 1))
    assert not left.isdisjoint(right)


def test_intersection_preserves_degenerate_continuous_ranges():
    point = IntervalSet(BaseInterval(1, 1))
    containing = IntervalSet(BaseInterval(0, 2))

    assert point.intersection(containing) == point
    assert containing.intersection(point) == point


def test_isdisjoint_for_continuous_ranges_requires_a_strict_gap():
    assert IntervalSet(BaseInterval(0, 1)).isdisjoint(IntervalSet(BaseInterval(2, 3)))
    assert not IntervalSet(BaseInterval(0, 1)).isdisjoint(IntervalSet(BaseInterval(1, 2)))


def test_intersection_update_replaces_contents():
    left = IntervalSet(BaseInterval(0, 3))
    right = IntervalSet(BaseInterval(2, 4))

    left.intersection_update(right)

    assert left == IntervalSet(BaseInterval(2, 3))


def test_intersection_with_empty_set_is_empty():
    assert IntervalSet(BaseInterval(0, 3)).intersection(IntervalSet()) == IntervalSet()
    assert IntervalSet().intersection(IntervalSet(BaseInterval(0, 3))) == IntervalSet()


def test_clip_returns_partial_continuous_coverage_and_endpoint_contact():
    coverage = IntervalSet([BaseInterval(0, 2), BaseInterval(4, 6)])

    assert coverage.clip(BaseInterval(1, 5)) == IntervalSet(
        [BaseInterval(1, 2), BaseInterval(4, 5)]
    )
    assert coverage.clip(BaseInterval(2, 3)) == IntervalSet(BaseInterval(2, 2))
    assert coverage.clip(BaseInterval(2.5, 3.5)).is_empty


def test_clip_uses_shared_discrete_points_and_accepts_empty_sets():
    from intervalues import BaseDiscreteInterval

    coverage = IntervalSet(BaseDiscreteInterval(0, count=5, step=2))
    assert coverage.clip(BaseDiscreteInterval(2, count=4, step=2)) == IntervalSet(
        BaseDiscreteInterval(2, count=4, step=2)
    )
    assert coverage.clip(BaseDiscreteInterval(1, count=3, step=2)).is_empty
    assert IntervalSet().clip(BaseInterval(0, 1)).is_empty
    assert IntervalSet().clip(BaseDiscreteInterval(0, 1)).is_empty


def test_clip_rejects_mixed_domains_and_non_interval_query():
    from intervalues import BaseDiscreteInterval

    with pytest.raises(TypeError, match="Cannot intersect discrete and continuous"):
        IntervalSet(BaseInterval(0, 2)).clip(BaseDiscreteInterval(0, 2))
    with pytest.raises(TypeError, match="interval must be a BaseInterval"):
        IntervalSet().clip((0, 2))


def test_contained_intervals_returns_sorted_normalized_segments():
    coverage = IntervalSet([BaseInterval(0, 2), BaseInterval(4, 6), BaseInterval(8, 10)])

    assert coverage.contained_intervals(BaseInterval(1, 7)) == (BaseInterval(4, 6),)
    assert coverage.contained_intervals(BaseInterval(0, 10)) == tuple(sorted(coverage.data))
    assert coverage.contained_intervals(BaseInterval(2, 4)) == ()


def test_contained_discrete_intervals_require_every_point_in_query_sequence():
    from intervalues import BaseDiscreteInterval

    coverage = IntervalSet([
        BaseDiscreteInterval(0, count=3, step=2),
        BaseDiscreteInterval(1, count=3, step=2),
    ])

    assert coverage.contained_intervals(BaseDiscreteInterval(0, count=6, step=1)) == tuple(
        sorted(coverage.data)
    )
    assert coverage.contained_intervals(BaseDiscreteInterval(0, count=3, step=2)) == (
        BaseDiscreteInterval(0, count=3, step=2),
    )


def test_contained_intervals_validates_query_type():
    with pytest.raises(TypeError, match="interval must be a BaseInterval"):
        IntervalSet().contained_intervals((0, 1))


def test_contained_intervals_rejects_mixed_coordinate_domains():
    from intervalues import BaseDiscreteInterval

    with pytest.raises(TypeError, match="Cannot compare discrete and continuous"):
        IntervalSet([BaseDiscreteInterval(0, 2)]).contained_intervals(BaseInterval(0, 2))


def test_set_operation_methods_match_operators_and_update_methods():
    left = IntervalSet(BaseInterval(0, 3))
    right = IntervalSet(BaseInterval(2, 5))

    assert left.union(right) == left | right
    assert left.intersection(right) == left & right
    assert left.difference(right) == left - right
    assert left.symmetric_difference(right) == left ^ right

    in_place_union = left.copy()
    in_place_union |= right
    assert in_place_union == left | right
    in_place_intersection = left.copy()
    in_place_intersection.intersection_update(right)
    assert in_place_intersection == left & right
    in_place_difference = left.copy()
    in_place_difference.difference_update(right)
    assert in_place_difference == left - right
    in_place_symmetric_difference = left.copy()
    in_place_symmetric_difference.symmetric_difference_update(right)
    assert in_place_symmetric_difference == left ^ right


def test_closed_interval_difference_retains_unrepresentable_boundary_point():
    left = IntervalSet(BaseInterval(0, 2))
    right = IntervalSet(BaseInterval(2, 3))

    assert left.difference(right) == IntervalSet(BaseInterval(0, 2))
    assert 2 in left.difference(right)


def test_remove_is_exact_while_discard_removes_geometric_coverage():
    whole = IntervalSet(BaseInterval(0, 3))

    with pytest.raises(KeyError):
        whole.remove(BaseInterval(1, 2))

    whole.remove(BaseInterval(0, 3, value=4))
    assert whole.is_empty

    remaining = IntervalSet(BaseInterval(0, 3))
    remaining.discard(BaseInterval(1, 2))
    assert remaining == IntervalSet([BaseInterval(0, 1), BaseInterval(2, 3)])


def test_discrete_intersection_uses_common_points_across_steps():
    from intervalues import BaseDiscreteInterval

    left = IntervalSet(BaseDiscreteInterval(0, count=5, step=1))
    right = IntervalSet(BaseDiscreteInterval(0, count=3, step=2))

    assert left.intersection(right) == IntervalSet(BaseDiscreteInterval(0, count=3, step=2))


def test_discrete_intersection_between_unaligned_step_sequences_is_empty():
    from intervalues import BaseDiscreteInterval

    left = IntervalSet(BaseDiscreteInterval(0, count=3, step=2))
    right = IntervalSet(BaseDiscreteInterval(1, count=3, step=2))

    assert left.intersection(right) == IntervalSet()
    assert left.isdisjoint(right)


def test_discrete_intersection_compacts_common_points_for_different_steps():
    from intervalues import BaseDiscreteInterval

    left = IntervalSet(BaseDiscreteInterval(0, count=3, step=1))
    right = IntervalSet(BaseDiscreteInterval(0, count=4, step=2))

    assert left.intersection(right) == IntervalSet(BaseDiscreteInterval(0, count=2, step=2))
    assert not left.isdisjoint(right)


def test_intersection_rejects_mixed_continuous_and_discrete_sets():
    import pytest
    from intervalues import BaseDiscreteInterval

    continuous = IntervalSet(BaseInterval(0, 3))
    discrete = IntervalSet(BaseDiscreteInterval(0, count=3))

    with pytest.raises(TypeError, match="Cannot intersect discrete and continuous"):
        continuous.intersection(discrete)


def test_interval_set_rejects_mixed_domains_in_comparison_and_construction():
    from intervalues import BaseDiscreteInterval

    continuous = IntervalSet(BaseInterval(0, 3))
    discrete = IntervalSet(BaseDiscreteInterval(0, count=3))

    with pytest.raises(TypeError, match="Cannot compare discrete and continuous"):
        continuous.isdisjoint(discrete)
    with pytest.raises(TypeError, match="Cannot compare discrete and continuous"):
        continuous.issubset(discrete)
    with pytest.raises(TypeError, match="Cannot compare discrete and continuous"):
        discrete.issuperset(continuous)
    with pytest.raises(TypeError, match="Cannot mix discrete and continuous"):
        IntervalSet([BaseInterval(0, 2), BaseDiscreteInterval(0, count=3)])
    with pytest.raises(TypeError, match="Cannot compare discrete and continuous"):
        BaseInterval(0, 1) in discrete
    with pytest.raises(TypeError, match="Cannot compare discrete and continuous"):
        discrete[BaseInterval(0, 1)]
    with pytest.raises(TypeError, match="Cannot mix discrete and continuous"):
        discrete.remove(BaseInterval(0, 1))


def test_difference_methods_accept_single_intervals_like_difference_operator():
    interval_set = IntervalSet(BaseInterval(0, 3))
    removed = BaseInterval(1, 2)

    assert interval_set.difference(removed) == interval_set - removed

    interval_set.difference_update(removed)
    assert interval_set == IntervalSet([BaseInterval(0, 1), BaseInterval(2, 3)])


def test_empty_set_subset_and_superset_rules_apply_across_domains():
    from intervalues import BaseDiscreteInterval

    empty = IntervalSet()
    continuous = IntervalSet(BaseInterval(0, 1))
    discrete = IntervalSet(BaseDiscreteInterval(0, count=2))

    assert empty.issubset(discrete)
    assert empty.issubset(continuous)
    assert discrete.issuperset(empty)
    assert continuous.issuperset(empty)
    assert not empty.issuperset(discrete)
    assert not discrete.issubset(empty)


def test_subset_compares_geometric_coverage_not_interval_segmentation():
    covering = IntervalSet()
    covering.data = {BaseInterval(0, 1), BaseInterval(1, 2)}
    target = IntervalSet(BaseInterval(0, 2))

    assert target.issubset(covering)
    assert covering.issuperset(target)


def test_discrete_set_union_and_difference_handle_overlapping_steps():
    from intervalues import BaseDiscreteInterval

    every_other = IntervalSet(BaseDiscreteInterval(0, count=3, step=2))
    every_point = IntervalSet(BaseDiscreteInterval(0, count=5, step=1))

    assert every_other | every_point == every_point
    assert every_point - every_other == IntervalSet(BaseDiscreteInterval(1, count=2, step=2))


def test_discrete_set_add_and_discard_accept_single_intervals():
    from intervalues import BaseDiscreteInterval

    interval_set = IntervalSet(BaseDiscreteInterval(0, count=5))
    interval_set.discard(BaseDiscreteInterval(1, count=2))

    assert interval_set == IntervalSet([BaseDiscreteInterval(0, count=1), BaseDiscreteInterval(3, count=2)])
    interval_set.add(BaseDiscreteInterval(1, count=2))
    assert interval_set == IntervalSet(BaseDiscreteInterval(0, count=5))
    interval_set.discard(BaseDiscreteInterval(0, count=5))
    assert interval_set == IntervalSet()


def test_continuous_set_add_and_discard_accept_single_intervals():
    interval_set = IntervalSet(BaseInterval(0, 3))
    interval_set.discard(BaseInterval(1, 2))

    assert interval_set == IntervalSet([BaseInterval(0, 1), BaseInterval(2, 3)])
    interval_set.add(BaseInterval(1, 2))
    assert interval_set == IntervalSet(BaseInterval(0, 3))


def test_continuous_set_add_merges_touching_regions():
    interval_set = IntervalSet([BaseInterval(0, 1), BaseInterval(2, 3)])

    interval_set.add(BaseInterval(1, 2))

    assert interval_set == IntervalSet(BaseInterval(0, 3))


def test_interval_set_add_ignores_interval_values():
    interval_set = IntervalSet()

    interval_set.add(BaseInterval(0, 1, value=4))

    assert interval_set == IntervalSet(BaseInterval(0, 1))


def test_superset_subset():
    a = IntervalSet([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    b = IntervalSet(BaseInterval(0, 1))
    c = IntervalSet([BaseInterval(0, 1), BaseInterval((2, 3))])
    assert a.issuperset(b)
    assert a.issuperset(c)
    assert a.issuperset(a)
    assert b.issubset(a)
    assert c.issubset(a)
    assert a.issubset(a)
