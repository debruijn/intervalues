from intervalues import BaseInterval, EmptyInterval, IntervalSet, IntervalMeter, IntervalList, IntervalCounter


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
