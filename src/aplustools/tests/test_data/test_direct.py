"""TBA"""

from ...data._direct import *
import pytest

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty

if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts


@pytest.mark.parametrize(
    "value, alignment, next_, previous", [(15, 20, 20, 0), (32, 10, 40, 30)]
)
def test_align(value: int, alignment: int, next_: int, previous: int) -> None:
    assert align_to_next(value, alignment) == next_
    assert align_to_previous(value, alignment) == previous


# @pytest.mark.filterwarnings("ignore:Unused function")
def test_reverse_map() -> None:
    with pytest.warns(DeprecationWarning):
        assert reverse_map([lambda x, y: x * y, lambda x, y: x**y], 10, y=20) == [
            200,
            100_000_000_000_000_000_000,
        ]


# @pytest.mark.filterwarnings("ignore:Unused function")
def test_gen_map() -> None:
    with pytest.warns(DeprecationWarning):
        lst: list[_ty.Any] = []
        for res in gen_map(
            [lambda x, y: x * y, lambda x, y: x**y],
            [(10,), (20,)],
            [{"y": 20}, {"y": 2}],
        ):
            lst.append(res)
        assert lst == [200, 400]


@pytest.mark.parametrize(
    "unsorted, sorted_",
    [([], []), ([3, 2, 1], [1, 2, 3]), (["Hello", "World"], ["Hello", "World"])],
)
def test_sorters(unsorted: list[int | str], sorted_: list[int | str]) -> None:
    for sorter_str in dir(Sorters):
        if sorter_str.startswith("_"):
            continue
        assert getattr(Sorters, sorter_str)(unsorted) == sorted_


class _NonString:
    def __str__(self) -> str:
        raise Exception


def test_beautify_json():
    result: str = beautify_json({"Hello": 15, "World": 21, "list": ["aa", "ss", "x"]})
    assert isinstance(result, str)
    beautify_json({"1": {1, 2, 3}})  # Can serialize set
    with pytest.raises(TypeError):
        beautify_json({"1": _NonString()})


@pytest.mark.parametrize(
    "reduce, min_, max_, expected", [(100, 10, 20, 20), (100, 100, 200, 100)]
)
def test_minmax(reduce: int, min_: int, max_: int, expected: int) -> None:
    assert minmax(reduce, min_, max_) == expected


def test_isEvenInt_bulk() -> None:
    for i in range(-500, 510):
        expected = int(i % 2 == 0)
        assert isEvenInt(i) == expected, f"Failed for isEvenInt({i})"


def test_isOddInt_bulk() -> None:
    for i in range(-500, 510):
        expected = int(i % 2 == 1)
        assert isOddInt(i) == expected, f"Failed for isOddInt({i})"


def test_isEvenFloat() -> None:
    assert isEvenFloat(2.2) == (True, True)
    assert isEvenFloat("4.4") == (True, True)
    assert isEvenFloat(float("nan")) == (False, False)
    assert isEvenFloat(float("inf")) == (False, False)
    assert isEvenFloat(0.0) == (True, True)


def test_isOddFloat() -> None:
    assert isOddFloat(3.3) == (True, True)
    assert isOddFloat("5.5") == (True, True)
    assert isOddFloat(float("nan")) == (False, False)
    assert isOddFloat(float("-inf")) == (False, False)
    assert isOddFloat(0.0) == (False, False)


def test_stdlist() -> None:
    lst = StdList(str)
    assert lst[0] == ""
    assert lst[1] == ""
    assert lst[100] == ""
    lst[1] = "Hello"
    lst[100] = "World"
    assert lst[1000, 100, 1] == ("", "World", "Hello")
    assert lst[1:10] == ("Hello", "", "", "", "", "", "", "", "")
    assert lst[1:3, 100:103] == ("Hello", "", "World", "", "")
    lst[1000, 100, 1] = ("", "", "")
    lst[1:10] = ("", "", "", "", "", "", "", "", "")
    lst[1:3, 100:103] = (("", ""), ("", "", ""))
    assert lst[1000, 100, 1] == ("", "", "")
    assert lst[1:10] == ("", "", "", "", "", "", "", "", "")
    assert lst[1:3, 100:103] == ("", "", "", "", "")
    assert lst.get(1001, int) == 0


def test_unnest_iterable() -> None:
    lst = [[[[[[1], 2], 3]], 4], 5]
    assert unnest_iterable(lst, max_depth=4) == [[1], 2, 3, 4, 5]
    assert unnest_iterable(lst, max_depth=5) == [1, 2, 3, 4, 5]


def test_cutoff_iterable() -> None:
    lst = [x for x in range(12_000)]
    assert (
        cutoff_iterable(lst, 7_500, 3, 0, True)
        == "[..[7500].., 7500, 7501, 7502, 7503, ..[4496]..]"
    )


def test_cutoff_string() -> None:
    string = "".join(chr(x) for x in range(32, 127))
    assert cutoff_string(string, 10, 10, True) == " !\"#$%&'()*..[74]..uvwxyz{|}~"
