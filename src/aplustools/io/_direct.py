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
from pathlib import Path as _Path
import logging as _logging
import sys as _sys

from ..data import SingletonMeta
from ..package import optional_import as _optional_import, enforce_hard_deps as _enforce_hard_deps

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

_local = _optional_import("werkzeug.local", ["LocalProxy"])

__deps__: list[str] = ["werkzeug>=3.0.4"]
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)


# Helper class to redirect streams to the logger
class _StreamToLogger:
    """
    File-like object that redirects writes to a logger instance.
    """

    def __init__(self, logger, log_level=_logging.INFO):
        """
        Initialize the stream redirection.

        :param logger: Logger instance where messages will be redirected.
        :param log_level: Logging level for the redirected messages.
        """
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        """
        Write method for the file-like object.

        :param buf: String to write.
        """
        self.linebuf += buf
        while '\n' in self.linebuf:
            line, self.linebuf = self.linebuf.split('\n', 1)
            if line:
                self.logger.log(self.log_level, line)
            else:
                # Handle empty lines (e.g., when there are multiple newlines)
                self.logger.log(self.log_level, '')

    def flush(self):
        """
        Flush method for file-like object.
        """
        if self.linebuf:
            self.logger.log(self.log_level, self.linebuf.rstrip())
            self.linebuf = ''


class ActLogger(metaclass=SingletonMeta):
    """
    A configurable logger for ActFramework that supports logging to both the console
    and an optional log file. It provides methods to log messages at different
    logging levels and can monitor and redirect system output streams.

    Attributes:
        _logger: The logger instance used for logging messages.
        handlers: A list of handlers attached to the logger (console, file handlers).

    Methods:
        __init__(name, log_to_file, filename):
            Initialize the logger with optional file logging.

        monitor_pipe(pipe, level):
            Redirect output streams (sys.stdout or sys.stderr) to the logger.

        log(level, message):
            Log a message with a specific logging level.

        info(message):
            Log an informational message.

        debug(message):
            Log a debug message.

        error(message):
            Log an error message.
    """
    def __init__(self, name: str = "ActLogger", log_to_file: bool = False, filename: str | _Path = "app.log") -> None:
        """
        Initialize the act logger.

        :param name: Name of the logger.
        :param log_to_file: Boolean indicating if logs should be written to a file.
        :param filename: Name of the log file.
        """
        self._logger = _logging.getLogger(name)
        self._logger.setLevel(_logging.DEBUG)
        self.handlers = []

        # Create formatter with the desired format
        formatter = _logging.Formatter(
            '[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = _logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        self.handlers.append(console_handler)

        # File handler (optional)
        if log_to_file:
            file_handler = _logging.FileHandler(filename)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
            self.handlers.append(file_handler)
        self.logging_level: int = -1

    def monitor_pipe(self, pipe, level: int = _logging.INFO) -> None:
        """
        Monitor a given pipe (sys.stdout or sys.stderr).

        :param pipe: The pipe to monitor (sys.stdout or sys.stderr).
        :param level: Logging level for messages from this pipe.
        """
        if pipe == _sys.stdout:
            _sys.stdout = _StreamToLogger(self._logger, level)
        elif pipe == _sys.stderr:
            _sys.stderr = _StreamToLogger(self._logger, level)

    def log(self, level: int, message: str) -> None:
        """Log a message with a specific logging level."""
        self._logger.log(level, message)

    # Convenience methods for different logging levels
    def info(self, message: str) -> None:
        """
        Log an informational message.

        :param message: The message to log at the INFO level. Typically used for
                        general application progress or operational messages.
        """
        self._logger.info(message)

    def debug(self, message: str) -> None:
        """
        Log a debug message.

        :param message: The message to log at the DEBUG level. Typically used for
                        detailed information useful for diagnosing issues or tracing execution flow.
        """
        self._logger.debug(message)

    def error(self, message: str) -> None:
        """
        Log an error message.

        :param message: The message to log at the ERROR level. Typically used to
                        indicate a significant issue or error in the application.
        """
        self._logger.error(message)

    def warning(self, message: str) -> None:
        """
        Log a warning message.

        :param message: The message to log at the WARNING level. Typically used to
                        indicate a slight issue or warn about an action.
        :return:
        """
        self._logger.warning(message)

    def setLevel(self, logging_level: int) -> None:
        self._logger.setLevel(logging_level)
        self.logging_level = logging_level


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
        self.orig_stdout = _sys.stdout
        self.orig_stderr = _sys.stderr
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
        _sys.stdout = _local.LocalProxy(self._get_stream(self.orig_stdout))
        _sys.stderr = _local.LocalProxy(self._get_stream(self.orig_stderr))

    def disable_proxy(self) -> None:
        """
        Restores sys.stdout and sys.stderr to their original state.
        """
        _sys.stdout = self.orig_stdout
        _sys.stderr = self.orig_stderr
