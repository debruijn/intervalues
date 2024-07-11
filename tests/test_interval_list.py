from intervalues import BaseInterval, EmptyInterval, IntervalCounterFloat, IntervalListFloat, IntervalSetFloat

INTERVAL_MANY = [5, 10, 25, 100, 250, 500, 1000, 10000]


def test_addition_base():
    a = IntervalListFloat([BaseInterval((0, 1))])
    b = BaseInterval((2, 3))
    c = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_list():
    a = IntervalListFloat([BaseInterval((0, 1))])
    b = IntervalListFloat([BaseInterval((2, 3))])
    c = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_overlap():
    a = IntervalListFloat([BaseInterval((0, 2))])
    b = IntervalListFloat([BaseInterval((1, 3))])
    c = IntervalListFloat([BaseInterval((0, 2)), BaseInterval((1, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_empty():
    a = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.copy()
    e = EmptyInterval()
    assert a + e == a
    assert e + a == a
    a += e
    assert a == b


def test_inequality_different_order():
    a = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = IntervalListFloat([BaseInterval((2, 3)), BaseInterval((0, 1))])
    assert not a == b


def test_equality_base():
    a = IntervalListFloat([BaseInterval((0, 1))])
    b = BaseInterval((0, 1))
    assert a == b
    assert b == a


def test_inequality_base_reduced():
    a = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((1, 2))])
    b = BaseInterval((0, 2))
    assert not a == b


def test_comparison():
    interval1 = IntervalListFloat([BaseInterval((0, 1))])
    interval2 = IntervalListFloat([BaseInterval((0, 2))])
    interval3 = IntervalListFloat([BaseInterval((1, 2))])
    interval4 = IntervalListFloat([BaseInterval((0, 1, 2))])
    interval5 = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((1, 2, 2))])
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
    interval1 = IntervalListFloat([BaseInterval((0, 1))])
    interval2 = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
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
    a = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((2, 4))*2])
    assert a.get_length() == 5
    assert a.get_length(BaseInterval((0, 1))) == 1
    assert a.get_length(BaseInterval((2, 4))) == 4


def test_find_which_contains():
    a = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((2, 3)) * 2])
    assert [a.find_which_contains(x) for x in [1, 2]] == [[x] for x in list(a)]


def test_contains():
    a = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert BaseInterval((0, 1)) in a
    assert BaseInterval((1, 3, 2)) in a
    assert 1 in a
    assert 2 in a
    assert 5.0 not in a


def test_contains_as_superset():
    a = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert BaseInterval((1, 2, 2)) in a
    assert BaseInterval((1.5, 2.5)) in a


def test_get_item():
    a = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert a[BaseInterval((0, 1))] == 1
    assert a[BaseInterval((1, 3))] == 2
    assert a[BaseInterval((1, 3, 2))] == 1
    assert a[1] == 3
    assert a[2] == 2
    assert a[5.0] == 0


def test_get_item_as_superset():
    a = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert a[BaseInterval((1.5, 2.5))] == 2
    assert a[BaseInterval((0, 0.5, 2))] == 1/2


def split_to_pairs(iterable):
    a = iter(iterable)
    return zip(a, a)


def test_min_max():
    a = IntervalListFloat([BaseInterval((0, 4))])
    b = IntervalListFloat([BaseInterval((0, 4)), BaseInterval((2, 3))])

    assert a.min() == 0
    assert b.min() == 0
    assert a.max() == 4
    assert b.max() == 4


def test_single_interval():
    a = IntervalListFloat([BaseInterval((0, 1))])
    b = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])

    assert a.as_single_interval() == BaseInterval(0, 1)
    assert b.as_single_interval() == BaseInterval(0, 3)


def test_as_counter():
    a = IntervalListFloat([BaseInterval((2, 3)), BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_counter()
    c = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((2, 3))*2])
    assert b == c


def test_as_set():
    a = IntervalCounterFloat([BaseInterval((0, 1)), BaseInterval((2, 3))*2])
    b = a.as_set()
    c = IntervalSetFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert b == c


def test_append():
    a = IntervalListFloat([BaseInterval((0, 1))])
    b = BaseInterval((2, 3))
    c = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    a.append(b)
    assert a == c


def test_extend():
    a = IntervalListFloat([BaseInterval((0, 1))])
    b = IntervalListFloat([BaseInterval((2, 3))])
    c = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    a.extend(b)
    assert a == c


def test_count():
    a = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert a.count(BaseInterval((0, 1))) == 1
    assert a.count(BaseInterval((1, 3))) == 2
    assert a.count(BaseInterval((1, 3, 2))) == 1
    assert a.count(1) == 3
    assert a.count(2) == 2
    assert a.count(5.0) == 0


def test_reverse():
    a = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = IntervalListFloat([BaseInterval((2, 3)), BaseInterval((0, 1))])
    assert not a == b
    a.reverse()
    assert a == b


def test_insert():
    a = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((2, 3))])
    a.insert(1, BaseInterval((4, 5)))
    b = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((4, 5)), BaseInterval((2, 3))])

    assert a == b


def test_sort():
    a = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((4, 5)), BaseInterval((2, 3))])
    a.sort()
    b = IntervalListFloat([BaseInterval((0, 1)), BaseInterval((2, 3)), BaseInterval((4, 5))])

    assert a == b