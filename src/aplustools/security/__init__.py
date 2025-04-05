"""TBA"""

from ..package import _setup_lazy_loaders
from . import _direct
from typing import TYPE_CHECKING as _TYPE_CHECKING

if _TYPE_CHECKING:
    from ._direct import *
    from . import rand, passwords, crypto

_setup_lazy_loaders(
    globals(),
    {
        #"prot": ".security.prot",
        "rand": ".security.rand",
        "passwords": ".security.passwords",
        "crypto": ".security.crypto"
    }, _direct
)
