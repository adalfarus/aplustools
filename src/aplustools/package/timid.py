from typing import (Callable as _Callable, Union as _Union, List as _List, Tuple as _Tuple, Optional as _Optional,
                    Type as _Type, Iterable as _Iterable, Any as _Any, Generator as _Generator, Literal as _Literal)
from sklearn.linear_model import RANSACRegressor as _RANSACRegressor
from datetime import timedelta as _timedelta, datetime as _datetime
from scipy.optimize import curve_fit as _curve_fit
from timeit import default_timer as _default_timer
import threading as _threading
import pickle as _pickle
import time as _time
import numpy as _np


class TimeFormat:
    """Used to define and convert to different TimeFormats"""
    WEEKS = 0
    DAYS = 1
    HOURS = 2
    MINUTES = 3
    SECONDS = 4
    MILISEC = 5
    MICROSEC = 6

    @classmethod
    def get_static_readable(cls, td: _timedelta, format_to: _Optional["TimeFormat"] = None) -> str:
        """Convert to a specific TimeFormat"""
        if format_to is None:
            format_to = cls.SECONDS

        total_seconds = int(td.total_seconds())
        micros = td.microseconds

        # Select the correct level of detail based on the format
        if format_to == TimeFormat.WEEKS:
            weeks = total_seconds // 604800
            days = (total_seconds % 604800) / 86400
            return f"{weeks} weeks, {days} days"

        elif format_to == TimeFormat.DAYS:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) / 3600
            return f"{days} days, {hours} hours"

        elif format_to == TimeFormat.HOURS:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) / 60
            return f"{hours} hours, {minutes} minutes"

        elif format_to == TimeFormat.MINUTES:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes} minutes, {seconds} seconds"

        elif format_to == TimeFormat.SECONDS:
            return f"{total_seconds} seconds, {micros / 1000} milliseconds"

        elif format_to == TimeFormat.MILISEC:
            millisecs = (total_seconds * 1000) + (micros // 1000)
            return f"{millisecs} milliseconds, {micros % 1000} microseconds"

        elif format_to == TimeFormat.MICROSEC:
            microsecs = (total_seconds * 1000000) + micros
            return f"{microsecs} microseconds"

        return "Invalid format specified"


class BasicTimer:
    def __init__(self, auto_start: bool = False):
        self.start_time = None
        self.stop_time = None
        self.pause_start_time = None
        self.pause_duration = 0
        self.tick_tocks = []
        self.is_stopped = False
        self.is_ended = False

        if auto_start:
            self.start()

    def start(self):
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

    def tick(self):
        tick_time = _time.time()
        if self.is_ended:
            raise RuntimeError("Cannot record time on a timer that has been ended.")
        if self.start_time is not None:
            self.tick_tocks.append((self.start_time, tick_time))
        else:
            raise RuntimeError("Timer has not been started.")
        return self

    def tock(self):
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
        return sum(tock - tick for tick, tock in self.tick_tocks)

    def average(self):
        total_time = self.tally()
        total_count = len(self.tick_tocks)
        if total_count == 0:
            return None  # Avoid division by zero
        return _timedelta(seconds=(total_time / total_count))

    def get_times(self):
        return self.tick_tocks

    def get(self):
        if self.start_time is None:
            return None
        elapsed_time = (self.stop_time or _time.time()) - self.start_time - self.pause_duration
        return _timedelta(seconds=elapsed_time)

    def stop(self):
        if self.is_stopped:
            raise RuntimeError("Timer is already stopped.")
        if self.start_time is not None:
            self.stop_time = _time.time()
            self.is_stopped = True
        else:
            raise RuntimeError("Timer has not been started.")
        return self

    def pause(self):
        if self.is_stopped:
            raise RuntimeError("Timer is stopped. Cannot pause a stopped timer.")
        if self.pause_start_time is not None:
            raise RuntimeError("Timer is already paused.")
        if self.start_time is not None:
            self.pause_start_time = _time.time()
        else:
            raise RuntimeError("Timer has not been started.")
        return self

    def resume(self):
        if self.pause_start_time is None:
            raise RuntimeError("Timer is not paused.")
        if self.is_ended:
            raise RuntimeError("Cannot resume a timer that has been ended.")
        pause_end_time = _time.time()
        self.pause_duration += pause_end_time - self.pause_start_time
        self.pause_start_time = None
        return self

    def end(self):
        self.is_ended = True
        return self

    def get_readable(self, format_to: int = TimeFormat.SECONDS) -> str:
        return TimeFormat.get_static_readable(self.get(), format_to)


class SmallTimeDiff:
    def __init__(self, days: _Union[float, int] = 0, seconds: _Union[float, int] = 0,
                 microseconds: _Union[float, int] = 0):
        total_seconds = days * 86400 + seconds + microseconds / 1e6
        self.negative = total_seconds < 0
        abs_seconds = abs(total_seconds)
        self._timedelta = _timedelta(seconds=abs_seconds)

    def __str__(self):
        total_seconds = self._timedelta.total_seconds()
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        microseconds = self._timedelta.microseconds

        time_str = f"{hours}:{minutes:02}:{seconds:02}"
        if microseconds > 0:
            time_str += f".{microseconds:06}"

        if self.negative:
            time_str = f"-{time_str}"

        return time_str

    def __repr__(self):
        return f"SmallTimeDiff({self.days}, {self.seconds}, {self.microseconds})"

    def __add__(self, other):
        if isinstance(other, _timedelta):
            result = self._timedelta + other
            return SmallTimeDiff(seconds=result.total_seconds() * (-1 if self.negative else 1))
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, _timedelta):
            result = self._timedelta - other
            return SmallTimeDiff(seconds=result.total_seconds() * (-1 if self.negative else 1))
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            result = self._timedelta * other
            return SmallTimeDiff(seconds=result.total_seconds() * (-1 if self.negative else 1))
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            result = self._timedelta / other
            return SmallTimeDiff(seconds=result.total_seconds() * (-1 if self.negative else 1))
        return NotImplemented

    @property
    def days(self) -> int:
        return -self._timedelta.days if self.negative else self._timedelta.days

    @property
    def seconds(self) -> int:
        return -self._timedelta.seconds if self.negative else self._timedelta.seconds

    @property
    def microseconds(self) -> int:
        return -self._timedelta.microseconds if self.negative else self._timedelta.microseconds

    def total_seconds(self) -> float:
        return -self._timedelta.total_seconds() if self.negative else self._timedelta.total_seconds()


class TimidTimer:
    """If a time value is not specified as something specific, it's in seconds."""
    EMPTY = (0, 0, 0, None)

    def __init__(self, start_at: _Union[float, int] = 0, start_now: bool = True):
        self._fires: _List[_Tuple[_Optional[_threading.Thread], _Optional[_threading.Event]]] = []
        self._times: _List[_Optional[_Tuple[
                        _Union[float, int]], _Union[float, int], _Union[float, int], _Optional[_threading.Lock]]] = []
        self._tick_tocks: _List[_List[_Union[float, int, _Tuple[_Union[float, int], _Union[float, int]]]]] = []
        self._thread_data = _threading.local()

        if start_now:
            self._warmup()
            self.start(start_at=start_at)

    @staticmethod
    def _time() -> _Union[float, int]:
        return _default_timer() * 1e9

    def start(self, *indices: _Optional[int], start_at: _Union[float, int] = 0) -> "TimidTimer":
        start_time = self._time()
        indices = indices or [len(self._times)]

        for index in indices:
            if index < len(self._times) and self._times[index][2] != 0:
                self.resume(index)
                return self
            while len(self._times) < index:  # Ensure the _times and _tick_tocks lists has enough elements
                self._times.append(self.EMPTY)
                self._tick_tocks.append([])
            if index < len(self._times) and self._times[index] is self.EMPTY:  # Append or replace the elements
                self._times[index] = (start_time + (start_at * 1e9), 0, 0, _threading.Lock())  # at the specified index
                self._tick_tocks[index] = []
            elif index == len(self._times):
                self._times.append((start_time + (start_at * 1e9), 0, 0, _threading.Lock()))
                self._tick_tocks.append([])
            else:
                raise Exception(f"A Timer already running on index {index}")
        return self

    def _get_first_index(self):
        for i, t in enumerate(self._times):
            if t is not self.EMPTY:
                return i
        raise IndexError("No active timers.")

    def pause(self, *indices: _Optional[int], for_seconds: _Optional[_Union[float, int]] = None) -> "TimidTimer":
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

    def resume(self, *indices: _Optional[int]) -> "TimidTimer":
        resumed_time = self._time()
        indices = indices or [self._get_first_index()]  # If it's 0 it just sets it to 0 so it's okay.

        for index in indices:
            if index >= len(self._times) or self._times[index] is self.EMPTY:
                raise IndexError(f"Index {index} doesn't exist or is not paused.")

            with self._times[index][-1]:
                self._resume(resumed_time, index)
        return self

    def _resume(self, resumed_time, index: _Optional[int] = None):
        start, end, paused_time, lock = self._times[index]
        if paused_time != 0:
            max_paused_timedelta = self._tick_tocks[index].pop(-1)
            actual_paused_time = min((resumed_time - paused_time), max_paused_timedelta)
            self._times[index] = (start + actual_paused_time, (end + actual_paused_time) if end > 0 else end, 0, lock)
        else:
            raise ValueError(f"Timer on index {index} isn't paused.")

    def stop(self, *indices: _Optional[int]) -> "TimidTimer":
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

    def get(self, *indices: _Optional[int], return_type: _Literal["timedelta", "SmallTimeDiff"] = "SmallTimeDiff"
            ) -> list[SmallTimeDiff | _timedelta] | SmallTimeDiff | _timedelta:
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
            if return_type == "SmallTimeDiff":
                returns.append(SmallTimeDiff(microseconds=elapsed_time / 1000))
            else:
                returns.append(_timedelta(microseconds=elapsed_time / 1000))
        return returns if len(returns) > 1 else returns[0]

    def delete(self, *indices: _Optional[int], return_type: _Literal["timedelta", "SmallTimeDiff", None] = "SmallTimeDiff"
               ) -> "TimidTimer":
        indices = indices or [self._get_first_index()]  # If it's 0 it just sets it to 0 so it's okay.
        returns = []

        for index in indices:
            if index >= len(self._times) or self._times[index] is self.EMPTY:
                raise IndexError(f"Index {index} doesn't exist or is not running.")
            with self._times[index][-1]:
                self._times[index] = self.EMPTY
                self._tick_tocks[index] = []
        if return_type is not None:
            return returns if len(returns) > 1 else returns[0]
        return self

    def end(self, *indices: _Optional[int], return_type: _Literal["timedelta", "SmallTimeDiff", None] = "SmallTimeDiff"
            ) -> _Union[list[SmallTimeDiff | _timedelta], SmallTimeDiff, _timedelta, "TimidTimer"]:
        end_time = self._time()
        indices = indices or [self._get_first_index()]  # If it's 0 it just sets it to 0 so it's okay.
        returns = []

        for index in indices:
            if index >= len(self._times) or self._times[index] is self.EMPTY:
                raise IndexError(f"Index {index} doesn't exist or is not running.")
            with self._times[index][-1]:
                start, _, paused_time, __ = self._times[index]
                if paused_time != 0:
                    self._resume(end_time, index)
                start, __, ___, ____ = self._times[index]
                self._times[index] = self.EMPTY
                self._tick_tocks[index] = []
            if return_type == "SmallTimeDiff":
                elapsed_time = end_time - start
                returns.append(SmallTimeDiff(microseconds=elapsed_time / 1000))
            elif return_type == "timedelta":
                elapsed_time = end_time - start
                returns.append(SmallTimeDiff(microseconds=elapsed_time / 1000))
        if return_type is not None:
            return returns if len(returns) > 1 else returns[0]
        return self

    def tick(self, *indices: _Optional[int], return_type: _Literal["timedelta", "SmallTimeDiff", None] = "SmallTimeDiff"
             ) -> _Union[list[SmallTimeDiff | _timedelta], SmallTimeDiff, _timedelta, "TimidTimer"]:
        """Return how much time has passed till the start. (Could also be called elapsed)"""
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
            if return_type == "SmallTimeDiff":
                returns.append(SmallTimeDiff(microseconds=(tick_time - start) / 1000))
            elif return_type == "timedelta":
                returns.append(_timedelta(microseconds=(tick_time - start) / 1000))
        if return_type is not None:
            return returns if len(returns) > 1 else returns[0]
        return self

    def tock(self, *indices: _Optional[int], return_type: _Literal["timedelta", "SmallTimeDiff", None] = "SmallTimeDiff"
             ) -> _Union[list[SmallTimeDiff | _timedelta], SmallTimeDiff, _timedelta, "TimidTimer"]:
        """Returns how much time has passed till the last tock. (Could also be called round/lap/split)"""
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
            if return_type == "SmallTimeDiff":
                returns.append(SmallTimeDiff(microseconds=(end - last_time) / 1000))
            elif return_type == "timedelta":
                returns.append(_timedelta(microseconds=(end - last_time) / 1000))
        if return_type is not None:
            return returns if len(returns) > 1 else returns[0]
        return self

    def tally(self, *indices: _Optional[int], return_type: _Literal["timedelta", "SmallTimeDiff"] = "SmallTimeDiff"
              ) -> SmallTimeDiff | _timedelta:
        """Return the total time recorded across all ticks and tocks."""
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

        return SmallTimeDiff(microseconds=total_time / 1000) if return_type == "SmallTimeDiff" \
            else _timedelta(microseconds=total_time / 1000)

    def average(self, *indices: _Optional[int], return_type: _Literal["timedelta", "SmallTimeDiff"] = "SmallTimeDiff"
                ) -> SmallTimeDiff | _timedelta:
        """Calculate the average time across all recorded ticks and tocks."""
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
            return SmallTimeDiff(0) if return_type == "SmallTimeDiff" else _timedelta(0)

        return self.tally(*indices, return_type=return_type) / total_tocks

    def show_tick_tocks(self, index: _Optional[int] = None, format_to: int = TimeFormat.SECONDS):
        index = index or self._get_first_index()  # If it's 0 it just sets it to 0 so it's okay.
        print("Tick Tock times:")
        with self._times[index][-1]:
            my_tick_tocks = self._tick_tocks[index].copy()
            _, __, is_paused, _ = self._times[index]
        if is_paused:
            my_tick_tocks.pop(-1)
        for i, (start, end) in enumerate(my_tick_tocks, start=1):
            td = _timedelta(microseconds=(end - start) / 1000)
            print(f"Lap {i}: {TimeFormat.get_static_readable(td, format_to)}")

    def get_readable(self, index: _Optional[int] = None, format_to: TimeFormat = TimeFormat.SECONDS) -> str:
        return TimeFormat.get_static_readable(self.get(index), format_to)

    def _warmup(self, rounds: int = 3):
        for _ in range(rounds):
            self.start()
            self.end()
        self._times = []
        self._tick_tocks = []

    def countdown(self, seconds: _Union[float, int], callback: _Callable = print, args: tuple = (),
                  kwargs: dict = None):
        if kwargs is None:
            kwargs = {}
        self.single_shot(seconds, callback, args or (f"Countdown for {seconds}s is done.",), kwargs)

    def countdown_ms(self, milliseconds: _Union[float, int], callback: _Callable = print, args: tuple = (),
                     kwargs: dict = None):
        if kwargs is None:
            kwargs = {}
        self.single_shot_ms(milliseconds, callback, args or (f"Countdown for {milliseconds}ms is done.",), kwargs)

    def interval(self, interval: _Union[float, int], count: _Union[int, _Literal["inf"]] = "inf",
                 callback: _Callable = print, args: tuple = (), kwargs: dict = None):
        if kwargs is None:
            kwargs = {}
        if count == "inf":
            self.fire(interval, callback, args or (f"{interval}s is over.",), kwargs)
        else:
            self.shoot(interval, callback, args or (f"{interval}s is over.",), kwargs, iterations=count)

    def interval_ms(self, interval_ms: _Union[float, int], count: _Union[int, _Literal["inf"]] = "inf",
                    callback: _Callable = print, args: tuple = (), kwargs: dict = None):
        if kwargs is None:
            kwargs = {}
        if count == "inf":
            self.fire_ms(interval_ms, callback, args or (f"{interval_ms}s is over.",), kwargs)
        else:
            self.shoot_ms(interval_ms, callback, args or (f"{interval_ms}s is over.",), kwargs, iterations=count)

    def set_alarm(self, alarm_time, callback: _Callable = print, args: tuple = (), kwargs: dict = None):
        alarm_time = _datetime.strptime(alarm_time, "%H:%M:%S").time()
        current_time = _datetime.now().time()
        current_datetime = _datetime.combine(_datetime.today(), current_time)
        alarm_datetime = _datetime.combine(_datetime.today(), alarm_time)
        if alarm_datetime < current_datetime:
            alarm_datetime += _timedelta(days=1)  # Set alarm for the next day if time has already passed today
        diff = alarm_datetime - current_datetime
        self.single_shot(diff.total_seconds(), callback, args or (f"Timer for {alarm_time} is over.",), kwargs)

    def save_state(self) -> bytes:
        """Saves the state of all timers, threads aren't possible as I can't pickle the reference to the function."""
        state = {
            "_times": self._times,
            "_tick_tocks": self._tick_tocks,
        }
        return _pickle.dumps(state)

    def load_state(self, state_bytes: bytes):
        """Loads the state of all timers, threads aren't possible as I can't pickle the reference to the function."""
        state = _pickle.loads(state_bytes)
        self._times = state["_times"]
        self._tick_tocks = state["_tick_tocks"]

    @classmethod
    def setup_timer_func(cls, func: _Callable, to_nanosecond_multiplier: _Union[float, int]) -> type["TimidTimer"]:
        NewClass = type('TimidTimerModified', (cls,), {
            '_time': lambda self=None: func() * to_nanosecond_multiplier
        })
        return NewClass

    @classmethod
    def _trigger(cls, interval: _Union[float, int], function, args: tuple, kwargs: dict, iterations: int,
                 stop_event: _threading.Event = _threading.Event()):
        cls.wait_static(interval)
        while not stop_event.is_set():
            if iterations == 0:
                break
            try:
                function(*args, **kwargs)
            except Exception as e:
                print(f"Error in _trigger thread: {e}")
            cls.wait_static(interval)
            iterations -= 1

    @classmethod
    def _trigger_ms(cls, interval_ms: _Union[float, int], function, args: tuple, kwargs: dict, iterations: int,
                    stop_event: _threading.Event = _threading.Event()):
        cls.wait_ms_static(interval_ms)
        while not stop_event.is_set():
            if iterations == 0:
                break
            try:
                function(*args, **kwargs)
            except Exception as e:
                print(f"Error in _trigger thread: {e}")
            cls.wait_ms_static(interval_ms)
            iterations -= 1

    @classmethod
    def single_shot(cls, wait_time: _Union[float, int], function: _Callable, args: tuple = (),
                    kwargs: _Optional[dict] = None) -> _Type["TimidTimer"]:
        if kwargs is None:
            kwargs = {}
        _threading.Thread(target=cls._trigger, args=(wait_time, function, args, kwargs, 1)).start()
        return cls

    @classmethod
    def single_shot_ms(cls, wait_time_ms: _Union[float, int], function: _Callable, args: tuple = (),
                       kwargs: _Optional[dict] = None) -> _Type["TimidTimer"]:
        if kwargs is None:
            kwargs = {}
        _threading.Thread(target=cls._trigger_ms, args=(wait_time_ms, function, args, kwargs, 1)).start()
        return cls

    @classmethod
    def shoot(cls, interval: _Union[float, int], function: _Callable, args: tuple = (), kwargs: _Optional[dict] = None,
              iterations: int = 1) -> _Type["TimidTimer"]:
        if kwargs is None:
            kwargs = {}
        _threading.Thread(target=cls._trigger, args=(interval, function, args, kwargs, iterations)).start()
        return cls

    @classmethod
    def shoot_ms(cls, interval_ms: _Union[float, int], function: _Callable, args: tuple = (),
                 kwargs: _Optional[dict] = None, iterations: int = 1) -> _Type["TimidTimer"]:
        if kwargs is None:
            kwargs = {}
        _threading.Thread(target=cls._trigger_ms, args=(interval_ms, function, args, kwargs, iterations)).start()
        return cls

    def fire(self, interval: _Union[float, int], function: _Callable, args: tuple = (), kwargs: _Optional[dict] = None,
             index: int = None) -> "TimidTimer":
        if kwargs is None:
            kwargs = {}
        if index is None:
            index = len(self._fires)
        while len(self._fires) < index:
            self._fires.append((None, None))

        event = _threading.Event()
        thread = _threading.Thread(target=self._trigger, args=(interval, function, args, kwargs, -1, event))

        if index < len(self._fires) and self._fires[index] == (None, None):
            self._fires[index] = (thread, event)
        else:
            self._fires.insert(index, (thread, event))
        thread.start()
        return self

    def fire_ms(self, interval_ms: _Union[float, int], function: _Callable, args: tuple = (),
                kwargs: _Optional[dict] = None, index: int = None) -> "TimidTimer":
        if kwargs is None:
            kwargs = {}
        if index is None:
            index = len(self._fires)
        while len(self._fires) < index:
            self._fires.append((None, None))

        event = _threading.Event()
        thread = _threading.Thread(target=self._trigger_ms, args=(interval_ms, function, args, kwargs, -1, event))

        if index < len(self._fires) and self._fires[index] == (None, None):
            self._fires[index] = (thread, event)
        else:
            self._fires.insert(index, (thread, event))
        thread.start()
        return self

    def stop_fire(self, index: _Optional[int] = None, amount: _Optional[int] = None) -> "TimidTimer":
        if amount is None:
            amount = 1
        for _ in range(amount):
            thread, event = self._fires.pop(index or 0)
            event.set()
            thread.join()
        return self

    def warmup_fire(self, rounds: int = 300) -> "TimidTimer":
        for _ in range(rounds):
            self.wait_ms_static(1)
        return self

    def wait(self, seconds: int = 0) -> "TimidTimer":
        self.wait_static(seconds)
        return self

    def wait_ms(self, milliseconds: int = 0) -> "TimidTimer":
        self.wait_ms_static(milliseconds)
        return self

    @classmethod
    def test_delay(cls, amount: _Union[float, int] = 0,
                   return_type: _Literal["timedelta", "SmallTimeDiff"] = "SmallTimeDiff"
                   ) -> _Union[SmallTimeDiff, _timedelta]:
        """Tests a ... second delay.
        Keep in mind that any amount that isn't 0 is subject to around a 2 ns extra delay."""
        timer = cls()
        if amount:
            timer.wait(amount)
        return timer.end(return_type=return_type)

    @classmethod
    def test_delay_ms(cls, amount_ms: _Union[float, int] = 0,
                      return_type: _Literal["timedelta", "SmallTimeDiff"] = "SmallTimeDiff"
                      ) -> _Union[SmallTimeDiff, _timedelta]:
        """Tests a ... second delay.
        Keep in mind that any amount that isn't 0 is subject to around a 2 ns extra delay."""
        timer = cls()
        if amount_ms:
            timer.wait_ms(amount_ms)
        return timer.end(return_type=return_type)

    @classmethod
    def wait_static(cls, seconds: int = 0) -> _Type["TimidTimer"]:
        _time.sleep(seconds)
        return cls

    @classmethod
    def wait_ms_static(cls, milliseconds: int = 0) -> _Type["TimidTimer"]:
        wanted_time = cls._time() + (milliseconds * 1e+6)
        while cls._time() < wanted_time:
            if wanted_time - cls._time() > 1_000_000:  # 3_000_000
                _time.sleep(0.001)
            else:
                continue
        return cls

    @classmethod
    def complexity(cls, func: _Callable, input_generator: _Union[_Iterable[_Tuple[_Tuple[_Any, ...], dict]],
                                                                 _Generator[_Tuple[_Tuple[_Any, ...], dict], None, None]
                                                                 ],
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
    def time(cls, time_format: TimeFormat = TimeFormat.SECONDS):
        """
        Time how long it takes a specific function to execute as a decorator. This function doesn't return anything, all results are printed

        Time how long it takes a specific function to execute as a decorator. It used the classes timer to time the function execution.
        This function doesn't return anything, all results are printed

        :param time_format:
        :type time_format: TimeFormat
        :return:
        """
        def _decorator(func):
            def _wrapper(*args, **kwargs):
                timer = cls()
                result = func(*args, **kwargs)
                elapsed = timer.end()
                print(f"Function {func.__name__} took {TimeFormat.get_static_readable(elapsed, time_format)} to complete.")
                return result
            return _wrapper
        return _decorator

    @staticmethod
    def display_current_time():
        current_time = _datetime.now().strftime("%H:%M:%S")
        print(f"Current Time: {current_time}")

    def enter(self, index: _Optional[int] = None):
        self.start(index)
        self._thread_data.entry_index = index
        return self.__enter__()

    def __enter__(self):
        entry_index = getattr(self._thread_data, 'entry_index', 0)
        if entry_index > len(self._times):
            self.start(entry_index)
        self._thread_data.entry_index = entry_index
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        exit_index = getattr(self._thread_data, 'entry_index', None)
        if exit_index is not None:
            elapsed_time = self.end(exit_index)
            print(f"Codeblock {exit_index} took {elapsed_time} to execute.")
        else:
            print(f"Error: exit index not found in thread-local storage")

    def __del__(self):
        self.stop_fire(amount=len(self._fires))


TimeTimer = TimidTimer.setup_timer_func(_time.time, 1e9)
TimeTimerNS = TimidTimer.setup_timer_func(_time.time_ns, 1)
PerfTimer = TimidTimer.setup_timer_func(_time.perf_counter, 1e9)
PerfTimerNS = TimidTimer.setup_timer_func(_time.perf_counter_ns, 1)
CPUTimer = TimidTimer.setup_timer_func(_time.process_time, 1e9)
CPUTimerNS = TimidTimer.setup_timer_func(_time.process_time_ns, 1)
MonotonicTimer = TimidTimer.setup_timer_func(_time.monotonic, 1e9)
MonotonicTimerNS = TimidTimer.setup_timer_func(_time.monotonic_ns, 1)
ThreadTimer = TimidTimer.setup_timer_func(_time.thread_time, 1e9)
ThreadTimerNS = TimidTimer.setup_timer_func(_time.thread_time_ns, 1)


class DateTimeTimer(TimidTimer):
    """This is obviously a joke and should not be taken seriously as it isn't performant."""
    def _time(self) -> float:
        return _datetime.now().timestamp() * 1e9


def local_test():
    try:
        print(TimidTimer(start_at=2).end())
        print(dir(TimidTimer))

        def test_timer(timer_class, description):
            timer = timer_class()
            timer.start()
            for _ in range(1000000):
                pass  # A simple loop to simulate computation
            elapsed = timer.end()
            print(f"{description} elapsed time: {TimeFormat.get_static_readable(elapsed)}")

        def sleep_and_measure(timer_class, description, sleep_time_ms=1000):
            """Measures how long the system sleeps using the given timer."""
            timer = timer_class()
            timer.start()
            TimidTimer.wait_ms_static(sleep_time_ms)  # Sleep for a specified time
            elapsed = timer.end()
            print(f"{description}, expected sleep: {sleep_time_ms / 1000}s, measured time: "
                  f"{TimeFormat.get_static_readable(elapsed)}")

        timer1 = TimidTimer()
        timer1.shoot(1, lambda: print(timer1.tock(return_type="timedelta")), iterations=3)
        print("400 ms,", timer1.wait_ms(400).get())
        TimidTimer.wait_static()

        timer = TimidTimer()
        for _ in range(4):
            timer.pause(for_seconds=0.1)
            timer.wait_ms_static(1100)
            timer.tock()
        print(timer.tally())
        print(timer.show_tick_tocks())
        print("Average 1 second sleep extra delay: ", timer.average() - _timedelta(seconds=1))
        print("TTD", TimidTimer.test_delay_ms(1000) - _timedelta(seconds=1))

        with TimidTimer().enter(index=1):
            timer.wait_ms_static(1)

        print("Starting timer tests...")
        test_timer(TimidTimer, "Timid Timer")
        test_timer(TimeTimer, "Time Timer")
        test_timer(TimeTimerNS, "Time Timer Nanosecond")
        test_timer(PerfTimer, "Performance Timer")
        test_timer(PerfTimerNS, "Performance Timer Nanosecond")
        test_timer(CPUTimer, "CPU Timer")
        test_timer(CPUTimerNS, "CPU Timer Nanosecond")
        test_timer(MonotonicTimer, "Monotonic Timer")
        test_timer(MonotonicTimerNS, "Monotonic Timer Nanosecond")

        print("\nTesting sleep accuracy...")
        sleep_and_measure(TimidTimer, "Timid Timer")
        sleep_and_measure(TimeTimer, "Time Timer")
        sleep_and_measure(TimeTimerNS, "Time Timer Nanosecond")
        sleep_and_measure(PerfTimer, "Performance Timer")
        sleep_and_measure(PerfTimerNS, "Performance Timer Nanosecond")
        sleep_and_measure(CPUTimer, "CPU Timer")
        sleep_and_measure(CPUTimerNS, "CPU Timer Nanosecond")
        sleep_and_measure(MonotonicTimer, "Monotonic Timer")
        sleep_and_measure(MonotonicTimerNS, "Monotonic Timer Nanosecond")

        def constant_time(n):
            # O(1) - Does nothing
            pass

        def logarithmic_time(n):
            # O(log N) - Simple loop with logarithmic complexity
            i = 1
            while i < n:
                i *= 2

        def linear_time(n):
            # O(N) - Simple loop with linear complexity
            for _ in range(n):
                pass

        def linearithmic_time(n):
            # O(N log N) - Nested loop with linearithmic complexity
            i = 1
            while i < n:
                for _ in range(n):
                    pass
                i *= 2

        def quadratic_time(n):
            # O(N^2) - Nested loop with quadratic complexity
            for _ in range(n):
                for _ in range(n):
                    pass

        def cubic_time(n):
            # O(N^3) - Triple nested loop with cubic complexity
            for _ in range(n):
                for _ in range(n):
                    for _ in range(n):
                        pass

        def square_root_time(n):
            # O(sqrt(N)) - Loop with square root complexity
            i = 0
            while i * i < n:
                i += 1

        def create_simple_input_generator(rng: range):
            return ((tuple([n]), {}) for n in rng)

        # Test functions with the complexity method
        print("Constant Time:", timer.complexity(constant_time, create_simple_input_generator(range(1, 100_001, 1000))))
        print("Logarithmic Time:", timer.complexity(logarithmic_time, create_simple_input_generator(range(1, 100_001, 1000))))
        print("Linear Time:", timer.complexity(linear_time, create_simple_input_generator(range(1, 100_001, 100))))
        print("Linearithmic Time:", timer.complexity(linearithmic_time, create_simple_input_generator(range(1, 100_001, 1000))))
        # print("Quadratic Time:", timer.complexity(quadratic_time, create_simple_input_generator(range(1, 10_001, 100))))
        # print("Cubic Time:", timer.complexity(cubic_time, create_simple_input_generator(range(1, 2001, 200))))
        print("Square Root Time:", timer.complexity(square_root_time, create_simple_input_generator(range(1, 100_001, 100))))

        timer = BasicTimer()

        timer.start()

        for _ in range(4):
            TimidTimer.wait_ms_static(1000)
            timer.tick()
        timer.stop()
        print(f"Average {timer.average()}, ({timer.get()})")

        timer.start()
        _time.sleep(1)
        timer.stop()
        print(timer.get())

        print(BasicTimer().start().pause().tock().tick().resume().stop().end().average())
    except Exception as e:
        print(f"Exception occurred {e}.")
        return False
    print("Test completed successfully.")
    return True


if __name__ == "__main__":
    local_test()
