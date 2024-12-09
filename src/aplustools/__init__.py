"""TBA"""
__version__ = "2.0.0.0a2"

from .package import _setup_lazy_loaders
from . import _direct
from typing import TYPE_CHECKING as _TYPE_CHECKING

if _TYPE_CHECKING:
    from ._direct import *
    from . import data, io, package, web, security

_setup_lazy_loaders(
    globals(),
    {
        "data": ".data",
        "io": ".io",
        "package": ".package",
        "web": ".web",
        "security": ".security"
    }, _direct
)
