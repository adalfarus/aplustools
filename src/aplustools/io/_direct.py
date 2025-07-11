"""
Module

This module provides logging functionality for the ActFramework application.
It includes a helper class, `_StreamToLogger`, which allows redirecting output
streams (such as `sys.stdout` and `sys.stderr`) to the logger. The main class
`ActLogger` sets up a logger with options to log to both console and a file.

Classes:
    _StreamToLogger: A file-like object that redirects writes to a logger.
    ActLogger: A logger utility for ActFramework, providing flexible logging to both
               console and file with configurable log levels.

Usage:
    logger = ActLogger(log_to_file=True, filename="app.log")
    logger.info("Application started.")
"""
from threading import get_ident as _get_ident
import sys

from ..data import SingletonMeta
from ..package import optional_import as _optional_import, enforce_hard_deps as _enforce_hard_deps

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty
if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts

__deps__: list[str] = []
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)
