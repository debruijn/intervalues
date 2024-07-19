from intervalues import BaseInterval, IntervalMeter, EmptyInterval, IntervalSet, IntervalList, IntervalCounter, IntervalPdf
import pytest


def test_total_length():
    a = IntervalPdf([BaseInterval(0, 1), BaseInterval(2, 3)])
    assert a.total_length() == 1
    assert a.total_length(force=True) == 1

    a.data[BaseInterval(0, 1)] = 3
    assert a.total_length() == 1
    assert a.total_length(force=True) > 1


def test_normalize():
    a = IntervalPdf(BaseInterval(0, 1))
    a.data[BaseInterval(0, 1)] = 3
    a.normalize()
    assert a.total_length(force=True) == 1


def test_normalize_init():
    a = IntervalPdf([BaseInterval(0, 1)])
    b = IntervalPdf([BaseInterval(0, 1, 2)])
    assert a == b


def test_normalize_pop():
    a = IntervalPdf([BaseInterval(0, 1), BaseInterval(2, 3)])
    assert a.total_length(force=True) == 1
    a.popitem()
    assert a.total_length(force=True) == 1

    a = IntervalPdf([BaseInterval(0, 1), BaseInterval(2, 3)])
    a.pop(BaseInterval(2, 3))
    assert a.total_length(force=True) == 1


def test_addition_base():
    a = IntervalPdf([BaseInterval((0, 1))])
    b = BaseInterval((2, 3))
    c = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_base_value():
    a = IntervalPdf([BaseInterval((0, 1))])
    b = BaseInterval((2, 3, 2))
    c = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3, 2))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_pdf():
    a = IntervalPdf([BaseInterval((0, 1))])
    b = IntervalPdf([BaseInterval((2, 3))])
    c = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_overlap():
    a = IntervalPdf([BaseInterval((0, 2))])
    b = IntervalPdf([BaseInterval((1, 3))])
    c = IntervalPdf([BaseInterval((0, 1)), BaseInterval((1, 2)) * 2, BaseInterval((2, 3))])
    assert a + b == c
    a += b
    assert a == c


def test_addition_empty():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.copy()
    e = EmptyInterval()
    assert a + e == a
    assert e + a == a
    a += e
    assert a == b


def test_subtraction_base():
    a = IntervalPdf([BaseInterval((0, 1))])
    b = BaseInterval((2, 3, 0.5))
    c = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert c - b == a
    assert -b + c == a
    c -= b
    assert a == c


def test_subtraction_pdf():
    a = IntervalPdf([BaseInterval((0, 1))])
    b = IntervalPdf([BaseInterval((2, 3))])
    c = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert c - b == a
    c -= b
    assert a == c


@pytest.mark.parametrize("mult", (2, -2, 0))
def test_multiplication(mult):
    a = IntervalPdf([BaseInterval((0, 2))]) * mult
    b = IntervalPdf([BaseInterval((0, 2))])
    assert a == b
    a *= mult
    assert a == b*mult


def test_equality_different_order():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = IntervalPdf([BaseInterval((2, 3)), BaseInterval((0, 1))])
    assert a == b


def test_find_which_contains():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((1, 3)) * 2])
    assert [a.find_which_contains(x) for x in [1, 2]] == list(a.keys())


def test_contains():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert BaseInterval((0, 1)) in a
    assert BaseInterval((1, 3, 2)) in a
    assert 1 in a
    assert 2 in a
    assert 5.0 not in a


def test_contains_as_superset():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert BaseInterval((1, 2, 2)) in a
    assert BaseInterval((1.5, 2.5)) in a


def test_get_item():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert a[BaseInterval((0, 1))] == 0.2
    assert a[BaseInterval((1, 3))] == 0.4
    assert a[BaseInterval((1, 3, 2))] == 0.2
    assert a[1] == 0.2
    assert a[2] == 0.4
    assert a[5.0] == 0


def test_get_item_as_superset():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((1, 3), value=2)])
    assert a[BaseInterval((1.5, 2.5))] == 0.4
    assert a[BaseInterval((0, 0.5, 2))] == 0.1


def split_to_pairs(iterable):
    a = iter(iterable)
    return zip(a, a)


def test_min_max():
    a = IntervalPdf([BaseInterval((0, 4))])
    b = IntervalPdf([BaseInterval((0, 4)), BaseInterval((2, 3))])

    assert a.min() == 0
    assert b.min() == 0
    assert a.max() == 4
    assert b.max() == 4


def test_single_interval():
    a = IntervalPdf([BaseInterval((0, 1))])
    b = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])

    assert a.as_single_interval() == BaseInterval(0, 1)
    assert b.as_single_interval() == BaseInterval(0, 3)


def test_as_set():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_set()
    c = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert b == c


def test_as_set_value():
    a = IntervalPdf([BaseInterval((0, 1, 2)), BaseInterval((2, 3, 3))])
    b = a.as_set()
    c = IntervalSet([BaseInterval((0, 1)), BaseInterval((2, 3))])
    assert b == c


def test_as_list():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_list()
    c = IntervalList([BaseInterval((0, 1, 0.5)), BaseInterval((2, 3, 0.5))])
    assert b == c


def test_as_list_value():
    a = IntervalPdf([BaseInterval((0, 1, 2)), BaseInterval((2, 3, 3))])
    b = a.as_list()
    c = IntervalList([BaseInterval((0, 1, 0.4)), BaseInterval((2, 3, 0.6))])
    assert b == c


def test_as_counter():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_counter()
    c = IntervalCounter()
    assert b == c


def test_as_meter():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3))])
    b = a.as_meter()
    c = IntervalMeter([BaseInterval((0, 1, 0.5)), BaseInterval((2, 3, 0.5))])
    assert b == c


def test_cumulative():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3, 2)), BaseInterval((3, 4))])
    assert a.cumulative(0) == 0
    assert a.cumulative(1) == 0.25
    assert a.cumulative(2) == 0.25
    assert a.cumulative(2.5) == 0.5
    assert a.cumulative(3) == 0.75
    assert a.cumulative(4) == 1


def test_inverse_cumulative():
    a = IntervalPdf([BaseInterval((0, 1)), BaseInterval((2, 3, 2)), BaseInterval((3, 4))])
    assert a.inverse_cumulative(0) == 0
    assert a.inverse_cumulative(0.25) == 1
    assert a.inverse_cumulative(0.5) == 2.5
    assert a.inverse_cumulative(0.75) == 3
    assert a.inverse_cumulative(1) == 4
