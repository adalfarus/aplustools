"""TBA"""
from ...data.dummy import *
import pytest

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty
if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts


@pytest.mark.skipif(condition='sys.version[0] != "2"', reason="Dummy2 is only available for Python 2")
def test_dummy2() -> None:
    dummy2 = Dummy2()  # for python 2
    assert dummy2.anything == dummy2
    assert dummy2() == dummy2
    dummy2['key'] = 'value'
    _ = dummy2['key']
    _ = str(dummy2)
    _ = repr(dummy2)
    with pytest.raises(AssertionError):
        assert dummy2 == 123
    for x in dummy2:
        assert False, "Should not iterate"  # dummy2 returns empty iterator
    assert len(dummy2) == 0
    assert False if dummy2 else True


@pytest.mark.skipif(condition='sys.version[0] != "3"', reason="Dummy2 is only available for Python 3")
def test_dummy3() -> None:
    dummy3 = Dummy3()  # for python 3
    assert dummy3.something == dummy3
    assert dummy3() == dummy3
    dummy3[42] = 'answer'
    _ = dummy3[42]
    _ = str(dummy3)
    _ = repr(dummy3)
    with pytest.raises(AssertionError):
        assert dummy3 == "whatever"
    for x in dummy3:
        assert False, "Should not iterate"  # dummy3 returns empty iterator
    assert len(dummy3) == 0
    assert False if dummy3 else True
