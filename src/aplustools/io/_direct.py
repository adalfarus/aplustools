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

_local = _optional_import("werkzeug.local", ["LocalProxy"])

__deps__: list[str] = ["werkzeug>=3.0.4"]
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)


class ThreadOutputRedirector:
    """
    A class that handles thread-specific redirection of stdout and stderr
    to StringIO objects, enabling threads to capture their own output independently.
    Copied & translated from https://stackoverflow.com/questions/14890997/redirect-stdout-to-a-file-only-for-a-specific-thread by umichscoots.
    """

    def __init__(self) -> None:
        """
        Initialize the thread output redirector, storing the original stdout and stderr.
        """
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr
        self.thread_proxies = {}

    def redirect(self, file: _ty.Any) -> None:
        """
        Enables the redirect for the current thread's output to the provided file-like object.

        :param file: A file-like object (e.g., open file) to which the current thread's
                     output will be redirected.
        """
        # Get the current thread's identity.
        ident = _get_ident()

        # Enable the redirect and associate the thread with the file object.
        self.thread_proxies[ident] = file

    def stop_redirect(self) -> _ty.Any | None:
        """
        Stops the redirect for the current thread and returns the captured output.

        :return: The final string value of the captured output.
        :rtype: str
        """
        # Get the current thread's identity.
        ident = _get_ident()

        # Only act on proxied threads.
        if ident not in self.thread_proxies:
            return None

        # Read the value, close/remove the buffer, and return the value.
        obj = self.thread_proxies[ident]
        del self.thread_proxies[ident]
        return obj

    def _get_stream(self, original) -> _a.Callable:
        """
        Returns a function to get the current thread's stream, either the original
        or a redirected one if it exists.

        :param original: The stream to return if the thread is not redirected.
        :type original: file-like object (e.g., sys.stdout or sys.stderr)
        :return: A function that returns the correct stream for the current thread.
        :rtype: function
        """

        def _proxy():
            # Get the current thread's identity.
            ident = _get_ident()

            # Return the proxy if it exists, otherwise return the original stream.
            return self.thread_proxies.get(ident, original)

        return _proxy

    def enable_proxy(self) -> None:
        """
        Overwrites sys.stdout and sys.stderr with proxies that will redirect output
        to thread-specific StringIO objects if redirection is enabled for the current thread.
        """
        if _local is None:
            raise ValueError("Optional dependency werkzeug not installed.")
        sys.stdout = _local.LocalProxy(self._get_stream(self.orig_stdout))
        sys.stderr = _local.LocalProxy(self._get_stream(self.orig_stderr))

    def disable_proxy(self) -> None:
        """
        Restores sys.stdout and sys.stderr to their original state.
        """
        sys.stdout = self.orig_stdout
        sys.stderr = self.orig_stderr
