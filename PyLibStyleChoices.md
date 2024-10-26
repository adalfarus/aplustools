We use _direct modules to make some of the package directly available, mostly used by smaller functions or Classes that don't fit into one of the sub-modules.

Each __init__ in aplustools2 has a set layout (This makes the code repetition as little as possible):
````python
"""DOCSTRING"""
from .package import _setup_lazy_loaders
from . import _direct
from typing import TYPE_CHECKING as _TYPE_CHECKING

if _TYPE_CHECKING:
    from ._direct import *
    import submodule1, submodule2

_setup_lazy_loaders(
    globals(),
    {
        "submodule1": ".module.submodule1",
        "submodule2": ".module.submodule2"
    }, _direct
)

````

Each module in aplustools2 has a few standard things (_direct is the same):

````python
"""DOCSTRING"""
# Default library imports
import threading
import ...

# 3rd party libraries that are known to exist (like packaging)
import packaging

# Internal imports
from .. import act
from ..package import optional_import as _optional_import, enforce_hard_deps as _enforce_hard_deps

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

# Optional imports (may or may not be installed) --> Some modules may refuse to load if a dependency is missing
_np = _optional_import("numpy")  # If the module isn't installed it gives back None
# __deps__ to tell the LazyLoader what dependencies are optionally expected
__deps__ = ["numpy==1.26.4"]  # If the module isn't installed it raises a warning
__hard_deps__ = ["PySide6>=6.7.0"]
_enforce_hard_deps(__hard_deps__, __name__)

# Module code
class SomeClass:
    def __init__(self):
        if _np is None:  # Check if optional dependency is None, if yes raise a ValueError
            raise ValueError("Numpy must be installed to use SomeClass.")
        _np.Test()
# ...

````
