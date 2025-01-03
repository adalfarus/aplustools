"""TBA"""

from ..package import setup_lazy_loaders as _setup_lazy_loaders
from . import _direct
from typing import TYPE_CHECKING as _TYPE_CHECKING

if _TYPE_CHECKING:
    from ._direct import *
    from . import request, utils

_setup_lazy_loaders(
    globals(),
    {
        "request": ".web.request",
        "utils": ".web.utils"
    }, _direct)
