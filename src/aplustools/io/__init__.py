"""TBA"""

from ..package import _setup_lazy_loaders
from . import _direct
from typing import TYPE_CHECKING as _TYPE_CHECKING

if _TYPE_CHECKING:
    from ._direct import *
    from . import env, fileio, concurrency

_setup_lazy_loaders(
    globals(),
    {
        "env": ".io.env",
        "fileio": ".io.fileio",
        "concurrency": ".io.concurrency",
    },
    _direct,
)
