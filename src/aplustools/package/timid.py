"""
This module provides a collection of timing utilities, including timers with different resolution levels,
time formatting and conversion utilities, and performance measurement tools for function execution time analysis.

Classes:
    TimeFormat:
        A utility class for converting time deltas into various formats such as weeks, days, hours, minutes, seconds, etc.

    BasicTimer:
        A simple timer class that supports starting, stopping, pausing, resuming, and measuring time intervals
        with functionalities to compute averages and tally recorded times.

    PreciseTimeDelta:
        A class for representing and manipulating small time differences in terms of days, seconds, and microseconds.
        Provides arithmetic operations for time differences.

    TimidTimer:
        A more advanced and flexible timer class supporting multiple timers, tick-tock recording, pausing, resuming,
        and measuring time intervals. It also supports interval firing and countdowns with callbacks.

    DateTimeTimer:
        A subclass of TimidTimer, using the current `datetime` timestamp for timing. This class is for illustrative purposes.

Timers:
    Several timers based on different clock functions:
    - TimeTimer
    - TimeTimerNS
    - PerfTimer
    - PerfTimerNS
    - CPUTimer
    - CPUTimerNS
    - MonotonicTimer
    - MonotonicTimerNS
    - ThreadTimer
    - ThreadTimerNS

Key Features:
    - Time measurement and formatting utilities to convert between various time units.
    - Basic and advanced timers supporting multiple intervals, pause/resume, and average time calculation.
    - Function decorators for timing and measuring function execution.
    - Performance complexity analysis of algorithms using generated input data and regression techniques.
    - The `TimidTimer` class includes several methods for setting up interval callbacks (e.g., countdowns, interval firing).
    - Various timer implementations based on different clock types, providing flexibility for different timing use cases.

Usage Example:
    To use a basic timer:
    >>> timer = BasicTimer(auto_start=True)
    >>> timer.tick()
    >>> _time.sleep(1)
    >>> timer.tock()
    >>> print(timer.get())

    For an advanced timer with tick-tock:
    >>> timid_timer = TimidTimer()
    >>> timid_timer.start()
    >>> _time.sleep(1)
    >>> timid_timer.tock()
    >>> print(timid_timer.tally())

    Measuring time complexity:
    >>> def test_func(n):
    >>>     for i in range(n): pass
    >>> timer = TimidTimer()
    >>> timer.complexity(test_func, ((i,), {}) for i in range(1, 10000))

Note:
    - `TimidTimer` is the primary class for advanced timing functionality.
    - The module also includes performance evaluation tools like time complexity estimators.
"""
from datetime import timedelta as _timedelta, datetime as _datetime
from timeit import default_timer as _default_timer
import time as _time

import threading as _threading
import pickle as _pickle
import math as _math

from ..package import optional_import as _optional_import, enforce_hard_deps as _enforce_hard_deps
# from ..io.concurrency import ThreadSafeList as _ThreadSafeList  # Circular import

# Standard typing imports for aps
import collections.abc as _a
import typing as _ty
import types as _ts

_RANSACRegressor = _optional_import("sklearn.linear_model.RANSACRegressor")
_curve_fit = _optional_import("scipy.optimize.curve_fit")
_np = _optional_import("numpy")

__deps__: list[str] = ["scikit-learn>=1.5.0", "scipy>=1.13.0", "numpy>=1.26.4"]
__hard_deps__: list[str] = []
_enforce_hard_deps(__hard_deps__, __name__)


_TimeType = int | float


# Duplicate code
class _ThreadSafeList(list):
    """
    A thread-safe implementation of a Python list, ensuring that all mutation operations are protected by a lock.

    This class extends the built-in Python `list` and overrides key methods to ensure that operations like
    appending, removing, setting items, and modifying the list are thread-safe. It uses a lock (`_Lock`)
    to synchronize access, making it safe for use in multithreaded environments.

    This class is useful when you need a list that can be shared between threads and you want to prevent
    race conditions when modifying the list. Read operations such as `__getitem__` and `__len__` are also
    protected for full thread safety, though read-only operations are generally safe unless done concurrently
    with writes.

    Attributes:
        _lock (_Lock): A threading lock used to synchronize access to the list and prevent race conditions.

    Example:
        ts_list = ThreadSafeList([1, 2, 3])
        ts_list.append(4)
        ts_list.remove(2)

        # Safe iteration over a copy
        for item in ts_list:
            print(item)

    Methods:
        append(item): Thread-safe method for appending an item to the list.
        remove(item): Thread-safe method for removing the first occurrence of an item.
        insert(index, item): Thread-safe method for inserting an item at a specific index.
        pop(index=-1): Thread-safe method for removing and returning an item at the given index (default last).
        __setitem__(index, value): Thread-safe method for setting the value at a specific index.
        __delitem__(index): Thread-safe method for deleting the item at a specific index.
        extend(iterable): Thread-safe method for extending the list with an iterable.
        sort(*args, **kwargs): Thread-safe method for sorting the list in place.
        reverse(): Thread-safe method for reversing the list in place.
        __getitem__(index): Thread-safe method for retrieving the item at the given index.
        __len__(): Thread-safe method for retrieving the length of the list.
        __iter__(): Thread-safe method for iterating over the list by returning a copy to avoid modification during iteration.

    Notes:
        - For full thread safety, both read and write operations are protected by a lock.
        - When iterating over the list, the `__iter__()` method returns a copy of the list to avoid issues
          when the list is modified during iteration by another thread.
        - If additional list methods are required, they should be overridden and wrapped with the lock to
          ensure thread safety.

    """
    def __init__(self, *args):
        super().__init__(*args)
        self._lock = _threading.Lock()

    def append(self, item: _ty.Any) -> None:
        """Append object to the end of the list."""
        with self._lock:
            super().append(item)

    def remove(self, item: _ty.Any) -> None:
        """Remove first occurrence of value.

Raises ValueError if the value is not present."""
        with self._lock:
            super().remove(item)

    def insert(self, index: int, item: _ty.Any) -> None:
        """Insert object before index."""
        with self._lock:
            super().insert(index, item)

    def pop(self, index: int = -1) -> _ty.Any:
        """Remove and return item at index (default last).

Raises IndexError if list is empty or index is out of range."""
        with self._lock:
            return super().pop(index)

    def __setitem__(self, index, value):
        with self._lock:
            super().__setitem__(index, value)

    def __delitem__(self, index):
        with self._lock:
            super().__delitem__(index)

    def extend(self, iterable: _a.Iterable[_ty.Any]) -> None:
        """Extend list by appending elements from the iterable."""
        with self._lock:
            super().extend(iterable)

    def sort(self, *, key: None = None, reverse: bool = False) -> None:
        """
        Sort the list in ascending order and return None.

        The sort is in-place (i. e. the list itself is modified) and stable (i. e. the order of two equal elements is maintained).

        If a key function is given, apply it once to each list item and sort them, ascending or descending, according to their function values.

        The reverse flag can be set to sort in descending order.
        """
        with self._lock:
            super().sort(key=key, reverse=reverse)

    def reverse(self) -> None:
        """ """
        with self._lock:
            super().reverse()

    # Optionally override other methods as needed to ensure thread safety
    # Reading operations, such as __getitem__, __contains__, len(), etc.,
    # are usually safe unless done concurrently with writes.

    def __getitem__(self, index):
        with self._lock:
            return super().__getitem__(index)

    def __len__(self):
        with self._lock:
            return super().__len__()

    def __iter__(self):
        with self._lock:
            return iter(super().copy())  # Returning a copy for thread-safe iteration


class TimeConverter:
    """
    Utility class to handle conversions between nanoseconds and timedelta,
    as well as other time units.
    """

    NANOS_IN_SEC = 1e9
    NANOS_IN_MICRO = 1e3
    SECS_IN_DAY = 86400
    SECS_IN_HOUR = 3600
    SECS_IN_MIN = 60
    NANOS_IN_MINUTE = SECS_IN_MIN * NANOS_IN_SEC

    @staticmethod
    def nanoseconds_to_timedelta(nanoseconds: float) -> _timedelta:
        """
        Convert nanoseconds into a timedelta object.

        Args:
            nanoseconds (int): Number of nanoseconds to convert.

        Returns:
            timedelta: Corresponding timedelta object.
        """
        seconds = nanoseconds // TimeConverter.NANOS_IN_SEC
        micros = (nanoseconds % TimeConverter.NANOS_IN_SEC) // TimeConverter.NANOS_IN_MICRO
        return _timedelta(seconds=seconds, microseconds=micros)

    @staticmethod
    def timedelta_to_nanoseconds(td: _timedelta) -> float:
        """
        Convert a timedelta object into nanoseconds.

        Args:
            td (timedelta): The timedelta object to convert.

        Returns:
            int: The equivalent number of nanoseconds.
        """
        return int(td.total_seconds() * TimeConverter.NANOS_IN_SEC)

    @staticmethod
    def parse_timedelta_string_to_nanoseconds(td_str: str) -> float:
        """
        Convert a `timedelta`-like string format (e.g., '00:00:00.123456789')
        into nanoseconds.

        Args:
            td_str (str): A string in the form 'HH:MM:SS.fffffffff'

        Returns:
            int: Equivalent nanoseconds.
        """
        time_parts = td_str.split(':')
        if len(time_parts) != 3:
            raise ValueError("Invalid time format, expected HH:MM:SS.fffffffff")

        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds_fraction = time_parts[2].split('.')
        seconds = int(seconds_fraction[0])
        fraction = int(seconds_fraction[1].ljust(9, '0'))  # Ensure 9 digits for nanoseconds

        # Convert everything into nanoseconds
        total_nanoseconds = (
                hours * TimeConverter.SECS_IN_HOUR * TimeConverter.NANOS_IN_SEC +
                minutes * TimeConverter.SECS_IN_MIN * TimeConverter.NANOS_IN_SEC +
                seconds * TimeConverter.NANOS_IN_SEC +
                fraction
        )
        return total_nanoseconds


class PreciseTimeFormat:
    """
    A utility class for defining time formats and converting time deltas to
    specific formats such as years, months, weeks, days, hours, minutes, seconds,
    milliseconds, microseconds, nanoseconds, and even down to attoseconds.

    Attributes:
        YEARS (int): Constant representing the time unit 'years'.
        MONTHS (int): Constant representing the time unit 'months'.
        WEEKS (int): Constant representing the time unit 'weeks'.
        DAYS (int): Constant representing the time unit 'days'.
        HOURS (int): Constant representing the time unit 'hours'.
        MINUTES (int): Constant representing the time unit 'minutes'.
        SECONDS (int): Constant representing the time unit 'seconds'.
        MILLISEC (int): Constant representing the time unit 'milliseconds'.
        MICROSEC (int): Constant representing the time unit 'microseconds'.
        NANOSEC (int): Constant representing the time unit 'nanoseconds'.
        PICOSEC (int): Constant representing the time unit 'picoseconds'.
        FEMTOSEC (int): Constant representing the time unit 'femtoseconds'.
        ATTOSEC (int): Constant representing the time unit 'attoseconds'.
    """
    YEARS = 0
    MONTHS = 1
    WEEKS = 2
    DAYS = 3
    HOURS = 4
    MINUTES = 5
    SECONDS = 6
    MILLISEC = 7
    MICROSEC = 8
    NANOSEC = 9
    PICOSEC = 10
    FEMTOSEC = 11
    ATTOSEC = 12

    @staticmethod
    def _pluralize(value: _TimeType, singular: str, plural: str) -> str:
        """
        Utility method to return the correct singular or plural form of a time unit.

        Args:
            value (int): The quantity of the time unit.
            singular (str): The singular form of the time unit.
            plural (str): The plural form of the time unit.

        Returns:
            str: The appropriately pluralized string.
        """
        return f"{value} {singular if value == 1 else plural}"

    @staticmethod
    def _format_value(value: float) -> _TimeType:
        # If the value is an integer, display as an integer, otherwise show full precision
        return int(value) if value.is_integer() else value

    @classmethod
    def get_static_readable(cls, nanos: _TimeType, format_to: int | None = None) -> str:
        """
        Convert a given timedelta to a human-readable string based on the specified
        time format. If no format is provided, it defaults to seconds.

        Args:
            nanos (int | float): The time in nanoseconds.
            format_to (Optional[TimeFormat]): The time unit format to convert to.
                If None, defaults to SECONDS.

        Returns:
            str: A human-readable string representing the timedelta in the specified
            time format.
        """

        # Handling different formats
        if format_to is None:
            format_to = cls.SECONDS

        # Conversion constants
        nanos_per_second = 1e9
        nanos_per_minute = nanos_per_second * 60
        nanos_per_hour = nanos_per_minute * 60
        nanos_per_day = nanos_per_hour * 24
        nanos_per_week = nanos_per_day * 7
        nanos_per_month = nanos_per_day * 30.44  # Average month duration in days
        nanos_per_year = nanos_per_day * 365.25  # Accounting for leap years

        if format_to == cls.YEARS:
            years, remainder = divmod(nanos, nanos_per_year)
            months = cls._format_value(remainder / nanos_per_month)
            return f"{cls._pluralize(cls._format_value(years), 'year', 'years')}, {cls._pluralize(months, 'month', 'months')}"

        elif format_to == cls.MONTHS:
            months, remainder = divmod(nanos, nanos_per_month)
            days = cls._format_value(remainder / nanos_per_day)
            return f"{cls._pluralize(cls._format_value(months), 'month', 'months')}, {cls._pluralize(days, 'day', 'days')}"

        elif format_to == cls.WEEKS:
            weeks, remainder = divmod(nanos, nanos_per_week)
            days = cls._format_value(remainder / nanos_per_day)
            return f"{cls._pluralize(cls._format_value(weeks), 'week', 'weeks')}, {cls._pluralize(days, 'day', 'days')}"

        elif format_to == cls.DAYS:
            days, remainder = divmod(nanos, nanos_per_day)
            hours = cls._format_value(remainder / nanos_per_hour)
            return f"{cls._pluralize(cls._format_value(days), 'day', 'days')}, {cls._pluralize(hours, 'hour', 'hours')}"

        elif format_to == cls.HOURS:
            hours, remainder = divmod(nanos, nanos_per_hour)
            minutes = cls._format_value(remainder / nanos_per_minute)
            return f"{cls._pluralize(cls._format_value(hours), 'hour', 'hours')}, {cls._pluralize(minutes, 'minute', 'minutes')}"

        elif format_to == cls.MINUTES:
            minutes, remainder = divmod(nanos, nanos_per_minute)
            seconds = cls._format_value(remainder / nanos_per_second)
            return f"{cls._pluralize(cls._format_value(minutes), 'minute', 'minutes')}, {seconds:.9f} second(s)"

        elif format_to == cls.SECONDS:
            seconds, remainder = divmod(nanos, nanos_per_second)
            milliseconds = cls._format_value(remainder / 1e6)
            return f"{cls._pluralize(cls._format_value(seconds), 'second', 'seconds')}, {milliseconds:.6f} millisecond(s)"

        elif format_to == cls.MILLISEC:
            millisecs, remainder = divmod(nanos, 1e6)
            microsecs = cls._format_value(remainder / 1e3)
            return f"{cls._pluralize(cls._format_value(millisecs), 'millisecond', 'milliseconds')}, {microsecs:.3f} microsecond(s)"

        elif format_to == cls.MICROSEC:
            microsecs = cls._format_value(nanos / 1e3)
            return f"{cls._pluralize(microsecs, 'microsecond', 'microseconds')}"

        elif format_to == cls.NANOSEC:
            return f"{cls._pluralize(cls._format_value(nanos), 'nanosecond', 'nanoseconds')}"

        elif format_to == cls.PICOSEC:
            picosecs = cls._format_value(nanos * 1e3)
            return f"{cls._pluralize(picosecs, 'picosecond', 'picoseconds')}"

        elif format_to == cls.FEMTOSEC:
            femtosecs = cls._format_value(nanos * 1e6)
            return f"{cls._pluralize(femtosecs, 'femtosecond', 'femtoseconds')}"

        elif format_to == cls.ATTOSEC:
            attosecs = cls._format_value(nanos * 1e9)
            return f"{cls._pluralize(attosecs, 'attosecond', 'attoseconds')}"

        return "Invalid format specified"

    @staticmethod
    def get_readable(nanoseconds: int | float) -> str:
        """
        Convert nanoseconds into a human-readable format with arbitrary precision,
        displaying the time in a format like 00:00:00.0000000000.

        Args:
            nanoseconds (Union[int, float]): The total number of nanoseconds to convert.

        Returns:
            str: Human-readable string with days, weeks, months, and years if applicable.
        """
        # Convert nanoseconds to timedelta
        total_seconds = nanoseconds / TimeConverter.NANOS_IN_SEC

        # Break down into higher units (years, months, etc.)
        years = total_seconds // (365.25 * TimeConverter.SECS_IN_DAY)
        total_seconds %= (365.25 * TimeConverter.SECS_IN_DAY)

        months = total_seconds // (30.44 * TimeConverter.SECS_IN_DAY)
        total_seconds %= (30.44 * TimeConverter.SECS_IN_DAY)

        days = total_seconds // TimeConverter.SECS_IN_DAY
        total_seconds %= TimeConverter.SECS_IN_DAY

        hours = total_seconds // TimeConverter.SECS_IN_HOUR
        total_seconds %= TimeConverter.SECS_IN_HOUR

        minutes = total_seconds // TimeConverter.SECS_IN_MIN
        total_seconds %= TimeConverter.SECS_IN_MIN

        seconds = int(total_seconds)
        fraction = int(nanoseconds % TimeConverter.NANOS_IN_SEC)

        # Build the formatted string
        formatted_time = f"{int(hours):02}:{int(minutes):02}:{seconds:02}.{fraction:09}"

        # Add larger units like days, months, and years if applicable
        result = []
        if years > 0:
            result.append(PreciseTimeFormat._pluralize(int(years), "year", "years"))
        if months > 0:
            result.append(PreciseTimeFormat._pluralize(int(months), "month", "months"))
        if days > 0:
            result.append(PreciseTimeFormat._pluralize(int(days), "day", "days"))

        # Join time units and append the formatted time
        if result:
            return ", ".join(result) + f", {formatted_time}"
        else:
            return formatted_time


class BasicTimer:
    """
    A class to represent a basic timer that can be started, stopped, paused, resumed,
    and records tick-tock intervals. It also supports tallying recorded time intervals,
    calculating the average duration, and converting elapsed time to a readable format.

    Attributes:
        start_time (float or None): The timestamp when the timer started.
        stop_time (float or None): The timestamp when the timer stopped.
        pause_start_time (float or None): The timestamp when the timer was paused.
        pause_duration (float): The total duration the timer has been paused.
        tick_tocks (list of tuples): A list of tuples containing the start and stop times for each tick-tock interval.
        is_stopped (bool): A flag indicating whether the timer is currently stopped.
        is_ended (bool): A flag indicating whether the timer has ended.

    Args:
        auto_start (bool): If True, starts the timer automatically upon initialization.
    """

    def __init__(self, auto_start: bool = False) -> None:
        """
        Initializes the BasicTimer object. Optionally starts the timer immediately.

        Args:
            auto_start (bool): If True, the timer starts automatically upon initialization.
        """
        self.start_time: float | None = None
        self.stop_time: float | None = None
        self.pause_start_time: float | None = None
        self.pause_duration: float = 0.0
        self.tick_tocks: list[tuple[float, float]] = []
        self.is_stopped: bool = False
        self.is_ended: bool = False

        if auto_start:
            self.start()

    def start(self) -> _ty.Self:
        """
        Starts the timer. If the timer was stopped or paused, it resets the start time and
        resumes recording. Raises an error if the timer has already been started or ended.

        Returns:
            self: The current BasicTimer instance for method chaining.
        """
        if self.is_ended:
            raise RuntimeError("Cannot start a timer that has been ended.")
        if self.is_stopped:
            # Overwrite the current timer
            self.start_time = _time.time()
            self.is_stopped = False
            self.stop_time = None
            self.tick_tocks = []
            self.pause_duration = 0
        elif self.start_time is None:
            self.start_time = _time.time()
        else:
            raise RuntimeError("Timer is already running.")
        return self

    def tick(self) -> _ty.Self:
        """
        Records a tick, which captures the current time as an interval start.
        Raises an error if the timer has ended or is not started.

        Returns:
            self: The current BasicTimer instance for method chaining.
        """
        tick_time = _time.time()
        if self.is_ended:
            raise RuntimeError("Cannot record time on a timer that has been ended.")
        if self.start_time is not None:
            self.tick_tocks.append((self.start_time, tick_time))
        else:
            raise RuntimeError("Timer has not been started.")
        return self

    def tock(self) -> _ty.Self:
        """
        Records a tock, which captures the current time as an interval end.
        Raises an error if the timer has ended or is not started.

        Returns:
            self: The current BasicTimer instance for method chaining.
        """
        tock_time = _time.time()
        if self.is_ended:
            raise RuntimeError("Cannot record time on a timer that has been ended.")
        if self.start_time is not None:
            last_time = self.stop_time or self.start_time
            self.stop_time = tock_time
            self.tick_tocks.append((last_time, self.stop_time))
        else:
            raise RuntimeError("Timer has not been started.")
        return self

    def tally(self):
        """
        Calculates the total time recorded between all tick-tock intervals.

        Returns:
            float: The total elapsed time in seconds.
        """
        return sum(tock - tick for tick, tock in self.tick_tocks)

    def average(self) -> _timedelta | None:
        """
        Calculates the average duration of all recorded tick-tock intervals.

        Returns:
            timedelta or None: The average duration as a timedelta object, or None if no intervals are recorded.
        """
        total_time = self.tally()
        total_count = len(self.tick_tocks)
        if total_count == 0:
            return None  # Avoid division by zero
        return _timedelta(seconds=(total_time / total_count))

    def get_times(self) -> list[tuple[float, float]]:
        """
        Retrieves the list of all tick-tock intervals recorded.

        Returns:
            list of tuples: Each tuple contains the start and stop times for each tick-tock interval.
        """
        return self.tick_tocks

    def get(self) -> _timedelta | None:
        """
        Retrieves the current elapsed time from when the timer was started.
        If the timer is paused or stopped, it calculates the time up to that point.

        Returns:
            timedelta or None: The total elapsed time as a timedelta object, or None if the timer has not been started.
        """
        if self.start_time is None:
            return None
        elapsed_time = (self.stop_time or _time.time()) - self.start_time - self.pause_duration
        return _timedelta(seconds=elapsed_time)

    def stop(self) -> _ty.Self:
        """
        Stops the timer and records the current time as the stop time.
        Raises an error if the timer is already stopped or not started.

        Returns:
            self: The current BasicTimer instance for method chaining.
        """
        if self.is_stopped:
            raise RuntimeError("Timer is already stopped.")
        if self.start_time is not None:
            self.stop_time = _time.time()
            self.is_stopped = True
        else:
            raise RuntimeError("Timer has not been started.")
        return self

    def pause(self) -> _ty.Self:
        """
        Pauses the timer, storing the current time as the pause start time.
        Raises an error if the timer is already paused, stopped, or not started.

        Returns:
            self: The current BasicTimer instance for method chaining.
        """
        if self.is_stopped:
            raise RuntimeError("Timer is stopped. Cannot pause a stopped timer.")
        if self.pause_start_time is not None:
            raise RuntimeError("Timer is already paused.")
        if self.start_time is not None:
            self.pause_start_time = _time.time()
        else:
            raise RuntimeError("Timer has not been started.")
        return self

    def resume(self) -> _ty.Self:
        """
        Resumes the timer from a paused state and adjusts the total paused duration.
        Raises an error if the timer is not paused or has ended.

        Returns:
            self: The current BasicTimer instance for method chaining.
        """
        if self.pause_start_time is None:
            raise RuntimeError("Timer is not paused.")
        if self.is_ended:
            raise RuntimeError("Cannot resume a timer that has been ended.")
        pause_end_time = _time.time()
        self.pause_duration += pause_end_time - self.pause_start_time
        self.pause_start_time = None
        return self

    def end(self) -> _ty.Self:
        """
        Ends the timer, preventing any further operations such as start, pause, or resume.

        Returns:
            self: The current BasicTimer instance for method chaining.
        """
        self.is_ended = True
        return self

    def get_readable(self, format_to: int = PreciseTimeFormat.SECONDS) -> str:
        """
        Converts the current elapsed time to a human-readable format based on the specified time unit.

        Args:
            format_to (int): The time format to convert to. Defaults to TimeFormat.SECONDS.

        Returns:
            str: A human-readable string representing the elapsed time in the specified format.
        """
        return PreciseTimeFormat.get_static_readable(TimeConverter.timedelta_to_nanoseconds(self.get()), format_to)


class PreciseTimeDelta:
    """
    A class to represent small and precise time differences, allowing arithmetic operations
    and formatted output. This class handles time values from years to attoseconds and
    stores the total time in nanoseconds internally.

    Attributes:
        negative (bool): Indicates if the time difference is negative.
        total_nanoseconds (float): The total time difference in nanoseconds, including fractional precision.
        max_precision (int): Number of decimal digits to display.
    """

    # Conversion constants
    NANOS_IN_SECOND = 1e9
    NANOS_IN_MICROSECOND = 1e3
    SECONDS_IN_MINUTE = 60
    SECONDS_IN_HOUR = 3600
    SECONDS_IN_DAY = 86400
    DAYS_IN_WEEK = 7
    DAYS_IN_MONTH = 30.44
    DAYS_IN_YEAR = 365.25

    def __init__(self, years: float = 0, months: float = 0, weeks: float = 0,
                 days: float = 0, hours: float = 0, minutes: float = 0,
                 seconds: float = 0, milliseconds: float = 0,
                 microseconds: float = 0, nanoseconds: float = 0,
                 picoseconds: float = 0, femtoseconds: float = 0,
                 attoseconds: float = 0, max_precision: int = 10) -> None:
        """
        Initializes the PreciseTimeDelta by converting all time formats into nanoseconds
        and summing them up.

        Args:
            years (float): Number of years in the time difference.
            months (float): Number of months in the time difference.
            weeks (float): Number of weeks in the time difference.
            days (float): Number of days in the time difference.
            hours (float): Number of hours in the time difference.
            minutes (float): Number of minutes in the time difference.
            seconds (float): Number of seconds in the time difference.
            milliseconds (float): Number of milliseconds in the time difference.
            microseconds (float): Number of microseconds in the time difference.
            nanoseconds (float): Number of nanoseconds in the time difference.
            picoseconds (float): Number of picoseconds in the time difference.
            femtoseconds (float): Number of femtoseconds in the time difference.
            attoseconds (float): Number of attoseconds in the time difference.
            max_precision (int): Number of decimal digits to display for fractional seconds.
        """
        total_nanoseconds = (
            years * self.DAYS_IN_YEAR * self.SECONDS_IN_DAY * self.NANOS_IN_SECOND +
            months * self.DAYS_IN_MONTH * self.SECONDS_IN_DAY * self.NANOS_IN_SECOND +
            weeks * self.DAYS_IN_WEEK * self.SECONDS_IN_DAY * self.NANOS_IN_SECOND +
            days * self.SECONDS_IN_DAY * self.NANOS_IN_SECOND +
            hours * self.SECONDS_IN_HOUR * self.NANOS_IN_SECOND +
            minutes * self.SECONDS_IN_MINUTE * self.NANOS_IN_SECOND +
            seconds * self.NANOS_IN_SECOND +
            milliseconds * 1e6 +
            microseconds * 1e3 +
            nanoseconds +
            picoseconds / 1e3 +
            femtoseconds / 1e6 +
            attoseconds / 1e9
        )

        self.negative = total_nanoseconds < 0
        self.total_nanoseconds = abs(total_nanoseconds)
        self.max_precision = max_precision

    def __truediv__(self, other):
        """
        Divides the current PreciseTimeDelta by a number or another PreciseTimeDelta.

        Args:
            other (Union[float, int, PreciseTimeDelta]): The divisor.

        Returns:
            Union[PreciseTimeDelta, float]: A new PreciseTimeDelta if divided by a number,
            or a float if divided by another PreciseTimeDelta.

        Raises:
            TypeError: If the divisor is not a number or PreciseTimeDelta.
        """
        if isinstance(other, (float, int)):
            if other == 0:
                raise ZeroDivisionError("Cannot divide by zero.")
            return PreciseTimeDelta(nanoseconds=self.total_nanoseconds / other, max_precision=self.max_precision)
        elif isinstance(other, PreciseTimeDelta):
            if other.total_nanoseconds == 0:
                raise ZeroDivisionError("Cannot divide by a PreciseTimeDelta with zero nanoseconds.")
            return self.total_nanoseconds / other.total_nanoseconds
        else:
            raise TypeError("Division only supports numbers or PreciseTimeDelta objects.")

    def __str__(self) -> str:
        """
        Returns a string representation of the time difference in a format
        'hours:minutes:seconds.nanoseconds' with the specified precision.

        Returns:
            str: The formatted time difference with arbitrary precision.
        """
        total_seconds = self.total_nanoseconds / self.NANOS_IN_SECOND
        hours, remainder = divmod(int(total_seconds), self.SECONDS_IN_HOUR)
        minutes, seconds = divmod(remainder, self.SECONDS_IN_MINUTE)

        # Get the fractional seconds with high precision
        fractional_seconds = total_seconds - _math.floor(total_seconds)

        # Adjust precision dynamically based on the fractional part
        if fractional_seconds > 0:
            fractional_part_str = f"{fractional_seconds:.{self.max_precision}f}".split('.')[1].rstrip('0')
            time_str = f"{hours}:{minutes:02}:{seconds:02}.{fractional_part_str}"
        else:
            time_str = f"{hours}:{minutes:02}:{seconds:02}"

        if self.negative:
            time_str = f"-{time_str}"

        return time_str

    def __repr__(self) -> str:
        """
        Returns a string representation for debugging purposes.

        Returns:
            str: Debug information showing the total time difference in nanoseconds.
        """
        return f"PreciseTimeDelta(nanoseconds={self.total_nanoseconds})"

    def years(self) -> float:
        """
        Returns the number of years in the time difference.

        Returns:
            float: The number of years.
        """
        return self.total_nanoseconds / (self.DAYS_IN_YEAR * self.SECONDS_IN_DAY * self.NANOS_IN_SECOND)

    def months(self) -> float:
        """
        Returns the number of months in the time difference.

        Returns:
            float: The number of months.
        """
        return self.total_nanoseconds / (self.DAYS_IN_MONTH * self.SECONDS_IN_DAY * self.NANOS_IN_SECOND)

    def weeks(self) -> float:
        """
        Returns the number of weeks in the time difference.

        Returns:
            float: The number of weeks.
        """
        return self.total_nanoseconds / (self.DAYS_IN_WEEK * self.SECONDS_IN_DAY * self.NANOS_IN_SECOND)

    def days(self) -> float:
        """
        Returns the number of days in the time difference.

        Returns:
            float: The number of days.
        """
        return self.total_nanoseconds / (self.SECONDS_IN_DAY * self.NANOS_IN_SECOND)

    def hours(self) -> float:
        """
        Returns the number of hours in the time difference.

        Returns:
            float: The number of hours.
        """
        return self.total_nanoseconds / (self.SECONDS_IN_HOUR * self.NANOS_IN_SECOND)

    def minutes(self) -> float:
        """
        Returns the number of minutes in the time difference.

        Returns:
            float: The number of minutes.
        """
        return self.total_nanoseconds / (self.SECONDS_IN_MINUTE * self.NANOS_IN_SECOND)

    def seconds(self) -> float:
        """
        Returns the number of seconds in the time difference.

        Returns:
            float: The number of seconds.
        """
        return self.total_nanoseconds / self.NANOS_IN_SECOND

    def milliseconds(self) -> float:
        """
        Returns the number of milliseconds in the time difference.

        Returns:
            float: The number of milliseconds.
        """
        return self.total_nanoseconds / 1e6

    def microseconds(self) -> float:
        """
        Returns the number of microseconds in the time difference.

        Returns:
            float: The number of microseconds.
        """
        return self.total_nanoseconds / 1e3

    def nanoseconds(self) -> float:
        """
        Returns the number of nanoseconds in the time difference.

        Returns:
            float: The number of nanoseconds.
        """
        return self.total_nanoseconds

    def picoseconds(self) -> float:
        """
        Returns the number of picoseconds in the time difference.

        Returns:
            float: The number of picoseconds.
        """
        return self.total_nanoseconds * 1e3

    def femtoseconds(self) -> float:
        """
        Returns the number of femtoseconds in the time difference.

        Returns:
            float: The number of femtoseconds.
        """
        return self.total_nanoseconds * 1e6

    def attoseconds(self) -> float:
        """
        Returns the number of attoseconds in the time difference.

        Returns:
            float: The number of attoseconds.
        """
        return self.total_nanoseconds * 1e9


class TimidTimer:
    """
    A timer class to manage multiple timers and track elapsed time with nanosecond precision.
    If a time value is not specified as something specific, it is assumed to be in seconds.

    Attributes:
        EMPTY (tuple): A constant tuple representing an empty timer slot.
    """
    EMPTY: tuple[_TimeType, _TimeType, _TimeType, _ty.Optional[_threading.Lock]] = (0, 0, 0, None)
    SENTINEL = object()
    _tracked_timers = _ThreadSafeList()

    def __init__(self, start_at: _TimeType = 0, start_now: bool = True) -> None:
        """
        Initializes the TimidTimer instance.

        Args:
            start_at (float or int, optional): The initial starting point of the timer. Defaults to 0.
            start_now (bool, optional): If True, the timer starts immediately. Defaults to True.
        """
        self._fires: list[tuple[_threading.Thread | None, _threading.Event | None]] = _ThreadSafeList()
        self._times: list[tuple[_TimeType, _TimeType, _TimeType, _threading.Lock | None] | None] = _ThreadSafeList()
        self._tick_tocks: list[list[_TimeType | tuple[_TimeType, _TimeType]]] = _ThreadSafeList()
        self._thread_data: _threading.local = _threading.local()

        if start_now:
            self._warmup()
            self.start(start_at=start_at)

    @staticmethod
    def _time() -> _TimeType:
        """
        Gets the current time in nanoseconds.

        Returns:
            float or int: The current time value in nanoseconds.
        """
        return _default_timer() * 1e9

    @classmethod
    def at(cls, index: int, *args, **kwargs) -> _ty.Self:
        """
        Retrieves or creates a timer object at the specified index.

        This method ensures that you can access or create a timer object at any index in the
        `_tracked_timers` list without having to pass a direct reference. If the index is beyond
        the current length of `_tracked_timers`, the list is extended to accommodate the new index.

        Args:
            index (int): The index of the timer to access or create.

        Returns:
            _ty.Self: The timer object at the specified index.
        """
        amount_to_extend = index - len(cls._tracked_timers) + 1  # We want to be able
        if amount_to_extend > 0:
            cls._tracked_timers.extend([cls.SENTINEL] * amount_to_extend)
        if cls._tracked_timers[index] is cls.SENTINEL:
            obj = cls(*args, **kwargs)
            cls._tracked_timers[index] = obj
        else:
            obj = cls._tracked_timers[index]
        return obj

    @classmethod
    def from_(cls, index: int) -> _ty.Self:
        """
        Retrieves the timer object at the specified index, if it exists.

        This method attempts to access an existing timer at the specified index
        in the `_tracked_timers` list. If no timer exists at the given index,
        it raises an `IndexError`.

        Args:
            index (int): The index of the timer to retrieve.

        Returns:
            _ty.Self: The timer object at the specified index.

        Raises:
            IndexError: If no timer exists at the given index.
        """
        if index >= len(cls._tracked_timers) or cls._tracked_timers[index] is cls.SENTINEL:
            raise IndexError(f"No timer found at index {index}")
        return cls._tracked_timers[index]

    def start(self, *indices: int | None, start_at: _TimeType = 0) -> _ty.Self:
        """
        Starts the timer at the specified indices.

        Args:
            indices (int, optional): The index or indices where the timer should be started. Defaults to the next available index.
            start_at (float or int, optional): The start time offset in seconds. Defaults to 0.

        Returns:
            TimidTimer: The current instance of the timer.
        """
        start_time = self._time()
        indices = indices or [self._get_first_other_index()]

        for index in indices:
            if index < len(self._times) and self._times[index][2] != 0:
                self.resume(index)
                return self
            length_to_extend = index - len(self._times) + 1
            if length_to_extend > 0:  # Ensure the _times and _tick_tocks lists has enough elements
                self._times.extend([self.EMPTY] * length_to_extend)
                self._tick_tocks.extend([[] for _ in range(length_to_extend)])
            if self._times[index] is self.EMPTY:
                self._times[index] = (start_time + (start_at * 1e9), 0, 0, _threading.Lock())
                self._tick_tocks[index].clear()  # List is always already here.
            else:
                raise Exception(f"A Timer already running on index {index}")
        return self

    def _get_first_index(self) -> int:
        """
        Gets the first available index where the timer is active.

        Returns:
            int: The first active timer index.

        Raises:
            IndexError: If no active timers are found.
        """
        for i, t in enumerate(self._times):
            if t is not self.EMPTY:
                return i
        raise IndexError("No active timers.")

    def _get_first_other_index(self) -> int:
        """
        Gets the first empty index.

        Returns:
            int: The first empty index.
        """
        for i, t in enumerate(self._times):
            if t is self.EMPTY:
                return i
        return len(self._times)

    def pause(self, *indices: int | None, for_seconds: _TimeType | None = None) -> _ty.Self:
        """
        Pauses the timer at the specified indices.

        Args:
            indices (int, optional): The index or indices where the timer should be paused. Defaults to the first active timer.
            for_seconds (float or int, optional): The duration to pause the timer in seconds. If not specified, pauses indefinitely.

        Returns:
            TimidTimer: The current instance of the timer.
        """
        pause_time = self._time()
        indices = indices or [self._get_first_index()]  # If it's 0 it just sets it to 0 so it's okay.

        for index in indices:
            if index >= len(self._times) or self._times[index] is self.EMPTY:
                raise IndexError(f"Index {index} doesn't exist or is not running.")

            with self._times[index][-1]:
                start, end, paused_time, lock = self._times[index]
                if paused_time != 0:
                    raise ValueError(f"Timer on index {index} is already paused.")
                self._times[index] = (start, end, pause_time, lock)
                if for_seconds:
                    self._tick_tocks[index].append(for_seconds * 1e9)
                else:
                    self._tick_tocks[index].append(float('inf'))
        return self

    def resume(self, *indices: int | None) -> _ty.Self:
        """
        Resumes the timer at the specified indices.

        Args:
            indices (int, optional): The index or indices where the timer should be resumed. Defaults to the first paused timer.

        Returns:
            TimidTimer: The current instance of the timer.
        """
        resumed_time = self._time()
        indices = indices or [self._get_first_index()]  # If it's 0 it just sets it to 0 so it's okay.

        for index in indices:
            if index >= len(self._times) or self._times[index] is self.EMPTY:
                raise IndexError(f"Index {index} doesn't exist or is not paused.")

            with self._times[index][-1]:
                self._resume(resumed_time, index)
        return self

    def _resume(self, resumed_time: _TimeType, index: int | None = None) -> None:
        start, end, paused_time, lock = self._times[index]
        if paused_time != 0:
            max_paused_timedelta = self._tick_tocks[index].pop(-1)
            actual_paused_time = min((resumed_time - paused_time), max_paused_timedelta)
            self._times[index] = (start + actual_paused_time, (end + actual_paused_time) if end > 0 else end, 0, lock)
        else:
            raise ValueError(f"Timer on index {index} isn't paused.")

    def stop(self, *indices: int | None) -> _ty.Self:
        """
        Stops the timer at the specified indices.

        Args:
            indices (int, optional): The index or indices where the timer should be stopped. Defaults to the first active timer.

        Returns:
            TimidTimer: The current instance of the timer.
        """
        end_time = self._time()
        indices = indices or [self._get_first_index()]  # If it's 0 it just sets it to 0 so it's okay.

        for index in indices:
            if index >= len(self._times) or self._times[index] is self.EMPTY:
                raise IndexError(f"Index {index} doesn't exist or is not running.")

            with self._times[index][-1]:
                start, end, paused_time, lock = self._times[index]
                if paused_time != 0:
                    self._resume(end_time, index)
                    start, _, __, ___ = self._times[index]
                self._times[index] = (start, end_time, 0, lock)
        return self

    def get(self, *indices: int | None, return_type: _ty.Literal["timedelta", "PreciseTimeDelta"] = "PreciseTimeDelta"
            ) -> list[PreciseTimeDelta | _timedelta] | PreciseTimeDelta | _timedelta:
        """
        Retrieves the elapsed time for the specified indices.

        Args:
            indices (int, optional): The index or indices to retrieve elapsed time for. Defaults to the first active timer.
            return_type (str, optional): The format to return the time in, either "timedelta" or "PreciseTimeDelta". Defaults to "PreciseTimeDelta".

        Returns:
            list[PreciseTimeDelta | timedelta] | PreciseTimeDelta | timedelta: The elapsed time(s).
        """
        indices = indices or [self._get_first_index()]  # If it's 0 it just sets it to 0 so it's okay.
        returns = []

        for index in indices:
            if index >= len(self._times) or self._times[index] is self.EMPTY:
                raise IndexError(f"Index {index} doesn't exist or is not running.")
            with self._times[index][-1]:
                start, end, paused_time, _ = self._times[index]
            max_paused_time = float('inf')
            if paused_time != 0:
                paused_time = self._time() - paused_time
                max_paused_time = self._tick_tocks[-1]
            elapsed_time = (end or self._time()) - min(max_paused_time, start + paused_time)
            if return_type == "PreciseTimeDelta":
                returns.append(PreciseTimeDelta(nanoseconds=elapsed_time))
            else:
                returns.append(_timedelta(microseconds=elapsed_time / 1000))
        return returns if len(returns) > 1 else returns[0]

    def delete(self, *indices: int | None, return_type: _ty.Literal["timedelta", "PreciseTimeDelta", None] = "PreciseTimeDelta"
               ) -> list[PreciseTimeDelta | _timedelta] | PreciseTimeDelta | _timedelta | _ty.Self:
        """
        Deletes the timer at the specified indices.

        Args:
            indices (int, optional): The index or indices to delete. Defaults to the first active timer.
            return_type (str, optional): The format to return the time in, either "timedelta", "PreciseTimeDelta", or None. Defaults to "PreciseTimeDelta".

        Returns:
            list[PreciseTimeDelta | timedelta] | PreciseTimeDelta | timedelta: The elapsed time(s) or TimidTimer: The current instance of the timer.
        """
        end_timer = self._time()
        indices = indices or [self._get_first_index()]  # If it's 0 it just sets it to 0 so it's okay.
        returns = []

        for index in indices:
            if index >= len(self._times) or self._times[index] is self.EMPTY:
                raise IndexError(f"Index {index} doesn't exist or is not running.")
            with self._times[index][-1]:
                start, end, paused_time, _ = self._times[index]
                max_paused_time = float('inf')
                if paused_time != 0:
                    paused_time = end_timer - paused_time
                    max_paused_time = self._tick_tocks[-1]
                elapsed_time = (end or end_timer) - min(max_paused_time, start + paused_time)
                if return_type == "PreciseTimeDelta":
                    returns.append(PreciseTimeDelta(nanoseconds=elapsed_time))
                else:
                    returns.append(_timedelta(microseconds=elapsed_time / 1000))
                self._times[index] = self.EMPTY
                self._tick_tocks[index] = []
        if return_type is not None:
            return returns if len(returns) > 1 else returns[0]
        return self

    def end(self, *indices: int | None, return_type: _ty.Literal["timedelta", "PreciseTimeDelta", None] = "PreciseTimeDelta"
            ) -> list[PreciseTimeDelta | _timedelta] | PreciseTimeDelta | _timedelta | _ty.Self:
        """
        Ends the timer at the specified indices.

        Args:
            indices (int, optional): The index or indices where the timer should be ended. Defaults to the first active timer.
            return_type (str, optional): The format to return the time in, either "timedelta", "PreciseTimeDelta", or None. Defaults to "PreciseTimeDelta".

        Returns:
            list[PreciseTimeDelta | timedelta] | PreciseTimeDelta | timedelta: The elapsed time(s) or TimidTimer: The current instance of the timer.
        """
        end_time = self._time()
        indices = indices or [self._get_first_index()]  # If it's 0 it just sets it to 0 so it's okay.
        returns = []

        for index in indices:
            if index >= len(self._times) or self._times[index] is self.EMPTY:
                raise IndexError(f"Index {index} doesn't exist or is not running.")
            with self._times[index][-1]:
                start, end, paused_time, _ = self._times[index]
                if paused_time != 0:
                    self._resume(end_time, index)
                    start, _, __, ___ = self._times[index]
                self._times[index] = self.EMPTY
                self._tick_tocks[index] = []
            elapsed_time = (end or end_time) - start
            if return_type == "PreciseTimeDelta":
                returns.append(PreciseTimeDelta(nanoseconds=elapsed_time))
            elif return_type == "timedelta":
                returns.append(_timedelta(microseconds=elapsed_time / 1000))
        if return_type is not None:
            return returns if len(returns) > 1 else returns[0]
        return self

    def restart(self, *indices: int | None, return_type: _ty.Literal["timedelta", "PreciseTimeDelta", None] = "PreciseTimeDelta"
            ) -> list[PreciseTimeDelta | _timedelta] | PreciseTimeDelta | _timedelta | _ty.Self:
        """
        Restarts an already running timer, skipping the whole .stop() .get_readable() .delete() boilerplate.

        Args:
            indices (int, optional): The index or indices where the timer should be ended. Defaults to the first active timer.
            return_type (str, optional): The format to return the time in, either "timedelta", "PreciseTimeDelta", or None. Defaults to "PreciseTimeDelta".

        Returns:
            list[PreciseTimeDelta | timedelta] | PreciseTimeDelta | timedelta: The elapsed time(s) or TimidTimer: The current instance of the timer.
        """
        end_timer = self._time()
        indices = indices or [self._get_first_index()]  # If it's 0 it just sets it to 0 so it's okay.
        returns = []

        for index in indices:
            if index >= len(self._times) or self._times[index] is self.EMPTY:
                raise IndexError(f"Index {index} doesn't exist or is not running.")
            with self._times[index][-1]:
                start, end, paused_time, _ = self._times[index]
                max_paused_time = float('inf')
                if paused_time != 0:
                    paused_time = end_timer - paused_time
                    max_paused_time = self._tick_tocks[-1]
                elapsed_time = (end or end_timer) - min(max_paused_time, start + paused_time)
                if return_type == "PreciseTimeDelta":
                    returns.append(PreciseTimeDelta(nanoseconds=elapsed_time))
                else:
                    returns.append(_timedelta(microseconds=elapsed_time / 1000))
                self._times[index] = self.EMPTY
                self._tick_tocks[index] = []
                self.start(index)
        if return_type is not None:
            return returns if len(returns) > 1 else returns[0]
        return self

    def tick(self, *indices: int | None, return_type: _ty.Literal["timedelta", "PreciseTimeDelta", None] = "PreciseTimeDelta"
             ) -> list[PreciseTimeDelta | _timedelta] | PreciseTimeDelta | _timedelta | _ty.Self:
        """
        Records how much time has passed since the start of the timer (similar to elapsed).

        Args:
            indices (int, optional): The index or indices to check the time for. Defaults to the first active timer.
            return_type (str, optional): The format to return the time in, either "timedelta", "PreciseTimeDelta", or None. Defaults to "PreciseTimeDelta".

        Returns:
            list[PreciseTimeDelta | timedelta] | PreciseTimeDelta | timedelta: The elapsed time(s) or TimidTimer: The current instance of the timer.
        """
        tick_time = self._time()
        indices = indices or [self._get_first_index()]  # If it's 0 it just sets it to 0 so it's okay.
        returns = []

        for index in indices:
            if index >= len(self._times) or self._times[index] is self.EMPTY:
                raise IndexError(f"Index {index} doesn't exist or is not running.")
            with self._times[index][-1]:
                start, _, paused_time, __ = self._times[index]
                if tick_time - start < 0:
                    raise ValueError(f"Please don't tick when the timer is paused.")
                if paused_time != 0:
                    self._resume(tick_time, index)
                self._tick_tocks[index].append((start, tick_time))
            if return_type == "PreciseTimeDelta":
                returns.append(PreciseTimeDelta(nanoseconds=tick_time - start))
            elif return_type == "timedelta":
                returns.append(_timedelta(microseconds=(tick_time - start) / 1000))
        if return_type is not None:
            return returns if len(returns) > 1 else returns[0]
        return self

    def tock(self, *indices: int | None, return_type: _ty.Literal["timedelta", "PreciseTimeDelta", None] = "PreciseTimeDelta"
             ) -> list[PreciseTimeDelta | _timedelta] | PreciseTimeDelta | _timedelta | _ty.Self:
        """
        Records the time between the last tock and the current tock (similar to lap or split time).

        Args:
            indices (int, optional): The index or indices to check the time for. Defaults to the first active timer.
            return_type (str, optional): The format to return the time in, either "timedelta", "PreciseTimeDelta", or None. Defaults to "PreciseTimeDelta".

        Returns:
            list[PreciseTimeDelta | timedelta] | PreciseTimeDelta | timedelta: The elapsed time(s) or TimidTimer: The current instance of the timer.
        """
        tock_time = self._time()
        indices = indices or [self._get_first_index()]  # If it's 0 it just sets it to 0 so it's okay.
        returns = []

        for index in indices:
            if index >= len(self._times) or self._times[index] is self.EMPTY:
                raise IndexError(f"Index {index} doesn't exist or is not running.")
            with self._times[index][-1]:
                start, end, paused_time, lock = self._times[index]

                if paused_time != 0:
                    self._resume(tock_time, index)
                    start, end, _, __ = self._times[index]
                last_time = end or start
                if tock_time - last_time < 0:
                    raise ValueError(f"Please don't tock when the timer is paused.")
                end = tock_time
                self._times[index] = (start, end, 0, lock)
                self._tick_tocks[index].append((last_time, end))
            if return_type == "PreciseTimeDelta":
                returns.append(PreciseTimeDelta(nanoseconds=end - last_time))
            elif return_type == "timedelta":
                returns.append(_timedelta(microseconds=(end - last_time) / 1000))
        if return_type is not None:
            return returns if len(returns) > 1 else returns[0]
        return self

    def tally(self, *indices: int | None, return_type: _ty.Literal["timedelta", "PreciseTimeDelta"] = "PreciseTimeDelta"
              ) -> PreciseTimeDelta | _timedelta:
        """
        Returns the total time recorded across all ticks and tocks.

        Args:
            indices (int, optional): The index or indices to tally the time for. Defaults to the first active timer.
            return_type (str, optional): The format to return the time in, either "timedelta" or "PreciseTimeDelta". Defaults to "PreciseTimeDelta".

        Returns:
            PreciseTimeDelta | timedelta: The total elapsed time across all ticks and tocks.
        """
        indices = indices or [self._get_first_index()]  # If it's 0 it just sets it to 0 so it's okay.
        total_time = 0

        for index in indices:
            if index >= len(self._times) or self._times[index] is self.EMPTY:
                continue
            with self._times[index][-1]:
                start, end, _, __ = self._times[index]
                tick_tocks = self._tick_tocks[index].copy()
            if end != 0 and len(tick_tocks) > 0:
                tick_tocks.append((tick_tocks[-1][1], end))
            elif end != 0:
                tick_tocks.append((start, end))
            total_time += sum((end - start for start, end in tick_tocks))

        return PreciseTimeDelta(nanoseconds=total_time) if return_type == "PreciseTimeDelta" \
            else _timedelta(microseconds=total_time / 1000)

    def average(self, *indices: int | None, return_type: _ty.Literal["timedelta", "PreciseTimeDelta"] = "PreciseTimeDelta"
                ) -> PreciseTimeDelta | _timedelta:
        """
        Calculates the average time recorded across all ticks and tocks.

        Args:
            indices (int, optional): The index or indices to average the time for. Defaults to the first active timer.
            return_type (str, optional): The format to return the time in, either "timedelta" or "PreciseTimeDelta". Defaults to "PreciseTimeDelta".

        Returns:
            PreciseTimeDelta | timedelta: The average elapsed time across all ticks and tocks.
        """
        indices = indices or [self._get_first_index()]  # If it's 0 it just sets it to 0 so it's okay.
        total_tocks = 0

        for index in indices:
            if index >= len(self._times) or self._times[index] is self.EMPTY:
                continue
            with self._times[index][-1]:
                _, end, __, ___ = self._times[index]
                tick_tocks = self._tick_tocks[index].copy()
            total_tocks += len(tick_tocks) + (1 if end != 0 and end != ([(0, 0)] + tick_tocks)[-1][1] else 0)

        if total_tocks == 0:
            return PreciseTimeDelta(0) if return_type == "PreciseTimeDelta" else _timedelta(0)

        return self.tally(*indices, return_type=return_type) / total_tocks

    def show_tick_tocks(self, index: int | None = None, format_to: int = PreciseTimeFormat.SECONDS) -> str:
        """
        Displays the recorded times for each tick and tock.

        Args:
            index (int, optional): The index to display tick and tock times for. Defaults to the first active timer.
            format_to (int, optional): The time format to use for displaying the times. Defaults to TimeFormat.SECONDS.

        Returns:
            str: The tick tocks of the index in a readable string format.
        """
        retstring = ""
        index = index or self._get_first_index()  # If it's 0 it just sets it to 0 so it's okay.
        retstring += "Tick Tock times:\n"
        with self._times[index][-1]:
            my_tick_tocks = self._tick_tocks[index].copy()
            _, __, is_paused, _ = self._times[index]
        if is_paused:
            my_tick_tocks.pop(-1)
        for i, (start, end) in enumerate(my_tick_tocks, start=1):
            td = _timedelta(microseconds=(end - start) / 1000)
            retstring += f"Lap {i}: {PreciseTimeFormat.get_static_readable(td, format_to)}\n"
        return retstring

    def get_readable(self, index: int | None = None, format_to: int = PreciseTimeFormat.SECONDS) -> str:
        """
        Returns a readable string of the timer's elapsed time.

        Args:
            index (int, optional): The index to retrieve the elapsed time for. Defaults to the first active timer.
            format_to (TimeFormat, optional): The format to return the time in. Defaults to TimeFormat.SECONDS.

        Returns:
            str: A human-readable string of the elapsed time.
        """
        return PreciseTimeFormat.get_static_readable(self.get(index or self._get_first_index()).nanoseconds(), format_to)

    def _warmup(self, rounds: int = 3) -> None:
        """
        Warms up the timer by starting and stopping it for a specified number of rounds.

        Args:
            rounds (int, optional): The number of warmup rounds. Defaults to 3.
        """
        for _ in range(rounds):
            self.start()
            self.end()
        self._times = []
        self._tick_tocks = []

    def timeout(self, seconds: float | int, callback: _a.Callable, args: tuple[_ty.Any, ...] = (),
                kwargs: dict = None) -> None:
        """
        Starts a countdown timer for a specified number of seconds.

        Args:
            seconds (float or int): The duration of the countdown in seconds.
            callback (Callable, optional): The function to call when the countdown ends. Defaults to print.
            args (tuple, optional): The arguments for the callback function. Defaults to a message with the countdown time.
            kwargs (dict, optional): The keyword arguments for the callback function. Defaults to None.
        """
        if kwargs is None:
            kwargs = {}
        self.single_shot(seconds, callback, args, kwargs)

    def timeout_ms(self, milliseconds: float | int, callback: _a.Callable, args: tuple[_ty.Any, ...] = (),
                   kwargs: dict = None) -> None:
        """
        Starts a countdown timer for a specified number of milliseconds.

        Args:
            milliseconds (float or int): The duration of the countdown in milliseconds.
            callback (Callable, optional): The function to call when the countdown ends. Defaults to print.
            args (tuple, optional): The arguments for the callback function. Defaults to a message with the countdown time.
            kwargs (dict, optional): The keyword arguments for the callback function. Defaults to None.
        """
        if kwargs is None:
            kwargs = {}
        self.single_shot_ms(milliseconds, callback, args, kwargs)

    def long_timeout(self, seconds: float | int, callback: _a.Callable, args: tuple[_ty.Any, ...] = (),
                     kwargs: dict = None) -> None:
        """
        Starts a long-running countdown timer for a specified number of seconds.

        Args:
            seconds (float or int): The duration of the countdown in seconds.
            callback (Callable, optional): The function to call when the countdown ends. Defaults to print.
            args (tuple, optional): The arguments for the callback function. Defaults to a message with the countdown time.
            kwargs (dict, optional): The keyword arguments for the callback function. Defaults to None.
        """
        if kwargs is None:
            kwargs = {}
        self.long_single_shot(seconds, callback, args, kwargs)

    def interval(self, interval: float | int, count: int | _ty.Literal["inf"], callback: _a.Callable,
                 args: tuple[_ty.Any, ...] = (), kwargs: dict = None) -> None:
        """
        Starts an interval timer that triggers the callback at specified intervals.

        Args:
            interval (float or int): The interval in seconds between each callback trigger.
            count (int or "inf", optional): The number of times to trigger the callback. Defaults to "inf" (infinite).
            callback (Callable, optional): The function to call at each interval. Defaults to print.
            args (tuple, optional): The arguments for the callback function. Defaults to a message with the interval time.
            kwargs (dict, optional): The keyword arguments for the callback function. Defaults to None.
        """
        if kwargs is None:
            kwargs = {}
        if count == "inf":
            self.fire(interval, callback, args, kwargs, daemon=True)
        else:
            self.shoot(interval, callback, args, kwargs, iterations=count)

    def interval_ms(self, interval_ms: float | int, count: int | _ty.Literal["inf"],
                    callback: _a.Callable, args: tuple[_ty.Any, ...] = (), kwargs: dict = None) -> None:
        """
        Starts an interval timer that triggers the callback at specified intervals in milliseconds.

        Args:
            interval_ms (float or int): The interval in milliseconds between each callback trigger.
            count (int or "inf", optional): The number of times to trigger the callback. Defaults to "inf" (infinite).
            callback (Callable, optional): The function to call at each interval. Defaults to print.
            args (tuple, optional): The arguments for the callback function. Defaults to a message with the interval time.
            kwargs (dict, optional): The keyword arguments for the callback function. Defaults to None.
        """
        if kwargs is None:
            kwargs = {}
        if count == "inf":
            self.fire_ms(interval_ms, callback, args, kwargs, daemon=True)
        else:
            self.shoot_ms(interval_ms, callback, args, kwargs, iterations=count)

    def long_interval(self, interval: float | int, count: int | _ty.Literal["inf"], callback: _a.Callable,
                      args: tuple[_ty.Any, ...] = (), kwargs: dict = None) -> None:
        """
        Starts a long-running interval timer that triggers the callback at specified intervals.

        Args:
            interval (float or int): The interval in seconds between each callback trigger.
            count (int or "inf", optional): The number of times to trigger the callback. Defaults to "inf" (infinite).
            callback (Callable, optional): The function to call at each interval. Defaults to print.
            args (tuple, optional): The arguments for the callback function. Defaults to a message with the interval time.
            kwargs (dict, optional): The keyword arguments for the callback function. Defaults to None.
        """
        if kwargs is None:
            kwargs = {}
        if count == "inf":
            self.long_fire(interval, callback, args, kwargs)
        else:
            self.long_shoot(interval, callback, args, kwargs, iterations=count)

    @staticmethod
    def schedule_task_at(time_str, callback: _a.Callable = print, args: tuple[_ty.Any, ...] = (),
                         kwargs: dict = None) -> None:
        """
        Schedules a task to run at a specified time of day, either today or the next day if the time has passed.

        Args:
            time_str (str): The time of day to run the task, in "HH:MM" or "HH:MM:SS" format.
            callback (Callable, optional): The function to run when the scheduled time is reached. Defaults to print.
            args (tuple, optional): The arguments for the callback function. Defaults to a message with the scheduled time.
            kwargs (dict, optional): The keyword arguments for the callback function. Defaults to None.
        """
        if len(time_str) == 5:
            time_format = "%H:%M"
        elif len(time_str) == 8:
            time_format = "%H:%M:%S"
        else:
            raise TypeError(f"Unsupported time format '{time_str}'")
        current_time = _datetime.now().time()
        target_time = _datetime.strptime(time_str, time_format).time()
        current_datetime = _datetime.combine(_datetime.today(), current_time)
        target_datetime = _datetime.combine(_datetime.today(), target_time)

        if target_datetime < current_datetime:
            target_datetime += _timedelta(days=1)  # Set alarm for the next day if time has already passed today
        diff = target_datetime - current_datetime

        # Schedule task
        _threading.Timer(diff.total_seconds(), callback, args or (f"Timer for {time_str} is over.",), kwargs or {}).start()

    def save_state(self) -> bytes:
        """
        Saves the current state of all timers (excluding threads).

        Returns:
            bytes: A serialized representation of the timer's state.
        """
        state = {
            "_times": self._times,
            "_tick_tocks": self._tick_tocks,
        }
        return _pickle.dumps(state)

    def load_state(self, state_bytes: bytes) -> None:
        """
        Loads a previously saved state for all timers (excluding threads).

        Args:
            state_bytes (bytes): The serialized state to load.
        """
        state = _pickle.loads(state_bytes)
        self._times = state["_times"]
        self._tick_tocks = state["_tick_tocks"]

    @staticmethod
    def load_state_static(state_bytes: bytes) -> "TimidTimer":
        """
        Loads a previously saved state for all timers (excluding threads).

        Args:
            state_bytes (bytes): The serialized state to load.
        """
        timer = TimidTimer(start_now=False)
        timer.load_state(state_bytes)
        return timer

    @classmethod
    def setup_timer_func(cls, func: _a.Callable, to_nanosecond_multiplier: float | int) -> _ty.Type[_ty.Self]:
        """
        Sets up a custom timing function for the timer, using a specified multiplier to convert the time to nanoseconds.

        Args:
            func (Callable): The function that returns the current time.
            to_nanosecond_multiplier (float or int): The multiplier to convert the function's output to nanoseconds.

        Returns:
            type: A new class with the modified timing function.
        """
        NewClass = type('TimidTimerModified', (cls,), {
            '_time': lambda self=None: func() * to_nanosecond_multiplier
        })
        return NewClass

    @classmethod
    def _trigger(cls, interval: _TimeType, function, args: tuple, kwargs: dict, iterations: int,
                 stop_event: _threading.Event = _threading.Event()) -> None:
        """
        A helper function to trigger a function at specified intervals, with a specified number of iterations.

        Args:
            interval (float or int): The interval in seconds between each function call.
            function (Callable): The function to call at each interval.
            args (tuple): The arguments for the function.
            kwargs (dict): The keyword arguments for the function.
            iterations (int): The number of times to call the function.
            stop_event (threading.Event, optional): An event to stop the timer. Defaults to a new event.
        """
        try:
            cls.wait_static(interval)
            while not stop_event.is_set() and iterations != 0:  # So infinite timers are possible
                try:
                    function(*args, **kwargs)
                except Exception as e:
                    print(f"Error in _trigger thread: {e}")
                cls.wait_static(interval)
                iterations -= 1
        except SystemExit:
            pass

    @classmethod
    def _trigger_ms(cls, interval_ms: _TimeType, function, args: tuple, kwargs: dict, iterations: int,
                    stop_event: _threading.Event = _threading.Event()) -> None:
        """
        A helper function to trigger a function at specified intervals in milliseconds, with a specified number of iterations.

        Args:
            interval_ms (float or int): The interval in milliseconds between each function call.
            function (Callable): The function to call at each interval.
            args (tuple): The arguments for the function.
            kwargs (dict): The keyword arguments for the function.
            iterations (int): The number of times to call the function.
            stop_event (threading.Event, optional): An event to stop the timer. Defaults to a new event.
        """
        try:
            cls.wait_ms_static(interval_ms)
            while not stop_event.is_set() and iterations != 0:  # So infinite timers are possible
                try:
                    function(*args, **kwargs)
                except Exception as e:
                    print(f"Error in _trigger_ms thread: {e}")
                cls.wait_ms_static(interval_ms)
                iterations -= 1
        except SystemExit:
            pass

    @classmethod
    def _long_trigger(cls, interval: _TimeType, function, args: tuple, kwargs: dict, iterations: int,
                      stop_event: _threading.Event = _threading.Event()) -> None:
        """
        A helper function to trigger a function at specified intervals indefinitely or for a specified number of iterations.

        Args:
            interval (float or int): The interval in seconds between each function call.
            function (Callable): The function to call at each interval.
            args (tuple): The arguments for the function.
            kwargs (dict): The keyword arguments for the function.
            iterations (int): The number of times to call the function.
            stop_event (threading.Event, optional): An event to stop the timer. Defaults to a new event.
        """
        def _trigger_function():
            try:
                nonlocal iterations
                if stop_event.is_set() or iterations == 0:  # So infinite timers are possible
                    return

                try:
                    function(*args, **kwargs)
                except Exception as e:
                    print(f"Error in _long_trigger thread: {e}")

                iterations -= 1
                # Reschedule the function
                _threading.Timer(interval, _trigger_function).start()
            except SystemExit:
                pass

        # Start the initial function call
        _threading.Timer(interval, _trigger_function).start()

    @classmethod
    def single_shot(cls, wait_time: _TimeType, function: _a.Callable, args: tuple[_ty.Any, ...] = (),
                    kwargs: dict[str, _ty.Any] | None = None, daemon: bool = False) -> _ty.Type[_ty.Self]:
        """
        Executes a single-shot timer that triggers the specified function after a set amount of time.

        Args:
            wait_time (float or int): The time to wait before executing the function, in seconds.
            function (Callable): The function to execute after the timer ends.
            args (tuple, optional): Arguments to pass to the function. Defaults to an empty tuple.
            kwargs (dict, optional): Keyword arguments to pass to the function. Defaults to None.
            daemon (bool, optional): Whether to run the timer thread as a daemon. Defaults to False.

        Returns:
            TimidTimer: The class itself.
        """
        if kwargs is None:
            kwargs = {}
        _threading.Thread(target=cls._trigger, kwargs={
            "interval": wait_time, "function": function, "args": args, "kwargs": kwargs, "iterations": 1
        }, daemon=daemon).start()
        return cls

    @classmethod
    def single_shot_ms(cls, wait_time_ms: _TimeType, function: _a.Callable, args: tuple[_ty.Any, ...] = (),
                       kwargs: dict[str, _ty.Any] | None = None, daemon: bool = False) -> _ty.Type[_ty.Self]:
        """
        Executes a single-shot timer that triggers the specified function after a set amount of time in milliseconds.

        Args:
            wait_time_ms (float or int): The time to wait before executing the function, in milliseconds.
            function (Callable): The function to execute after the timer ends.
            args (tuple, optional): Arguments to pass to the function. Defaults to an empty tuple.
            kwargs (dict, optional): Keyword arguments to pass to the function. Defaults to None.
            daemon (bool, optional): Whether to run the timer thread as a daemon. Defaults to False.

        Returns:
            TimidTimer: The class itself.
        """
        if kwargs is None:
            kwargs = {}
        _threading.Thread(target=cls._trigger_ms, kwargs={
            "interval_ms": wait_time_ms, "functions": function, "args": args, "kwargs": kwargs, "iterations": 1
        }, daemon=daemon).start()
        return cls

    @classmethod
    def long_single_shot(cls, wait_time: _TimeType, function: _a.Callable, args: tuple[_ty.Any, ...] = (),
                         kwargs: dict[str, _ty.Any] | None = None) -> _ty.Type[_ty.Self]:
        """
        Executes a long-running single-shot timer that triggers the specified function after a set amount of time.

        Args:
            wait_time (float or int): The time to wait before executing the function, in seconds.
            function (Callable): The function to execute after the timer ends.
            args (tuple, optional): Arguments to pass to the function. Defaults to an empty tuple.
            kwargs (dict, optional): Keyword arguments to pass to the function. Defaults to None.

        Returns:
            TimidTimer: The class itself.
        """
        if kwargs is None:
            kwargs = {}
        cls._long_trigger(wait_time, function, args, kwargs, 1)
        return cls

    @classmethod
    def shoot(cls, interval: _TimeType, function: _a.Callable, args: tuple[_ty.Any, ...] = (),
              kwargs: dict[str, _ty.Any] | None = None, iterations: int = 1,
              daemon: bool = False) -> _ty.Type[_ty.Self]:
        """
        Repeatedly triggers a function at a specified interval for a set number of iterations.

        Args:
            interval (float or int): The time interval between each execution, in seconds.
            function (Callable): The function to execute at each interval.
            args (tuple, optional): Arguments to pass to the function. Defaults to an empty tuple.
            kwargs (dict, optional): Keyword arguments to pass to the function. Defaults to None.
            iterations (int, optional): The number of times to execute the function. Defaults to 1.
            daemon (bool, optional): Whether to run the timer thread as a daemon. Defaults to False.

        Returns:
            TimidTimer: The class itself.
        """
        if kwargs is None:
            kwargs = {}
        _threading.Thread(target=cls._trigger, kwargs={
            "interval": interval, "function": function, "args": args, "kwargs": kwargs, "iterations": iterations
        }, daemon=daemon).start()
        return cls

    @classmethod
    def shoot_ms(cls, interval_ms: _TimeType, function: _a.Callable, args: tuple[_ty.Any, ...] = (),
                 kwargs: dict[str, _ty.Any] | None = None, iterations: int = 1,
                 daemon: bool = False) -> _ty.Type[_ty.Self]:
        """
        Repeatedly triggers a function at a specified interval in milliseconds for a set number of iterations.

        Args:
            interval_ms (float or int): The time interval between each execution, in milliseconds.
            function (Callable): The function to execute at each interval.
            args (tuple, optional): Arguments to pass to the function. Defaults to an empty tuple.
            kwargs (dict, optional): Keyword arguments to pass to the function. Defaults to None.
            iterations (int, optional): The number of times to execute the function. Defaults to 1.
            daemon (bool, optional): Whether to run the timer thread as a daemon. Defaults to False.

        Returns:
            TimidTimer: The class itself.
        """
        if kwargs is None:
            kwargs = {}
        _threading.Thread(target=cls._trigger_ms, kwargs={
            "interval_ms": interval_ms, "function": function, "args": args, "kwargs": kwargs, "iterations": iterations
        }, daemon=daemon).start()
        return cls

    @classmethod
    def long_shoot(cls, interval: _TimeType, function: _a.Callable, args: tuple[_ty.Any, ...] = (),
                   kwargs: dict[str, _ty.Any] | None = None, iterations: int = 1) -> _ty.Type[_ty.Self]:
        """
        Repeatedly triggers a function at a specified interval for a long-running timer, for a set number of iterations.

        Args:
            interval (float or int): The time interval between each execution, in seconds.
            function (Callable): The function to execute at each interval.
            args (tuple, optional): Arguments to pass to the function. Defaults to an empty tuple.
            kwargs (dict, optional): Keyword arguments to pass to the function. Defaults to None.
            iterations (int, optional): The number of times to execute the function. Defaults to 1.

        Returns:
            TimidTimer: The class itself.
        """
        if kwargs is None:
            kwargs = {}
        cls._long_trigger(interval=interval, function=function, args=args, kwargs=kwargs, iterations=iterations)
        return cls

    def fire(self, interval: _TimeType, function: _a.Callable, args: tuple[_ty.Any, ...] = (),
             kwargs: dict[str, _ty.Any] | None = None, index: int = None, daemon: bool = False) -> _ty.Self:
        """
        Starts a repeating timer that triggers the specified function at set intervals indefinitely.

        Args:
            interval (float or int): The interval between each execution, in seconds.
            function (Callable): The function to execute at each interval.
            args (tuple, optional): Arguments to pass to the function. Defaults to an empty tuple.
            kwargs (dict, optional): Keyword arguments to pass to the function. Defaults to None.
            index (int, optional): The index for the timer in the internal list. Defaults to None (appends a new timer).
            daemon (bool, optional): Whether to run the timer thread as a daemon. Defaults to False.

        Returns:
            TimidTimer: The current instance of the timer.
        """
        if kwargs is None:
            kwargs = {}
        if index is None:
            index = len(self._fires)
        while len(self._fires) < index:
            self._fires.append((None, None))

        event = _threading.Event()
        thread = _threading.Thread(target=self._trigger, kwargs={
            "interval": interval, "function": function, "args": args, "kwargs": kwargs, "iterations": -1,
            "stop_event": event
        }, daemon=daemon)

        if index < len(self._fires) and self._fires[index] == (None, None):
            self._fires[index] = (thread, event)
        else:
            self._fires.insert(index, (thread, event))
        thread.start()
        return self

    def fire_ms(self, interval_ms: _TimeType, function: _a.Callable, args: tuple[_ty.Any, ...] = (),
                kwargs: dict[str, _ty.Any] | None = None, index: int = None, daemon: bool = False) -> _ty.Self:
        """
        Starts a repeating timer that triggers the specified function at set intervals in milliseconds indefinitely.

        Args:
            interval_ms (float or int): The interval between each execution, in milliseconds.
            function (Callable): The function to execute at each interval.
            args (tuple, optional): Arguments to pass to the function. Defaults to an empty tuple.
            kwargs (dict, optional): Keyword arguments to pass to the function. Defaults to None.
            index (int, optional): The index for the timer in the internal list. Defaults to None (appends a new timer).
            daemon (bool, optional): Whether to run the timer thread as a daemon. Defaults to False.

        Returns:
            TimidTimer: The current instance of the timer.
        """
        if kwargs is None:
            kwargs = {}
        if index is None:
            index = len(self._fires)
        while len(self._fires) < index:
            self._fires.append((None, None))

        event = _threading.Event()
        thread = _threading.Thread(target=self._trigger_ms, kwargs={
            "interval_ms": interval_ms, "function": function, "args": args, "kwargs": kwargs, "iterations": -1,
            "stop_event": event
        }, daemon=daemon)

        if index < len(self._fires) and self._fires[index] == (None, None):
            self._fires[index] = (thread, event)
        else:
            self._fires.insert(index, (thread, event))
        thread.start()
        return self

    def long_fire(self, interval: _TimeType, function: _a.Callable, args: tuple[_ty.Any, ...] = (),
                  kwargs: dict[str, _ty.Any] | None = None, index: int = None) -> _ty.Self:
        """
        Starts a long-running repeating timer that triggers the specified function at set intervals indefinitely.

        Args:
            interval (float or int): The interval between each execution, in seconds.
            function (Callable): The function to execute at each interval.
            args (tuple, optional): Arguments to pass to the function. Defaults to an empty tuple.
            kwargs (dict, optional): Keyword arguments to pass to the function. Defaults to None.
            index (int, optional): The index for the timer in the internal list. Defaults to None (appends a new timer).

        Returns:
            TimidTimer: The current instance of the timer.
        """
        if kwargs is None:
            kwargs = {}
        if index is None:
            index = len(self._fires)
        while len(self._fires) < index:
            self._fires.append((None, None))

        event = _threading.Event()
        self._long_trigger(interval=interval, function=function, args=args, kwargs=kwargs, iterations=-1,
                           stop_event=event)

        if index < len(self._fires) and self._fires[index] == (None, None):
            self._fires[index] = (None, event)
        else:
            self._fires.insert(index, (None, event))
        return self

    def stop_fire(self, index: int | None = None, amount: int | None = None) -> _ty.Self:
        """
        Stops the specified timer(s) and removes them from the internal list.

        Args:
            index (int, optional): The index of the timer to stop. Defaults to None (stops the first timer).
            amount (int, optional): The number of timers to stop. Defaults to 1.

        Returns:
            TimidTimer: The current instance of the timer.
        """
        if amount is None:
            amount = 1
        for i in range(amount):
            thread, event = self._fires.pop((index + i) if index is not None else 0)
            event.set()
            if thread is not None:
                thread.join()
        return self

    def stop_fires(self, *indices: int | None, not_exists_okay: bool = False) -> _ty.Self:
        """
        Stops the specified timer(s) and removes them from the internal list.

        Args:
            indices (int, optional): The indices of the timers to stop. Defaults to None (stops the first timer).
            not_exists_okay (bool): Raise IndexError if index does not exist and this is False.

        Returns:
            TimidTimer: The current instance of the timer.
        """
        for index in indices:
            try:
                thread, event = self._fires.pop(index if index is not None else 0)
            except IndexError as e:
                if not not_exists_okay:
                    raise e
            else:
                event.set()
                if thread is not None:
                    thread.join()
        return self

    def warmup_fire(self, rounds: int = 300) -> _ty.Self:
        """
        Warms up the timer by running short intervals repeatedly.

        Args:
            rounds (int, optional): The number of warmup rounds. Defaults to 300.

        Returns:
            TimidTimer: The current instance of the timer.
        """
        for _ in range(rounds):
            self.wait_ms_static(1)
        return self

    def wait(self, seconds: _TimeType = 0) -> _ty.Self:
        """
        Pauses execution for a specified number of seconds.

        Args:
            seconds (int, optional): The time to wait in seconds. Defaults to 0.

        Returns:
            TimidTimer: The current instance of the timer.
        """
        self.wait_static(seconds)
        return self

    def wait_ms(self, milliseconds: _TimeType = 0) -> _ty.Self:
        """
        Pauses execution for a specified number of milliseconds.

        Args:
            milliseconds (int, optional): The time to wait in milliseconds. Defaults to 0.

        Returns:
            TimidTimer: The current instance of the timer.
        """
        self.wait_ms_static(milliseconds)
        return self

    @classmethod
    def test_delay(cls, amount: _TimeType = 0, return_type: _ty.Literal["timedelta", "PreciseTimeDelta"] = "PreciseTimeDelta"
                   ) -> PreciseTimeDelta | _timedelta:
        """
        Tests a delay of a specified amount of time and returns the elapsed time.

        Args:
            amount (float or int, optional): The amount of time to delay, in seconds. Defaults to 0.
            return_type (str, optional): The format to return the elapsed time in, either "timedelta" or "PreciseTimeDelta". Defaults to "PreciseTimeDelta".

        Returns:
            PreciseTimeDelta | timedelta: The elapsed time during the delay.
        """
        timer = cls()
        if amount:
            timer.wait(amount)
        return timer.end(return_type=return_type)

    @classmethod
    def test_delay_ms(cls, amount_ms: _TimeType = 0, return_type: _ty.Literal["timedelta", "PreciseTimeDelta"] = "PreciseTimeDelta"
                      ) -> PreciseTimeDelta | _timedelta:
        """
        Tests a delay of a specified amount of time in milliseconds and returns the elapsed time.

        Args:
            amount_ms (float or int, optional): The amount of time to delay, in milliseconds. Defaults to 0.
            return_type (str, optional): The format to return the elapsed time in, either "timedelta" or "PreciseTimeDelta". Defaults to "PreciseTimeDelta".

        Returns:
            PreciseTimeDelta | timedelta: The elapsed time during the delay.
        """
        timer = cls()
        if amount_ms:
            timer.wait_ms(amount_ms)
        return timer.end(return_type=return_type)

    @classmethod
    def wait_static(cls, seconds: _TimeType = 0) -> _ty.Type[_ty.Self]:
        """
        Pauses execution for a specified number of seconds, statically.

        Args:
            seconds (int, optional): The time to wait in seconds. Defaults to 0.

        Returns:
            TimidTimer: The class itself.
        """
        _time.sleep(seconds)
        return cls

    @classmethod
    def wait_ms_static(cls, milliseconds: _TimeType = 0) -> _ty.Type[_ty.Self]:
        """
        Pauses execution for a specified number of milliseconds, statically.

        Args:
            milliseconds (int, optional): The time to wait in milliseconds. Defaults to 0.

        Returns:
            TimidTimer: The class itself.
        """
        wanted_time = cls._time() + (milliseconds * 1e+6)
        while cls._time() < wanted_time:
            if wanted_time - cls._time() > 1_000_000:  # 3_000_000
                _time.sleep(0.001)
            else:
                continue
        return cls

    @classmethod
    def complexity(cls, func: _a.Callable,
                   input_generator: _a.Iterable[tuple[tuple[_ty.Any, ...], dict]] | _a.Generator[tuple[tuple[_ty.Any, ...], dict], None, None],
                   matplotlib_pyplt=None) -> str:
        """
        Measures the execution time of a function over a range of input sizes and estimates the time complexity.
        Too little data points will lead to bigger error rates.
        Around 100 data points is the sweet spot.
        The first argument/keyword argument you pass (in the generator) will be used as the x
        so you need to enable int conversion for that class.

        Parameters:
        func (Callable): The function to measure.
        input_generator (Iterable): A generator that yields increasing input sizes (e.g., range).
        matplotlib_pyplt: The pyplot class from the matplotlib library.

        Returns:
        str: Estimated time complexity (e.g., "O(N)", "O(N^2)", etc.).
        """
        if None in (_RANSACRegressor, _curve_fit, _np):
            raise RuntimeError("Optional libraries not installed")
        input_sizes = []
        times = []

        for args, kwargs in input_generator:
            # Start the timer
            start_time = cls._time()

            # Execute the function
            func(*args, **kwargs)

            # Stop the timer
            end_time = cls._time()

            # Calculate elapsed time in seconds
            elapsed_time = (end_time - start_time) / 1e9

            # Store the input size and the elapsed time if valid
            if elapsed_time > 0:
                input_sizes.append(int(args[0]) if args else (int(next(iter(kwargs))) if kwargs else 0))
                times.append(elapsed_time)

        # Ensure there are no zero or negative times and input sizes
        input_sizes = _np.array(input_sizes)
        times = _np.array(times)

        if len(input_sizes) == 0 or len(times) == 0:
            return "Insufficient data"

        if _np.any(input_sizes <= 0) or _np.any(times <= 0):
            raise ValueError("Input sizes and times must be positive")

        # Define complexity functions
        complexity_classes = {
            "O(1)": lambda n, a: a * _np.ones_like(n),
            "O(log N)": lambda n, a, b: a * _np.log(n) + b,
            "O(N)": lambda n, a: a * n,
            "O(N log N)": lambda n, a, b: a * n * _np.log(n) + b,
            "O(N^2)": lambda n, a: a * n ** 2,
            "O(N^3)": lambda n, a: a * n ** 3,
            "O(sqrt(N))": lambda n, a: a * _np.sqrt(n),
        }

        best_fit = None
        best_params = None
        best_mse = _np.inf

        for name, func in complexity_classes.items():
            try:
                # Use RANSAC to find the robust subset of data points
                ransac = _RANSACRegressor()
                input_sizes_reshaped = input_sizes.reshape(-1, 1)
                ransac.fit(input_sizes_reshaped, times)
                inlier_mask = ransac.inlier_mask_

                # Fit the curve to the inliers only
                popt, *_ = _curve_fit(func, input_sizes[inlier_mask], times[inlier_mask], maxfev=10000)
                predictions = func(input_sizes, *popt)
                mse = _np.mean((times - predictions) ** 2)
                if mse < best_mse:
                    best_mse = mse
                    best_fit = name
                    best_params = popt
            except (RuntimeError, TypeError):
                continue

        if matplotlib_pyplt:
            plt = matplotlib_pyplt
            # Plotting the input sizes vs times
            plt.scatter(input_sizes, times, label='Actual Times')

            # Plot the best fit curve
            if best_fit:
                fitted_func = complexity_classes[best_fit]
                x_model = _np.linspace(min(input_sizes), max(input_sizes), 100)
                y_model = fitted_func(x_model, *best_params)
                plt.plot(x_model, y_model, label=f'Best Fit: {best_fit}')

            plt.xlabel('Input Size')
            plt.ylabel('Execution Time (s)')
            plt.title('Execution Time vs Input Size')
            plt.legend()
            plt.show()
        else:
            cls.wait_static(1.5)

        return best_fit

    @classmethod
    def time(cls, time_format: int = PreciseTimeFormat.SECONDS) -> _a.Callable:
        """
        A decorator to measure the execution time of a function and print the result.

        This decorator uses the TimidTimer class to time how long a specific function takes to execute.
        The result is printed in the specified time format, and the function's return value is passed through.

        Args:
            time_format (TimeFormat, optional): The time format to display the elapsed time. Defaults to TimeFormat.SECONDS.

        Returns:
            Callable: A decorator function.
        """
        def _decorator(func):
            def _wrapper(*args, **kwargs):
                timer = cls()
                result = func(*args, **kwargs)
                elapsed = timer.end().nanoseconds()
                print(f"Function {func.__name__} took {PreciseTimeFormat.get_static_readable(elapsed, time_format)} to complete.")
                return result
            return _wrapper
        return _decorator

    @staticmethod
    def system_time() -> str:
        """
        This method retrieves the current system time and returns it in "HH:MM:SS" format.
        :return: The current system time.
        """
        return _datetime.now().strftime("%H:%M:%S")

    def enter(self, index: int | None = None) -> _ty.Self:
        """
        Starts the timer and sets the index for thread-local storage when using the timer in a context manager.

        Args:
            index (int, optional): The index of the timer to start. Defaults to None.

        Returns:
            TimidTimer: The current instance of the timer.
        """
        index: int = index or self._get_first_other_index()
        self.start(index)
        self._thread_data.entry_index = index
        return self.__enter__()

    def __enter__(self) -> _ty.Self:
        """
        Enters the context manager by starting the timer at the specified entry index.

        This method is used when the TimidTimer is used as a context manager to time a block of code.

        Returns:
            TimidTimer: The current instance of the timer.
        """
        entry_index = getattr(self._thread_data, 'entry_index', 0)
        if entry_index > len(self._times):
            self.start(entry_index)
        self._thread_data.entry_index = entry_index
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exits the context manager and prints the elapsed time for the code block.

        This method stops the timer and prints how long the code block took to execute.
        If an entry index is not found in thread-local storage, an error message is displayed.

        Args:
            exc_type: The exception type (if any) raised in the context block.
            exc_val: The exception value (if any) raised in the context block.
            exc_tb: The traceback (if any) of the exception raised in the context block.
        """
        exit_index = getattr(self._thread_data, 'entry_index', None)
        if exit_index is not None:
            elapsed_time = self.end(exit_index)
            print(f"Codeblock {exit_index} took {elapsed_time} to execute.")
        else:
            print(f"Error: exit index not found in thread-local storage")

    def __del__(self) -> None:
        """
        Destructor for the TimidTimer instance that ensures all active timers are stopped.

        This method is called when the TimidTimer instance is deleted, and it stops all active timers to clean up resources.
        """
        self.stop_fire(amount=len(self._fires))


TimeTimer: _ty.Type[TimidTimer] = TimidTimer.setup_timer_func(_time.time, 1e9)
TimeTimerNS: _ty.Type[TimidTimer] = TimidTimer.setup_timer_func(_time.time_ns, 1)
PerfTimer: _ty.Type[TimidTimer] = TimidTimer.setup_timer_func(_time.perf_counter, 1e9)
PerfTimerNS: _ty.Type[TimidTimer] = TimidTimer.setup_timer_func(_time.perf_counter_ns, 1)
CPUTimer: _ty.Type[TimidTimer] = TimidTimer.setup_timer_func(_time.process_time, 1e9)
CPUTimerNS: _ty.Type[TimidTimer] = TimidTimer.setup_timer_func(_time.process_time_ns, 1)
MonotonicTimer: _ty.Type[TimidTimer] = TimidTimer.setup_timer_func(_time.monotonic, 1e9)
MonotonicTimerNS: _ty.Type[TimidTimer] = TimidTimer.setup_timer_func(_time.monotonic_ns, 1)
ThreadTimer: _ty.Type[TimidTimer] = TimidTimer.setup_timer_func(_time.thread_time, 1e9)
ThreadTimerNS: _ty.Type[TimidTimer] = TimidTimer.setup_timer_func(_time.thread_time_ns, 1)


class DateTimeTimer(TimidTimer):
    """This is a joke and should not be taken seriously as it isn't performant."""
    def _time(self) -> float:
        return _datetime.now().timestamp() * 1e9
