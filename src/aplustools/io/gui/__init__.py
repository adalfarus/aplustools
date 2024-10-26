"""TBA"""

from ...package import _setup_lazy_loaders
from . import _direct
from typing import TYPE_CHECKING as _TYPE_CHECKING

if _TYPE_CHECKING:
    from ._direct import *
    import actdirect, quick, chat

_setup_lazy_loaders(
    globals(),
    {
        "actdirect": ".io.gui.actdirect",
        "quick": ".io.gui.quick",
        "chat": ".io.gui.chat"
    }, _direct
)
