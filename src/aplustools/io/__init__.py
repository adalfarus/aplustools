"""TBA"""

from ..package import _setup_lazy_loaders
from . import _direct
from typing import TYPE_CHECKING as _TYPE_CHECKING

if _TYPE_CHECKING:
    from ._direct import *
    from . import gui, env, fileio, concurrency

_setup_lazy_loaders(
    globals(),
    {
        "gui": ".io.gui",
        "env": ".io.env",
        "fileio": ".io.fileio",
        "concurrency": ".io.concurrency"
    }, _direct
)
