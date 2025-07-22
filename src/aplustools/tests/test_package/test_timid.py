"""TBA"""

from ...package.chronokit import *
import pytest

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty

if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts


def test_() -> (
    None
):  # That the package structure works is proof enough it works (for now)
    try:
        for i in range(100):
            timer = FlexTimer()
            timer.wait_ms(100)
            print(timer.end())
    except Exception as e:
        raise RuntimeError(f"Chronokit tests failed") from e
