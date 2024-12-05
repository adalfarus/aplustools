"""TBA"""
import secrets as _secrets
import random as _random
import math as _math
import os as _os

from ..package import enforce_hard_deps as _enforce_hard_deps, optional_import as _optional_import

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

__deps__ = ["numpy"]
__hard_deps__ = []
_enforce_hard_deps(__hard_deps__, __name__)

_np_random = _optional_import("numpy.random")
_ndarray = _optional_import("numpy.ndarray")


class _SupportsLenAndGetItem(_ty.Protocol):
    def __len__(self) -> int:
        ...

    def __getitem__(self, index: int) -> str | list:
        ...
