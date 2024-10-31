"""
Module providing lazy loading of specific submodules and dynamic imports for the aplus tools package.

This module leverages a `LazyLoader` to lazily load the `timid` and `argumint` modules when they are first accessed.
It also dynamically imports public members from the `_direct` module, updates the `__all__` list, and cleans up
globals to remove private symbols (those starting with an underscore).

Attributes:
    timid (LazyLoader): Lazy loader for the `timid` submodule.
    argumint (LazyLoader): Lazy loader for the `argumint` submodule.
    __all__ (list): List of public symbols exported by this module, including dynamically added symbols
                    from the `_direct` module.

Lazy loading allows for deferred loading of these modules, improving performance and memory efficiency in cases where
they are not always needed.

Usage:
    from aplus.tools.package import timid, argumint
"""

from ._direct import setup_lazy_loaders as _setup_lazy_loaders
from . import _direct
from typing import TYPE_CHECKING as _TYPE_CHECKING

if _TYPE_CHECKING:
    from ._direct import *
    from . import timid

_setup_lazy_loaders(
    globals(),
    {
        "timid": ".package.timid",
        "argumint": ".package.argumint"
    }, _direct)
