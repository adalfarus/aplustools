from typing import Callable, Union, List, Tuple, Optional, Type, Dict
from timeit import default_timer
from datetime import timedelta
import threading
import time


class TimeFormat:
    WEEKS = 0
    DAYS = 1
    HOURS = 2
    MINUTES = 3
    SECONDS = 4
    MILISEC = 5
    MICROSEC = 6


class TimidTimer:
    """If a time value is not specified as something specific, it's in seconds."""
    def __init__(self, start_at: Union[float, int] = 0, start_now: bool = True):
        self._fires: List[threading.Timer] = []
        self._times: List[Tuple[Union[float, int], Optional[Union[float, int]], Optional[Union[float, int]], Union[float, int]]] = []
        self._tick_tocks: List[List[Tuple[Union[float, int], Union[float, int]]]] = []

        if start_now:
            self.warmup()
            self.start(start_at=start_at)

    @staticmethod
    def _time() -> Union[float, int]:
        return default_timer() * 1e9

    def start(self, index: int = None, start_at: Union[float, int] = 0):
        start_time = self._time()
        if index and index < len(self._times):
            self.resume(index)
            return
        if index is None:
            index = len(self._times)
        self._times.insert(index, (start_time + (start_at * 1e9), None, None, 0))
        self._tick_tocks.insert(index, [])

    def pause(self, index: int = None, for_seconds: int = None):
        pause_time = self._time()
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        start, end, paused_at, paused_time = self._times[index]
        if for_seconds:
            self._times[index] = (start, end, None, paused_time + (for_seconds * 1e9))
        else:
            self._times[index] = (start, end, pause_time, paused_time)

    def resume(self, index: int = None):
        resumed_time = self._time()
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        start, end, paused_at, paused_time = self._times[index]
        if paused_at is not None:
            self._times[index] = (start, end, None, paused_time + (resumed_time - paused_at))

    def stop(self, index: int = None):
        end_time = self._time()
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        if index >= len(self._times):
            raise IndexError(f"Index {index} doesn't exist in {self._times}.")
        start, end, paused_at, paused_time = self._times[index]
        if paused_time is not None:
            self.resume()
        _, __, ___, paused_time = self._times[index]
        self._times[index] = (start, end_time, None, paused_time)

    def end(self, index: int = None, return_datetime: bool = True) -> Optional[timedelta]:
        end_time = self._time()
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        if index >= len(self._times):
            raise IndexError(f"Index {index} doesn't exist in {self._times}.")
        start, _, paused_at, __ = self._times[index]
        if paused_at is not None:
            self.resume(index)
        _, __, ___, paused_time = self._times[index]
        del self._times[index]
        del self._tick_tocks[index]
        if return_datetime:
            elapsed_time = end_time - start - paused_time
            return timedelta(microseconds=elapsed_time / 1000)

    def tick(self, index: int = None, return_datetime: bool = True) -> timedelta:
        """Return how much time has passed till the start."""
        tick_time = self._time()
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        if index >= len(self._times):
            raise IndexError(f"Index {index} doesn't exist in {self._times}.")
        start, _, __, ___ = self._times[index]
        self._tick_tocks[index].append((start, tick_time))
        if return_datetime:
            return timedelta(microseconds=(tick_time - start) / 1000)

    def tock(self, index: int = None, return_datetime: bool = True):
        """Returns how much time has passed till the last tock."""
        tock_time = self._time()
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        if index >= len(self._times):
            raise IndexError(f"Index {index} doesn't exist in {self._times}.")
        start, end, paused_at, paused_time = self._times[index]

        last_time = end or start
        end = tock_time
        self._times[index] = (start, end, paused_at, paused_time)
        self._tick_tocks[index].append((last_time, end))
        if return_datetime:
            return timedelta(microseconds=(end - last_time) / 1000)

    def tally(self, index: int = None) -> timedelta:
        """Return the total time recorded across all ticks and tocks."""
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        start, end, _, __ = self._times[index]
        tick_tocks = self._tick_tocks[index].copy()
        if end is not None and len(tick_tocks) > 0:
            tick_tocks.append((tick_tocks[-1][1], end))
        elif end is not None:
            tick_tocks.append((start, end))
        total_time = sum((end - start for start, end in tick_tocks))
        return timedelta(microseconds=total_time / 1000)

    def average(self, index: int = None) -> timedelta:
        """Calculate the average time across all recorded ticks and tocks."""
        index = index or 0  # If it's 0 it just sets it to 0 so it's okay.
        _, end, __, ___ = self._times[index]
        tick_tocks = self._tick_tocks[index].copy()
        return self.tally() / max(1, len(tick_tocks) + (1 if end is not None and end != ([(0, 0)] + tick_tocks)[-1][1] else 0))

    def warmup(self, rounds: int = 3):
        for _ in range(rounds):
            self.start()
            self.end()

    @classmethod
    def setup_timer_func(cls, func: Callable, to_nanosecond_multiplier: Union[float, int]) -> Type["TimidTimer"]:
        NewClass = type('TimidTimerModified', (cls,), {
            '_time': lambda self=None: func() * to_nanosecond_multiplier
        })
        return NewClass

    @classmethod
    def _trigger(cls, wait_time, function, args: tuple, kwargs: dict, _continues: Union[bool, int] = False,
                 _interval: int = None, _interval_func: Callable = None, _index: int = None):
        time.sleep(wait_time)
        function(*args, **kwargs)

        if _continues and _interval and _interval_func:
            _interval_func(_interval, function, args, kwargs, _index, _continues)

    @classmethod
    def single_shot(cls, wait_time: Union[float, int], function: Callable, args: tuple = (), kwargs: dict = None):
        if kwargs is None:
            kwargs = {}
        threading.Thread(target=cls._trigger, args=(wait_time, function, args, kwargs)).start()

    @classmethod
    def shoot(cls, interval: Union[float, int], function: Callable, args: tuple = (), kwargs: dict = None,
              _index: int = None, _continued: int = -1, iterations: int = 1):
        if kwargs is None:
            kwargs = {}
        if _continued or _continued == -1:
            _continued = (_continued if _continued > 0 else iterations) - 1
        else:
            return
        threading.Timer(interval, cls._trigger, args=(0, function, args, kwargs, _continued, interval, cls.shoot)).start()

    def fire(self, interval: Union[float, int], function: Callable, args: tuple = (), kwargs: dict = None,
             index: int = None, _continued: bool = False):
        if kwargs is None:
            kwargs = {}
        if index is None:
            index = len(self._fires)
        timer = threading.Timer(interval, self._trigger, args=(0, function, args, kwargs, True, interval, self.fire,
                                                               index))
        if not _continued:
            self._fires.insert(index, timer)
        else:
            self._fires[index] = timer
        timer.start()

    def stop_fire(self, index: int = None, amount: int = None):
        if amount is None:
            amount = 1
        for _ in range(amount):
            timer = self._fires.pop(index or 0)
            timer.cancel()

    @classmethod
    def test_delay(cls, amount: int = 0) -> timedelta:
        """Tests a ... second delay.
        Keep in mind that any amount that isn't 0 is subject to around a 2 ns extra delay."""
        timer = cls()
        if amount:
            time.sleep(amount)
        return timer.end()

    @staticmethod
    def wait(seconds: int = 0):
        time.sleep(seconds)

    @staticmethod
    def get_readable(td: timedelta, format_to: int = TimeFormat.SECONDS) -> str:
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

    @classmethod
    def time(cls, func):
        def wrapper(*args, **kwargs):
            timer = cls()
            result = func(*args, **kwargs)
            elapsed = timer.end()
            print(f"Function {func.__name__} took {timer.get_readable(elapsed)} to complete.")
            return result
        return wrapper


Timer = TimidTimer.setup_timer_func(time.time, 1e9)
PerfTimer = TimidTimer.setup_timer_func(time.perf_counter, 1e9)
PerfTimerNS = TimidTimer.setup_timer_func(time.perf_counter_ns, 1)
CPUTimer = TimidTimer.setup_timer_func(time.process_time, 1e9)
CPUTimerNS = TimidTimer.setup_timer_func(time.process_time_ns, 1)
MonotonicTimer = TimidTimer.setup_timer_func(time.monotonic, 1e9)
MonotonicTimerNS = TimidTimer.setup_timer_func(time.monotonic_ns, 1)


def local_test():
    try:
        def test_timer(timer_class, description):
            timer = timer_class()
            timer.start()
            for _ in range(1000000):
                pass  # A simple loop to simulate computation
            elapsed = timer.end()
            print(f"{description} elapsed time: {timer.get_readable(elapsed)}")

        def sleep_and_measure(timer_class, description, sleep_time=1):
            """Measures how long the system sleeps using the given timer."""
            timer = timer_class()
            timer.start()
            time.sleep(sleep_time)  # Sleep for a specified time
            elapsed = timer.end()
            print(f"{description}, expected sleep: {sleep_time}s, measured time: {timer.get_readable(elapsed)}")

        timer = TimidTimer()
        for _ in range(10):
            time.sleep(1)
            timer.tock()
        print("Average 1 second sleep extra delay: ", timer.average() - timedelta(seconds=1))

        print("Starting timer tests...")
        test_timer(TimidTimer, "Timid Timer")
        test_timer(Timer, "Normal Timer")
        test_timer(PerfTimer, "Performance Timer")
        test_timer(PerfTimerNS, "Performance Timer Nanosecond")
        test_timer(CPUTimer, "CPU Timer")
        test_timer(CPUTimerNS, "CPU Timer Nanosecond")
        test_timer(MonotonicTimer, "Monotonic Timer")
        test_timer(MonotonicTimerNS, "Monotonic Timer Nanosecond")

        print("\nTesting sleep accuracy...")
        sleep_and_measure(TimidTimer, "Timid Timer")
        sleep_and_measure(Timer, "Normal Timer")
        sleep_and_measure(PerfTimer, "Performance Timer")
        sleep_and_measure(PerfTimerNS, "Performance Timer Nanosecond")
        sleep_and_measure(CPUTimer, "CPU Timer")
        sleep_and_measure(CPUTimerNS, "CPU Timer Nanosecond")
        sleep_and_measure(MonotonicTimer, "Monotonic Timer")
        sleep_and_measure(MonotonicTimerNS, "Monotonic Timer Nanosecond")
    except Exception as e:
        print(f"Exception occurred {e}.")
        return False
    print("Test completed successfully.")
    return True


if __name__ == "__main__":
    local_test()
